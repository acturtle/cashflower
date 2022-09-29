from unittest import TestCase

from cashflower import *
from cashflower.start import load_settings


class TestAssign(TestCase):
    def test_assign(self):
        my_var = ModelVariable()

        assert my_var.assigned_formula is None

        @assign(my_var)
        def my_func(t):
            return t

        assert my_var.assigned_formula == my_func


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

        assert mv.assigned_formula == mv_formula

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

        mv.name = "mv"
        mv.formula = mv.assigned_formula
        mv.calculate()

        assert mv.result == [[2, 2, 2, 2]]
        assert mv(1) == 2
        assert mv(2000) == 0

    def test_model_variable_measures_runtime(self):
        settings = {
            "T_CALCULATION_MAX": 1,
            "POLICY_ID_COLUMN": "POLICY_ID",
        }

        mp = ModelPoint(data=pd.DataFrame({"POLICY_ID": [1]}))
        mp.settings = settings
        mp.policy_id = 1
        mp.record_num = 0

        mv = ModelVariable(modelpoint=mp)
        mv.name = "mv"
        mv.settings = settings

        @assign(mv)
        def mv_formula(t):
            time.sleep(1)
            return 0

        mv.formula = mv.assigned_formula

        assert mv.runtime == 0
        mv.calculate()
        assert mv.runtime > 0


class TestModel(TestCase):
    def test_model_sets_grandchildren(self):
        a = ModelVariable(name="a")
        b = ModelVariable(name="b")
        c = ModelVariable(name="c")
        d = ModelVariable(name="d")
        e = ModelVariable(name="e")
        f = ModelVariable(name="f")
        g = ModelVariable(name="g")

        a.children = [b, c]
        b.children = [d, e, f]
        e.children = [g]

        variables = [a, b, c, d, e, f]
        modelpoints = []
        settings = {}
        model = Model(variables, modelpoints, settings)
        model.set_grandchildren()

        assert a.grandchildren == [b, c, d, e, f, g]
        assert b.grandchildren == [d, e, f, g]
        assert e.grandchildren == [g]
