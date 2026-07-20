"""Convert LaTeX documents and projects to Markdown."""

from .api import convert, convert_path
from .exceptions import (
    ConversionError,
    InputError,
    SourceSelectionError,
    UnsupportedFormatError,
)

__version__ = "0.2.1"

__all__ = [
    "ConversionError",
    "InputError",
    "SourceSelectionError",
    "UnsupportedFormatError",
    "__version__",
    "convert",
    "convert_path",
]
