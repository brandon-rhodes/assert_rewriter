
=================================================================
assert_rewriter: rewrite Python bytecode for assert introspection
=================================================================

Maybe I’ll wind up as the only user of this rather abstruse Python module.
But it seemed like this functionality was worth splitting out
from inside of my personal Python testing framework,
where it was hidden.

This ``assert_rewriter`` package
uses fast and efficient regular expressions to rewrite the bytecode
of Python assert statements
so that, on failure, they print out the comparison that failed —
a feature called ‘assert introspection’
that’s more commonly implemented
using slow and ponderous depth-first searches of abstract syntax trees.
It supports Python 2.7 through 3.12.

It’s a deep loss that Python 3 didn’t add assert introspection hooks
as a fully supported part of the language.
It would have been far more useful than most of the other changes they made.
(The only thing more useful that Python 3 could have done
would have been to eliminate the awful ``if __name__ == '__main__':``
that is utter nonsense at the language level
and that deeply and desperately confuses every student
to whom I’ve tried to teach the language.
But, alas, they missed the opportunity.)

Here’s an example of what happens without assert introspection.
You write a test:

>>> def test_function():
...     assert 1 + 1 == 3

But when it fails, you get zero useful information back:

>>> test_function()
Traceback (most recent call last):
  ...
AssertionError

This package aims to solve that.
Take your test functions and pass them to ``rewrite_function()``.
It will rewrite their bytecode in-place.
The functions will then report failures using easy-to-read assert exceptions
that explain what went wrong:

>>> from assert_rewriter import rewrite_function
>>> rewrite_function(test_function)
>>> test_function()
Traceback (most recent call last):
...
AssertionError: 2 != 3

By default,
the rewritten function will call ``unittest.TestCase`` methods
instead of the corresponding asserts.
In the above example,
the ``TestCase.assertEqual()`` method was called with the values
on either side of the ``==`` sign.
If you instead want to provide callables of your own,
then put them in a tuple with the same length as the operations listed in
the ``assert_rewriter.core.comparison_constants`` tuple
and then pass your tuple as a second argument to ``rewrite_function()``.

My own testing framework only does assert rewriting after a test fails,
to save time in the common case that a test passes;
but that runs the risk that the test behaves differently the second time,
so other folks might want to rewrite tests ahead of time.

Anyway, this might be quietly ignored for all time,
which would be fine,
but here it is in case you need it —
or are at least curious how it works,
and think you might learn something by giving it a quick read-through.

Here’s the GitHub repository, for reporting issues with the package:

https://github.com/brandon-rhodes/assert_rewriter/

— Brandon Rhodes
