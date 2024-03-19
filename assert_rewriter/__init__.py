"""Rewrite Python bytecode to add ``assert`` introspection."""

from .core import rewrite_bytecode, rewrite_function, search_for_function
__all__ = 'rewrite_bytecode', 'rewrite_function', 'search_for_function'
