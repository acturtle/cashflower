import pytest

from pandas.testing import assert_frame_equal
from unittest import TestCase

from cashflower.start import *
from cashflower.cashflow import *
from cashflower.utils import get_object_by_name


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


class TestGetColDict(TestCase):
    def test_get_col_dict(self):
        settings = load_settings()
        main = ModelPointSet(data=pd.DataFrame({"id": [1]}), name="main")
        premium = ModelVariable(name="premium", model_point_set=main)
        col_dict = get_col_dict(model_point_sets=[main], variables=[premium], constants=[], settings=settings)
        output_dict = {
            "main": {
                "ModelVariable": ["premium"],
                "Constant": []
            }
        }
        assert col_dict == output_dict

    def test_get_col_dict_with_column_subset(self):
        settings = load_settings()
        settings["OUTPUT_COLUMNS"] = ["b"]
        main = ModelPointSet(data=pd.DataFrame({"id": [1]}), name="main")
        a = ModelVariable(name="a", model_point_set=main)
        b = ModelVariable(name="b", model_point_set=main)
        col_dict = get_col_dict(model_point_sets=[main], variables=[a, b], constants=[], settings=settings)
        output_dict = {
            "main": {
                "ModelVariable": ["b"],
                "Constant": []
            }
        }
        assert col_dict == output_dict

    def test_get_col_dict_with_constant(self):
        settings = load_settings()
        settings["AGGREGATE"] = False
        main = ModelPointSet(data=pd.DataFrame({"id": [1]}), name="main")
        a = ModelVariable(name="a", model_point_set=main)
        b = Constant(name="b", model_point_set=main)
        col_dict = get_col_dict(model_point_sets=[main], variables=[a], constants=[b], settings=settings)
        output_dict = {
            "main": {
                "ModelVariable": ["a"],
                "Constant": ["b"]
            }
        }
        assert col_dict == output_dict


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

    def test_runplan_raises_error_when_non_existent_attribute_is_get(self):
        runplan = Runplan(data=pd.DataFrame({
            "version": [1, 2],
            "value": [57, 89]
        }))
        with pytest.raises(CashflowModelError):
            runplan.get("foo")


class TestModelPointSet(TestCase):
    def test_model_point_set(self):
        main = ModelPointSet(data=pd.DataFrame({
            "id": [1, 2, 3],
            "age": [52, 47, 35]
        }))
        assert len(main) == 3

        main.name = "main"
        main.settings = load_settings()
        main.initialize()
        assert main.id == "1"
        assert main.model_point_record_num == 0
        assert main.model_point_size == 1
        assert main.get("age") == 52
        assert repr(main) == "ModelPointSet: main"

        with pytest.raises(CashflowModelError):
            main.id = 4

    def test_model_point_set_raises_error_when_no_policy_id_col(self):
        main = ModelPointSet(
            data=pd.DataFrame({"age": [52, 47, 35]}),
            name="policy",
            settings=load_settings()
        )
        with pytest.raises(CashflowModelError):
            main.initialize()

    def test_model_point_set_raises_error_when_no_unique_keys(self):
        main = ModelPointSet(
            data=pd.DataFrame({"id": [1, 2, 2]}),
            name="main",
            settings=load_settings()
        )
        with pytest.raises(CashflowModelError):
            main.initialize()


class TestModelVariable(TestCase):
    def test_model_variable(self):
        premium = ModelVariable()

        @assign(premium)
        def _mv(t):
            pass

        assert premium.assigned_formula == _mv

        premium.name = "premium"
        assert repr(premium) == "ModelVariable: premium"

    def test_model_variable_is_lower_when_fewer_grandchildren(self):
        mv = ModelVariable()
        other_mv = ModelVariable()
        mv.grandchildren = [1, 2, 3]
        other_mv.grandchildren = [1, 3]
        assert mv > other_mv

    def test_model_variable_gets_called(self):
        settings = load_settings()
        policy = ModelPointSet(
            data=pd.DataFrame({"id": [1]}),
            name="policy",
            settings=settings
        )
        policy.initialize()

        mv = ModelVariable(name="mv", model_point_set=policy, settings=load_settings())

        @assign(mv)
        def mv_formula(t):
            return t

        mv.initialize()
        mv.calculate()
        assert mv(5) == 5
        assert mv(-1) == 0
        assert mv(3, 0) == 3

    def test_model_variable_raises_error_when_formula_has_no_parameter_t(self):
        policy = ModelPointSet(pd.DataFrame({"id": [1]}))
        mv = ModelVariable(name="mv", model_point_set=policy, settings=load_settings())

        @assign(mv)
        def mv_formula():
            return 0

        with pytest.raises(CashflowModelError):
            mv.initialize(policy)

    def test_model_variable_calculates_for_recursive_formula(self):
        settings = load_settings()

        policy = ModelPointSet(
            data=pd.DataFrame({"id": [1]}),
            name="policy",
            settings=settings
        )
        policy.initialize()

        mv_1 = ModelVariable(name="mv_1", model_point_set=policy, settings=settings)
        mv_2 = ModelVariable(name="mv_2", model_point_set=policy, settings=settings)

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

        policy = ModelPointSet(
            data=pd.DataFrame({"id": [1]}),
            name="policy",
            settings=settings
        )
        policy.initialize()

        mv = ModelVariable(name="mv", settings=settings)

        @assign(mv)
        def mv_formula(t):
            return t

        mv.initialize(policy)
        assert mv.model_point_set == policy


class TestConstant(TestCase):
    def test_constant(self):
        premium = Constant()

        @assign(premium)
        def _c():
            pass

        assert premium.assigned_formula == _c

        premium.name = "premium"
        assert repr(premium) == "Constant: premium"

    def test_constant_is_lower_when_fewer_grandchildren(self):
        p1 = Constant()
        p2 = Constant()

        p1.grandchildren = [1, 2, 3]
        p2.grandchildren = [4, 5]
        assert p1 > p2

    def test_constant_gets_called(self):
        policy = ModelPointSet(
            data=pd.DataFrame({"id": [1]}),
            name="policy",
            settings=load_settings()
        )
        policy.initialize()
        p = Constant(name="p", model_point_set=policy)

        @assign(p)
        def mv_formula():
            return 10

        p.initialize()
        p.calculate()
        assert p() == 10
        assert p(0) == 10
        with pytest.raises(CashflowModelError):
            p(1)

    def test_constant_raises_error_when_formula_has_parameters(self):
        p = Constant()

        @assign(p)
        def mv_formula(x):
            return x

        p.name = "p"
        with pytest.raises(CashflowModelError):
            p.initialize()

    def test_constant_raises_error_when_no_asigned_formula(self):
        p = Constant()
        with pytest.raises(CashflowModelError):
            p.initialize()


class TestModel(TestCase):
    def test_get_component_by_name(self):
        m = ModelVariable(name="my-variable")
        p = Constant(name="my-parameter")
        model = Model(None, [m], [p], None, None)
        assert get_object_by_name(model.components, "my-variable") == m
        assert get_object_by_name(model.components, "my-parameter") == p

    def test_get_model_point_set_by_name(self):
        mps = ModelPointSet(data=None, name="my-model-point-set")
        model = Model(None, [], [], [mps], None)
        assert get_object_by_name(model.model_point_sets, "my-model-point-set") == mps

    def test_set_children(self):
        a = ModelVariable(name="a")
        b = ModelVariable(name="b")
        c = Constant(name="c")

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

    def test_set_grandchildren(self):
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

        settings = load_settings()
        model = Model(None, [a, b, c], [], None, settings)
        model.set_queue()
        assert model.queue == [c, b, a]

    def test_queue_with_columns_subset(self):
        settings = load_settings()

        a = ModelVariable(name="a")
        b = ModelVariable(name="b")
        c = ModelVariable(name="c")

        a.grandchildren = [c]
        b.grandchildren = [c]
        c.grandchildren = []

        settings["OUTPUT_COLUMNS"] = ["a", "c"]
        model = Model(None, [a, b, c], [], None, settings)
        model.set_queue()
        assert model.queue == [c, a]

    def test_queue_with_columns_subset_and_unnecessary_col(self):
        settings = load_settings()

        a = ModelVariable(name="a")
        b = ModelVariable(name="b")
        c = ModelVariable(name="c")

        a.grandchildren = [c]
        b.grandchildren = [c]
        c.grandchildren = []

        settings["OUTPUT_COLUMNS"] = ["a", "z", "c"]
        model = Model(None, [a, b, c], [], None, settings)
        model.set_queue()

        assert model.queue == [c, a]

    def test_queue_with_cycle(self):
        settings = load_settings()

        a = ModelVariable(name="a")
        b = ModelVariable(name="b")
        c = ModelVariable(name="c")

        a.children = [b]
        b.children = [c]
        c.children = [a]

        model = Model(None, [a, b, c], [], None, settings)
        model.set_grandchildren()
        with pytest.raises(CashflowModelError):
            model.set_queue()

    def test_calculate_model_point(self):
        settings = load_settings()
        main = ModelPointSet(data=pd.DataFrame({"id": [1]}), name="main")

        premium = ModelVariable(name="premium", model_point_set=main, settings=settings)

        @assign(premium)
        def mv_formula(t):
            return 1

        premium.initialize()

        model = Model(None, [premium], [], [main], settings)
        model.initialize()
        col_dict = get_col_dict(model.model_point_sets, model.variables, model.constants, model.settings)
        model_point_output = model.calculate_model_point(0, 1, main, col_dict)
        left = model_point_output["main"]["ModelVariable"][:, 0]
        right = np.array([1.0] * (settings.get("T_OUTPUT_MAX") + 1))
        assert all(left == right)

    def test_calculate(self):
        settings = load_settings()
        main = ModelPointSet(data=pd.DataFrame({"id": [1, 2]}), name="main")

        premium = ModelVariable(name="a", model_point_set=main, settings=settings)

        @assign(premium)
        def premium_formula(t):
            return t + 100

        premium.initialize()

        # Aggregated output
        model = Model(None, [premium], [], [main], settings)
        model.initialize()

        model_output = model.calculate_model()
        test_output = pd.DataFrame({
            "a": [2 * (i + 100) for i in range(1201)]
        })

        assert_frame_equal(model_output["main"], test_output, check_dtype=False)

        # Individual output
        settings["AGGREGATE"] = False
        model = Model(None, [premium], [], [main], settings)
        model.initialize()

        model_output = model.calculate_model()
        test_output = pd.DataFrame({
            "r": [1 for _ in range(1201 * 2)],
            "a": [(i + 100) for i in range(1201)] * 2
        })

        assert_frame_equal(model_output["main"].reset_index(drop=True), test_output.reset_index(drop=True), check_dtype=False)

    def test_run(self):
        settings = load_settings()
        main = ModelPointSet(data=pd.DataFrame({"id": [1, 2]}), name="main")

        premium = ModelVariable(name="a", model_point_set=main, settings=settings)

        @assign(premium)
        def premium_formula(t):
            return t + 100

        premium.initialize()

        test_output = pd.DataFrame({"a": [2 * (i + 100) for i in range(1201)]})

        model = Model(None, [premium], [], [main], settings)
        model_output, _ = model.run()
        assert_frame_equal(model_output["main"], test_output, check_dtype=False)
