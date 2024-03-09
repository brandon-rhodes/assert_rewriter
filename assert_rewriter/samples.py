"""Sample tests for the Assay test suite to exercise."""

def test_assert0():
    assert False

def test_assert1():
    assert 1+1 == 2+2

def test_assert2():
    f = int
    n = f()+0+1+2+3+4+5+6+7+8+9+0+1+2+3+4+5+6+7+8+9+0+1+2+3+4+5+6+7+8+9
    n += f()+0+1+2+3+4+5+6+7+8+9+0+1+2+3+4+5+6+7+8+9+0+1+2+3+4+5+6+7+8+9
    assert n == 100

def test_assert_tab():
    assert	1+1 == 3

# We use the same order here that dis.cmp_op used in old versions of Python:
# ('<', '<=', '==', '!=', '>', '>=',
#  'in', 'not in', 'is', 'is not', 'exception match', 'BAD')

def test_lt():
    assert 3+4 < 1+2

def test_le():
    assert 3+4 <= 1+2

def test_eq():
    assert 1+2 == 3+4

def test_ne():
    assert 1+2 != 0+3

def test_gt():
    assert 1+2 > 3+4

def test_ge():
    assert 1+2 >= 3+4

def test_in():
    assert 1 in ()

def test_not_in():
    assert 1 not in (1,)

def test_is():
    a, b = 1, 2
    assert a is b

def test_is_not():
    a = 1
    assert a is not a

def test_is_None():
    a = 1
    assert a is None

def test_is_not_None():
    a = None
    assert a is not None
