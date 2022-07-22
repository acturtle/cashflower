import numpy as np
import pandas as pd
import unittest

from cashflower.utils import get_cell


class TestGetCell(unittest.TestCase):
    def test_get_cell(self):
        df = pd.DataFrame(np.arange(9).reshape((3, 3)), columns=list('abc'))
        assert get_cell(df, column="b", a=3) == 4

    def test_raises_error_when_incorrect_column(self):
        df = pd.DataFrame(np.arange(9).reshape((3, 3)), columns=list('abc'))
        self.assertRaises(ValueError, get_cell, df, column="d", a=3)
