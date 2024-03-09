"""Rewrite Python bytecode to add ``assert`` introspection."""

# Is this becoming complicated enough that I should split it into a
# separate module for each version of Python?

import dis
import re
import sys
import unittest
from types import FunctionType
from .compatibility import code_object_replace, get_code, set_code

PLACEHOLDER = b'{%PHDR%}'  # hope this substring never appears in real bytecode
python_version = sys.version_info[:2]

# Turn bytecode opcodes into the attributes of a single object `op`, so
# we can write them conveniently like `op.compare_op`.

class op(object): pass
for i, symbol in enumerate(dis.opname):
    setattr(op, symbol.lower(), i)

# The master sequence of comparisons that we rewrite.  Their integer
# indexes are important, because indexes are how a function's bytecode
# reaches into its table of constants, which we will be extending with a
# block of methods in the same order as the comparisons are listed here.

comparison_names = (
    '<',
    '<=',
    '==',
    '!=',
    '>',
    '>=',
    'in',
    'not in',
    'is',
    'is not',
    'is None',
    'is not None',
)
comparison_indexes = {name: i for i, name in enumerate(comparison_names)}

# Figure out what each comparison will look like in bytecode, using the
# table of comparisons built in to Python's `dis` module.

if python_version == (3,12):
    bytecode_map = {
        b'%c%c' % (op.compare_op, i << 4): comparison_indexes[name]
        for i, name in enumerate(dis.cmp_op)
        if name not in ('BAD', 'exception match')
    }
else:
    bytecode_map = {
        b'%c%c' % (op.compare_op, i): comparison_indexes[name]
        for i, name in enumerate(dis.cmp_op)
        if name not in ('BAD', 'exception match')
    }

# Recent Python versions have special opcodes for some comparisons.

if python_version >= (3,9):
    bytecode_map[b'%c%c' % (op.contains_op, 0)] = comparison_indexes['in']
    bytecode_map[b'%c%c' % (op.contains_op, 1)] = comparison_indexes['not in']
    bytecode_map[b'%c%c' % (op.is_op, 0)] = comparison_indexes['is']
    bytecode_map[b'%c%c' % (op.is_op, 1)] = comparison_indexes['is not']

if python_version >= (3,11):
    if python_version == (3,11):
        jump_if_none = op.pop_jump_forward_if_none
        jump_if_not_none = op.pop_jump_forward_if_not_none
    else:
        jump_if_none = op.pop_jump_if_none
        jump_if_not_none = op.pop_jump_if_not_none

    bytecode_map[b'%c%c' % (jump_if_none, 2)] = comparison_indexes['is None']
    bytecode_map[b'%c%c' % (jump_if_not_none, 2)] = comparison_indexes[
        'is not None']

# Assemble a regular expression pattern for each comparison.

operator_patterns = {
    re.escape(bytecode) for bytecode in bytecode_map
}

# Build a block of constants that offers a rich comparison method for
# each of the comparisons defined above.

test_case = unittest.TestCase('setUp')
test_case.maxDiff = 2048

comparison_constants = (
    test_case.assertLess,
    test_case.assertLessEqual,
    test_case.assertEqual,
    test_case.assertNotEqual,
    test_case.assertGreater,
    test_case.assertGreaterEqual,
    test_case.assertIn,
    test_case.assertNotIn,
    test_case.assertIs,
    test_case.assertIsNot,
    test_case.assertIsNone,
    test_case.assertIsNotNone,
)

# How to assemble regular expressions and replacement strings.

if python_version >= (3,0):
    def chr(n):
        return bytes((n,))

def assemble_replacement(things):
    return b''.join((t if isinstance(t, bytes) else chr(t)) for t in things)

def assemble_pattern(things):
    return b''.join((t if isinstance(t, bytes) else re.escape(chr(t)))
                    for t in things)

# How an "assert" statement looks in each version of Python, along with
# a working replacement for it.

class Comparator(object):
    def __init__(self, comparison_method):
        self.comparison_method = comparison_method

    def __setitem__(self, value2, value1):
        self.comparison_method(value1, value2)

    def __delitem__(self, value):
        self.comparison_method(value)

if python_version == (3,12):
    def clear_bits(bytecode):
        opcode, operand = bytecode
        if opcode == op.compare_op:
            operand &= 0b11110000
        return b'%c%c' % (opcode, operand)
else:
    def clear_bits(bytecode):
        return bytecode

if python_version <= (3,5):

    assert_pattern_text = assemble_pattern([
        b'(', b'|'.join(operator_patterns), b')', 0,
        op.pop_jump_if_true, b'..',
        op.load_global, b'(..)',
        op.raise_varargs, 1, 0,
        ])

    replacement = assemble_replacement([
        op.load_const, PLACEHOLDER, # stack: ... op1 op2 function
        op.rot_three,               # stack: ... function op1 op2
        op.call_function, 2, 0,     # stack: ... return_value
        op.pop_top,                 # stack: ...
        ])

elif python_version <= (3,8):

    assert_pattern_text = assemble_pattern([
        b'(', b'|'.join(operator_patterns), b')',
        b'(?:', op.extended_arg, b'.)?',
        op.pop_jump_if_true, b'.',
        op.load_global, b'(.)',
        op.raise_varargs, 1,
    ])

    replacement = assemble_replacement([
        op.load_const, PLACEHOLDER, # stack: ... op1 op2 function
        op.rot_three, 0,            # stack: ... function op1 op2
        op.call_function, 2,        # stack: ... return_value
        op.pop_top, 0,              # stack: ...
    ])

elif python_version <= (3,10):

    assert_pattern_text = assemble_pattern([
        b'(', b'|'.join(operator_patterns), b')',
        b'(?:', op.extended_arg, b'.)?',
        op.pop_jump_if_true, b'.',
        op.load_assertion_error, 0,
        op.raise_varargs, 1,
    ])

    replacement = assemble_replacement([
        op.load_const, PLACEHOLDER, # stack: ... op1 op2 function
        op.rot_three, 0,            # stack: ... function op1 op2
        op.call_function, 2,        # stack: ... return_value
        op.pop_top, 0,              # stack: ...
    ])

else:

    # Some comparisons now use JUMP opcodes that themselves perform a
    # comparison instead of being preceded by a separate comparison
    # opcode, so we need to handle assert stanzas and replacements of
    # different lengths.

    replacement_binary = assemble_replacement([
        op.load_const, PLACEHOLDER, # stack: *rest op1 op2 myobj
        op.swap, 2,                 # stack: *rest myobj op1 op2
        op.store_subscr, 0,         # stack: *rest
        0, 0,                       # (cache line for STORE_SUBSCR)
    ])

    replacement_unary = assemble_replacement([
        op.load_const, PLACEHOLDER, # stack: *rest op myobj
        op.swap, 2,                 # stack: *rest myobj op
        op.delete_subscr, 0,        # stack: *rest
    ])

    operator_patterns = set()
    replacements = {}

    if python_version == (3,11):
        jump_if_true = op.pop_jump_forward_if_true
    else:
        jump_if_true = op.pop_jump_if_true

    _lower_bits = range(16)

    def escape_compare_bytecode(bytecode):
        opcode = re.escape(bytecode[0:1])
        if python_version == (3,12):
            byte = bytecode[1]
            characters = list(chr(byte | b) for b in _lower_bits)
            operation = b'[' + b''.join(
                (b'\\' + c if c in b']\\' else c) for c in characters
            )+ b']'
        else:
            operation = re.escape(bytecode[1:2])
        return opcode + operation

    def expand_cmp_op(cmp):
        """Build an RE that matches every possible bitting of `cmp`."""

    for bytecode, i in bytecode_map.items():
        operator = bytecode[0]

        if operator == op.compare_op:
            cache = b'....' if python_version == (3,11) else b'..'
            pattern = assemble_pattern([
                escape_compare_bytecode(bytecode),
                cache,
                jump_if_true, 2,
                op.load_assertion_error, b'.',
                op.raise_varargs, 1,
            ])
            replacement = replacement_binary

        elif operator in (op.contains_op, op.is_op):
            pattern = assemble_pattern([
                re.escape(bytecode),  # no cache lines
                jump_if_true, 2,
                op.load_assertion_error, 0,
                op.raise_varargs, 1,
            ])
            replacement = replacement_binary

        else:
            pattern = assemble_pattern([
                re.escape(bytecode),  # bytecode is itself the conditional jump
                op.load_assertion_error, 0,
                op.raise_varargs, 1,
            ])
            replacement = replacement_unary

        operator_patterns.add(pattern)
        replacements[i] = replacement

    assert_pattern_text = b'(' + b'|'.join(operator_patterns) + b')'

    # Wrap each comparison method in an object that implements the
    # __setitem__ and __delitem__ methods, that will be invoked by the
    # replacement bytecode above.

    comparison_constants = tuple(
        Comparator(method) for method in comparison_constants
    )

# Note that "re.S" is crucial when compiling this pattern, as a byte we
# are trying to match with "." might happen to have the numeric value of
# an ASCII newline.
assert_pattern = re.compile(assert_pattern_text, re.S)

def rewrite_asserts_in(function):

    def replace(match):
        comparison_bytecode = match.group(1)
        comparison_key = comparison_bytecode[:2]  # comparison instruction
        comparison_key = clear_bits(comparison_key)
        comparison_index = bytecode_map[comparison_key]
        if python_version >= (3,11):
            code = replacements[comparison_index]
            code = code.replace(PLACEHOLDER, chr(offset + comparison_index))
        elif python_version >= (3,6):
            code = replacement.replace(PLACEHOLDER,
                                       chr(offset + comparison_index))
        else:
            msb, lsb = divmod(offset + comparison_index, 256)
            code = replacement.replace(PLACEHOLDER, chr(lsb) + chr(msb))
        short = len(match.group(0)) - len(code)
        if short < 0:
            raise ValueError('Internal error in Assay: bytecode overflow')
        if short > 0:
            code += chr(op.nop) * short
        return code

    c = get_code(function)
    offset = len(c.co_consts)
    newcode = assert_pattern.sub(replace, c.co_code)
    code_object = code_object_replace(
        c,
        new_code=newcode,
        new_consts=c.co_consts + comparison_constants,
        new_stacksize=c.co_stacksize + 1,
    )
    set_code(function, code_object)

def search_for_function(code, candidate, frame, name):
    """Find the function whose code object is `code`, else return None."""
    if get_code(candidate) is code:
        return candidate
    candidate = frame.f_locals.get(name) or frame.f_globals.get(name)
    if isinstance(candidate, FunctionType):
        if get_code(candidate) is code:
            return candidate
    return None
