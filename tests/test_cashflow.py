from unittest import TestCase

from cashflower.cashflow import assign, ModelVariable, Model


class TestAssign(TestCase):
    def test_assign(self):
        my_var = ModelVariable()

        assert my_var.assigned_formula is None

        @assign(my_var)
        def my_func(t):
            return t

        assert my_var.assigned_formula == my_func


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
        model = Model("test", variables, [], modelpoints, settings)
        model.set_grandchildren()

        assert a.grandchildren == [b, c, d, e, f, g]
        assert b.grandchildren == [d, e, f, g]
        assert e.grandchildren == [g]
