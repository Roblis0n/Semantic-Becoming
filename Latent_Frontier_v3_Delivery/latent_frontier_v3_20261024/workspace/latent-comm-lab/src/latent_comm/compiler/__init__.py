"""Typed, default-deny research compiler; model execution is NOT_RUN."""
from .pipeline import Compiler, compile_recipe, request_research_execution, PASSES
from .registry import mechanism_registry, builtin_registry
from .types import CompilationError, CompiledIR, Diagnostic, SourceLocation, TypeSpec, IRNode, BoundedLoop
from .export import ir_text, ir_dot
__all__ = ['Compiler','compile_recipe','request_research_execution','PASSES','mechanism_registry','builtin_registry','CompilationError','CompiledIR','Diagnostic','SourceLocation','TypeSpec','IRNode','BoundedLoop','ir_text','ir_dot']
