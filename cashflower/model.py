from functools import lru_cache


T_MAX = 1440


class ModelPoint:
    def __init__(self, data, record_num=0):
        self.data = data
        self.record_num = record_num

    def get(self, attribute):
        return self.data.iloc[self.record_num][attribute]

    def set_record_num(self, value):
        self.record_num = value


class ModelVariable:
    def __init__(self, function):
        self.function = function
        self.name = function.__name__
        self.result = [None] * T_MAX

    @lru_cache
    def formula(self, t):
        return self.function(t)

    def __call__(self, t):
        if not self.result[t]:
            self.result[t] = self.formula(t)
        return self.result[t]
