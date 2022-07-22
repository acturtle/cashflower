
T_MAX = 1440


class ModelVariable:
    def __init__(self, function):
        self.function = function
        self.name = function.__name__
        self.result = [None] * T_MAX

    def __call__(self, t):
        if not self.result[t]:
            self.result[t] = self.function(t)
        return self.result[t]
