import argparse
import pytest

from unittest import TestCase
from unittest.mock import Mock

from cashflower.core import *
from cashflower.start import *


@variable()
def level_first(t):
    return 1


@variable()
def level_second(t):
    return 2


@variable()
def level_total(t):
    return level_first(t) + level_second(t)


@variable()
def recursive_forward(t):
    if t == 0:
        return 0
    return recursive_forward(t - 1) + 1


@variable()
def recursive_backward(t):
    if t == 10:
        return 0
    return recursive_backward(t + 1) + 1


@variable()
def runtime_first(t):
    return 1


@variable()
def runtime_second(t):
    return 2


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
            "GROUP_BY": None,
            "MULTIPROCESSING": False,
            "NUM_STOCHASTIC_SCENARIOS": None,
            "OUTPUT_VARIABLES": None,
            "SAVE_DIAGNOSTIC": False,
            "SAVE_LOG": False,
            "SAVE_OUTPUT": True,
            "T_MAX_CALCULATION": 720,
            "T_MAX_OUTPUT": 720,
        }
        assert get_settings() == default_settings

        my_settings1 = {}
        settings = get_settings(my_settings1)
        assert settings == default_settings

        my_settings2 = {
            "T_MAX_CALCULATION": 100,
            "OUTPUT_VARIABLES": ["a", "b", "c"],
        }
        settings = get_settings(my_settings2)
        assert settings == {
            "GROUP_BY": None,
            "MULTIPROCESSING": False,
            "NUM_STOCHASTIC_SCENARIOS": None,
            "OUTPUT_VARIABLES": ["a", "b", "c"],
            "SAVE_DIAGNOSTIC": False,
            "SAVE_LOG": False,
            "SAVE_OUTPUT": True,
            "T_MAX_CALCULATION": 100,
            "T_MAX_OUTPUT": 100,
        }


class TestGetRunplan(TestCase):
    def test_get_runplan(self):
        runplan = Runplan(data=pd.DataFrame({"version": [1]}))
        input_members = [("foo", "foo"), ("runplan", runplan), ("bar", "bar")]
        assert get_runplan(input_members) == runplan


class TestGetModelPointSets(TestCase):
    def test_get_model_point_sets(self):
        main = ModelPointSet(data=pd.DataFrame({"id": [1]}))
        input_members_1 = [("main", main)]
        settings = get_settings()
        model_point_sets = get_model_point_sets(input_members_1, settings)
        assert model_point_sets == [main]


class TestGetVariables(TestCase):
    def test_get_variables(self):
        settings = get_settings()

        @variable()
        def foo(t):
            return t

        model_members = [("foo", foo), ("bar", "bar")]
        variables = get_variables(model_members, settings)
        assert variables == [foo]

    def test_get_variables_raises_error_when_name_is_t_or_r(self):
        settings = get_settings()

        @variable()
        def t(t):
            return 1

        model_members = [("foo", "foo"), ("t", t)]
        with pytest.raises(CashflowModelError):
            get_variables(model_members, settings)


class TestDetermineCalculationOrder:
    @staticmethod
    def test_independent_variables_share_calculation_level():
        variables = determine_calculation_order(
            [level_first, level_second, level_total],
            {"OUTPUT_VARIABLES": None},
        )
        calculation_order = {v.name: v.calc_order for v in variables}

        assert calculation_order == {"level_first": 1, "level_second": 1, "level_total": 2}

    @staticmethod
    def test_independent_recursive_variables_keep_their_own_direction():
        variables = determine_calculation_order(
            [recursive_forward, recursive_backward],
            {"OUTPUT_VARIABLES": None},
        )
        calculation = {v.name: (v.calc_order, v.calc_direction) for v in variables}

        assert calculation == {"recursive_backward": (1, -1), "recursive_forward": (1, 1)}

    @staticmethod
    def test_variables_at_same_level_are_not_calculated_as_cycle():
        variables = determine_calculation_order(
            [runtime_first, runtime_second],
            {"OUTPUT_VARIABLES": None},
        )
        for item in variables:
            item.result = np.empty(1)
            item.calculate = Mock(wraps=item.calculate)

        model_point_set = ModelPointSet(pd.DataFrame({"id": [1]}))
        model = Model(
            variables,
            [model_point_set],
            {
                "OUTPUT_VARIABLES": None,
                "T_MAX_CALCULATION": 0,
                "T_MAX_OUTPUT": 0,
            },
        )

        model.calculate_model_point(0, one_core=False, progressbar_max=1)

        assert all(item.calculate.call_count == 1 for item in variables)
