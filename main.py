import developers as talented_developers

def test_sort_list():
    f = talented_developers.implement_function(
        requirements='sort a list',
        test_cases=[
            lambda f : f([3, 1, 2]) == [1, 2, 3],
            lambda f : f([9, 0, 2, 1, 0]) == [0, 0, 1, 2, 9],
        ]
    )

    assert f([8, 7, 3, 8, 5, 9, 1, 5, 7, 9, 4]) == [1, 3, 4, 5, 5, 7, 7, 8, 8, 9, 9]


def test_reverse_list():
    f = talented_developers.implement_function(
        requirements='reverse a list',
        test_cases=[
            lambda f : list(f([1, 2, 3])) == [3, 2, 1],
            lambda f : f('banana') == list('ananab'),
        ]
    )
    assert f(['h', 'e', 'l', 'l', 'o']) == ['o', 'l', 'l', 'e', 'h']


def test_uppercase_string():
    f = talented_developers.implement_function(
        requirements = 'uppercase string',
        test_cases=[
            lambda f : f('hello') == 'HELLO',
        ]
    )

    assert f('goodbye') == 'GOODBYE'


def test_unique_list_elements():
    f = talented_developers.implement_function(
        requirements = 'unique elements of list',
        test_cases=[
            lambda f : f(['a', 'b', 'b', 'a']) == ['a', 'b'],
        ]
    )

    assert f([5, 4, 3, 3, 2, 1]) == [1, 2, 3, 4, 5]



if __name__ == '__main__':
    test_sort_list()
    test_reverse_list()
    test_uppercase_string()
    test_unique_list_elements()

