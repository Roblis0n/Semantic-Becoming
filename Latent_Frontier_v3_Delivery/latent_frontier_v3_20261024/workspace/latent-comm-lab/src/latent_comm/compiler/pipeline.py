"""Seven auditable compilation passes. Compilation never calls implementations."""
from __future__ import annotations
from dataclasses import replace
from collections.abc import Mapping
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from latent_comm.core import ContractError, TensorSpec, VersionSet
from latent_comm.core.scopes import RESEARCH_COMPONENTS
from latent_comm.core.views import FORBIDDEN_FIELDS
from .source import SourceDocument, pointer
from .types import BoundedLoop, CompilationError, CompiledIR, Diagnostic, IRNode, TypeSpec
from .registry import builtin_registry, mechanism_registry

PASSES = ('syntax_schema', 'reference_resolution', 'type_shape_scope', 'version_migration', 'role_view_leakage', 'differentiability_boundaries', 'bounded_schedule_gate')

def topological(nodes, edges):
    names = tuple(nodes); outgoing = {n: set() for n in names}; degree = dict.fromkeys(names, 0)
    for a, b in edges:
        if a not in outgoing or b not in outgoing: raise ValueError('edge refers to missing node')
        if b not in outgoing[a]: outgoing[a].add(b); degree[b] += 1
    ready = sorted(n for n in names if degree[n] == 0); order = []
    for _ in names:
        if not ready: raise ValueError('cycle requires an explicit bounded_loop with carried state')
        n = ready.pop(0); order.append(n)
        for child in sorted(outgoing[n]):
            degree[child] -= 1
            if degree[child] == 0: ready.append(child); ready.sort()
    return tuple(order)

class Compiler:
    """One compilation owns its state; instances may be reused sequentially."""
    def __init__(self, capabilities=None):
        self.additional_capabilities = dict(capabilities or {})
        if set(self.additional_capabilities) & (mechanism_registry().keys() | builtin_registry().keys()):
            raise ValueError('registered semantic capabilities cannot be replaced')

    def compile(self, recipe: dict | str | Path, *, source='<recipe>') -> CompiledIR:
        if isinstance(recipe, Path): self.doc = SourceDocument.from_path(recipe)
        elif isinstance(recipe, str): self.doc = SourceDocument(recipe, source)
        else: self.doc = SourceDocument.from_value(recipe, source)
        self.data = deepcopy(self.doc.value); self.diags = []; self.trace = []; self.pass_no = 0
        self.caps = mechanism_registry() | builtin_registry() | self.additional_capabilities; self.nodes = []; self.objects = {}; self.producer = {}; self.loops = []; self.migration_roles = {}; self.migration_parent = {}
        for number, name in enumerate(PASSES, 1):
            self.pass_no = number
            try: getattr(self, '_' + name)()
            except CompilationError: raise
            except (KeyError, TypeError, ValueError, AttributeError, ContractError) as error:
                self.error('InvalidSchema', str(error), '')
            if any(d.severity == 'error' for d in self.diags): raise CompilationError(tuple(self.diags))
            self.trace.append(name)
        return CompiledIR(self.data['id'], tuple(self.nodes), tuple(sorted(self.objects.items())), tuple(sorted(self.edges)), self.schedule, tuple(self.loops), tuple(self.diags), tuple(self.trace), self.cost, self.max_steps, hashlib.sha256(self.doc.text.encode()).hexdigest(), deepcopy(self.data.get('parameters',{})), deepcopy(self.data.get('runtime_budget',{})))

    def error(self, code, message, path, severity='error'):
        self.diags.append(Diagnostic(code, message, self.doc.location(path), self.pass_no, severity))
    def require(self, condition, code, message, path):
        if not condition: self.error(code, message, path)
        return condition
    def _syntax_schema(self):
        d = self.data
        self.require(d.get('schema_version') == 3, 'SchemaVersion', 'schema_version must be 3', '/schema_version')
        self.require(isinstance(d.get('id'), str) and bool(d.get('id')), 'RecipeID', 'nonempty recipe ID required', '/id')
        self.require(d.get('research_execution_authorized', False) is False, 'ResearchForbidden', 'recipe cannot grant research execution', '/research_execution_authorized')
        self.require(d.get('design_only', True) is True, 'ResearchForbidden', 'only design compilation is allowed', '/design_only')
        self.require(d.get('kind') != 'task_graph' and 'tasks' not in d, 'PlanIsNotResearchIR', 'authoring task DAG is not a research recipe', '')
        self.high_level = 'nodes' not in d
        if self.high_level:
            mechanisms = d.get('mechanisms', [])
            if not self.require(isinstance(mechanisms, list) and 0 < len(mechanisms) <= 64, 'MechanismList', 'declare 1..64 mechanism nodes', '/mechanisms'): return
            d['nodes'], d['objects'] = [], {}
            for i, key in enumerate(mechanisms):
                if key not in self.caps or not key.startswith('H'):
                    self.error('UnknownMechanism', str(key), f'/mechanisms/{i}'); continue
                cap = self.caps[key]; node = {'id': key.lower(), 'mechanism': key, 'inputs': {}, 'outputs': {}, 'role': 'public'}
                for direction, ports in [('inputs', cap.inputs), ('outputs', cap.outputs)]:
                    for port, name in ports:
                        ref = key.lower() + ':' + port
                        node[direction][port] = ref
                        d['objects'][ref] = {'type': name, 'versions': {'schema': '3'}, 'bound': False}
                d['nodes'].append(node)
            self.error('BindingsRequired', 'high-level recipe lowered to typed declarations; external objects, semantic versions, and composition edges remain explicitly unbound', '/mechanisms', 'warning')
        self.require(isinstance(d.get('nodes'), list) and 0 < len(d['nodes']) <= 128, 'NodeCount', 'declare 1..128 nodes', '/nodes')
        self.require(isinstance(d.get('objects', {}), dict), 'ObjectSchema', 'objects must be a mapping', '/objects')
        for i, n in enumerate(d.get('nodes', [])):
            path = f'/nodes/{i}'
            if not self.require(isinstance(n, dict), 'NodeSchema', 'node must be an object', path): continue
            self.require(isinstance(n.get('id'), str) and bool(n['id']), 'NodeID', 'node ID required', path + '/id')
            key = n.get('mechanism', n.get('operation'))
            self.require(isinstance(key, str) and key in self.caps, 'UnknownCapability', str(key), path)
            for field in ('inputs', 'outputs'):
                value = n.get(field)
                self.require(isinstance(value, dict) and all(isinstance(k,str) and isinstance(v,str) for k,v in value.items()), 'PortSchema', field+' must map ports to object IDs', path+'/'+field)
        for field in ('bounded_loops','migrations'):
            self.require(isinstance(d.get(field, []), list), 'InvalidSchema', field+' must be a list', '/'+field)

    def _reference_resolution(self):
        self.raw_nodes = {n['id']: n for n in self.data['nodes']}
        self.require(len(self.raw_nodes) == len(self.data['nodes']), 'DuplicateNode', 'node IDs must be unique', '/nodes')
        object_defs = self.data.get('objects', {})
        for i, n in enumerate(self.data['nodes']):
            cap = self.caps[n.get('mechanism', n.get('operation'))]; path = f'/nodes/{i}'
            for field, signatures in [('inputs', cap.inputs), ('outputs', cap.outputs)]:
                self.require(set(n[field]) == {p for p,_ in signatures}, 'PortMismatch', f'{field} expected {list(signatures)}', path+'/'+field)
                for port, ref in n[field].items():
                    self.require(ref in object_defs, 'UnboundReference', ref, path+'/'+field+'/'+port)
                    if field == 'outputs':
                        self.require(ref not in self.producer, 'MultipleWriters', ref, path+'/outputs/'+port)
                        self.producer[ref] = n['id']
        for i,n in enumerate(self.data['nodes']):
            for dep in n.get('depends_on',[]): self.require(dep in self.raw_nodes, 'UnboundReference', dep, f'/nodes/{i}/depends_on')
        def embedded_refs(value):
            if isinstance(value,dict):
                if '$ref' in value:
                    if not isinstance(value['$ref'],str): self.error('ReferenceSchema','$ref must be an object identity','/objects')
                    else: yield value['$ref']
                for child in value.values(): yield from embedded_refs(child)
            elif isinstance(value,list):
                for child in value:yield from embedded_refs(child)
        for ref, spec in object_defs.items():
            if not self.require(isinstance(spec, dict), 'ObjectSchema', 'object declaration must be a mapping', '/objects/'+ref): continue
            refs=set(embedded_refs(spec.get('value')))
            self.require(refs <= set(spec.get('dependencies',[])), 'UndeclaredReference', 'embedded $ref must be declared as a dependency', '/objects/'+ref+'/value')
            for dependency in spec.get('dependencies', []): self.require(dependency in object_defs, 'UnboundReference', dependency, '/objects/'+ref+'/dependencies')
        if any(d.severity == 'error' for d in self.diags): return
        deps = {(dep, ref) for ref, spec in object_defs.items() for dep in spec.get('dependencies', [])}
        try: topological(object_defs, deps)
        except ValueError as error: self.error('ObjectDependencyCycle', str(error), '/objects')

    def _type_shape_scope(self):
        allowed = frozenset(self.data.get('scope', sorted(RESEARCH_COMPONENTS)))
        self.require(allowed <= RESEARCH_COMPONENTS, 'ScopeViolation', 'scope cannot include host/control-plane effects', '/scope')
        for ref, obj in self.data.get('objects', {}).items():
            path = '/objects/'+ref
            if not self.require(isinstance(obj.get('type'), str) and bool(obj['type']), 'ObjectType', 'object type required', path+'/type'): continue
            try:
                tensor = obj.get('tensor')
                if tensor is not None:
                    tensor = TensorSpec(axes=tuple(tensor['axes']), shape=tuple(tensor['shape']), dtype=tensor['dtype'], semantic_role=tensor['semantic_role'], trainable_owner=tensor.get('trainable_owner'), device_policy=tensor.get('device_policy','unallocated'), mask_axes=tuple(tensor.get('mask_axes',[])))
                spec = TypeSpec(obj['type'], VersionSet(**obj.get('versions', {})), obj.get('visibility', 'public'), tensor, tuple(obj.get('fields', [])), tuple(obj.get('dependencies', [])), frozenset(obj.get('scope', allowed)), obj.get('bound', True))
                self.require(spec.visibility in {'public','sender','receiver','supervision'}, 'RoleVisibility', 'unknown visibility', path+'/visibility')
                self.require(spec.scope <= allowed, 'ScopeViolation', 'object scope exceeds recipe', path+'/scope')
                self.objects[ref] = spec
            except (ContractError, KeyError, TypeError) as error: self.error('TypeContract', str(error), path)
        if any(d.severity == 'error' for d in self.diags): return
        for i,n in enumerate(self.data['nodes']):
            path = f'/nodes/{i}'; cap = self.caps[n.get('mechanism', n.get('operation'))]
            writes = frozenset(n.get('write_set', cap.write_set)); reads = frozenset(n.get('read_set', cap.read_set))
            self.require(writes == cap.write_set and writes <= allowed, 'ScopeViolation', 'write set must include exactly the capability effects and stay within scope', path+'/write_set')
            self.require(cap.read_set <= reads and reads <= RESEARCH_COMPONENTS, 'ScopeViolation', 'read set cannot omit capability dependencies or include host state', path+'/read_set')
            for field, signatures in [('inputs', cap.inputs), ('outputs', cap.outputs)]:
                for port,name in signatures:
                    spec = self.objects[n[field][port]]
                    self.require(spec.name == name, 'TypeMismatch', f'{port}: expected {name}, found {spec.name}', path+'/'+field+'/'+port)
                    if field == 'inputs':
                        self.require(writes <= spec.scope, 'ScopeViolation', 'effect exceeds input object scope', path+'/inputs/'+port)
                        wanted = n.get('input_tensors', {}).get(port)
                        if wanted is not None:
                            self.require(spec.tensor is not None, 'ShapeMismatch', 'tensor contract required', path+'/input_tensors/'+port)
                            if spec.tensor is not None:
                                for axis in ('axes','shape','dtype','mask_axes','semantic_role'):
                                    if axis in wanted:
                                        val = tuple(wanted[axis]) if axis in {'axes','shape','mask_axes'} else wanted[axis]
                                        self.require(getattr(spec.tensor,axis) == val, 'ShapeMismatch', f'{port}.{axis} does not match', path+'/input_tensors/'+port+'/'+axis)
            cost = n.get('budget_cost', 1)
            self.require(type(cost) is int and 1 <= cost <= 128, 'BudgetCost', 'cost must be 1..128', path+'/budget_cost')
            self.nodes.append(IRNode(n['id'], cap.operation, n.get('mechanism'), tuple(n['inputs'].items()), tuple(n['outputs'].items()), tuple((p,self.objects[r]) for p,r in n['inputs'].items()), tuple((p,self.objects[r]) for p,r in n['outputs'].items()), reads, writes, cap.differentiability, cap.determinism, cost, cap.required_capabilities, cap.implementation, self.doc.location(path)))

    def _version_migration(self):
        for ref,spec in self.objects.items():
            for dependency in spec.dependencies:
                dep=self.objects[dependency]
                axes=tuple(a for a,v in dep.versions.as_dict().items() if v is not None)
                try: compatible=dep.versions.matches(spec.versions,axes)
                except ContractError: compatible=False
                self.require(compatible,'DependencyVersionMismatch',f'{ref} depends on incompatible versions of {dependency}','/objects/'+ref+'/dependencies')
        migrations = self.data.get('migrations', []); by_id = {m['id']: m for m in migrations}
        self.require(len(by_id) == len(migrations), 'DuplicateMigration', 'migration IDs must be unique', '/migrations')
        try: order = topological(by_id, [(d,m['id']) for m in migrations for d in m.get('depends_on',[])])
        except ValueError as error: self.error('MigrationConflict', str(error), '/migrations'); return
        transitions = [(m.get('object'),m.get('axis'),m.get('from')) for m in migrations]
        self.require(len(set(transitions)) == len(transitions), 'AmbiguousMigration', 'a source/axis transition must be uniquely declared', '/migrations')
        for i,m in enumerate(migrations):
            self.require(m.get('axis') in VersionSet.__dataclass_fields__ and isinstance(m.get('from'),str) and isinstance(m.get('to'),str) and m['from'] != m['to'] and isinstance(m.get('implementation'),str) and bool(m['implementation']), 'MigrationSchema', 'explicit axis, unequal source/target and implementation required', f'/migrations/{i}')
        if any(d.severity == 'error' for d in self.diags): return
        expanded = []
        for index, node in enumerate(self.nodes):
            raw = self.raw_nodes[node.node_id]; cap = self.caps[raw.get('mechanism',raw.get('operation'))]; inputs = []
            for port, ref in node.inputs:
                spec = self.objects[ref]; targets = raw.get('required_versions', {})
                for axis in set(cap.required_version_axes) | set(targets):
                    self.require(axis in VersionSet.__dataclass_fields__, 'VersionAxis', axis, f'/nodes/{index}/required_versions')
                    if axis in VersionSet.__dataclass_fields__ and getattr(spec.versions,axis) is None and spec.bound:
                        self.error('MissingVersion', f'{ref} lacks required {axis}', f'/nodes/{index}/inputs/{port}')
                current = spec.versions.as_dict(); applied = set(); original = ref
                for mid in order:
                    migration = by_id[mid]; axis = migration['axis']
                    if migration.get('object',original) != original or axis not in targets or current[axis] == targets[axis]: continue
                    if migration['from'] != current[axis]: continue
                    if not set(migration.get('depends_on',[])) <= applied:
                        self.error('MigrationDependency', 'dependency not applied to this object', '/migrations'); continue
                    current[axis] = migration['to']; changed = replace(spec, versions=VersionSet(**current), dependencies=(ref,))
                    new_ref = ref + '@' + mid; mid_node = 'migrate:'+node.node_id+':'+port+':'+mid
                    if new_ref in self.objects: new_ref += ':'+node.node_id+':'+port
                    self.objects[new_ref] = changed; self.producer[new_ref] = mid_node
                    self.migration_roles[mid_node] = raw.get('role','public'); self.migration_parent[mid_node] = node.node_id
                    expanded.append(IRNode(mid_node, 'MigrateObject', None, (('in0',ref),), (('out0',new_ref),), (('in0',spec),), (('out0',changed),), node.read_set, node.write_set, 'discrete', 'deterministic_given_inputs', 1, ('migration:'+mid,), migration['implementation'], self.doc.location('/migrations/'+str(migrations.index(migration)))))
                    ref, spec = new_ref, changed; applied.add(mid)
                for axis,target in targets.items():
                    if axis in current: self.require(current[axis] == target, 'MigrationRequired', f'{original} cannot reach {axis}={target}', f'/nodes/{index}/required_versions/{axis}')
                inputs.append((port,ref))
            expanded.append(replace(node, inputs=tuple(inputs), input_types=tuple((p,self.objects[r]) for p,r in inputs)))
        self.nodes = expanded

    def _role_view_leakage(self):
        def fields(value):
            if isinstance(value, Mapping):
                for k,v in value.items():
                    if k in FORBIDDEN_FIELDS: yield k
                    yield from fields(v)
            elif isinstance(value,(tuple,list)):
                for v in value: yield from fields(v)
        taint = {r: ({s.visibility} if s.visibility != 'public' else set()) for r,s in self.objects.items()}
        forbidden = {r: set(s.fields)&FORBIDDEN_FIELDS for r,s in self.objects.items()}
        for ref,spec in self.objects.items():
            forbidden[ref].update(fields(self.data.get('objects',{}).get(ref,{}).get('value')))
            if spec.tensor and spec.tensor.semantic_role in {'supervision','label','hidden_solution'}: forbidden[ref].add(spec.tensor.semantic_role)
        # Fixed point propagates dependency and producer taint; bounded by object count.
        for _ in range(len(self.objects) + 1):
            changed = False
            for ref,spec in self.objects.items():
                for dependency in spec.dependencies:
                    before = (len(taint[ref]),len(forbidden[ref])); taint[ref] |= taint[dependency]; forbidden[ref] |= forbidden[dependency]
                    changed |= before != (len(taint[ref]),len(forbidden[ref]))
            for node in self.nodes:
                for _,out in node.outputs:
                    for _,ref in node.inputs:
                        before = (len(taint[out]),len(forbidden[out])); taint[out] |= taint[ref]; forbidden[out] |= forbidden[ref]
                        changed |= before != (len(taint[out]),len(forbidden[out]))
            if not changed: break
        for index,node in enumerate(self.nodes):
            raw = self.raw_nodes.get(node.node_id, {}); role = raw.get('role', self.migration_roles.get(node.node_id,'public'))
            self.require(role in {'public','sender','receiver','supervision'}, 'RoleVisibility', role, f'/nodes/{index}/role')
            if role != 'supervision':
                for port,ref in node.inputs:
                    self.require(not (taint[ref]-{role}) and not forbidden[ref], 'RoleLeakage', f'{ref} carries roles={sorted(taint[ref])}, forbidden={sorted(forbidden[ref])}', node.location.path+'/inputs/'+port)
            if node.operation == 'EncodeView':
                self.require(role in {'sender','receiver'}, 'RoleViewRequired', 'EncodeView requires a physical sender/receiver view', node.location.path+'/role')
            for field in ('public_task','features'):
                bad = set(fields(raw.get(field)))
                self.require(not bad, 'RoleLeakage', str(sorted(bad)), node.location.path+'/'+field)

    def _differentiability_boundaries(self):
        updated = []
        for node in self.nodes:
            raw = self.raw_nodes.get(node.node_id, {}); declarations = raw.get('gradient_edges', {}); edges = []
            self.require(set(declarations) <= dict(node.inputs).keys(), 'GradientPort', 'gradient declaration names an unknown input', node.location.path+'/gradient_edges')
            for port,_ in node.inputs:
                mode = declarations.get(port, 'differentiable' if node.differentiability == 'differentiable' else 'stop')
                self.require(mode in {'differentiable','stop','straight_through','score_function','enumeration'}, 'GradientEstimator', str(mode), node.location.path+'/gradient_edges/'+port)
                self.require(not (node.differentiability in {'discrete','exact'} and mode == 'differentiable'), 'DiscreteGradient', 'exact/discrete operations require an explicit estimator or stop edge', node.location.path+'/gradient_edges/'+port)
                if port in raw.get('required_input_gradients',[]):
                    self.require(mode != 'stop', 'GradientDisconnected', 'required input gradient is stopped; frozen weights do not authorize this', node.location.path+'/gradient_edges/'+port)
                edges.append((port,mode))
            action = raw.get('research_action')
            if action is not None:
                self.require(action in {'model_download','model_initialize','model_forward','model_train','model_eval','model_api'}, 'ResearchAction', str(action), node.location.path+'/research_action')
            updated.append(replace(node, gradient_edges=tuple(edges), gate_action=action))
        self.nodes = updated

    def _bounded_schedule_gate(self):
        budget = self.data.get('runtime_budget', {}); self.max_steps = budget.get('max_steps',128)
        self.require(type(self.max_steps) is int and self.max_steps > 0, 'BudgetLimit', 'max_steps must be an explicit positive integer; compilation does not execute it', '/runtime_budget/max_steps')
        for name,cap in [('max_branches',64),('max_cases',64),('max_dimension',64)]:
            value = budget.get(name,cap)
            self.require(type(value) is int and value > 0, 'BudgetLimit', f'{name} must be a positive finite integer', '/runtime_budget/'+name)
        names = {n.node_id for n in self.nodes}; self.edges = {(self.producer[ref],node.node_id) for node in self.nodes for _,ref in node.inputs if ref in self.producer}
        self.edges |= {(dep,n['id']) for n in self.data['nodes'] for dep in n.get('depends_on',[])}
        membership = {}; self.loops = []
        for i,loop in enumerate(self.data.get('bounded_loops', [])):
            path = f'/bounded_loops/{i}'; lid = loop.get('id'); body = tuple(loop.get('body',[])); body += tuple(n for n,parent in self.migration_parent.items() if parent in body); limit = loop.get('max_iterations')
            if not self.require(isinstance(lid,str) and lid not in names and lid not in {l.loop_id for l in self.loops}, 'LoopID', 'loop ID must be unique', path+'/id'): continue
            self.require(bool(body) and len(set(body)) == len(body) and set(body) <= names, 'LoopBody', 'body must name distinct IR nodes', path+'/body')
            self.require(type(limit) is int and limit > 0, 'UnboundedLoop', 'max_iterations must be an explicit positive finite integer', path+'/max_iterations')
            for n in body:
                self.require(n not in membership, 'NestedLoopAmbiguous', 'overlapping/nested loop declarations are rejected; flatten to a single bounded budget', path+'/body'); membership[n] = lid
            carried = tuple(tuple(pair) for pair in loop.get('carried',[]))
            for pair in carried:
                if not self.require(len(pair)==2 and all(ref in self.objects for ref in pair), 'LoopCarry', 'carry must map source output to existing next-iteration input', path+'/carried'): continue
                src,dst = pair
                self.require(self.producer.get(src) in body and dst not in self.producer, 'LoopCarry', 'carry source must be in body, destination an external loop input', path+'/carried')
                self.require(any(dst in dict(n.inputs).values() for n in self.nodes if n.node_id in body), 'LoopCarry', 'carry destination must be read by body', path+'/carried')
                self.require(self.objects[src] == self.objects[dst], 'LoopCarryType', 'carried types, versions, visibility and scope must match exactly', path+'/carried')
            self.loops.append(BoundedLoop(lid,body,limit,carried,self.doc.location(path)))
        if any(d.severity == 'error' for d in self.diags): return
        try:
            full_order = topological([n.node_id for n in self.nodes], self.edges)
            groups = tuple(dict.fromkeys(membership.get(n,n) for n in full_order))
            grouped_edges = {(membership.get(a,a),membership.get(b,b)) for a,b in self.edges if membership.get(a,a) != membership.get(b,b)}
            self.schedule = topological(groups, grouped_edges)
            self.loops = [replace(loop, body=tuple(n for n in full_order if n in loop.body)) for loop in self.loops]
        except ValueError as error: self.error('ScheduleCycle', str(error), '/nodes'); return
        limits = {l.loop_id:l.max_iterations for l in self.loops}
        self.cost = sum(n.budget_cost * limits.get(membership.get(n.node_id),1) for n in self.nodes)
        self.require(self.cost <= self.max_steps, 'BudgetExceeded', f'worst-case {self.cost} exceeds max_steps={self.max_steps}', '/runtime_budget')


def compile_recipe(recipe: dict | str | Path, *, source='<recipe>') -> CompiledIR:
    return Compiler().compile(recipe, source=source)

def request_research_execution(ir: CompiledIR, action: str = 'model_forward') -> None:
    """A declarative IR never grants authority. The immutable policy always denies."""
    from latent_comm.safety.policy import require_research_action
    require_research_action(action)
    raise ContractError('ResearchForbidden', 'compiled design is not an executable model binding')
