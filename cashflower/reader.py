import csv
from collections import defaultdict


class CSVReader:
    def __init__(self, filename):
        self.filename = filename
        self.data = defaultdict(dict)
        self.row_index = None
        self.col_index = None
        self.load_data()

    def load_data(self):
        with open(self.filename, 'r') as file:
            reader = csv.reader(file)
            header = next(reader)
            self.row_index = {row[0]: i for i, row in enumerate(reader)}
            self.col_index = {label: i for i, label in enumerate(header[1:])}

            file.seek(0)  # Reset the file pointer to the beginning
            next(reader)  # Skip the header line

            for row in reader:
                row_label = row[0]
                if row_label in self.row_index:
                    for col_label, cell_value in zip(header[1:], row[1:]):
                        if col_label in self.col_index:
                            self.data[row_label][col_label] = cell_value

    def get_value(self, row_label, col_label):
        value = self.data.get(row_label, {}).get(col_label, None)
        if value is not None:
            return value
        else:
            raise ValueError("Row or column label not found.")
