"""lcomm: inspect source contracts without initializing research models."""
import argparse
import importlib
import json
from pathlib import Path
import sys
from latent_comm import __version__
HORIZONS=('identity_continuum','plural_worlds','problem_invention','plasticity_network','language_ecology','multiscale_cognition','trajectory_semantics','discovery_continuations','shared_dreams','cognitive_commons','concept_lifecycle','semantic_compiler')
def design(argv):
    from latent_comm.compiler.registry import mechanism_registry
    from latent_comm.compositions.contracts import _plain
    parser=argparse.ArgumentParser(prog='lcomm design');group=parser.add_mutually_exclusive_group();group.add_argument('--mechanism',choices=[f'H{i:02}' for i in range(1,49)]);group.add_argument('--composition',choices=[f'C{i:02}' for i in range(1,21)]);group.add_argument('--horizon',choices=[f'X{i:02}' for i in range(1,13)]);args=parser.parse_args(argv)
    if args.mechanism:payload=_plain(mechanism_registry()[args.mechanism])
    elif args.composition:
        module=importlib.import_module('latent_comm.compositions.'+args.composition.lower());payload=module.describe_training()
    elif args.horizon:
        module=importlib.import_module('latent_comm.horizon.'+HORIZONS[int(args.horizon[1:])-1]);payload={'horizon':args.horizon,'assumptions':_plain(module.ASSUMPTIONS),'finite_entry':module.__name__+'.run','not_executed':True}
    else:payload={'project':'Semantic Becoming','mechanisms':tuple(mechanism_registry()),'compositions':[f'C{i:02}' for i in range(1,21)],'horizons':[f'X{i:02}' for i in range(1,13)],'interpretation':'source contracts, not model results'}
    print(json.dumps({'research_state':'NOT_RUN','execution_authorized':False,'design':payload},ensure_ascii=False,indent=2,allow_nan=False));return 0

def inspect_json(argv):
    from latent_comm.compiler.source import SourceDocument
    from latent_comm.compiler import CompilationError
    parser=argparse.ArgumentParser(prog='lcomm inspect');parser.add_argument('path',type=Path);args=parser.parse_args(argv)
    try:document=SourceDocument.from_path(args.path)
    except (CompilationError,OSError) as error:print(str(error),file=sys.stderr);return 2
    value=document.value;summary={'source':str(args.path),'strict_json_object':True,'fields':sorted(value),'declared_versions':value.get('versions'),'research_state':'NOT_RUN','execution_performed':False}
    print(json.dumps(summary,ensure_ascii=False,indent=2,allow_nan=False));return 0

def main(argv=None):
    argv=list(sys.argv[1:] if argv is None else argv)
    parser=argparse.ArgumentParser(prog='lcomm',description=__doc__);parser.add_argument('--version',action='version',version=__version__);parser.add_argument('command',choices=('design','compile','inspect','research'))
    if not argv or argv[0] in ('-h','--help','--version'):parser.parse_args(argv);return 0
    command=argv[0]
    if command=='design':return design(argv[1:])
    if command=='inspect':return inspect_json(argv[1:])
    if command=='compile':
        from .compile import main as compile_main
        return compile_main(argv[1:])
    if command=='research':
        from .research import main as research_main
        return research_main(argv[1:])
    parser.parse_args(argv);return 2
if __name__=='__main__':raise SystemExit(main())
