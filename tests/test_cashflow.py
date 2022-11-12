import pytest

from pandas.testing import assert_frame_equal
from unittest import TestCase

from cashflower.start import *
from cashflower.cashflow import *


class TestAssign(TestCase):
    def test_assign(self):
        my_var = ModelVariable()
        assert my_var.assigned_formula is None

        @assign(my_var)
        def my_func(t):
            return t

        assert my_var.assigned_formula == my_func


class TestUpdt(TestCase):
    def test_updt(self):
        assert updt(100, 20) is None
        assert updt(100, 110) is None


class TestRunplan(TestCase):
    def test_runplan(self):
        runplan = Runplan(data=pd.DataFrame({
            "version": [1, 2],
            "value": [57, 89]
        }))
        assert runplan.version == "1"
        assert runplan.get("value") == 57

        empty_runplan = Runplan()
        assert empty_runplan.version == "1"

    def test_runplan_raises_error_when_no_version_column(self):
        with pytest.raises(CashflowModelError):
            Runplan(data=pd.DataFrame({"a": [1, 2, 3]}))


class TestModelPoint(TestCase):
    def test_model_point(self):
        policy = ModelPoint(data=pd.DataFrame({
            "policy_id": [1, 2, 3],
            "age": [52, 47, 35]
        }))
        print(policy)
        assert len(policy) == 3

        policy.name = "policy"
        policy.settings = load_settings()
        policy.initialize()
        assert policy.policy_id == "1"
        assert policy.record_num == 0
        assert policy.size == 1
        assert policy.get("age") == 52

        with pytest.raises(CashflowModelError):
            policy.policy_id = 4

    def test_model_point_raises_error_when_no_policy_id_col(self):
        policy = ModelPoint(
            data=pd.DataFrame({"age": [52, 47, 35]}),
            name="policy",
            settings=load_settings()
        )
        with pytest.raises(CashflowModelError):
            policy.initialize()

    def test_policy_raises_error_when_no_unique_keys(self):
        policy = ModelPoint(
            data=pd.DataFrame({"policy_id": [1, 2, 2]}),
            name="policy",
            settings=load_settings()
        )
        with pytest.raises(CashflowModelError):
            policy.initialize()


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

    def test_model_variable_gets_called(self):
        policy = ModelPoint(
            data=pd.DataFrame({"policy_id": [1]}),
            name="policy",
            settings=load_settings()
        )
        policy.initialize()

        mv = ModelVariable(name="mv", modelpoint=policy, settings=load_settings())

        @assign(mv)
        def mv_formula(t):
            return t

        mv.initialize()
        mv.calculate()
        assert mv(5) == 5
        assert mv(-1) == 0
        assert mv(3, 0) == 3

    def test_model_variable_raises_error_when_formula_has_no_parameter_t(self):
        policy = ModelPoint(pd.DataFrame({"policy_id": [1]}))
        mv = ModelVariable(name="mv", modelpoint=policy, settings=load_settings())

        @assign(mv)
        def mv_formula():
            return 0

        with pytest.raises(CashflowModelError):
            mv.initialize(policy)

    def test_model_variable_calculates_for_recursive_formula(self):
        settings = load_settings()

        policy = ModelPoint(
            data=pd.DataFrame({"policy_id": [1]}),
            name="policy",
            settings=settings
        )
        policy.initialize()

        mv_1 = ModelVariable(name="mv_1", modelpoint=policy, settings=settings)
        mv_2 = ModelVariable(name="mv_2", modelpoint=policy, settings=settings)

        @assign(mv_1)
        def mv_1_formula(t):
            if t == 0:
                return 0
            return mv_1(t-1) + 2

        @assign(mv_2)
        def mv_2_formula(t):
            if t == settings["T_CALCULATION_MAX"]:
                return 100
            return mv_2(t + 1) - 1

        mv_1.initialize()
        mv_2.initialize()
        mv_1.calculate()
        mv_2.calculate()

        assert mv_1(1) == 2
        assert mv_2(1199) == 99

    def test_model_variable_raises_error_when_no_assigned_formula(self):
        mv = ModelVariable(name="mv")
        with pytest.raises(CashflowModelError):
            mv.initialize()

    def test_model_variable_has_policy_model_point_by_default(self):
        settings=load_settings()

        policy = ModelPoint(
            data=pd.DataFrame({"policy_id": [1]}),
            name="policy",
            settings=settings
        )
        policy.initialize()

        mv = ModelVariable(name="mv", settings=settings)

        @assign(mv)
        def mv_formula(t):
            return t

        mv.initialize(policy)
        assert mv.modelpoint == policy


class TestParameter(TestCase):
    def test_parameter(self):
        Parameter()

    def test_parameter_is_lower_when_fewer_grandchildren(self):
        p1 = Parameter()
        p2 = Parameter()

        p1.grandchildren = [1, 2, 3]
        p2.grandchildren = [4, 5]
        assert p1 > p2

    def test_parameter_gets_called(self):
        policy = ModelPoint(
            data=pd.DataFrame({"policy_id": [1]}),
            name="policy",
            settings=load_settings()
        )
        policy.initialize()
        p = Parameter(name="p", modelpoint=policy)

        @assign(p)
        def mv_formula():
            return 10

        p.initialize()
        p.calculate()
        assert p() == 10

    def test_parameter_raises_error_when_formula_has_parameters(self):
        p = Parameter()

        @assign(p)
        def mv_formula(x):
            return x

        p.name = "p"
        with pytest.raises(CashflowModelError):
            p.initialize()

    def test_parameter_raises_error_when_no_asigned_formula(self):
        p = Parameter()
        with pytest.raises(CashflowModelError):
            p.initialize()


class TestModel(TestCase):
    def test_get_component_by_name(self):
        m = ModelVariable(name="my-variable")
        p = Parameter(name="my-parameter")
        model = Model(None, [m], [p], None, None)
        assert model.get_component_by_name("my-variable") == m
        assert model.get_component_by_name("my-parameter") == p

    def test_get_modelpoint_by_name(self):
        mp = ModelPoint(data=None, name="my-model-point")
        model = Model(None, [], [], [mp], None)
        assert model.get_modelpoint_by_name("my-model-point") == mp

    def test_model_sets_children(self):
        a = ModelVariable(name="a")
        b = ModelVariable(name="b")
        c = Parameter(name="c")

        @assign(a)
        def a_formula(t):
            return b(t) + c() + t

        @assign(b)
        def b_formula(t):
            return c() * t

        @assign(c)
        def c_formula():
            return 10

        a.initialize()
        b.initialize()
        c.initialize()

        model = Model(None, [a, b], [c], None, None)
        model.set_children()
        assert a.children == [b, c]

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
        model = Model(None, variables, [], None, None)
        model.set_grandchildren()

        assert a.grandchildren == [b, c, d, e, f, g]
        assert b.grandchildren == [d, e, f, g]
        assert e.grandchildren == [g]

    def test_remove_from_granchildren(self):
        a = ModelVariable()
        b = ModelVariable()
        c = ModelVariable()

        a.grandchildren = [b, c]
        b.grandchildren = [c]
        c.grandchildren = []

        model = Model(None, [a, b, c], [], None, None)
        model.remove_from_grandchildren(c)
        assert a.grandchildren == [b]
        assert b.grandchildren == []
        assert c.grandchildren == []

    def test_queue(self):
        a = ModelVariable()
        b = ModelVariable()
        c = ModelVariable()

        a.grandchildren = [b, c]
        b.grandchildren = [c]
        c.grandchildren = []

        model = Model(None, [a, b, c], [], None, None)
        model.set_queue()
        assert model.queue == [c, b, a]

    def test_set_empty_output(self):
        settings = load_settings()

        policy = ModelPoint(data=pd.DataFrame({"policy_id": [1, 2, 3]}), name="policy")
        fund = ModelPoint(data=pd.DataFrame({"policy_id": [1, 2, 2, 3]}), name="fund")

        a = ModelVariable(name="a", modelpoint="policy")
        b = Parameter(name="b", modelpoint="policy")
        c = ModelVariable(name="c", modelpoint="fund")

        model = Model(None, [a, c], [b], [policy, fund], settings)
        model.set_empty_output()

        empty_output = {
            "policy": pd.DataFrame({
                "t": None,
                "a": None,
                "b": None
            }),
            "fund": pd.DataFrame(

            ),
        }

        df1 = pd.DataFrame({"a": [1]})
        df2 = pd.DataFrame({"a": [3]})
        assert_frame_equal(df1, df2)
