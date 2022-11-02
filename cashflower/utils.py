import re


from datetime import datetime


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
    time_dep
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


def flatten(lst):
    """Flatten a list of sublists.

    Parameters
    ----------
    lst : list
        List of sublists.

    Returns
    -------
    list
    """
    return sum(lst, [])


def aggregate(lst):
    """Sums each n-th element of sublists.

    Parameters
    ----------
    lst : list
        List of subslists.

    Returns
    -------
    list
    """
    return [sum(i) for i in zip(*lst)]


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


def clean_formula_source(formula_source):
    """Clean formula's source.

    Prepares the formula's source to be analysed in terms of which function it calls.
    Removes first line (function name), comments and whitespaces before brackets.

    Parameters
    ----------
    formula_source : str
        A function presented as a string.


    Returns
    -------
    str
        A function presented as a string without definition, comments and whitespaces before brackets.
    """
    # Get rid off function's definition
    clean = re.sub(r"def.*?:\n", "\n", formula_source, count=1)

    # Get rid off whitespaces before function's call
    clean = re.sub(r"\s*\(", "(", clean)

    # Get rid off whitespaces inside brackets
    clean = re.sub(r"\(\s*", "(", clean)
    clean = re.sub(r"\s*\)", ")", clean)
    clean = re.sub(r"\(t\s*", "(t", clean)
    clean = re.sub(r"\s*1\)", "1)", clean)

    # Get rid off comments
    clean = re.sub(r"#.*\n", "\n", clean)
    clean = re.sub(r"\"\"\".*?\"\"\"", "", clean)
    clean = re.sub(r"\'\'\'.*?\'\'\'", "", clean)
    return clean


def list_called_funcs(formula_source, funcs):
    """

    Parameters
    ----------
    formula_source : str
        A function's body presented a string.
    funcs : list
        List of functions' names to be checked if they are called in formula source.

    Returns
    -------
    list
        List of functions' names that are called within formula source.
    """
    called_funcs = []
    for func in funcs:
        search = re.search(r"\W" + func + r"\(", formula_source)
        is_called = bool(search)
        if is_called:
            called_funcs.append(func)
    return called_funcs


def is_recursive(formula_source, name):
    """

    Parameters
    ----------
    formula_source : str
        A function's body presented a string.
    name : str
        Name of the function.

    Returns
    -------
    str
        Indication if a function is recursive and, if so, whether forward or backward.
    """
    search1 = re.search(r"\W" + name + r"\(t\-1\)", formula_source)
    if bool(search1):
        return "forward"

    search2 = re.search(r"\W" + name + r"\(t\+1\)", formula_source)
    if bool(search2):
        return "backward"

    return "not_recursive"


def print_log(msg):
    now = datetime.now()
    print(now.strftime("%H:%M:%S") + " | " + msg)
