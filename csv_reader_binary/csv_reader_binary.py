import csv
from bisect import bisect_left


class CSVDataProcessor:
    def __init__(self, csv_file):
        self.data = []
        self.row_labels = []
        self.col_labels = []
        self.load_data(csv_file)

    def load_data(self, csv_file):
        with open(csv_file, 'r') as file:
            csv_reader = csv.reader(file)
            self.col_labels = next(csv_reader)[1:]  # First row contains column labels
            for row in csv_reader:
                row_label = int(row[0])
                values = list(map(float, row[1:]))
                self.row_labels.append(row_label)
                self.data.append(values)

    def get_value(self, row_label, col_label):
        row_index = bisect_left(self.row_labels, row_label)

        if row_index < len(self.row_labels) and self.row_labels[row_index] == row_label:
            col_index = self.col_labels.index(col_label)
            return self.data[row_index][col_index]
        else:
            return None


# Example usage
csv_file_path = 'data.csv'  # Replace with the actual path to your CSV file
data_processor = CSVDataProcessor(csv_file_path)

row_label_to_lookup = 3
col_label_to_lookup = 'B'
result = data_processor.get_value(row_label_to_lookup, col_label_to_lookup)

if result is not None:
    print(f"Value at row {row_label_to_lookup}, col {col_label_to_lookup}: {result}")
else:
    print(f"Value not found for row {row_label_to_lookup}, col {col_label_to_lookup}")
