import re


from datetime import datetime


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
    """Replace a word (_from) with another word (_to) in a file (_file)."""
    # Read in the file
    with open(_file, "r") as file:
        filedata = file.read()

    # Replace the target string
    filedata = filedata.replace(_from, _to)

    # Write the file out again
    with open(_file, "w") as file:
        file.write(filedata)


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
    string
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
    """List functions called in the  formula.

    Parameters
    ----------
    formula_source : str
        A function's body presented a string.
    funcs : list
        List of functions' names to be checked if they are called in formula source.

    Returns
    -------
    list
    """
    called_funcs = []
    for func in funcs:
        search = re.search(r"\W" + func + r"\(", formula_source)
        is_called = bool(search)
        if is_called:
            called_funcs.append(func)
    return called_funcs


def is_recursive(formula_source, name):
    """Check if formula is recursive.
    0 = not_recursive
    1 = forward (t-1)
    2 = backward (t+1)

    Parameters
    ----------
    formula_source : str
        A function's body presented a string.
    name : str
        Name of the function.

    Returns
    -------
    integer
    """
    search1 = re.search(r"\W" + name + r"\(t\-1\)", formula_source)
    if bool(search1):
        return 1

    search2 = re.search(r"\W" + name + r"\(t\+1\)", formula_source)
    if bool(search2):
        return 2

    return 0


def print_log(msg):
    """ Print a log message with the timestamp."""
    now = datetime.now()
    print(now.strftime("%H:%M:%S") + " | " + msg)


def split_to_ranges(n, num_ranges):
    """n = 20, num_ranges = 3 --> (0, 6), (6, 12), (12, 20)"""
    if n < num_ranges:
        return [(0, n)]

    range_size = n // num_ranges
    # remainding items are added to the last range
    remainder = n - num_ranges * range_size

    output = [None] * num_ranges
    add_items = 0
    for i in range(num_ranges):
        if i == num_ranges-1:
            add_items = remainder
        range_tuple = (range_size * i, range_size * (i + 1) + add_items)
        output[i] = range_tuple
    return output
