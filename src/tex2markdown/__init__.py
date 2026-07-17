"""Source-preserving LaTeX-to-Markdown for scientific papers."""

from importlib.metadata import PackageNotFoundError, version

from .api import (
    ConversionError,
    ConversionResult,
    PaperMetadata,
    SourceSelectionError,
    Tex2MarkdownError,
    UnsupportedFormatError,
    convert,
    convert_bundle,
    convert_path,
)

try:
    __version__ = version("tex2markdown")
except PackageNotFoundError:
    __version__ = "0.0.0"

__all__ = [
    "ConversionError", "ConversionResult", "PaperMetadata", "SourceSelectionError",
    "Tex2MarkdownError", "UnsupportedFormatError", "convert", "convert_bundle",
    "convert_path", "__version__",
]
