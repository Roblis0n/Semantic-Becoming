"""Inspect future research commands; execution is forbidden in this release."""
import argparse
import json
from latent_comm.safety.policy import require_research_action
from latent_comm.core import ContractError

DESCRIPTIONS={
 'train':{'action':'model_train','required':['independent_authorization','run_id','model_manifest','data_manifest','budget','loss_and_gradient_ledger'],'source_path':'latent_comm.learning'},
 'eval':{'action':'model_eval','required':['independent_authorization','run_id','frozen_model_manifest','heldout_data_manifest','budget'],'source_path':'latent_comm.learning'},
 'benchmark':{'action':'model_benchmark','required':['independent_authorization','run_id','model_manifest','comparison_protocol','budget'],'source_path':'latent_comm.learning'},
 'forward':{'action':'model_forward','required':['independent_authorization','typed_role_batch','backend_capability_contract'],'source_path':'latent_comm.backends'},
 'generate':{'action':'model_generate','required':['independent_authorization','decoding_contract','model_manifest'],'source_path':'latent_comm.backends'},
 'initialize':{'action':'model_initialize','required':['independent_authorization','model_configuration'],'source_path':'latent_comm.safety.model_access'},
 'download':{'action':'model_download','required':['independent_authorization','model_manifest'],'source_path':'latent_comm.safety.model_access'}}

def describe(operation: str) -> dict:
    return {'operation':operation,**DESCRIPTIONS[operation],'research_state':'NOT_RUN','executable_in_current_task':False,'hard_sandbox_guaranteed':False}

def main(argv: list[str] | None=None) -> int:
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('operation',choices=tuple(DESCRIPTIONS));p.add_argument('--describe',action='store_true');p.add_argument('--run-id')
    args=p.parse_args(argv)
    if args.describe:
        print(json.dumps(describe(args.operation),indent=2));return 0
    try:require_research_action(DESCRIPTIONS[args.operation]['action'])
    except ContractError as e:
        print(json.dumps({'allowed':False,'code':e.failure.code,'reason':e.failure.message,'research_state':'NOT_RUN'}));return 2
    raise AssertionError('Current-task research gate must not return.')

if __name__=='__main__':raise SystemExit(main())
