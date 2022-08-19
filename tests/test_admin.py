import os
import shutil

from unittest import TestCase

from cashflower.admin import create_model


class TestCreateModel(TestCase):
    def test_create_model(self):
        create_model("annuity")
        assert os.path.exists("annuity")
        assert os.path.exists("annuity/assumption.py")
        assert os.path.exists("annuity/model.py")
        assert os.path.exists("annuity/modelpoint.py")
        assert os.path.exists("annuity/run.py")
        assert os.path.exists("annuity/settings.py")
        shutil.rmtree("annuity")
