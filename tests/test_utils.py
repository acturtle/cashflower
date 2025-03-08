from unittest import TestCase

from cashflower.utils import get_first_indexes, get_object_by_name, log_message, split_to_chunks, update_progressbar


class TestSplitToChunks(TestCase):
    def test_split_to_chunks(self):
        assert split_to_chunks(20, 3) == [(0, 6), (6, 12), (12, 20)]
        assert split_to_chunks(2, 3) == [(0, 2)]


class TestGetObjectByName(TestCase):
    def test_get_object_by_name(self):
        class Object:
            def __init__(self, name):
                self.name = name

        a = Object(name="a")
        b = Object(name="b")
        objects = [a, b]

        assert get_object_by_name(objects, "a") == a
        assert get_object_by_name(objects, "c") is None


class TestPrintFunctions(TestCase):
    def test_print_functions(self):
        assert update_progressbar(100, 20) is None
        assert update_progressbar(100, 110) is None
        assert log_message("my message") is None


class TestGetFirstIndexes(TestCase):
    def test_get_first_indexes(self):
        assert get_first_indexes(["A", "A", "B", "A", "C", "D"]) == [0, 2, 4, 5]
