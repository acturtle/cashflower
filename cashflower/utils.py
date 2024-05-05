import os
import subprocess
import sys

from datetime import datetime


log_messages = []


def log_message(msg, show_time=False, print_and_save=True):
    """
    Log a message with the timestamp and add to global log messages to be saved later on.

    Parameters:
        msg (str): The message to be logged.
        show_time (bool): Whether to show the time in the log message. Default is False.
        print_and_save (bool): Whether to print the log message to the console and log it. Default is True.

    Returns:
        None
    """
    if print_and_save:
        if show_time:
            log_msg = datetime.now().strftime("%H:%M:%S") + " | " + msg
        else:
            log_msg = f"{' ' * 10} {msg}"
        print(log_msg)
        log_messages.append(log_msg)
    return None


def save_log_to_file(timestamp):
    """
    Save the log messages to a file and then clear the log.

    The file is created in the "output" directory and its name is the timestamp followed by "_log.txt".

    Parameters:
    timestamp (str): The timestamp to use in the filename.

    Returns:
    None
    """
    try:
        filename = f"{timestamp}_log.txt"
        filepath = os.path.join("output", filename)
        with open(filepath, "w") as file:
            file.write('\n'.join(log_messages))
    finally:
        log_messages.clear()


def split_to_ranges(n, num_ranges):
    """
    Split a number into a specified number of ranges. The ranges are of equal size, except for the last one
    which may be larger if n is not evenly divisible by num_ranges. The remaining elements are added to the last range.

    Args:
        n (int): The number to split.
        num_ranges (int): The number of ranges to split into.

    Returns:
        list: A list of tuples, where each tuple represents a range.

    Example:
        # >>> split_to_ranges(20, 3)
        [(0, 6), (6, 12), (12, 20)]
    """
    if n < num_ranges:
        return [(0, n)]

    range_size = n // num_ranges
    remainder = n - num_ranges * range_size

    output = []
    for i in range(num_ranges):
        start = range_size * i
        end = range_size * (i + 1) + (remainder if i == num_ranges - 1 else 0)
        output.append((start, end))
    return output


def get_object_by_name(objects, name):
    """
    Returns the first object in the list that has the given name.

    Args:
        objects (list): A list of objects.
        name (str): The name to search for.

    Returns:
        object: The first object in the list that has the given name. If no object is found, returns None.
    """
    for obj in objects:
        if obj.name == name:
            return obj
    return None


def update_progressbar(total, progress):
    """
    Displays or updates a console progress bar.

    Args:
        total (int): The total number of steps in the process.
        progress (int): The current step in the process.

    Returns:
        None
    """
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


def get_git_commit_info():
    """
    Retrieves the current Git commit hash and checks if there are any local changes.

    Returns:
        str: The current Git commit hash, or the commit hash followed by " (with local changes)"
        if there are any uncommitted changes. Returns None if the current directory is not a Git repository.
    """
    try:
        subprocess.check_output(["git", "rev-parse", "--is-inside-work-tree"], stderr=subprocess.STDOUT, text=True)
        commit_hash = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
        status_output = subprocess.check_output(["git", "status", "--porcelain"], text=True).strip()
    except subprocess.CalledProcessError:
        # Not a git repository
        return None

    if status_output:
        return f"{commit_hash} (with local changes)"
    else:
        return f"{commit_hash}"


def get_first_indexes(items):
    """Get the list of indexes for the first occurrence of each item in the list.

    Example:
    ["A", "A", "B", "A", "C", "D"] --> [0, 2, 4, 5]
    """
    first_indexes = {}
    for index, item in enumerate(items):
        if item not in first_indexes:
            first_indexes[item] = index
    return list(first_indexes.values())
