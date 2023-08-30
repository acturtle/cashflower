import csv

cdef class CSVReaderCython:
    cdef str filename
    cdef dict data
    cdef dict row_index
    cdef dict col_index

    def __init__(self, str filename):
        self.filename = filename
        self.data = {}
        self.load_data()

    cdef void load_data(self):
        cdef int i, col_idx
        cdef str row_label, col_label, cell_value

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
                            self.data[row_label, col_label] = cell_value

    cpdef str get_value(self, str row_label, str col_label):
        return self.data.get((row_label, col_label), None)
