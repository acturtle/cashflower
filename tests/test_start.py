import pytest

from unittest import TestCase

from cashflower.start import *
from cashflower.cashflow import *


class TestLoadSettings(TestCase):
    def test_load_settings(self):
        default_settings = {
            "AGGREGATE": True,
            "MULTIPROCESSING": False,
            "OUTPUT_COLUMNS": [],
            "ID_COLUMN": "id",
            "SAVE_OUTPUT": True,
            "SAVE_RUNTIME": False,
            "T_CALCULATION_MAX": 1200,
            "T_OUTPUT_MAX": 1200,
        }
        assert load_settings() == default_settings

        my_settings1 = {}
        settings = load_settings(my_settings1)
        assert settings == default_settings

        my_settings2 = {
            "ID_COLUMN": "polnumber",
            "T_CALCULATION_MAX": 100,
            "OUTPUT_COLUMNS": ["a", "b", "c"],
        }
        settings = load_settings(my_settings2)
        assert settings == {
            "AGGREGATE": True,
            "MULTIPROCESSING": False,
            "OUTPUT_COLUMNS": ["a", "b", "c"],
            "ID_COLUMN": "polnumber",
            "SAVE_OUTPUT": True,
            "SAVE_RUNTIME": False,
            "T_CALCULATION_MAX": 100,
            "T_OUTPUT_MAX": 1200,
        }


class TestGetRunplan(TestCase):
    def test_get_runplan(self):
        runplan = Runplan()
        input_members = [("foo", "foo"), ("runplan", runplan), ("bar", "bar")]
        assert get_runplan(input_members) == runplan


class TestGetModelPointSets(TestCase):
    def test_get_model_point_sets(self):
        main = ModelPointSet(data=pd.DataFrame({"id": [1]}))
        input_members_1 = [("main", main)]
        settings = load_settings()
        model_point_sets, _ = get_model_point_sets(input_members_1, settings)
        assert model_point_sets == [main]

        input_members_2 = [("foo", "foo"), ("bar", "bar")]
        with pytest.raises(CashflowModelError):
            get_model_point_sets(input_members_2, settings)


class TestGetConstants(TestCase):
    def test_get_constants(self):
        my_constant = Constant()

        @assign(my_constant)
        def my_constant_formula():
            return 1

        model_members = [("foo", "foo"), ("my_constant", my_constant)]
        main = ModelPointSet(data=pd.DataFrame({"id": [1]}))
        constants = get_constants(model_members, main)
        assert constants == [my_constant]

    def test_get_constants_raises_error_when_name_is_t_or_r(self):
        t = Constant()

        @assign(t)
        def t_formula():
            return 1

        model_members = [("foo", "foo"), ("t", t)]
        main = ModelPointSet(data=pd.DataFrame({"id": [1]}))
        with pytest.raises(CashflowModelError):
            get_constants(model_members, main)
