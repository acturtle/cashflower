import subprocess
import sys

from datetime import datetime


log_messages = []


def print_log(msg, show_time=False, visible=True):
    """Print a log message with the timestamp and add to global messages to be saved later on."""
    if visible:
        if show_time:
            log_msg = datetime.now().strftime("%H:%M:%S") + " | " + msg
        else:
            log_msg = f"{' ' * 10} {msg}"
        print(log_msg)
        log_messages.append(log_msg)


def save_log_to_file(timestamp):
    with open(f"output/{timestamp}_log.txt", "w") as file:
        for message in log_messages:
            file.write(message + '\n')
        log_messages.clear()


def split_to_ranges(n, num_ranges):
    """n = 20, num_ranges = 3 --> (0, 6), (6, 12), (12, 20)"""
    if n < num_ranges:
        return [(0, n)]

    range_size = n // num_ranges
    # remaining items are added to the last range
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


def get_git_commit_number():
    try:
        # Run the git command to get the commit number
        result = subprocess.run(["git", "rev-parse", "HEAD"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                check=True)

        # Extract the commit number from the output
        commit_number = result.stdout.strip()

        return commit_number
    except subprocess.CalledProcessError:
        # Git command failed, indicating it's not a Git repository
        return None
