import numpy as np
import pandas as pd
import pytest

from unittest import TestCase

from cashflower.core import CashflowModelError, ModelPointSet, Runplan, variable, Variable
from cashflower.start import get_settings


class TestVariableDecorator(TestCase):
    def test_variable_decorator(self):

        @variable()
        def foo(t):
            return t

        assert isinstance(foo, Variable)


class TestRunplan(TestCase):
    def test_runplan(self):
        runplan = Runplan(data=pd.DataFrame({
            "version": [1, 2],
            "value": [57, 89]
        }))
        assert runplan.version == "1"
        assert runplan.get("value") == 57

        runplan.version = "2"
        assert runplan.version == "2"

    def test_runplan_raises_error_when_no_version_column(self):
        with pytest.raises(CashflowModelError):
            Runplan(data=pd.DataFrame({"a": [1, 2, 3]}))

    def test_runplan_raises_error_when_non_existent_version_is_set(self):
        runplan = Runplan(data=pd.DataFrame({
            "version": [1, 2],
            "value": [57, 89]
        }))
        with pytest.raises(CashflowModelError):
            runplan.version = "3"


class TestModelPointSet(TestCase):
    def test_model_point_set(self):
        main = ModelPointSet(data=pd.DataFrame({
            "id": [1, 2, 3],
            "age": [52, 47, 35]
        }))
        assert len(main) == 3

        main.name = "main"
        main.settings = get_settings()
        main.set_model_point_data(0)
        assert main.get("age") == 52
        assert repr(main) == "MPS: main"


class TestVariable(TestCase):
    def test_variable_is_called(self):
        @variable()
        def foo(t):
            return t

        foo.name = "foo"
        foo.result = np.empty(720)

        foo.calculate_t(10)

        assert foo(10) == 10

        with pytest.raises(CashflowModelError):
            foo(721)
