import re


from datetime import datetime


def unique_append(lst, item):
    """Append a unique item to a list.

    Parameters
    ----------
    lst : list
        List to append item to.

    item : scalar
        Item to be appended to the list.

    Returns
    -------
    list
    """
    output = lst.copy()
    if item not in lst:
        output.append(item)
    return output


def unique_extend(lst1, lst2):
    """Extend list with items of other list if they are unique.

    Parameters
    ----------
    lst1 : list
        List to be extended with items from lst2.
    lst2 : list
        List which items are uniquely appended to lst1.

    Returns
    -------
    list
    """
    output = lst1.copy()
    for item in lst2:
        if item not in lst1:
            output.append(item)
    return output


def list_used_words(text, words):
    """Choose words from a list that were used in a text.

    Parameters
    ----------
    text : string
        Text in which the function looks for words.
        
    words : list
        List of words to be looked for in the text.

    Returns
    -------
    list
    """
    used_words = []
    for word in words:
        if word in text:
            used_words.append(word)
    return used_words


def replace_in_file(_file, _from, _to):
    """Replace a word with other word in a file.

    Parameters
    ----------
    _file : str
        Path to the file in which words are to be replaced.
        
    _from : str
        Word that needs to be replaced.
        
    _to :
        Word to be replaced with.
    """
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
    n : integer
        (Optionally) number of items to use.

    Returns
    -------
    list
    """
    if n is not None:
        lst = [sublist[:n] for sublist in lst]

    return sum(lst, [])


def aggregate(lst, n=None):
    """Sums each n-th element of sublists.

    Parameters
    ----------
    lst : list
        List of subslists.
    n : integer
        (Optionally) number of items to use.

    Returns
    -------
    list
    """
    if n is not None:
        lst = [sublist[:n] for sublist in lst]

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

    Parameters
    ----------
    formula_source : str
        A function's body presented a string.
    name : str
        Name of the function.

    Returns
    -------
    string
    """
    search1 = re.search(r"\W" + name + r"\(t\-1\)", formula_source)
    if bool(search1):
        return "forward"

    search2 = re.search(r"\W" + name + r"\(t\+1\)", formula_source)
    if bool(search2):
        return "backward"

    return "not_recursive"


def print_log(msg):
    """ Print a log message with timestamp.

    Parameters
    ----------
    msg : string
        Message to be displayed.
    """
    now = datetime.now()
    print(now.strftime("%H:%M:%S") + " | " + msg)

