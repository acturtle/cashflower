from unittest import TestCase

from cashflower.start import *


class TestLoadSettings(TestCase):
    def test_load_settings(self):
        default_settings = {
            "AGGREGATE": True,
            "MULTIPROCESSING": False,
            "OUTPUT_COLUMNS": [],
            "POLICY_ID_COLUMN": "id",
            "SAVE_RUNTIME": False,
            "T_CALCULATION_MAX": 1200,
            "T_OUTPUT_MAX": 1200,
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
            "AGGREGATE": True,
            "MULTIPROCESSING": False,
            "OUTPUT_COLUMNS": ["a", "b", "c"],
            "POLICY_ID_COLUMN": "polnumber",
            "SAVE_RUNTIME": False,
            "T_CALCULATION_MAX": 100,
            "T_OUTPUT_MAX": 1200,
        }
