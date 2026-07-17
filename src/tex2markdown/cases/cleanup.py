"""Remove recurring front-matter and presentation-only source residue."""

from __future__ import annotations

import re

from .. import _legacy as legacy

DROP_ARGUMENT_COMMAND = re.compile(r"\\(?:institute|dedicatory|affiliation|affil|copyrightnotice)\s*\{")
DROP_BARE_COMMAND = re.compile(
    r"\\(?:nocopyright|tableofcontents|listoffigures|listoftables|ifnmr|"
    r"newpage|clearpage|pagebreak|nopagebreak|smallskip|medskip|bigskip)\b"
)


def strip_front_matter_residue(text: str) -> str:
    text = strip_publication_front_matter(text)
    text = re.sub(r"\\begin\{bottomstuff\}.*?\\end\{bottomstuff\}", "", text,
                  flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(
        r"\\twocolumn\s*\[\s*\\hsize\\textwidth\\columnwidth\\hsize"
        r"\\csname@twocolumnfalse%?\s*\\endcsname", "", text,
        flags=re.IGNORECASE,
    )
    text = re.sub(r"\\begin\{frontmatter\}.*?\\end\{frontmatter\}", "", text,
                  flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"\\twocolumn\[.*?(?=\\(?:sloppy|narrowtext)\b)", "", text,
                  flags=re.DOTALL | re.IGNORECASE)
    text = legacy.drop_balanced_argument_commands(text, DROP_ARGUMENT_COMMAND)
    text = DROP_BARE_COMMAND.sub(" ", text)
    text = re.sub(r"\\(?:sloppy|narrowtext|twocolumn|onecolumn|columnwidth|textwidth|hsize)\b", " ", text)
    text = re.sub(r"\\(?:hbadness|vbadness|hfuzz|vfuzz)\s*=\s*[-+]?\d+", " ", text)
    text = re.sub(r"\\(?:markboth|runninghead)\s*\{[^{}]*\}\s*\{[^{}]*\}", " ", text)
    text = legacy.drop_balanced_argument_commands(
        text, re.compile(r"\\(?:journame|volnumber|issuenumber|issuemonth|volyear|received|revised|"
                         r"authorrunninghead|titlerunninghead|shortauthor|shorttitle)\s*\{")
    )
    text = re.sub(r"(?m)^\s*\[(?:h|t|b|p|!)+\]\s*$", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\\begin\s*\{(?:titlepage|center|flushleft|flushright)\}|"
                  r"\\end\s*\{(?:titlepage|center|flushleft|flushright)\}", " ", text,
                  flags=re.IGNORECASE)
    text = re.sub(r"(?m)^\s*\\vskip[^\n]*\]?\s*$", "", text)
    text = re.sub(r"(?m)^\s*\\?(?:itemsep|parsep|topsep|partopsep)[^\n]*$", "", text)
    text = re.sub(r"\\include\s*\{[^{}]*\.(?:sty|cls|def)\}", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\\input\s*\{?[^{}\s]*\.(?:sty|cls|def|tex)\}?", " ", text, flags=re.IGNORECASE)
    text = strip_layout_declarations(text)
    return strip_declaration_preamble(strip_declaration_residue(text))


def strip_publication_front_matter(text: str) -> str:
    text = re.sub(
        r"(?is)\bPrevious Issues of [^:\n]{1,80}:.*?(?=\\begin\{titlepage\})", "", text
    )
    text = re.sub(
        r"(?is)\b(?:CIP-Kurztitelaufnahme|Cataloging-in-Publication)\b.*?"
        r"(?=\\textbf\s*\{\s*(?:Acknowledgements?|Abstract|Preface)\s*\})",
        "", text,
    )
    pattern = re.compile(r"\\begin\{titlepage\}(.*?)\\end\{titlepage\}",
                         re.DOTALL | re.IGNORECASE)

    def replacement(match: re.Match) -> str:
        body = match.group(1)
        scientific = re.search(r"\\(?:section|chapter|begin\{(?:abstract|equation|tabular))\b", body)
        return match.group(0) if scientific or len(re.findall(r"[A-Za-z]{3,}", body)) > 300 else ""

    return pattern.sub(replacement, text)


def strip_layout_declarations(text: str) -> str:
    text = re.sub(r"\\newlength\s*\{?\\[A-Za-z@]+\}?", " ", text)
    text = re.sub(
        r"\\(?:setlength|addtolength)\s*\{\\[A-Za-z@]+\}\s*\{[^{}]*\}", " ", text
    )
    text = re.sub(r"(?m)^\s*\\let\\[A-Za-z@]+\\[A-Za-z@]+\s*$", "", text)
    text = re.sub(r"\\newcounter\s*\{[^{}]*\}(?:\s*\[[^\]]*\])?", " ", text)
    text = re.sub(r"\\settowidth\s*\{[^{}]*\}\s*\{[^{}]*\}", " ", text)
    return text


def strip_declaration_preamble(text: str) -> str:
    introduction = re.search(r"\\section\*?\s*\{\s*Introduction\b", text, re.IGNORECASE)
    if not introduction:
        return text
    prefix = text[:introduction.start()]
    declarations = len(re.findall(
        r"\\(?:newcommand|renewcommand|newenvironment|renewenvironment|newtheorem|let)\b", prefix
    ))
    return text[introduction.start():] if declarations >= 5 else text


def strip_declaration_residue(text: str) -> str:
    commands = re.compile(r"\\(?:newenvironment|renewenvironment|newtheorem)\*?\b")
    for match in reversed(list(commands.finditer(text))):
        end = _declaration_end(text, match.end())
        if end > match.end():
            text = text[:match.start()] + " " + text[end:]
    return text


def _declaration_end(text: str, cursor: int) -> int:
    groups = 0
    while cursor < len(text):
        while cursor < len(text) and text[cursor].isspace():
            cursor += 1
        if cursor >= len(text) or text[cursor] not in "[{":
            break
        opening = text[cursor]
        close = _matching(text, cursor, opening, "]" if opening == "[" else "}")
        if close < 0:
            break
        groups += opening == "{"
        cursor = close + 1
    return cursor if groups >= 2 else -1


def _matching(text: str, start: int, opening: str, closing: str) -> int:
    depth = 0
    for index in range(start, len(text)):
        if text[index] == opening and (index == 0 or text[index - 1] != "\\"):
            depth += 1
        elif text[index] == closing and (index == 0 or text[index - 1] != "\\"):
            depth -= 1
            if depth == 0:
                return index
    return -1


def clean_title(title: str) -> str:
    title = re.sub(r"\\hfill\b", " ", title)
    title = re.sub(r"\\ifnmr\b", " ", title)
    title = re.sub(r"A slightly different version appeared in.*?(?=Measures\b)", "", title)
    title = re.sub(r"\\em\b|\\emph\b|\\unskip(?=[A-Z]|\b)", " ", title)
    return re.sub(r"\s+", " ", title).strip(" #:" )


def normalize_manual_sections(text: str) -> str:
    text = re.sub(
        r"\\subhead\s+(.+?)\s*\\endsubhead",
        lambda match: rf"\section{{{' '.join(match.group(1).split())}}}", text,
        flags=re.DOTALL | re.IGNORECASE,
    )
    pattern = re.compile(
        r"\\par\s+\\centerline\s*\{\s*\\bf\s+([IVX]+[.)]?\s+[^{}\n]+)\}",
        re.IGNORECASE,
    )
    text = pattern.sub(lambda match: rf"\section{{{match.group(1).strip()}}}", text)
    text = re.sub(
        r"\\begin\{center\}\s*\{\\bf\s+([^{}]+)\}\s*\\end\{center\}",
        lambda match: rf"\section*{{{' '.join(match.group(1).split())}}}", text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"\\begin\{center\}\s*\{?\\bf\s+([^{}\n]+)\}?\s*\\end\{center\}",
        lambda match: rf"\section*{{{' '.join(match.group(1).split())}}}", text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"\\noindent\s*\{\\bf\s+((?:Sub)?Case\s+[^{}\n]+)\}\s*\\\\",
        lambda match: rf"\subsubsection*{{{match.group(1).strip()}}}", text,
        flags=re.IGNORECASE,
    )
    text = re.sub(r"\\(?:begin|end)sentences\b", "\n", text)
    text = re.sub(r"\\smainitem\b", "\n- ", text)
    text = re.sub(r"\\smainlabel\s*\{[^{}]*\}", "", text)
    text = re.sub(r"\\refstepcounter\s*\{[^{}]*\}", "", text)
    text = re.sub(
        r"(?m)^\s*(\d{1,2}\s+[A-Z][A-Za-z][A-Za-z' -]{8,80})\s*$",
        lambda match: rf"\section*{{{match.group(1).strip()}}}", text,
    )
    return re.sub(
        r"\\(chapter|section|subsection|subsubsection|paragraph)(\*?)\s*\[[^\]\n]*\]\s*\{",
        lambda match: rf"\{match.group(1)}{match.group(2)}{{", text,
        flags=re.IGNORECASE,
    )
