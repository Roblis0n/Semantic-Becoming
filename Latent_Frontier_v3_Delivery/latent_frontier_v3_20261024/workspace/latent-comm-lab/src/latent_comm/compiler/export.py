"""Deterministic human-readable IR and DOT exports without executing nodes."""
import json
from .types import CompiledIR

def ir_text(ir: CompiledIR) -> str:
    lines = [f'recipe {ir.recipe_id}', 'research_state NOT_RUN; execution LOCKED', 'passes '+', '.join(ir.pass_trace), f'budget {ir.worst_case_steps}/{ir.max_steps}']
    for n in ir.nodes:
        ins = ', '.join(f'{p}:{t.name}' for p,t in n.input_types); outs = ', '.join(f'{p}:{t.name}' for p,t in n.output_types)
        lines.append(f'{n.node_id} = {n.operation}[{n.mechanism or "builtin"}] ({ins}) -> ({outs}); effects={"".join(sorted(n.write_set))}; diff={n.differentiability}; gate={n.gate_action or "no research dispatch"}')
    for loop in ir.loops: lines.append(f'bounded_loop {loop.loop_id} max_iterations={loop.max_iterations} body={list(loop.body)} carried={list(loop.carried)}')
    lines.append('schedule '+', '.join(ir.schedule))
    return '\n'.join(lines)+'\n'

def ir_dot(ir: CompiledIR) -> str:
    q = json.dumps; lines = ['digraph ResearchIR {', '  label="NOT_RUN / policy locked";']
    for n in ir.nodes: lines.append(f'  {q(n.node_id)} [label={q(n.node_id+"\\n"+n.operation)}];')
    for a,b in ir.edges: lines.append(f'  {q(a)} -> {q(b)};')
    for loop in ir.loops:
        lines.append(f'  subgraph {q("cluster_"+loop.loop_id)} {{ label={q("bounded <= "+str(loop.max_iterations))};')
        lines.extend('    '+q(n)+';' for n in loop.body); lines.append('  }')
    return '\n'.join(lines+['}'])+'\n'
