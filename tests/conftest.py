"""
Configuration file for pytest.
Contains fixtures and settings for the test suite.
"""

import sys
import os

# Add the parent directory to the path so that we can import the local package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
