from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import tex2markdown
from tex2markdown import InputError, SourceSelectionError, UnsupportedFormatError


def document(title: str = "Example", body: str = "Body text.") -> str:
    return (
        rf"\documentclass{{article}}\title{{{title}}}"
        rf"\begin{{document}}\maketitle\section{{Intro}}{body}\end{{document}}"
    )


class ConversionApiTests(unittest.TestCase):
    def test_convert_returns_markdown_string(self):
        result = tex2markdown.convert(document(body=r"Math $x^2$ remains."))
        self.assertIsInstance(result, str)
        self.assertIn("# Example", result)
        self.assertIn("$x^2$", result)

    def test_convert_path_reads_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "paper.tex"
            path.write_text(document("From File"), encoding="utf-8")
            self.assertIn("# From File", tex2markdown.convert_path(path))

    def test_directory_auto_selects_main_and_expands_nested_inputs(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "parts").mkdir()
            (root / "paper.tex").write_text(
                document("Project", r"\input{parts/one}"), encoding="utf-8"
            )
            (root / "parts/one.tex").write_text(r"Nested first. \input{two}", encoding="utf-8")
            (root / "parts/two.tex").write_text("Nested second.", encoding="utf-8")
            output = tex2markdown.convert_path(root)
            self.assertIn("# Project", output)
            self.assertIn("Nested first", output)
            self.assertIn("Nested second", output)

    def test_explicit_main_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "long.tex").write_text(document("Automatic") + " word" * 100, encoding="utf-8")
            (root / "chosen.tex").write_text(document("Chosen"), encoding="utf-8")
            output = tex2markdown.convert_path(root, main_file="chosen.tex")
            self.assertIn("# Chosen", output)
            self.assertNotIn("# Automatic", output)

    def test_main_file_is_rejected_for_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "paper.tex"
            path.write_text(document(), encoding="utf-8")
            with self.assertRaises(InputError):
                tex2markdown.convert_path(path, main_file="paper.tex")

    def test_missing_main_and_support_only_project_are_selection_errors(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "only.sty").write_text(
                r"\ProvidesPackage{only}\newcommand{\x}{x}", encoding="utf-8"
            )
            with self.assertRaises(SourceSelectionError):
                tex2markdown.convert_path(root)
            with self.assertRaises(SourceSelectionError):
                tex2markdown.convert_path(root, main_file="missing.tex")

    def test_unsupported_format(self):
        with self.assertRaises(UnsupportedFormatError):
            tex2markdown.convert("<html><body>not latex</body></html>")

    def test_output_is_deterministic_and_today_is_literal(self):
        source = document(body=r"Generated on \today.")
        first = tex2markdown.convert(source)
        self.assertEqual(first, tex2markdown.convert(source))
        self.assertIn(r"\today", first)

    def test_source_only_title_fallback(self):
        source = r"\documentclass{article}\begin{document}Body.\end{document}"
        self.assertTrue(tex2markdown.convert(source).startswith("# Untitled\n"))

    def test_multiline_optional_and_nested_title(self):
        source = r"""
\documentclass{article}
\begin{document}
\title[Short
title]{\textbf{Full Source Title}\\}
\maketitle
\section{Body}Text.
\end{document}
"""
        self.assertTrue(tex2markdown.convert(source).startswith("# Full Source Title\n"))

    def test_class_specific_source_title(self):
        source = r"""
\documentclass{article}
\begin{document}
\Name{A Class-Specific Source Title}
\begin{abstract}Summary.\end{abstract}
\section{Body}Text.
\end{document}
"""
        self.assertTrue(
            tex2markdown.convert(source).startswith("# A Class-Specific Source Title\n")
        )

    def test_title_uses_active_source_variant(self):
        source = r"""
\documentclass{article}
\newcommand{\shortonly}{0}
\newcommand{\shortversion}[1]{\ifthenelse{\equal{\shortonly}{1}}{#1}{}}
\newcommand{\longversion}[1]{\ifthenelse{\equal{\shortonly}{1}}{}{#1}}
\shortversion{\title{Short Title}}
\longversion{\title{Full Title Extended Version}}
\begin{document}\maketitle Body.\end{document}
"""
        self.assertTrue(tex2markdown.convert(source).startswith("# Full Title Extended Version\n"))

    def test_title_ignores_inactive_source_variant(self):
        source = r"""
\documentclass{article}
\newcommand{\shortonly}{1}
\newcommand{\shortversion}[1]{\ifthenelse{\equal{\shortonly}{1}}{#1}{}}
\newcommand{\longversion}[1]{\ifthenelse{\equal{\shortonly}{1}}{}{#1}}
\longversion{\title{Inactive Full Title}}
\shortversion{\title{Active Short Title}}
\begin{document}\maketitle Body.\end{document}
"""
        result = tex2markdown.convert(source)
        self.assertTrue(result.startswith("# Active Short Title\n"))
        self.assertNotIn("Inactive Full Title", result)

    def test_title_expands_local_name_macro(self):
        source = r"""
\documentclass{article}
\newcommand{\systemname}{PaperFinder}
\title{The \systemname{} Search System}
\begin{document}\maketitle Body.\end{document}
"""
        self.assertTrue(tex2markdown.convert(source).startswith("# The PaperFinder Search System\n"))

    def test_title_drops_footnote_and_keeps_subtitle(self):
        source = r"""
\documentclass{article}
\title{Main Title\footnote{Funding statement}\\{\large A Useful Subtitle}}
\begin{document}\maketitle Body.\end{document}
"""
        self.assertTrue(tex2markdown.convert(source).startswith("# Main Title A Useful Subtitle\n"))

    def test_title_decodes_tex_accents(self):
        source = r"""\documentclass{article}
\title{Garc\'ia and G\"odel}
\begin{document}\maketitle Body.\end{document}"""
        self.assertTrue(tex2markdown.convert(source).startswith("# García and Gödel\n"))

    def test_title_preserves_compacted_math_and_texmacs_name(self):
        source = r"""
\documentclass{article}
\newcommand{\TeXmacs}{{\TeX macs}}
\title{\TeXmacs{} and $N\hspace{-0.1cm}P$}
\begin{document}\maketitle Body.\end{document}
"""
        self.assertTrue(tex2markdown.convert(source).startswith("# TeXmacs and $NP$\n"))

    def test_manually_centered_source_title(self):
        source = r"""
\documentclass{article}
\begin{document}
\begin{center}{\LARGE\bf A Manually Typeset Paper Title}\end{center}
\begin{abstract}Summary.\end{abstract}
\section{Body}Text.
\end{document}
"""
        self.assertTrue(
            tex2markdown.convert(source).startswith("# A Manually Typeset Paper Title\n")
        )

    def test_public_api_is_conversion_only(self):
        self.assertEqual(tex2markdown.__version__, "0.2.1")
        for removed in ("PaperMetadata", "ConversionResult", "convert_bundle"):
            self.assertFalse(hasattr(tex2markdown, removed))


class CliTests(unittest.TestCase):
    def run_cli(self, *arguments: str, source: str | None = None):
        return subprocess.run(
            [sys.executable, "-m", "tex2markdown.cli", *arguments],
            input=source,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_stdin_and_output_file(self):
        result = self.run_cli("-", source=document("Standard Input"))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Standard Input", result.stdout)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source_path, output_path = root / "paper.tex", root / "output.md"
            source_path.write_text(document("Output File"), encoding="utf-8")
            result = self.run_cli(str(source_path), "-o", str(output_path))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "")
            self.assertIn("# Output File", output_path.read_text(encoding="utf-8"))

    def test_main_file_is_rejected_for_stdin(self):
        result = self.run_cli("-", "--main-file", "main.tex", source=document())
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("only valid for folder input", result.stderr)


if __name__ == "__main__":
    unittest.main()
