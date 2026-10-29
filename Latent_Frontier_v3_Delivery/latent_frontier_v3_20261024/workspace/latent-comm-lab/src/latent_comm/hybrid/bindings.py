"""Compatibility facade. Algorithms remain uniquely owned by H16."""
from importlib import import_module

IMPLEMENTATIONS = ('latent_comm.mechanisms.h16_legacy',)

def __getattr__(name: str):
    if name.startswith("_"):
        raise AttributeError(name)
    for base in IMPLEMENTATIONS:
        for part in ("types", "reference", "adapter", "losses"):
            module = import_module(base + "." + part)
            if hasattr(module, name):
                return getattr(module, name)
    raise AttributeError(f"No compatible export {name!r} in {IMPLEMENTATIONS}")
