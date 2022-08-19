def get_cell(df, column, **kwargs):
    """Get a single cell value from a data frame.

    Parameters
    ----------
    df : data frame
    column : str
        Column to get a cell from.
    **kwargs
        Keys are columns names which are filtered based on values.

    Returns
    -------
    scalar
    """
    for key, val in kwargs.items():
        df = df[df[key] == val]

    # Filtering should return one row from data frame
    if df.shape[0] > 1:
        print(df)
        raise ValueError("get_cell() has returned multiple rows.")

    if df.shape[0] == 0:
        raise ValueError(f"get_cell() has returned 0 rows. \nParameters: {str(kwargs)}")

    return df[column].values[0]


def unique_append(lst, item):
    """Append a unique item to a list."""
    output = lst.copy()
    if item not in lst:
        output.append(item)
    return output


def unique_extend(lst1, lst2):
    """Extend list with items of other list if they are unique."""
    output = lst1.copy()
    for item in lst2:
        if item not in lst1:
            output.append(item)
    return output


def list_used_words(text, words):
    """Choose words from a list that were used in a text."""
    used_words = []
    for word in words:
        if word in text:
            used_words.append(word)
    return used_words


def replace_in_file(_file, _from, _to):
    """Replace a word with other word in a file."""
    # Read in the file
    with open(_file, "r") as file:
        filedata = file.read()

    # Replace the target string
    filedata = filedata.replace(_from, _to)

    # Write the file out again
    with open(_file, "w") as file:
        file.write(filedata)


def flatten(lst, n=None):
    """Flatten a list of sublists.

    Parameters
    ----------
    lst : list
        List of sublists.
    n : int
        Optional number of elements to take from each of the sublists. All if not set.

    Returns
    -------
    list
    """
    flat_list = []

    if n is not None:
        lst = [sublist[:n] for sublist in lst]

    for sublist in lst:
        for item in sublist:
            flat_list.append(item)

    return flat_list


def aggregate(lst, n=None):
    """Sums each n-th element of sublists.

    Parameters
    ----------
    lst : list
        List of subslists.
    n : int
        Optional number of elements to take from each of the sublists. All if not set.

    Returns
    -------
    list
    """
    if n is not None:
        lst = [sublist[:n] for sublist in lst]

    aggregated_list = [sum(i) for i in zip(*lst)]
    return aggregated_list


def repeated_numbers(m, n):
    """Create a list of repeated consecutive numbers.

    Parameters
    ----------
    m : int
        The upper bound of the range of numbers.
    n : int
        Number of times each number is repeated.

    Returns
    -------
    list
    """
    lst = []
    for i in range(1, m + 1):
        lst.append([i] * n)

    lst = flatten(lst)
    return lst
