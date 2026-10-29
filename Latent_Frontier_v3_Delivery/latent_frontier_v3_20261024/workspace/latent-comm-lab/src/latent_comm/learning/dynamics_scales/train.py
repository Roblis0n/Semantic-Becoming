"""Policy-locked future training command; --describe is metadata-only."""
import argparse
import hashlib
import json
from pathlib import Path
from latent_comm.safety.policy import require_research_action

def describe():
    return {'stage': 'L06', 'mechanisms': ['H28', 'H33', 'H34', 'H35'], 'variants': ['reciprocal', 'boundary', 'scales', 'bifurcation'], 'research_state': 'NOT_RUN', 'model_bindings': 'UNBOUND', 'execution_authorized': False, 'source_complete': True}

def run(config,root,*,resume=None):
    require_research_action('model_train')
    from latent_comm.core import VersionSet
    from latent_comm.learning.engine import train
    from latent_comm.learning.source import JsonlSource
    from latent_comm.learning.contracts import Phase,TrainingPlan
    from . import build_stage
    stage=build_stage(config['variant'],VersionSet(**config.get('variant_versions',{}).get(config['variant'],config['versions'])),device=config['device'],**config.get('dimensions',{}))
    manifest=json.loads((root/config['data_manifest']).read_text(encoding='utf-8'))
    source=JsonlSource(root,manifest,config['batch_size'])
    phases=tuple(Phase(p['name'],tuple(p['parameter_owners']),tuple(p['loss_weights'].items()),p['optimizer_steps'],p['learning_rate'],p.get('weight_decay',0.)) for p in config['phases'][config['variant']])
    digest=hashlib.sha256(json.dumps(config,sort_keys=True,allow_nan=False).encode()).hexdigest()
    plan=TrainingPlan(config['run_id'],phases,config['accumulation'],config['maximum_unroll'],config['gradient_clip'],config['checkpoint_interval'],config['model_manifest_digest'],source.identity,digest)
    return train(stage,source,plan,root,resume=resume)

def main(argv=None):
    parser=argparse.ArgumentParser();parser.add_argument('--describe',action='store_true');parser.add_argument('--config');parser.add_argument('--root',default='.');parser.add_argument('--resume-record');parser.add_argument('--resume-sha256')
    args=parser.parse_args(argv)
    if args.describe:print(json.dumps(describe(),ensure_ascii=False,indent=2));return 0
    require_research_action('model_train')
    if bool(args.resume_record)!=bool(args.resume_sha256):parser.error('both resume record and digest are required')
    resume={'record':args.resume_record,'sha256':args.resume_sha256} if args.resume_record else None
    return run(json.loads(Path(args.config).read_text(encoding='utf-8')),Path(args.root),resume=resume)
if __name__=='__main__':main()
