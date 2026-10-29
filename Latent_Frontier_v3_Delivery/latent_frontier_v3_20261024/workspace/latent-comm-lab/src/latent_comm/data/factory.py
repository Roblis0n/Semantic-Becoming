"""Full future sampling/resume path; only explicit single fixtures are allowed now."""
from dataclasses import dataclass,asdict
import hashlib
import json
from pathlib import Path
from collections.abc import Callable,Iterator
from latent_comm.core import ContractError,ErrorCode,VersionSet
from latent_comm.packets.storage import save_finite_json,load_finite_json
from latent_comm.safety.policy import require_research_action
from .records import WorldRecord,SplitProvenance,SupervisionView,ProjectionContract
from .splits import StructureSignature,SplitManifest

@dataclass(frozen=True)
class FactoryCursor:
    manifest_digest: str
    template_index: int
    instance_index: int
    emitted: int
    generator_version: str

class WorldFactory:
    def __init__(self,signature: StructureSignature,projection: ProjectionContract) -> None:
        self.signature=signature;self.projection=projection
    def fixture(self,public_and_private_fields: dict,targets: dict, *, versions: VersionSet,evidence: tuple[str,...]=(),fixture_name: str='declared') -> WorldRecord:
        sender,receiver=self.projection.project(public_and_private_fields,versions)
        sig=self.signature.digest
        identifier='fixture:'+hashlib.sha256((sig+':'+fixture_name).encode()).hexdigest()[:16]
        provenance=SplitProvenance('math_fixture',sig,'fixture-not-training-data')
        return WorldRecord(identifier,sender,receiver,SupervisionView(targets,{},'finite_program'),sig,self.signature.generator_version,provenance,evidence,'math_fixture',True)

def generate_dataset(manifest: SplitManifest,build_instance: Callable[[StructureSignature,int,SplitProvenance],WorldRecord], *, instances_per_template: int,seed: int,cursor: FactoryCursor | None=None) -> Iterator[WorldRecord]:
    require_research_action('research_execution')
    if type(instances_per_template) is not int or instances_per_template<=0:raise ContractError(ErrorCode.OUT_OF_DOMAIN,'instance count required')
    if cursor and cursor.manifest_digest!=manifest.digest:raise ContractError(ErrorCode.CONFLICT,'resume manifest changed')
    start_template=cursor.template_index if cursor else 0;start_instance=cursor.instance_index if cursor else 0
    for ti,assignment in enumerate(manifest.assignments):
        if ti<start_template:continue
        provenance=manifest.for_template(assignment.signature)
        for ii in range(start_instance if ti==start_template else 0,instances_per_template):
            instance_seed=int(hashlib.sha256(f'{seed}:{assignment.signature.digest}:{ii}'.encode()).hexdigest(),16)%(2**63)
            record=build_instance(assignment.signature,instance_seed,provenance)
            if record.split_provenance!=provenance or record.purpose=='math_fixture':raise ContractError(ErrorCode.CONFLICT,'generator must preserve partition and use explicit research-data purpose')
            yield record

def save_cursor(root: Path,name: str,cursor: FactoryCursor) -> str:
    return save_finite_json(root,name,asdict(cursor))

def load_cursor(root: Path,name: str,digest: str,manifest: SplitManifest) -> FactoryCursor:
    cursor=FactoryCursor(**load_finite_json(root,name,digest))
    if cursor.manifest_digest!=manifest.digest:raise ContractError(ErrorCode.CONFLICT,'cursor manifest mismatch')
    return cursor
