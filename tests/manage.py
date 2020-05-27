#!/usr/bin/env python
import os
import sys


def main():

    # To emulate drf_expandable_proxy already being installed we forcibly
    # insert the entire project into the PTYHONPATH.
    package_dir = os.getcwd().rsplit('/', 1)[0]
    sys.path.insert(0, package_dir)

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()