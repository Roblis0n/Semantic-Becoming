"""X05: finite joint ontology/ISA/world/population version scheduling."""
from dataclasses import dataclass
from latent_comm.core import ContractError,VersionSet
from latent_comm.compositions.c16 import CounterfactualEcologyInput,SyntheticLineageArchive
from latent_comm.mechanisms.h27_ontology.types import OntologySnapshot,OntologyDelta,ConceptDefinition,Predicate
from latent_comm.mechanisms.h40_instruction_set.types import ISARevision,MacroDefinition,Expr
from .contracts import bounded_horizon,assumptions
ASSUMPTIONS=assumptions('An explicit synthetic world mutation request, ontology and versioned protocol seed exist.','New conceptual and instruction definitions must be bound to generated task semantics and retain synthetic lineage.','A finite generation schedule registers four separate version axes with dependency invalidation.','Future models may co-adapt to these changing languages without an a priori fixed vocabulary; NOT_RUN.')
@dataclass(frozen=True)
class EcologyRequest:
    generations: tuple[CounterfactualEcologyInput,...]
    ontology: OntologySnapshot
    initial_isa: ISARevision
    versions: VersionSet
@dataclass(frozen=True)
class EcologyGeneration:
    generation: int
    world_archive: SyntheticLineageArchive
    ontology_delta: OntologyDelta
    isa: ISARevision
    version_bindings: tuple[tuple[str,str],...]
    migration_edges: tuple[tuple[str,str,str],...]
@dataclass(frozen=True)
class LanguageEcologyRecord:
    generations: tuple[EcologyGeneration,...]
    pending_generation: int | None
    status: str
@bounded_horizon('X05',ASSUMPTIONS)
def run(request,meter):
    from latent_comm.compositions.c16 import run_reference
    from latent_comm.mechanisms.h27_ontology.reference import revise_ontology
    from latent_comm.mechanisms.h40_instruction_set.reference import lower
    q=request
    if not 1<=len(q.generations)<=2 or q.ontology.version!=q.versions.ontology or q.initial_isa.version!=q.versions.isa:raise ContractError('VersionMismatch','bounded scheduler needs initial ontology/ISA bindings')
    ontology=q.ontology;isa=q.initial_isa;history=[]
    for index,seed in enumerate(q.generations):
        meter.consume(steps=1)
        if seed.versions!=q.versions:raise ContractError('VersionMismatch','each requested world proposal declares its original source context; it is not silently reinterpreted')
        result=run_reference(seed)
        if result.status!='Complete':return LanguageEcologyRecord(tuple(history),index,'PartialGenerationBudget'),('Earlier generations retained; the incomplete proposal must not become a new version.',)
        archive=result.value;evidence=archive.evidence.evidence_id;tasks=() if archive.population is None else archive.population.tasks
        additions=[];macros=list(isa.macros)
        for j,task in enumerate(tasks[:4]):
            meter.consume(steps=1)
            name='g'+str(index+1)+'_threshold_'+str(j)
            additions.append(ConceptDefinition(name,Predicate('le','x',task.threshold),(),(evidence,),('x',)))
            # A sign-reversed offset is named as such, never advertised as a
            # mathematical inverse of an arbitrary conditional program.
            if not task.conditional:
                body=Expr('add',(Expr('var',name='x'),Expr('const',value=-task.offset if task.inverse else task.offset)))
                macros.append(MacroDefinition('g'+str(index+1)+'_task_'+str(j),('x',),body,('scalar',)))
        delta=revise_ontology(ontology,'ontology:g'+str(index+1),tuple(additions));next_isa=ISARevision('isa:g'+str(index+1),tuple(macros))
        for macro in next_isa.macros[len(isa.macros):]:lower(Expr('call',(Expr('const',value=0.),),name=macro.name),next_isa)
        population_version='population:g'+str(index+1)
        bindings=(('ontology',delta.after.version),('isa',next_isa.version),('world',archive.world.kernel.version),('population',population_version))
        edges=((ontology.version,delta.after.version,'versioned concept readers'),(isa.version,next_isa.version,'old-reader lowering to immutable base'),(seed.versions.world,archive.world.kernel.version,'synthetic world lineage'),(population_version,next_isa.version,'protocol compilation depends on ISA'))
        history.append(EcologyGeneration(index+1,archive,delta,next_isa,bindings,edges));ontology=delta.after;isa=next_isa
    return LanguageEcologyRecord(tuple(history),None,'FiniteGenerationsComplete'),('Static expressibility is not model competence.','Generations are explicitly budgeted; no unbounded self-evolution loop or control-plane rewrite.')
