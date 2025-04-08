import sys
import os

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from .fixtures import types  # noqa: F401
from .fixtures import example_data  # noqa: F401
from .fixtures import simple_app  # noqa: F401
from .fixtures import complex_app  # noqa: F401
