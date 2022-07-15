import numpy as np
import pandas as pd

from cashflower.utils import dfget


def test_dfget():
    df = pd.DataFrame(np.arange(9).reshape((3, 3)), columns=list('abc'))
    assert dfget(df, column="b", a=3) == 4
