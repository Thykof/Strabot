from trabot.stream import *

class BaseTestMod(object):
    def setup_method(self, test_method):
        pass

class TestClient(BaseTestMod):
    def test_read_seq(self):
        steps, seq = read_seq('data/seq_test')
        assert steps == [0, 1, 2, 3, 4, 5, 6, 7]
        assert seq == [0, 5, 9, 31, 5.2, 2.00645214, 3.031641, 14.1]
