import pandas as pd

from functools import lru_cache


class ModelPoint:
    def __init__(self, data, record_num=0):
        self.data = data
        self.record_num = record_num

    def __len__(self):
        return self.data.shape[0]

    def get(self, attribute):
        return self.data.iloc[self.record_num][attribute]

    def set_record_num(self, value):
        self.record_num = value


class ModelVariable:
    def __init__(self, function, settings):
        self.function = function
        self.settings = settings
        self.name = function.__name__
        self.result = [None] * self.settings["T_MAX"]

    def __call__(self, t):
        if not self.result[t]:
            self.result[t] = self.formula(t)
        return self.result[t]

    @lru_cache
    def formula(self, t):
        return self.function(t)

    def clear(self):
        self.result = [None] * self.settings["T_MAX"]

    def calculate(self):
        self.result = [self(t) for t in range(self.settings["T_MAX"])]


class Model:
    def __init__(self, model_point, model_variables):
        self.model_point = model_point
        self.model_variables = model_variables
        self.output = None

    def calculate(self):
        output = pd.DataFrame()
        for i in range(len(self.model_point)):
            policy_output = pd.DataFrame()
            for model_variable in self.model_variables:
                model_variable.clear()
                model_variable.calculate()
                policy_output[model_variable.name] = model_variable.result
            self.model_point.record_num += 1
            output = pd.concat([output, policy_output])
        self.output = output
