"""To run these tests, simply invoke::

    $ python -m assert_rewriter.tests

"""
import linecache
import sys
import unittest
from . import rewrite_function
from . import samples

class AssertTests(unittest.TestCase):

    maxDiff = 10000

    def execute(self, test):
        """Rewrite the asserts in ``test()``; run it; return exception data."""
        rewrite_function(test)
        try:
            test()
        except AssertionError as e:
            _, _, tb = sys.exc_info()
            tb = tb.tb_next  # skip past the frame that simply says "test()"
            filename = tb.tb_frame.f_code.co_filename
            lineno = tb.tb_lineno
            line = linecache.getline(filename, lineno)
            return line.strip(), str(e)
        else:
            raise RuntimeError('no AssertionError raised in %r' % test)

    def test_plain_assertion(self):
        result = self.execute(samples.test_assert0)
        self.assertEqual(result, ('assert False', ''))

    def test_equality_assertion(self):
        result = self.execute(samples.test_assert1)
        self.assertEqual(result, ('assert 1+1 == 2+2', '2 != 4'))

    def test_assertion_in_long_function_that_uses_EXTENDED_ARG(self):
        # It uses EXTENDED_ARG in older Pythons, where jumps are non-relative.
        result = self.execute(samples.test_assert2)
        self.assertEqual(result, ('assert n == 100', '270 != 100'))

    def test_assert_with_tab(self):
        result = self.execute(samples.test_assert_tab)
        self.assertEqual(result, ('assert\t1+1 == 3', '2 != 3'))

    # The following tests verify that we intercept and correctly report
    # failed results for all basic asserts in `opcode.cmp_op`:
    # ('<', '<=', '==', '!=', '>', '>=')

    def test_assert_lt(self):
        result = self.execute(samples.test_lt)
        self.assertEqual(result, ('assert 3+4 < 1+2', '7 not less than 3'))

    def test_assert_le(self):
        result = self.execute(samples.test_le)
        self.assertEqual(result, ('assert 3+4 <= 1+2',
                                  '7 not less than or equal to 3'))

    def test_assert_eq(self):
        result = self.execute(samples.test_eq)
        self.assertEqual(result, ('assert 1+2 == 3+4', '3 != 7'))

    def test_assert_ne(self):
        result = self.execute(samples.test_ne)
        self.assertEqual(result, ('assert 1+2 != 0+3', '3 == 3'))

    def test_assert_gt(self):
        result = self.execute(samples.test_gt)
        self.assertEqual(result, ('assert 1+2 > 3+4', '3 not greater than 7'))

    def test_assert_ge(self):
        result = self.execute(samples.test_ge)
        self.assertEqual(result, ('assert 1+2 >= 3+4',
                                  '3 not greater than or equal to 7'))

    def test_assert_in(self):
        result = self.execute(samples.test_in)
        self.assertEqual(result, ('assert 1 in ()', '1 not found in ()'))

    def test_assert_not_in(self):
        result = self.execute(samples.test_not_in)
        self.assertEqual(result, ('assert 1 not in (1,)',
                                  '1 unexpectedly found in (1,)'))

    def test_assert_is(self):
        result = self.execute(samples.test_is)
        self.assertEqual(result, ('assert a is b', '1 is not 2'))

    def test_assert_is_not(self):
        result = self.execute(samples.test_is_not)
        self.assertEqual(result, ('assert a is not a',
                                  'unexpectedly identical: 1'))

    def test_assert_is_None(self):
        result = self.execute(samples.test_is_None)
        self.assertEqual(result, ('assert a is None', '1 is not None'))

    def test_assert_is_not_None(self):
        result = self.execute(samples.test_is_not_None)
        if sys.version_info >= (3, 11):
            message = 'unexpectedly None'
        else:
            message = 'unexpectedly identical: None'
        self.assertEqual(result, ('assert a is not None', message))

if __name__ == '__main__':
    unittest.main()
