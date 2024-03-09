"""Handle a few discrepancies between Python versions."""

import sys
import types

if sys.version_info >= (3,8):
    def code_object_replace(c, new_code, new_consts, new_stacksize):
        return c.replace(
            co_code=new_code,
            co_consts=new_consts,
            co_stacksize=new_stacksize,
        )
else:
    def code_object_replace(c, new_code, new_consts, new_stacksize):
        """Emulate `.replace()` method for code objects in older Pythons."""
        args = (
            c.co_argcount,
            c.co_nlocals,
            new_stacksize,
            c.co_flags,
            new_code,
            new_consts,
            c.co_names,
            c.co_varnames,
            c.co_filename,
            c.co_name,
            c.co_firstlineno,
            c.co_lnotab,
            c.co_freevars,
            c.co_cellvars,
        )
        if sys.version_info >= (3,0):
            args = args[0:1] + (c.co_kwonlyargcount,) + args[1:]
        return types.CodeType(*args)

if sys.version_info >= (3,):
    def get_code(function):
        return function.__code__
    def set_code(function, code):
        function.__code__ = code
else:
    def get_code(function):
        return function.func_code
    def set_code(function, code):
        function.func_code = code
