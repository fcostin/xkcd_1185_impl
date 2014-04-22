`developers.py` - a meta-algorithm for implementing functions
-------------------------------------------------------------

[![Build Status](https://travis-ci.org/fcostin/xkcd_1185_impl.png)](https://travis-ci.org/fcostin/xkcd_1185_impl)

### inspiration

[XKCD #1185](http://xkcd.com/1185/)

> StackSort connects to StackOverflow,
> searches for 'sort a list', and
> downloads and runs code snippets
> until the list is sorted.

### features

*   this code, `developers.py`, is a terrible idea and should not be run by anyone
*   there are obvious security risks to running this code
*   `developers.py`
    1.  connects to StackOverflow
    2.  searches for your function requirements, stated as as a string in plain english
    3.  downloads code snippets
    4.  attempts to coerce the snippets into runnable functions using advanced techniques such as: string manipulation, automated repair of recognised pylint errors, and enumeration over possible interpretations while hoping for the best!
    5.  recognises and returns the correct implementation as the first patched code snippet to pass given list of unit tests
*   automates the latter D in TDD / BDD!
*   do not run this code

### example of usage

```python
import developers as talented_developers # give them some credit.

def test_sort_list():
    f = talented_developers.implement_function(
        requirements='sort a list of integers',
        test_cases=[
            lambda f : f([3, 1, 2]) == [1, 2, 3],
            lambda f : f([9, 0, 2, 1, 0]) == [0, 0, 1, 2, 9],
        ],
    )

    assert f([8, 7, 3, 8, 5, 9, 1, 5, 7, 9, 4]) == [1, 3, 4, 5, 5, 7, 7, 8, 8, 9, 9]
```


### apologies

apologies to stack overflow


### possible extensions

*   rewrite using `ast` module
*   rewrite using machine learning / optimisation techniques to explore space of code snippet interpretations / patches / refactors / repairs

