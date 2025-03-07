import numpy as np
from unittest import TestCase

from cashflower import discount  # Replace 'your_module' with the actual module name


class TestDiscountFunction(TestCase):
    def test_discount(self):
        cash_flows = np.array([100, 200, 300], dtype=np.float64)
        discount_rates = np.array([0.9, 0.8, 0.7], dtype=np.float64)
        expected_result = np.array([428., 410., 300.], dtype=np.float64)
        result = discount(cash_flows, discount_rates)
        np.testing.assert_array_almost_equal(result, expected_result, decimal=6)
