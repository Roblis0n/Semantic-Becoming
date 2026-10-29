"""Describe safely; construction and training remain hard-locked in this task."""
import argparse
import json
from pathlib import Path
from latent_comm.safety.policy import require_research_action

def describe():
    return {'stage':'L03','mechanisms':['H25','H26'],'variants':['gauge','cross_map','restrictions'],'research_state':'NOT_RUN','model_bindings':'UNBOUND','execution_authorized':False,'source_complete':True,'gradient_boundary':'Frozen base parameters do not imply no_grad on receiver inputs. Checkpoints require recomputation.','objectives':'Explicit weighted phases; covariance/effect or section/overlap/obstruction. No shared empirical score.'}

def run(config,root,*,resume=None):
    require_research_action('model_train')
    import hashlib
    from latent_comm.core import VersionSet
    from latent_comm.learning.engine import train
    from latent_comm.learning.source import JsonlSource
    from latent_comm.learning.contracts import Phase,TrainingPlan
    from . import build_stage
    stage=build_stage(config['variant'],VersionSet(**config['versions']),**config['dimensions'],device=config['device'])
    manifest=json.loads((root/config['data_manifest']).read_text(encoding='utf-8'))
    source=JsonlSource(root,manifest,config['batch_size'])
    phases=tuple(Phase(p['name'],tuple(p['parameter_owners']),tuple((k,v) for k,v in p['loss_weights'].items()),p['optimizer_steps'],p['learning_rate'],p.get('weight_decay',0.)) for p in config['phases'][config['variant']])
    digest=hashlib.sha256(json.dumps(config,sort_keys=True,allow_nan=False).encode()).hexdigest()
    plan=TrainingPlan(config['run_id'],phases,config['accumulation'],config['maximum_unroll'],config['gradient_clip'],config['checkpoint_interval'],config['model_manifest_digest'],source.identity,digest)
    return train(stage,source,plan,root,resume=resume)

def main(argv=None):
    p=argparse.ArgumentParser();p.add_argument('--describe',action='store_true');p.add_argument('--config');p.add_argument('--root',default='.');p.add_argument('--resume-record');p.add_argument('--resume-sha256')
    args=p.parse_args(argv)
    if args.describe:print(json.dumps(describe(),ensure_ascii=False,indent=2));return 0
    require_research_action('model_train')
    if bool(args.resume_record)!=bool(args.resume_sha256):p.error('both resume record and digest are required')
    resume={'record':args.resume_record,'sha256':args.resume_sha256} if args.resume_record else None
    return run(json.loads(Path(args.config).read_text(encoding='utf-8')),Path(args.root),resume=resume)
if __name__=='__main__':main()
