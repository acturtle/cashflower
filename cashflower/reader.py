import csv
from collections import defaultdict


class CSVReader:
    def __init__(self, filename, num_row_label_cols=1):
        self.filename = filename
        self.n = num_row_label_cols
        self.data = defaultdict(dict)
        self.row_index = None
        self.col_index = None
        if self.n == 1:
            self.load_data_n_equal_1()
        else:
            self.load_data_n_greater_than_1()

    def __getitem__(self, key):
        row_label, col_label = key
        return self.get_value(row_label, col_label)

    def load_data_n_equal_1(self):
        with open(self.filename, 'r') as file:
            reader = csv.reader(file)
            header = next(reader)
            self.row_index = {row[0]: i for i, row in enumerate(reader)}
            self.col_index = {label: i for i, label in enumerate(header[1:])}

            file.seek(0)
            next(reader)

            for row in reader:
                row_label = row[0]
                if row_label in self.row_index:
                    for col_label, cell_value in zip(header[1:], row[1:]):
                        if col_label in self.col_index:
                            self.data[row_label][col_label] = cell_value

    def load_data_n_greater_than_1(self):
        with open(self.filename, 'r') as file:
            reader = csv.reader(file)
            header = next(reader)
            self.row_index = {tuple(row[:self.n]): i for i, row in enumerate(reader)}
            self.col_index = {label: i for i, label in enumerate(header[self.n:])}

            file.seek(0)
            next(reader)

            for row in reader:
                row_label = tuple(row[:self.n])
                if row_label in self.row_index:
                    for col_label, cell_value in zip(header[self.n:], row[self.n:]):
                        if col_label in self.col_index:
                            self.data[row_label][col_label] = cell_value

    def get_value(self, row_label, col_label):
        value = self.data.get(row_label, {}).get(col_label, None)
        if value is not None:
            return value
        else:
            raise ValueError(f"Row '{row_label}' or column '{col_label}' label not found in '{self.filename}'.\n"
                             f"Please ensure that row label(s) and column label are strings.")
