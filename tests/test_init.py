import importlib
import pandas as pd

from unittest import TestCase

from cashflower import assign, load_settings, get_model_input, Model, ModelVariable, ModelPoint


class TestAssign(TestCase):
    def test_assign(self):
        my_var = ModelVariable()

        assert my_var.formula is None

        @assign(my_var)
        def my_func(t):
            return t

        assert my_var.formula == my_func


class TestLoadSettings(TestCase):
    def test_load_settings(self):
        default_settings = {
            "POLICY_ID_COLUMN": "POLICY_ID",
            "T_CALCULATION_MAX": 1440,
            "T_OUTPUT_MAX": 1440,
            "AGGREGATE": False,
            "OUTPUT_COLUMNS": [],
        }
        assert load_settings() == default_settings

        my_settings1 = {}
        settings = load_settings(my_settings1)
        assert settings == default_settings

        my_settings2 = {
            "POLICY_ID_COLUMN": "polnumber",
            "T_CALCULATION_MAX": 100,
            "OUTPUT_COLUMNS": ["a", "b", "c"],
        }
        settings = load_settings(my_settings2)
        assert settings == {
            "POLICY_ID_COLUMN": "polnumber",
            "T_CALCULATION_MAX": 100,
            "T_OUTPUT_MAX": 1440,
            "AGGREGATE": False,
            "OUTPUT_COLUMNS": ["a", "b", "c"],
        }


class TestGetModelInput(TestCase):
    def test_get_model_input(self):
        modelpoint_module = importlib.import_module("tests.fix1.modelpoint")
        model_module = importlib.import_module("tests.fix1.model")
        settings = load_settings()
        variables, modelpoints = get_model_input(modelpoint_module, model_module, settings)

        var = variables[0]
        mp = modelpoints[0]

        assert isinstance(var, ModelVariable)
        assert var.name == "projection_year"
        assert var.settings == settings
        assert var.modelpoint == mp

        assert isinstance(mp, ModelPoint)
        assert mp.name == "policy"
        assert mp.settings == settings


class TestModelPoint(TestCase):
    def test_model_point(self):
        data = pd.DataFrame({
            "POLICY_ID": [1, 2, 2, 3],
            "value1": [100, 120, 90, 80],
            "value2": ["a", "b", "c", "d"],
        })

        mp = ModelPoint(data=data)
        mp.settings = load_settings()

        mp.policy_id = 2
        mp.record_num = 1

        assert len(mp) == 4
        assert mp.size == 2

        assert mp.policy_data.reset_index(drop=True).equals(pd.DataFrame({
            "POLICY_ID": [2, 2],
            "value1": [120, 90],
            "value2": ["b", "c"],
        }))

        assert mp.policy_record.reset_index(drop=True).equals(pd.DataFrame({
            "POLICY_ID": [2],
            "value1": [90],
            "value2": ["c"],
        }))


class TestModelVariable(TestCase):
    def test_model_variable(self):
        mv = ModelVariable()

        @assign(mv)
        def mv_formula(t):
            pass

        assert mv.formula == mv_formula

    def test_model_variable_is_lower_when_fewer_grandchildren(self):
        mv = ModelVariable()
        other_mv = ModelVariable()

        mv.grandchildren = [1, 2, 3]
        other_mv.grandchildren = [1, 3]
        assert mv > other_mv

    def test_model_variables_calculates_result(self):
        data = pd.DataFrame({"POLICY_ID": [1]})
        settings = load_settings({"T_CALCULATION_MAX": 3})

        mp = ModelPoint(data=data)
        mp.settings = settings
        mp.policy_id = 1
        mp.record_num = 0

        mv = ModelVariable()
        mv.settings = settings
        mv.modelpoint = mp

        @assign(mv)
        def mv_formula(t):
            return 2

        mv.calculate()

        assert mv.result == [[2, 2, 2, 2]]
        assert mv(1) == 2
        assert mv(2000) == 0


class TestModel(TestCase):
    def test_model(self):
        modelpoint_module = importlib.import_module("tests.fix2.modelpoint")
        model_module = importlib.import_module("tests.fix2.model")
        settings = load_settings()
        variables, modelpoints = get_model_input(modelpoint_module, model_module, settings)
        model = Model(variables, modelpoints, settings)
        var_a, var_b, var_c = model.variables

        model.set_children()
        assert var_a.children == []
        assert var_b.children == [var_a]
        assert var_c.children == [var_b]

        model.set_grandchildren()
        assert var_a.grandchildren == []
        assert var_b.grandchildren == [var_a]
        assert var_c.grandchildren == [var_b, var_a]

        model.set_queue()
        assert model.queue == [var_a, var_b, var_c]

        model.set_empty_output()
        assert model.empty_output["policy"].equals(pd.DataFrame(columns=["t", "r", "var_a", "var_b", "var_c"]))

        model.calculate_all_policies()
        t_max = model.settings.get("T_CALCULATION_MAX") + 1
        output = pd.DataFrame({
            "t": list(range(t_max)) * len(model.get_modelpoint("policy")),
            "r": 1,
            "var_a": 2,
            "var_b": 4,
            "var_c": 8,
        })
        assert model.output["policy"].reset_index(drop=True).equals(output.reset_index(drop=True))
