import developers as talented_developers # give them some credit.


def test_sort_list():
    f = talented_developers.implement_function(
        requirements='sort a list',
        test_cases=[
            lambda f : f([3, 1, 2]) == [1, 2, 3],
            lambda f : f([9, 0, 2, 1, 0]) == [0, 0, 1, 2, 9],
        ],
    )

    assert f([8, 7, 3, 8, 5, 9, 1, 5, 7, 9, 4]) == [1, 3, 4, 5, 5, 7, 7, 8, 8, 9, 9]


def test_reverse_list():
    f = talented_developers.implement_function(
        requirements='reverse a list',
        test_cases=[
            lambda f : list(f([1, 2, 3])) == [3, 2, 1],
            lambda f : f('banana') == list('ananab'),
        ],
    )
    assert f(['h', 'e', 'l', 'l', 'o']) == ['o', 'l', 'l', 'e', 'h']


def test_palindrome():
    f = talented_developers.implement_function(
        requirements = 'is string a palindrome?',
        test_cases=[
            lambda f : f('palindrome') == False,
            lambda f : f('palindromemordnilap') == True,
        ]
    )

    assert f('goodbye') == False
    assert f('tattarrattat') == True


def test_gcd():
    f = talented_developers.implement_function(
        requirements = 'greatest common divisor',
        test_cases=[
            lambda f : f(10, 7) == 1,
            lambda f : f(3, 9) == 3,
            lambda f : f(121, 33) == 11,
        ]
    )

    assert f(2, 3) == 1
    assert f(2, 4) == 2
    assert f(60, 48) == 12
    assert f(14, 21) == 7


