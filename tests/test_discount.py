import numpy as np
import pytest
from unittest import TestCase

from cashflower import discount, variable
from cashflower.error import CashflowModelError


class TestDiscountFunction(TestCase):
    def test_discount(self):
        cash_flows = np.array([100, 200, 300], dtype=np.float64)
        discount_rates = np.array([0.9, 0.8, 0.7], dtype=np.float64)
        expected_result = np.array([428., 410., 300.], dtype=np.float64)
        result = discount(cash_flows, discount_rates)
        np.testing.assert_array_almost_equal(result, expected_result, decimal=6)


class TestDiscountInVariable(TestCase):
    """The discount() function returns the values for all the periods at once."""

    @staticmethod
    def calculate_components(t_max):
        @variable()
        def cash_flow(t):
            return t

        @variable()
        def discount_rate(t):
            return 1 / (1 + t)

        for v in (cash_flow, discount_rate):
            v.result = np.empty(t_max)
            v.calc_direction = 0
            v.calculate()

        return cash_flow, discount_rate

    def test_discount_needs_an_array_variable(self):
        cash_flow, discount_rate = self.calculate_components(3)

        @variable()
        def present_value():
            return discount(cash_flows=cash_flow(), discount_rates=discount_rate())

        present_value.result = np.empty(3)
        with pytest.raises(CashflowModelError, match="array=True"):
            present_value.calculate()

    def test_discount_works_in_an_array_variable(self):
        cash_flow, discount_rate = self.calculate_components(3)

        @variable(array=True)
        def present_value():
            return discount(cash_flows=cash_flow(), discount_rates=discount_rate())

        present_value.calculate()
        expected_result = discount(cash_flow(), discount_rate())
        np.testing.assert_array_almost_equal(present_value.result, expected_result, decimal=6)
