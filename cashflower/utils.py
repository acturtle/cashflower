import sys

from datetime import datetime


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


def print_log(msg, show=True):
    """Print a log message with the timestamp."""
    if show:
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


def get_object_by_name(objects, name):
    for _object in objects:
        if _object.name == name:
            return _object
    return None


def updt(total, progress):
    """Display or update a console progress bar.
    Original source: https://stackoverflow.com/a/15860757/1391441"""
    bar_length, status = 20, ""
    progress = float(progress) / float(total)
    if progress >= 1.:
        progress, status = 1, "\r\n"
    block = int(round(bar_length * progress))
    text = "\r[{}] {:.0f}% {}".format(
        "#" * block + "-" * (bar_length - block), round(progress * 100, 0),
        status)
    sys.stdout.write(text)
    sys.stdout.flush()
