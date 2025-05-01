import os
import subprocess
import sys

from datetime import datetime


log_messages = []


def get_git_commit_info():
    """
    Retrieves the current Git commit hash and checks if there are any local changes.

    Returns:
        str: The current Git commit hash, or the commit hash followed by " (with local changes)"
        if there are any uncommitted changes.
        Returns None if the current directory is not a Git repository or if Git not installed.
    """
    try:
        subprocess.check_output(["git", "rev-parse", "--is-inside-work-tree"], stderr=subprocess.STDOUT, text=True)
        commit_hash = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
        status_output = subprocess.check_output(["git", "status", "--porcelain"], text=True).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Not a git repository or git is not installed
        return None

    if status_output:
        return f"{commit_hash} (with local changes)"
    else:
        return f"{commit_hash}"


def get_first_indexes(items):
    """
    Get the list of indexes for the first occurrence of each item in the list.

    Example:
        # >>> get_first_indexes(["A", "A", "B", "A", "C", "D"])
        [0, 2, 4, 5]
    """
    first_indexes = {}
    for index, item in enumerate(items):
        if item not in first_indexes:
            first_indexes[item] = index
    return list(first_indexes.values())


def get_main_model_point_set(model_point_sets):
    """
    Iterates through a list of model point sets and returns the first one that is marked as 'main'.

    Parameters:
        model_point_sets (list): A list of model point set objects.

    Returns:
        object: The first model point set object with the 'main' attribute set to True, or None if no such object is found.
    """
    for model_point_set in model_point_sets:
        if model_point_set.main:
            return model_point_set
    return None


def get_object_by_name(objects, name):
    """
    Returns the first object in the list that has the given name.

    Parameters:
        objects (list): A list of objects.
        name (str): The name to search for.

    Returns:
        object: The first object in the list that has the given name. If no object is found, returns None.
    """
    for obj in objects:
        if obj.name == name:
            return obj
    return None


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

    The file is created in the "output" directory and its name is the timestamp with .log extension.

    Parameters:
        timestamp (str): The timestamp to use in the filename.

    Returns:
        None
    """
    try:
        filename = f"{timestamp}.log"
        filepath = os.path.join("output", filename)
        with open(filepath, "w") as file:
            file.write('\n'.join(log_messages))
    finally:
        log_messages.clear()


def split_to_chunks(n, num_chunks):
    """
    Split a number into a specified number of chunks. The ranges are of equal size, except for the last one
    which may be larger if n is not evenly divisible by num_ranges. The remaining elements are added to the last range.

    Parameters:
        n (int): The number to split.
        num_chunks (int): The number of chunks to split into.

    Returns:
        list: A list of tuples, where each tuple represents a range.

    Example:
        # >>> split_to_chunks(20, 3)
        [(0, 6), (6, 12), (12, 20)]
    """
    if n < num_chunks:
        return [(0, n)]

    range_size = n // num_chunks
    remainder = n - num_chunks * range_size

    output = []
    for i in range(num_chunks):
        start = range_size * i
        end = range_size * (i + 1) + (remainder if i == num_chunks - 1 else 0)
        output.append((start, end))
    return output


def update_progressbar(total, progress):
    """
    Displays or updates a console progress bar.

    Parameters:
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
