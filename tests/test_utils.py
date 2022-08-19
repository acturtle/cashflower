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

