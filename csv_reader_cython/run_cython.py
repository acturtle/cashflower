from csv_reader_cython import CSVReaderCython

reader = CSVReaderCython("disc_rate_ann.csv")
value = reader.get_value("140", "zero_spot")
print(value)
