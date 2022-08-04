import inspect


def get_cell(df, column, **kwargs):
    """Get a single cell value from a table.

    Parameters
    ----------
    df : data frame
        
    column : column to get a cell from
        
    **kwargs : columns names and values to filter rows
        

    Returns
    -------
    scalar
    """
    if column not in df.columns:
        raise ValueError(f"There is no column {column} in the data frame.")

    for key, val in kwargs.items():
        df = df[df[key] == val]

    # Filtering should return one row from data frame
    if df.shape[0] > 1:
        print(df)
        raise ValueError("get_cell() has returned multiple rows.")

    if df.shape[0] == 0:
        raise ValueError(f"get_cell() has returned 0 rows. \nParameters: {str(kwargs)}")

    return df[column].values[0]


# def get_called_functions(function_source, functions):
#     called_functions = []
#     for func in functions:
#         if func + "(" in function_source:
#             called_functions.append(func)
#     return called_functions


def unique_append(lst, item):
    if item not in lst:
        lst.append(item)
    return lst


def unique_extend(lst1, lst2):
    for item in lst2:
        if item not in lst1:
            lst1.append(item)
    return lst1


def list_used_words(text, words):
    used_words = []
    for word in words:
        if word in text:
            used_words.append(word)
    return used_words


def get_second_element(lst, value):
    # You have a list of tuples with 2 elements
    # You know the value of 1st element
    # You want to get the 2nd element
    for item1, item2 in lst:
        if item1 == value:
            return item2

