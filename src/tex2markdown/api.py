"""Public conversion-only API."""

from __future__ import annotations

from pathlib import Path

from . import _legacy as legacy
from . import _project as source_selection
from ._renderer import render_retrieval_document
from .exceptions import InputError, SourceSelectionError, UnsupportedFormatError

MAX_FILE_BYTES = 20 * 1024 * 1024
VCS_PARTS = {".git", ".hg", ".svn", "__pycache__"}
BINARY_SUFFIXES = {
    ".7z",
    ".avi",
    ".bmp",
    ".bz2",
    ".dvi",
    ".eps",
    ".exe",
    ".gif",
    ".gz",
    ".ico",
    ".jpeg",
    ".jpg",
    ".mov",
    ".mp3",
    ".mp4",
    ".o",
    ".pdf",
    ".png",
    ".ps",
    ".pyc",
    ".so",
    ".tar",
    ".tgz",
    ".tif",
    ".tiff",
    ".wav",
    ".webp",
    ".xz",
    ".zip",
}


def convert(tex_source: str) -> str:
    """Convert one in-memory LaTeX document to Markdown."""
    if not isinstance(tex_source, str):
        raise TypeError("tex_source must be a string")
    if not tex_source.strip():
        raise SourceSelectionError("the LaTeX source is empty")
    if not source_selection.is_paper_candidate("source.tex", tex_source):
        _raise_source_error(tex_source)
    return render_retrieval_document(tex_source)[0]


def convert_path(path: str | Path, *, main_file: str | None = None) -> str:
    """Convert a UTF-8 TeX file or a directory containing a TeX project."""
    source_path = Path(path)
    if source_path.is_file():
        if main_file is not None:
            raise InputError("main_file is only valid for directory input")
        return convert(_read_utf8(source_path))
    if source_path.is_dir():
        return _convert_directory(source_path, main_file)
    raise InputError(f"input path does not exist: {source_path}")


def _convert_directory(root: Path, main_file: str | None) -> str:
    files = _load_project_files(root)
    if not files:
        raise SourceSelectionError(f"no readable project files found in {root}")
    if main_file is not None:
        source = _select_explicit_main(root, files, main_file)
    else:
        selected = source_selection.select_paper_source(_bundle(files))
        if selected is None:
            raise SourceSelectionError(f"no main LaTeX document found in {root}")
        source = selected[0]
    return render_retrieval_document(source)[0]


def _load_project_files(root: Path) -> list[tuple[str, str]]:
    files = []
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        if not path.is_file() or _skip_project_path(path, root):
            continue
        try:
            if path.stat().st_size > MAX_FILE_BYTES:
                continue
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if "\x00" not in content:
            files.append((path.relative_to(root).as_posix(), content))
    return files


def _skip_project_path(path: Path, root: Path) -> bool:
    relative = path.relative_to(root)
    if any(part.startswith(".") or part in VCS_PARTS for part in relative.parts):
        return True
    return path.suffix.lower() in BINARY_SUFFIXES


def _select_explicit_main(root: Path, files: list[tuple[str, str]], main_file: str) -> str:
    requested = Path(main_file)
    if requested.is_absolute() or ".." in requested.parts:
        raise SourceSelectionError("main_file must identify a file inside the project")
    normalized = requested.as_posix().removeprefix("./")
    file_map = dict(files)
    if normalized not in file_map:
        raise SourceSelectionError(f"main LaTeX file not found: {main_file}")
    content = file_map[normalized]
    if not source_selection.is_paper_candidate(normalized, content):
        _raise_source_error(content, f"main file is not a LaTeX document: {main_file}")
    return _expand_project_source(content, files, normalized)


def _expand_project_source(content: str, files: list[tuple[str, str]], main_name: str) -> str:
    content = legacy.extract_embedded_tex_document(content)
    content = legacy.expand_bundled_inputs(content, files, main_name)
    content = legacy.expand_bundled_bibliography(content, files)
    content = legacy.expand_bundled_code_listings(content, files, main_name)
    return legacy.prepend_bundled_package_macros(content, files)


def _bundle(files: list[tuple[str, str]]) -> str:
    return "\n".join(
        f"================\nFILE: {name}\n================\n{content}" for name, content in files
    )


def _read_utf8(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as error:
        raise InputError(f"input file is not UTF-8: {path}") from error
    except OSError as error:
        raise InputError(f"could not read input file: {path}") from error


def _raise_source_error(source: str, message: str | None = None) -> None:
    source_format = legacy.detect_format(source)
    if source_format != "latex":
        raise UnsupportedFormatError(message or f"unsupported input format: {source_format}")
    raise SourceSelectionError(message or "input does not contain a LaTeX document body")
