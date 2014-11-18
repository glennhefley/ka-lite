#!/usr/bin/env python
import os
import sys
import warnings

if __name__ == "__main__":

    # We are overriding a few packages (like Django) from the system path. Suppress those warnings
    warnings.filterwarnings('ignore', message=r'Module .*? is being added to sys\.path', append=True)

    sys.path = [os.path.join(os.path.dirname(os.path.realpath(__file__)), "../../.."), # python-packages (if available)
                os.path.join(os.path.dirname(os.path.realpath(__file__)), "../..") # fle_utils (or whatever parent of flexmodels is)
                ] + sys.path

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "flexmodels.demo.settings")

    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
