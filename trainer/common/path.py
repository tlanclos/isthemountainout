import sys
import os


def get_script_path() -> str:
    return os.path.dirname(os.path.abspath(sys.argv[0]))


def unclassified_dir_name() -> str:
    return 'Unclassified'
