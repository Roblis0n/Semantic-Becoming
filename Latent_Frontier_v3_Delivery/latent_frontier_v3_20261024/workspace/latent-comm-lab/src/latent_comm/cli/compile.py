"""Compile recipes to locked research IR. This command has no execution switch."""
import argparse
import json
from pathlib import Path
import sys
from latent_comm.compiler import CompilationError, compile_recipe, ir_dot, ir_text

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('recipe', type=Path)
    parser.add_argument('--format', choices=['json','text','dot'], default='json')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args(argv)
    try: ir = compile_recipe(args.recipe)
    except CompilationError as error:
        print(str(error), file=sys.stderr); return 2
    result = json.dumps(ir.to_dict(), ensure_ascii=False, indent=2)+'\n' if args.format == 'json' else ir_text(ir) if args.format == 'text' else ir_dot(ir)
    if args.output: args.output.write_text(result, encoding='utf-8')
    else: print(result, end='')
    return 0

if __name__ == '__main__': raise SystemExit(main())
