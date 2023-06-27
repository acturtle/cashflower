import pytest

from pandas.testing import assert_frame_equal
from unittest import TestCase

from cashflower.cashflow import *
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
            "MULTIPROCESSING": False,
            "OUTPUT_COLUMNS": [],
            "ID_COLUMN": "id",
            "SAVE_OUTPUT": True,
            "SAVE_RUNTIME": False,
            "T_MAX_CALCULATION": 1200,
            "T_MAX_OUTPUT": 1200,
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
            "MULTIPROCESSING": False,
            "OUTPUT_COLUMNS": ["a", "b", "c"],
            "ID_COLUMN": "polnumber",
            "SAVE_OUTPUT": True,
            "SAVE_RUNTIME": False,
            "T_MAX_CALCULATION": 100,
            "T_MAX_OUTPUT": 100,
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


class TestGetVariables(TestCase):
    def test_get_variables(self):
        settings = load_settings()
        my_variable = ModelVariable()

        @assign(my_variable)
        def my_variable_formula(t):
            return t

        model_members = [("foo", "foo"), ("my_constant", my_variable)]
        main = ModelPointSet(data=pd.DataFrame({"id": [1]}))
        variables = get_variables(model_members, main, settings)
        assert variables == [my_variable]

    def test_get_variables_raises_error_when_name_is_t_or_r(self):
        settings = load_settings()
        t = ModelVariable()

        @assign(t)
        def t_formula():
            return 1

        model_members = [("foo", "foo"), ("t", t)]
        main = ModelPointSet(data=pd.DataFrame({"id": [1]}))
        with pytest.raises(CashflowModelError):
            get_variables(model_members, main, settings)


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


class TestSimpleModel(TestCase):
    def test_simple_model_runs(self):
        model_name = "my_test_model"
        settings = load_settings()

        # Single core
        create_model(model_name)
        model_output = start(model_name, settings, [])
        shutil.rmtree(model_name)
        shutil.rmtree("output")
        test_output = pd.DataFrame({
            "t": range(settings["T_MAX_CALCULATION"]+1),
            "projection_year": [0] + [x for x in range(1, 101) for _ in range(12)],
        })
        assert_frame_equal(model_output["main"], test_output, check_dtype=False)

    def test_simple_model_runs_multiprocessing(self):
        model_name = "my_test_model"
        settings = load_settings()

        # Multiprocessing
        settings["MULTIPROCESSING"] = True
        create_model(model_name)
        model_output = start(model_name, settings, [])
        shutil.rmtree(model_name)
        shutil.rmtree("output")
        test_output = pd.DataFrame({
            "t": range(settings["T_MAX_CALCULATION"] + 1),
            "projection_year": [0] + [x for x in range(1, 101) for _ in range(12)],
        })
        assert_frame_equal(model_output["main"], test_output, check_dtype=False)
