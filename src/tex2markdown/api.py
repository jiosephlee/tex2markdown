"""Public conversion API."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping

from . import converter


class Tex2MarkdownError(Exception):
    """Base exception for conversion failures."""


class UnsupportedFormatError(Tex2MarkdownError):
    """Raised when the selected input is not LaTeX."""


class SourceSelectionError(Tex2MarkdownError):
    """Raised when no paper body can be selected."""


class ConversionError(Tex2MarkdownError):
    """Raised when a selected LaTeX source cannot be converted."""


@dataclass(frozen=True)
class PaperMetadata:
    id: str | None = None
    title: str = ""
    abstract: str = ""
    authors: str = ""
    categories: str = ""
    doi: str | None = None
    update_date: str = ""


@dataclass(frozen=True)
class ConversionResult:
    markdown: str
    selected_file: str
    source_file_count: int
    conversion_method: str
    warnings: tuple[str, ...] = ()
    risk_flags: tuple[str, ...] = ()
    retrieval_status: str = "clean_candidate"
    metrics: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self, include_markdown: bool = True) -> dict[str, Any]:
        result = asdict(self)
        if not include_markdown:
            result.pop("markdown")
        return result


def bundle_source(files: Mapping[str, str]) -> str:
    if not files:
        raise SourceSelectionError("source bundle is empty")
    blocks = []
    for name in sorted(files):
        content = files[name]
        blocks.append(f"================\nFILE: {name}\n================\n{content}")
    return "\n".join(blocks)


def paper_record(source: str, metadata: PaperMetadata | None) -> dict[str, Any]:
    values = asdict(metadata or PaperMetadata())
    values["latex"] = source
    return values


def result_from_item(item: dict[str, Any]) -> ConversionResult:
    record = item["record"]
    legacy = item["legacy_metrics"]
    metrics = dict(legacy)
    metrics["source_inventory"] = item["source_inventory"]
    metrics["markdown_inventory"] = item["markdown_inventory"]
    return ConversionResult(
        markdown=record["markdown"], selected_file=record["source_file"],
        source_file_count=legacy["source_file_count"],
        conversion_method=record["conversion_method"], warnings=tuple(record["warnings"]),
        risk_flags=tuple(item["risk_flags"]), retrieval_status=item["retrieval_status"],
        metrics=metrics,
    )


def convert(source: str, *, filename: str = "source.tex", metadata: PaperMetadata | None = None,
            conversion_date: str = r"\today") -> ConversionResult:
    if not isinstance(source, str):
        raise TypeError("source must be a string")
    if "\nFILE:" not in source and converter.legacy.detect_format(source) != "latex":
        raise UnsupportedFormatError(f"unsupported source format: {filename}")
    bundled = source if "\nFILE:" in source else bundle_source({filename: source})
    return _convert(bundled, metadata, None, conversion_date)


def convert_bundle(files: Mapping[str, str], *, main_file: str | None = None,
                   metadata: PaperMetadata | None = None,
                   conversion_date: str = r"\today") -> ConversionResult:
    support_only = files and all(name.lower().endswith(converter.source_selection.SUPPORT_SUFFIXES)
                                 for name in files)
    if files and not support_only and not any(converter.legacy.detect_format(content) == "latex"
                                              for content in files.values()):
        raise UnsupportedFormatError("source bundle contains no LaTeX files")
    return _convert(bundle_source(files), metadata, main_file, conversion_date)


def convert_path(path: str | Path, *, main_file: str | None = None,
                 metadata: PaperMetadata | None = None,
                 conversion_date: str = r"\today") -> ConversionResult:
    source_path = Path(path)
    if source_path.is_file():
        return convert(source_path.read_text(encoding="utf-8"), filename=source_path.name,
                       metadata=metadata, conversion_date=conversion_date)
    if not source_path.is_dir():
        raise FileNotFoundError(source_path)
    return convert_bundle(load_project(source_path), main_file=main_file, metadata=metadata,
                          conversion_date=conversion_date)


def load_project(root: Path) -> dict[str, str]:
    files = {}
    binary_suffixes = {".pdf", ".png", ".jpg", ".jpeg", ".gif", ".dvi", ".gz", ".zip", ".tar"}
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        if path.suffix.lower() in binary_suffixes or path.stat().st_size > 20_000_000:
            continue
        try:
            files[path.relative_to(root).as_posix()] = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
    return files


def _convert(source: str, metadata: PaperMetadata | None, main_file: str | None,
             conversion_date: str) -> ConversionResult:
    token = converter.legacy.set_document_date(conversion_date)
    try:
        return result_from_item(converter.convert_paper(paper_record(source, metadata), main_file))
    except ValueError as error:
        message = str(error)
        if "unsupported selected source" in message:
            raise UnsupportedFormatError(message) from error
        raise SourceSelectionError(message) from error
    except Tex2MarkdownError:
        raise
    except Exception as error:
        raise ConversionError(str(error)) from error
    finally:
        converter.legacy.reset_document_date(token)
