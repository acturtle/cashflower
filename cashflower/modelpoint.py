class ModelPoint:
    def __init__(self, data):
        self.data = data

    def get(self, attribute):
        return self.data.iloc[0][attribute]
