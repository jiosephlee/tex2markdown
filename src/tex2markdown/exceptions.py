"""Typed errors raised by :mod:`tex2markdown`."""


class ConversionError(Exception):
    """Base class for conversion failures."""


class InputError(ConversionError):
    """The requested filesystem or standard-input operation is invalid."""


class UnsupportedFormatError(ConversionError):
    """The input is not a supported LaTeX document."""


class SourceSelectionError(ConversionError):
    """A main LaTeX document could not be selected."""
