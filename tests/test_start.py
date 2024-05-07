import argparse
import pytest

from unittest import TestCase

from cashflower.core import *
from cashflower.start import *


class TestCreateModel(TestCase):
    def test_create_model(self):
        create_model("annuity")
        assert os.path.exists("./annuity/input.py")
        assert os.path.exists("./annuity/model.py")
        assert os.path.exists("./annuity/run.py")
        assert os.path.exists("./annuity/settings.py")
        shutil.rmtree("./annuity")


class TestLoadSettings(TestCase):
    def test_load_settings(self):
        default_settings = {
            "AGGREGATE": True,
            "GROUP_BY_COLUMN": None,
            "ID_COLUMN": "id",
            "MULTIPROCESSING": False,
            "NUM_STOCHASTIC_SCENARIOS": None,
            "OUTPUT_COLUMNS": [],
            "SAVE_DIAGNOSTIC": True,
            "SAVE_LOG": True,
            "SAVE_OUTPUT": True,
            "T_MAX_CALCULATION": 720,
            "T_MAX_OUTPUT": 720,
        }
        assert load_settings() == default_settings

        my_settings1 = {}
        settings = load_settings(my_settings1)
        assert settings == default_settings

        my_settings2 = {
            "ID_COLUMN": "polnumber",
            "T_MAX_CALCULATION": 100,
            "OUTPUT_COLUMNS": ["a", "b", "c"],
        }
        settings = load_settings(my_settings2)
        assert settings == {
            "AGGREGATE": True,
            "GROUP_BY_COLUMN": None,
            "ID_COLUMN": "polnumber",
            "MULTIPROCESSING": False,
            "NUM_STOCHASTIC_SCENARIOS": None,
            "OUTPUT_COLUMNS": ["a", "b", "c"],
            "SAVE_DIAGNOSTIC": True,
            "SAVE_LOG": True,
            "SAVE_OUTPUT": True,
            "T_MAX_CALCULATION": 100,
            "T_MAX_OUTPUT": 100,
        }


class TestGetRunplan(TestCase):
    def test_get_runplan(self):
        runplan = Runplan(data=pd.DataFrame({"version": [1]}))
        input_members = [("foo", "foo"), ("runplan", runplan), ("bar", "bar")]
        assert get_runplan(input_members, args=argparse.Namespace(**{'version': None})) == runplan


class TestGetModelPointSets(TestCase):
    def test_get_model_point_sets(self):
        main = ModelPointSet(data=pd.DataFrame({"id": [1]}))
        input_members_1 = [("main", main)]
        settings = load_settings()
        model_point_sets = get_model_point_sets(input_members_1, settings, argparse.Namespace(**{'id': None}))
        assert model_point_sets == [main]

        input_members_2 = [("foo", "foo"), ("bar", "bar")]
        with pytest.raises(CashflowModelError):
            get_model_point_sets(input_members_2, settings, argparse.Namespace(**{'id': None}))


class TestGetVariables(TestCase):
    def test_get_variables(self):
        settings = load_settings()

        @variable()
        def foo(t):
            return t

        model_members = [("foo", foo), ("bar", "bar")]
        variables = get_variables(model_members, settings)
        assert variables == [foo]

    def test_get_variables_raises_error_when_name_is_t_or_r(self):
        settings = load_settings()

        @variable()
        def t(t):
            return 1

        model_members = [("foo", "foo"), ("t", t)]
        with pytest.raises(CashflowModelError):
            get_variables(model_members, settings)
