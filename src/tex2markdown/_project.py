"""Select genuine paper bodies and reject support-only bundles."""

from __future__ import annotations

from . import _legacy as legacy

SUPPORT_SUFFIXES = (".bbl", ".bib", ".sty", ".cls", ".bst", ".clo", ".cfg", ".def")


def select_paper_source(bundle: str) -> tuple[str, str, int] | None:
    files = legacy.split_source_files(bundle)
    candidates = [(name, content) for name, content in files if is_paper_candidate(name, content)]
    if not candidates:
        return None
    name, content = max(candidates, key=lambda item: legacy.score_source_file(*item))
    content = legacy.extract_embedded_tex_document(content)
    content = legacy.expand_bundled_inputs(content, files, name)
    content = legacy.expand_bundled_bibliography(content, files)
    content = legacy.expand_bundled_code_listings(content, files, name)
    content = legacy.prepend_bundled_package_macros(content, files)
    return content, name, len(files)


def is_paper_candidate(name: str, content: str) -> bool:
    if name.lower().endswith(SUPPORT_SUFFIXES):
        return False
    if legacy.detect_format(content) != "latex":
        return False
    if legacy.has_article_body_cue(content) or "\\begin{document}" in content:
        return True
    if legacy.looks_like_tex_package(content):
        return False
    return len(content) >= 4000 and len(content.split()) >= 300
