from unittest import TestCase

from cashflower.admin import *


class TestCreateModel(TestCase):
    def test_create_model(self):
        create_model("annuity")
        assert os.path.exists("./annuity/input.py")
        assert os.path.exists("./annuity/model.py")
        assert os.path.exists("./annuity/run.py")
        assert os.path.exists("./annuity/settings.py")
        shutil.rmtree("./annuity")
