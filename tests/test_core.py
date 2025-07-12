import pytest

from unittest import TestCase

from cashflower.core import *
from cashflower.start import get_settings
from cashflower.error import CashflowModelError


class TestGetVariableType(TestCase):
    def test_get_variable_type(self):

        def foo(t):
            return t

        v = Variable(func=foo, aggregation_type="sum")
        cv = ConstantVariable(func=foo, aggregation_type="sum")
        av = ArrayVariable(func=foo, aggregation_type="sum")
        sv = StochasticVariable(func=foo, aggregation_type="sum")

        assert get_variable_type(v) == "default"
        assert get_variable_type(cv) == "constant"
        assert get_variable_type(av) == "array"
        assert get_variable_type(sv) == "stochastic"


class TestCheckArguments(TestCase):
    def test_check_arguments_with_correct_setting(self):
        def foo():
            return 1

        check_arguments(foo, array=False)
        check_arguments(foo, array=True)

        def bar(t):
            return t

        check_arguments(bar, array=False)

        def baz(t, stoch):
            return t + stoch

        check_arguments(baz, array=False)

    def test_check_arguments_with_incorrect_setting(self):
        def foo(a):
            return a

        with self.assertRaises(CashflowModelError):
            check_arguments(foo, array=False)

        def bar(t):
            return t

        with self.assertRaises(CashflowModelError):
            check_arguments(bar, array=True)

        def baz(a, b, c):
            return a + b + c

        with self.assertRaises(CashflowModelError):
            check_arguments(baz, array=True)


class TestVariableDecorator(TestCase):
    def test_variable_decorator(self):

        @variable()
        def foo(t):
            return t

        assert isinstance(foo, Variable)

    def test_decorator_must_be_called_with_parentheses(self):
        def foo():
            return 1

        with self.assertRaises(CashflowModelError):
            variable(foo)

    def test_zero_arg_function_becomes_constant_variable(self):
        @variable()
        def foo():
            return 1

        self.assertIsInstance(foo, ConstantVariable)

    def test_zero_arg_array_function_becomes_array_variable(self):
        @variable(array=True)
        def foo():
            return [1, 2, 3]

        self.assertIsInstance(foo, ArrayVariable)

    def test_one_arg_function_becomes_generic_variable(self):
        @variable()
        def foo(t):
            return t

        self.assertIsInstance(foo, Variable)

    def test_two_arg_function_becomes_stochastic_variable(self):
        @variable()
        def foo(t, stoch):
            return t * stoch

        self.assertIsInstance(foo, StochasticVariable)


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

        foo.result = np.empty(720)
        foo.calculate_t(10)
        assert foo(10) == 10

        with pytest.raises(CashflowModelError):
            foo(721)
