import os
import re


def find_files(directory, pattern):
    """
    Walk given directory and finds all files that match the given pattern.

    @param directory: directory to walk
    @type directory: string
    @param pattern: regular expression as string to match
    @type pattern: string
    @return: generator for matched file paths
    @rtype: generator
    """
    for root, dirs, files in os.walk(directory):
        for basename in files:
            filename = os.path.join(root, basename)
            if re.match(pattern, filename):
                yield filename


def datetime_to_date(datetime_str):
    """
    Converts datetime string of format YYYY-mm-ddTHH:MM:SS%z to date string of form YYYY-mm-dd

    @param datetime_str:
    @type datetime_str:
    @return: truncate datetime string to just a date
    @rtype: string
    """
    return datetime_str.split('T')[0] if 'T' in datetime_str else datetime_str





