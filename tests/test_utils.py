import inspect
import numpy as np
import os
import pandas as pd

from unittest import TestCase

from cashflower.utils import *


class TestGetCell(TestCase):
    def test_get_cell(self):
        df = pd.DataFrame(np.arange(9).reshape((3, 3)), columns=list('abc'))
        assert get_cell(df, column="b", a=3) == 4


class TestUniqueAppend(TestCase):
    def test_unique_append(self):
        lst = [1, 2, 3]
        assert unique_append(lst, 4) == [1, 2, 3, 4]
        assert unique_append(lst, 2) == [1, 2, 3]


class TestUniqueExtend(TestCase):
    def test_unique_extend(self):
        lst = [1, 2, 3]
        assert unique_extend(lst, [2, 4]) == [1, 2, 3, 4]
        assert unique_extend(lst, [5]) == [1, 2, 3, 5]


class TestListUsedWords(TestCase):
    def test_list_used_words(self):
        text = "An actuary is a business professional who deals with the measurement and management of risk " \
               "and uncertainty."
        words = ["professional", "basketball", "risk"]
        assert list_used_words(text, words) == ["professional", "risk"]


class TestReplaceInFile(TestCase):
    def test_replace_in_file(self):
        filename = "my-file.txt"

        with open(filename, "w") as f:
            f.write("Our model is called {{ model }}. Let's calculate {{ model }}.")

        replace_in_file(filename, "{{ model }}", "annuity")

        with open(filename, "r") as f:
            text = f.read()
            assert text == "Our model is called annuity. Let's calculate annuity."

        os.remove(filename)


class TestFlatten(TestCase):
    def test_flatten(self):
        assert flatten([[1, 2, 3], [4, 5, 6]]) == [1, 2, 3, 4, 5, 6]
        assert flatten([[1, 2], [3, 4], [5, 6]]) == [1, 2, 3, 4, 5, 6]
        assert flatten([[1, 2, 3], [4, 5, 6]], n=2) == [1, 2, 4, 5]


class TestAggregate(TestCase):
    def test_aggregate(self):
        assert aggregate([[1, 2, 3], [4, 5, 6]]) == [5, 7, 9]
        assert aggregate([[1, 2, 3], [4, 5, 6]], n=2) == [5, 7]


class TestRepeatedNumbers(TestCase):
    def test_repeated_numbers(self):
        assert repeated_numbers(3, 2) == [1, 1, 2, 2, 3, 3]
        assert repeated_numbers(2, 4) == [1, 1, 1, 1, 2, 2, 2, 2]


class TestListCalledFuncs(TestCase):
    def test_list_called_funcs(self):
        def two():
            return 2

        def my_formula():
            """This is a formula that doesn't call one()"""
            '''Remember: no one()'''
            three = 3
            result = two  () + three  # I have not called one() here
            return result

        my_formula_source = inspect.getsource(my_formula)
        result1 = list_called_funcs(my_formula_source, ["one", "two", "three"])
        assert result1 == ["one"]

        clean = clean_formula_source(my_formula_source)
        result2 = list_called_funcs(clean, ["one", "two", "three"])
        assert result2 == ["two"]


class TestIsRecursive(TestCase):
    def test_is_recursive(self):
        def my_func1(t):
            return my_func1(t+1)

        def my_func2(t):
            return my_func2(t-1)

        def my_func3(t):
            return 2

        def my_func4(t):
            return my_func4(t + 1)

        def my_func5(t):
            return my_func5(t - 1)

        cfs1 = clean_formula_source(inspect.getsource(my_func1))
        cfs2 = clean_formula_source(inspect.getsource(my_func2))
        cfs3 = clean_formula_source(inspect.getsource(my_func3))
        cfs4 = clean_formula_source(inspect.getsource(my_func4))
        cfs5 = clean_formula_source(inspect.getsource(my_func5))

        assert is_recursive(cfs1, "my_func1") == "backward"
        assert is_recursive(cfs2, "my_func2") == "forward"
        assert is_recursive(cfs3, "my_func3") == "not_recursive"
        assert is_recursive(cfs4, "my_func4") == "backward"
        assert is_recursive(cfs5, "my_func5") == "forward"
