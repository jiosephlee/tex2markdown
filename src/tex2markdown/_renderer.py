"""Self-contained source-preserving Markdown renderer."""

from __future__ import annotations

import re

from . import _cleanup as cleanup_case
from . import _figures as figure_case
from . import _legacy as legacy
from . import _tabbing as tabbing_case
from . import _tables as table_case


def retrieval_math_identifier_spacing(text: str) -> str:
    """Avoid legacy math-spacing heuristics over ordinary prose."""
    return text


legacy.normalize_math_identifier_spacing = retrieval_math_identifier_spacing
legacy.RE_DOCUMENTSTYLE_FRAGMENT = re.compile(r"(?!x)x")

THEOREM_NAMES = (
    "theorem",
    "lemma",
    "proposition",
    "corollary",
    "definition",
    "claim",
    "conjecture",
    "remark",
    "example",
    "proof",
    "tef",
    "prop",
    "lem",
    "teo",
    "defin",
    "nemma",
)

MARKDOWN_TABLE = re.compile(r"(?m)^\s*\|.+\|\s*$\n^\s*\|\s*:?-{3,}")

PANDOC_GRID_TABLE = re.compile(r"(?m)^\+[-:=]+\+")

TABULAR_BEGIN = re.compile(r"\\begin\{(tabular\*?|longtable)\}", re.IGNORECASE)

ENV_TOKEN = re.compile(r"\\(begin|end)\s*\{([^{}]+)\}", re.IGNORECASE)

FORMAL_TOKEN_RE = re.compile(r"⟬\d{6}⟭")

ACTIVE_BEGIN_DOCUMENT = re.compile(r"(?m)^[ \t]*\\begin\s*\{document\}")

ACTIVE_END_DOCUMENT = re.compile(r"(?m)^[ \t]*\\end\s*\{document\}")

AMSTEX_DOCUMENT_START = re.compile(r"(?m)^[ \t]*\\document\b")

AMSTEX_DOCUMENT_END = re.compile(r"(?m)^[ \t]*\\enddocument\b")

TEXT_STYLE_COMMAND = re.compile(
    r"\\(?:textsc|textsf|textit|textbf|texttt|textnormal|textipa|emph|textrm|textmd)\*?\s*\{"
)

OLD_TEXT_FONT_GROUP = re.compile(r"\{\\(?:rm|bf|it|sc|tt)\s+([^{}]*)\}")

OLD_TEXT_FONT_BRACED_GROUP = re.compile(r"\{\\(?:rm|bf|it|sc|tt)\s+\{([^{}]*)\}\}")

UNRESOLVED_COMMENT_COMMAND = re.compile(r"\\(?:Comment|[A-Z][A-Za-z]*comment)\s*\{")

SOURCE_ABSTRACT = re.compile(
    r"\\begin\{abstract\}(.*?)\\end\{abstract\}|\\abstract\b(.*?)\\endabstract",
    re.DOTALL | re.IGNORECASE,
)

CUSTOM_ABSTRACT = re.compile(r"\\abstracts\s*\{", re.IGNORECASE)

ENVIRONMENT_ABSTRACT = re.compile(
    r"\\begin\{abstract\}(.*?)\\end\{abstract\}",
    re.DOTALL | re.IGNORECASE,
)

SUBSECTION_ABSTRACT = re.compile(
    r"\\subsection\*\s*\{\s*Abstract\.?\s*\}\s*(.*?)"
    r"(?=\n\s*\}\s*\n\s*\\(?:medskip|bigskip)|\\section\*?\s*\{)",
    re.DOTALL | re.IGNORECASE,
)

STYLED_ABSTRACT = re.compile(
    r"\{\\large\\bfseries(?:\\noindent)?\s+Abstract\\\\\s*\}\s*(.*?)"
    r"(?=\\copyright\b|\\newpage\b|\\section\*?\s*\{)",
    re.DOTALL | re.IGNORECASE,
)

BRACED_ABSTRACT = re.compile(r"\\abstract\s*\{", re.IGNORECASE)

DECLARATIVE_ABSTRACT = re.compile(r"\{\\abstract\b", re.IGNORECASE)

SOURCE_TITLE_COMMANDS = ("title", "articletitle", "Name", "mytitle", "cbb")

LEGACY_ABSTRACT_HEADING = re.compile(
    r"\\centerline\s*\{[^{}\n]*\\(?:bf|textbf)\s+Abstract[^{}\n]*\}"
    r"|\\textbf\s*\{\s*Abstract\s*\}"
    r"|\{[^{}\n]*\\(?:bf|textbf|Large|large|footnotesize)\s+Abstract\.?\s*\}"
    r"|\\(?:subsection|paragraph)\*?\s*\{\s*Abstract[:.]?\s*\}",
    re.IGNORECASE,
)

QUOTE_ABSTRACT_HEADING = re.compile(r"\bABSTRACT\s*\\\\", re.IGNORECASE)

QUOTE_ABSTRACT_STOP = re.compile(
    r"(?:1991\s+)?Computing\s+Reviews\s+Classification|Keywords?\s+and\s+Phrases|\\end\{quote\}",
    re.IGNORECASE,
)

ABSTRACT_STOP = re.compile(
    r"\\(?:section|chapter|head)\*?\s*\{|\\end\{titlepage\}|\\newpage\b"
    r"|\\par\s+\\centerline\s*\{\s*\\bf\s+[IVX]+[.)]?\s+"
    r"|\\begin\{center\}\s*\{\\bf\s+(?:Introduction|[IVX0-9]+[.)]?\s+)"
    r"|(?:\\textit\s*\{|\{[^{}\n]*\\(?:bf|textbf)\s+)Keywords?\b",
    re.IGNORECASE,
)

NONCONTENT_COMMAND = re.compile(r"\\(?:typeout|message)\s*\{", re.IGNORECASE)

BODY_METADATA_COMMAND = re.compile(
    r"\\(?:title|author|address|date|thanks|subjclass|email|pacs|keywords|copyrightheading)"
    r"\*?(?:\s*\[[^\]\n]*\])?\s*\{",
    re.IGNORECASE,
)

ANNOTATED_CONTENT = re.compile(
    r"\\head\s*\{[^{}]*Annotated\s+Content[^{}]*\}.*?(?=\\head\s*\{[^{}]*(?:Introduction|\\S\s*0)[^{}]*\})",
    re.DOTALL | re.IGNORECASE,
)

CONTROL_TEX_REPLACEMENTS = {
    1: "_",
    19: r"\times ",
    24: r"\gets ",
    26: r"\ne ",
    28: r"\le ",
    29: r"\ge ",
}

PLAIN_FORMAL_BLOCK = re.compile(
    r"\\(xalignat|align|cases|Vmatrix|matrix|pmatrix|bmatrix|displaylines|multline|gather)\b"
    r".*?\\end\1\b",
    re.DOTALL,
)

CUSTOM_DERIVATION_BLOCK = re.compile(r"\\start([A-Za-z]+)\b.*?\\end\1\b", re.DOTALL)

CUSTOM_DISPLAY_COMMAND_BLOCK = re.compile(
    r"\\beq(?:\{[^{}\n]*\})?.*?(?:\\eeq\b|\\end\{equation\})", re.DOTALL
)

CUSTOM_PAIRED_BLOCK = re.compile(
    r"\\Begin([A-Za-z]+)\b.*?\\End\1\b(?:\s*\{[^{}]*\}){0,3}", re.DOTALL
)

PSEUDOCODE_BLOCK = re.compile(r"\bREPEAT\s+\\newline\b.*?\bEND\s+REPEAT\s+\\newline\b", re.DOTALL)

LEGACY_DISPLAY_BLOCK = re.compile(
    r"\\bea\b.*?\\eea\b|\\<.*?\\>",
    re.DOTALL,
)

BRACKET_DISPLAY_BLOCK = re.compile(r"(?<!\\)\\\[.*?(?<!\\)\\\]", re.DOTALL)

ENCODED_CODE_BLOCK = re.compile(r"CODEBLOCKSTART\s*(.*?)\s*CODEBLOCKEND", re.DOTALL)

CUSTOM_CITATION_COMMAND = re.compile(r"\\rf\s*\{[^{}]*\}")

NAMED_CITATION_COMMAND = re.compile(
    r"\\[A-Za-z]*cite[A-Za-z]*\*?(?:\s*\[[^\]\n]*\]){0,2}\s*\{[^{}\n]*\}", re.IGNORECASE
)

CUSTOM_REFERENCE_COMMAND = re.compile(r"\\(?:refeq|reftab|reffig)\s*\{[^{}]*\}")

BIBLIOGRAPHY_ENVIRONMENT = re.compile(
    r"\\begin\{(?:thebibliography|bibliography|references)\}.*?"
    r"\\end\{(?:thebibliography|bibliography|references)\}",
    re.DOTALL | re.IGNORECASE,
)

AMSTEX_BIBLIOGRAPHY_ENVIRONMENT = re.compile(r"\\Refs\b.*?\\endRefs\b", re.DOTALL | re.IGNORECASE)

BIBLIOGRAPHY_HEADING = re.compile(
    r"\\(?:subsection|section|chapter)\*?\s*\{\s*(?:References|Bibliography)\s*\}",
    re.IGNORECASE,
)

MANUAL_BIBLIOGRAPHY_HEADING = re.compile(
    r"(?im)^[^\n]{0,100}(?:\\(?:[A-Za-z]*bf|centerline)|\\begin\{center\})"
    r"[^\n]{0,100}\b(?:References|Bibliography)\b[^\n]{0,100}$"
)

STRUCTURAL_POST_BIBLIOGRAPHY = re.compile(
    r"(?im)^[ \t]*\\(?:appendix\b|(?:subsection|section|chapter)\*?\s*\{)"
)

MARKDOWN_BIBLIOGRAPHY_HEADING = re.compile(r"(?mi)^#{1,6}\s+(?:References|Bibliography)\s*$")

FRAGILE_DISPLAY_MACRO = re.compile(r"\\(?:binom|genfrac|overset|underset)\b")

FRAGILE_DOLLAR_DISPLAY = re.compile(
    r"^[ \t]*\$\$(?=\S)(?:(?!^[ \t]*\$\$).)*?\$\$[ \t]*$", re.DOTALL | re.MULTILINE
)

CUSTOM_BRACKET_TOKEN = re.compile(r"\\(prop|disp|ifthen|ifandonlyif|ifthenotherwise)(\[|\])")

LITERAL_CODE_ENVS = {
    "verbatim",
    "verbatim*",
    "lstlisting",
    "listing",
    "acmlisting",
    "verbcode",
    "ce",
}

TEX_FORMATTED_CODE_ENVS = {"alltt", "lyxcode"}

CODE_ENVS = LITERAL_CODE_ENVS | TEX_FORMATTED_CODE_ENVS

TEXT_EXAMPLE_ENVS = {"verse"}

FORMAL_RAW_TABLE_ENV = table_case.FORMAL_TABLE_ENV

BASE_FORMAL_ENVS = (
    {
        "table",
        "table*",
        "tabular",
        "tabular*",
        "longtable",
        "figure",
        "figure*",
        "algorithm",
        "algorithm*",
        "algorithmic",
        "program",
        "tabbing",
        "picture",
        "pspicture",
        "avm",
        "description",
        "description*",
        "ex",
        "exo",
        "subex",
        "equation",
        "equation*",
        "align",
        "align*",
        "aligned",
        "aligned*",
        "eqnarray",
        "eqnarray*",
        "array",
        "matrix",
        "pmatrix",
        "bmatrix",
        "vmatrix",
        "cases",
        "gather",
        "gather*",
        "split",
        "multline",
        "multline*",
        "displaymath",
        "math",
        FORMAL_RAW_TABLE_ENV,
    }
    | CODE_ENVS
    | TEXT_EXAMPLE_ENVS
)

PANDOC_COMPLEX_TABLE = re.compile(
    r"\\(?:multi(?:column|row)|tableline)\b|\\begin\{(?:minipage|description|turn)",
    re.IGNORECASE,
)

PANDOC_TABLE_RESIDUE = re.compile(
    r"\\(?:begin|end)\{|\\(?:multi(?:column|row)|tableline)\b|<table\b|^\s*:::",
    re.IGNORECASE | re.MULTILINE,
)

MATH_PRESENTATION_COMMAND = re.compile(
    r"\\(?:begin|end)\{(?:tiny|small|footnotesize|scriptsize)\}|"
    r"\\(?:tiny|small|footnotesize|scriptsize|normalsize)\b"
)

OVERFULL_DRAFT_CONDITIONAL = re.compile(r"\\ifdim\s*\\overfullrule\b(?:(?!\\if).)*?\\fi", re.DOTALL)

TABLE_OUT_OF_SCOPE_CONTENT = re.compile(
    r"\\(?:includegraphics|epsfig)\b|\\begin\{(?:picture|pspicture)\}", re.IGNORECASE
)

MATH_ENVS = {
    "equation",
    "equation*",
    "align",
    "align*",
    "aligned",
    "aligned*",
    "eqnarray",
    "eqnarray*",
    "array",
    "matrix",
    "pmatrix",
    "bmatrix",
    "vmatrix",
    "cases",
    "gather",
    "gather*",
    "split",
    "multline",
    "multline*",
    "displaymath",
    "math",
}

STRUCTURAL_MACRO_NAMES = {
    "begin",
    "end",
    "item",
    "label",
    "ref",
    "cite",
    "section",
    "subsection",
    "subsubsection",
    "chapter",
    "part",
    "paragraph",
    "abstract",
    "title",
    "author",
}

CHOICE_MACRO_BODY = re.compile(
    r"\\if\s*\*\s*#1(.*?)\\else\s*\\if\s*-\s*#1(.*?)\\else(.*?)\\fi\s*\\fi",
    re.DOTALL,
)

OPTIONAL_ARGUMENT_DEFINITION = re.compile(
    r"\\(?:re)?newcommand\s*\{?(\\[A-Za-z]+)\}?\s*\[\d+\]\s*\["
)


def remove_environment_spans(text: str, targets: set[str]) -> str:
    for start, end, _ in reversed(environment_spans(text, targets)):
        text = text[:start] + text[end:]
    return text


def theorem_environment_names(source: str) -> dict[str, str]:
    aliases = {
        "tef": "Theorem",
        "teo": "Theorem",
        "prop": "Proposition",
        "lem": "Lemma",
        "nemma": "Lemma",
        "defin": "Definition",
    }
    names = {name: aliases.get(name, name.title()) for name in THEOREM_NAMES}
    names.update(
        {env.lower(): title for _, _, env, title in legacy.collect_newtheorem_definitions(source)}
    )
    return names


def custom_formal_environment_names(source: str) -> set[str]:
    names = re.findall(r"\\newenvironment\s*\{([^{}]+)\}", source, re.IGNORECASE)
    semantic = re.compile(r"algo|procedure|program|protocol|code|example|proof|rule", re.IGNORECASE)
    return {name.lower() for name in names if semantic.search(name)}


def safe_retrieval_macro(name: str, nargs: int, body: str) -> bool:
    body = simplify_tex_mode_guard(body)
    dangerous = re.compile(
        r"\\(?:if[A-Za-z@]*|@?ifnextchar|futurelet|csname|expandafter|edef|xdef|gdef|def|let|newcommand|newenvironment|"
        r"newcounter|newlength|setlength|raise(?:box)?|special|input|documentclass|usepackage|global)\b|\\@"
    )
    return (
        name.lstrip("\\").lower() not in STRUCTURAL_MACRO_NAMES
        and legacy.should_expand_macro(name)
        and (nargs == 0 or bool(body.strip()))
        and nargs <= 3
        and len(body) <= 300
        and body.count("\n") <= 2
        and "%" not in body
        and "$" not in body
        and (bool(CHOICE_MACRO_BODY.search(body)) or not dangerous.search(body))
    )


def simplify_tex_mode_guard(body: str) -> str:
    pattern = re.compile(
        r"\\relax\s*\\ifmmode\s*(.*?)\\else\s*"
        r"\\errmessage\s*\{[^{}]*\}\s*\\fi",
        re.DOTALL,
    )
    return pattern.sub(r"\1", body)


def retrieval_macros(text: str) -> list[tuple[int, int, str, int, str]]:
    macros = []
    for pattern in (legacy.RE_NEWCOMMAND, legacy.RE_DEF, legacy.RE_DEFINE):
        macros.extend(legacy.collect_macros(pattern, text))
    macros.extend(collect_command_alias_macros(text))
    macros.extend(collect_spaced_command_macros(text))
    macros.extend(collect_class_alias_macros(text))
    macros.extend(collect_commented_newcommand_macros(text))
    return macros


def collect_commented_newcommand_macros(text: str) -> list[tuple[int, int, str, int, str]]:
    pattern = re.compile(
        r"\\(?:re)?newcommand\s*\{?(\\[A-Za-z]+)\}?\s*(?:\[(\d+)\])?"
        r"\s*%[^\n]*\n\s*\{"
    )
    macros = []
    for match in pattern.finditer(text):
        close = legacy.find_matching_brace(text, match.end() - 1)
        if close >= 0:
            macros.append(
                (
                    match.start(),
                    close + 1,
                    match.group(1),
                    int(match.group(2) or 0),
                    text[match.end() : close],
                )
            )
    return macros


def collect_spaced_command_macros(text: str) -> list[tuple[int, int, str, int, str]]:
    pattern = re.compile(r"\\newcommand\s*\{(\\[A-Za-z]+)\s+\}\s*(?:\[(\d+)\])?\s*\{")
    macros = []
    for match in pattern.finditer(text):
        close = legacy.find_matching_brace(text, match.end() - 1)
        if close >= 0:
            macros.append(
                (
                    match.start(),
                    close + 1,
                    match.group(1),
                    int(match.group(2) or 0),
                    text[match.end() : close],
                )
            )
    return macros


def collect_command_alias_macros(text: str) -> list[tuple[int, int, str, int, str]]:
    if not re.search(r"\\newcommand\s*\\(?:r?nc)\b", text):
        return []
    macros = []
    pattern = re.compile(r"\\(?:r?nc)\s*(\\[A-Za-z]+)\s*(?:\[(\d+)\])?\s*\{")
    for match in pattern.finditer(text):
        close = legacy.find_matching_brace(text, match.end() - 1)
        if close >= 0:
            macros.append(
                (
                    match.start(),
                    close + 1,
                    match.group(1),
                    int(match.group(2) or 0),
                    text[match.end() : close],
                )
            )
    return macros


def collect_class_alias_macros(text: str) -> list[tuple[int, int, str, int, str]]:
    if not re.search(r"\\newclass\s*\{", text):
        return []
    macros = []
    pattern = re.compile(r"\\newclass\s*\{(\\[A-Za-z]+)\}\s*\{([^{}]+)\}")
    for match in pattern.finditer(text):
        macros.append((match.start(), match.end(), match.group(1), 0, match.group(2)))
    return macros


def unscoped_retrieval_macros(text: str) -> list[tuple[int, int, str, int, str]]:
    spans = environment_spans(text, BASE_FORMAL_ENVS)
    return [
        macro
        for macro in retrieval_macros(text)
        if not any(start <= macro[0] < end for start, end, _ in spans)
    ]


def expand_retrieval_macros(text: str, definitions: str | None = None) -> str:
    text = expand_numeric_choice_macros(text, definitions or text)
    definition_text = definitions if definitions is not None else text
    macros = (
        retrieval_macros(definitions)
        if definitions is not None
        else unscoped_retrieval_macros(text)
    )
    optional_names = optional_argument_macro_names(definition_text)
    if definitions is None:
        spans = legacy.merged_spans((m[0], m[1]) for m in macros)
        for start, end in sorted(spans, key=lambda span: span[0], reverse=True):
            text = text[:start] + text[end:]
    used = set(re.findall(r"\\[A-Za-z]+", text))
    latest_by_name = {}
    for _, _, name, nargs, body in macros:
        if name in used:
            latest_by_name[name] = (name, nargs, body)
    for _ in range(3):
        dependencies = (
            set().union(
                *(set(re.findall(r"\\[A-Za-z]+", body)) for _, _, body in latest_by_name.values())
            )
            if latest_by_name
            else set()
        )
        for _, _, name, nargs, body in macros:
            if name in dependencies:
                latest_by_name[name] = (name, nargs, body)
    safe = [
        macro
        for macro in latest_by_name.values()
        if macro[0] not in optional_names and safe_retrieval_macro(*macro)
    ][:1000]
    for _ in range(2):
        for name, nargs, body in safe:
            text = expand_one_retrieval_macro(text, name, nargs, body)
    return text


def expand_numeric_choice_macros(text: str, definitions: str) -> str:
    constants = {}
    for _, _, name, nargs, body in legacy.collect_macros(legacy.RE_NEWCOMMAND, definitions):
        if nargs == 0 and re.fullmatch(r"\s*\d+\s*", body):
            constants[name] = int(body)
    choice = re.compile(
        r"\\(?:re)?newcommand\s*\{(\\[A-Za-z]+)\}\s*\[3\]\s*\{"
        r"\\ifnum\s*(\\[A-Za-z]+)\s*<\s*#1\s*#2\s*\\else\s*#3\s*\\fi\s*\}"
    )
    for name, constant_name in choice.findall(definitions):
        if constant_name not in constants:
            continue
        pattern = re.compile(re.escape(name) + r"(?![A-Za-z])")
        for match in reversed(list(pattern.finditer(text))[:5000]):
            parsed = read_macro_args(text, match.end(), 3)
            if not parsed or not parsed[0][0].strip().isdigit():
                continue
            args, end = parsed
            branch = args[1] if constants[constant_name] < int(args[0].strip()) else args[2]
            text = text[: match.start()] + branch + text[end:]
    return text


def optional_argument_macro_names(source: str) -> set[str]:
    return set(OPTIONAL_ARGUMENT_DEFINITION.findall(source))


def expand_one_retrieval_macro(text: str, name: str, nargs: int, body: str) -> str:
    body = simplify_tex_mode_guard(body)
    if nargs == 0 and len(body) < 200:
        pattern = re.compile(re.escape(name) + r"(?![A-Za-z])")
        return pattern.sub(lambda match: zero_argument_replacement(text, match, body), text)
    if nargs < 1 or nargs > 3:
        return text
    pattern = re.escape(name) + r"(?![A-Za-z])"
    for match in reversed(list(re.finditer(pattern, text))[:5000]):
        if match_on_commented_line(text, match.start()):
            continue
        parsed = read_macro_args(text, match.end(), nargs)
        if not parsed:
            continue
        args, end = parsed
        replacement = choice_macro_replacement(body, args[0]) if nargs == 1 else None
        replacement = body if replacement is None else replacement
        replacement = substitute_macro_arguments(replacement, args)
        text = text[: match.start()] + replacement + text[end:]
    return text


def zero_argument_replacement(text: str, match: re.Match, body: str) -> str:
    if re.fullmatch(r"\s*\\(?:begin|end)\{[^{}]+\}\s*", body):
        return body
    cursor = match.end()
    while cursor < len(text) and text[cursor].isspace():
        cursor += 1
    if cursor < len(text) and text[cursor] == "{" and re.fullmatch(r"\s*\\[A-Za-z]+\s*", body):
        return body
    return "{" + body + "}"


def substitute_macro_arguments(body: str, arguments: list[str]) -> str:
    for index, argument in enumerate(arguments, 1):
        marker = f"#{index}"
        body = re.sub(
            rf"(\\[A-Za-z]+){re.escape(marker)}",
            lambda match: f"{match.group(1)}{{{argument}}}",
            body,
        )
        body = body.replace(marker, argument)
    return body


def match_on_commented_line(text: str, position: int) -> bool:
    line_start = text.rfind("\n", 0, position) + 1
    prefix = text[line_start:position]
    comment = prefix.find("%")
    return comment >= 0 and (comment == 0 or prefix[comment - 1] != "\\")


def choice_macro_replacement(body: str, argument: str) -> str | None:
    match = CHOICE_MACRO_BODY.search(body)
    if not match:
        return None
    branch = (
        match.group(1) if argument == "*" else match.group(2) if argument == "-" else match.group(3)
    )
    return body[: match.start()] + branch + body[match.end() :]


def read_macro_args(text: str, position: int, count: int) -> tuple[list[str], int] | None:
    args = []
    cursor = position
    for _ in range(count):
        while cursor < len(text) and text[cursor].isspace():
            cursor += 1
        if cursor >= len(text):
            return None
        if text[cursor] == "{":
            close = legacy.find_matching_brace(text, cursor)
            if close < 0:
                return None
            args.append(text[cursor + 1 : close])
            cursor = close + 1
        else:
            match = re.match(r"\\[A-Za-z]+|\\.|.", text[cursor:], re.DOTALL)
            if not match:
                return None
            args.append(match.group(0))
            cursor += len(match.group(0))
    return args, cursor


def normalize_source_control_bytes(text: str) -> str:
    for code, replacement in CONTROL_TEX_REPLACEMENTS.items():
        text = text.replace(chr(code), replacement)
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", " ", text)


def source_abstract_parts(source: str) -> tuple[int, int, str] | None:
    document = ACTIVE_BEGIN_DOCUMENT.search(source)
    search_start = document.end() if document else 0
    match = ENVIRONMENT_ABSTRACT.search(source, search_start)
    if match:
        return match.start(), match.end(), match.group(1)
    match = SUBSECTION_ABSTRACT.search(source, search_start)
    if match:
        return match.start(), match.end(), match.group(1)
    match = STYLED_ABSTRACT.search(source, search_start)
    if match:
        return match.start(), match.end(), match.group(1)
    match = SOURCE_ABSTRACT.search(source, search_start)
    if match:
        body = match.group(1) if match.group(1) is not None else match.group(2)
        return match.start(), match.end(), body
    match = re.search(
        r"\\abstract\b(.*?)(?=\\(?:section|chapter|head)\*?\s*\{)",
        source[search_start:],
        re.DOTALL | re.IGNORECASE,
    )
    if match:
        return search_start + match.start(), search_start + match.end(), match.group(1)
    match = BRACED_ABSTRACT.search(source, search_start)
    if match:
        close = legacy.find_matching_brace(source, match.end() - 1)
        if close >= 0:
            return match.start(), close + 1, source[match.end() : close]
    match = CUSTOM_ABSTRACT.search(source, search_start)
    if match:
        parsed = read_macro_args(source, match.end() - 1, 3)
        if parsed:
            args, end = parsed
            return match.start(), end, args[0]
    match = DECLARATIVE_ABSTRACT.search(source, search_start)
    if match:
        close = legacy.find_matching_brace(source, match.start())
        if close >= 0:
            return match.start(), close + 1, source[match.end() : close]
    marker = LEGACY_ABSTRACT_HEADING.search(source, search_start)
    stop_pattern = ABSTRACT_STOP
    if not marker:
        marker = QUOTE_ABSTRACT_HEADING.search(source, search_start)
        stop_pattern = QUOTE_ABSTRACT_STOP
    if not marker:
        return None
    stop = stop_pattern.search(source, marker.end())
    end = stop.start() if stop else min(len(source), marker.end() + 20000)
    return marker.start(), end, source[marker.end() : end]


def strip_noncontent_source(text: str) -> str:
    text = legacy.drop_balanced_argument_commands(text, NONCONTENT_COMMAND)
    text = ANNOTATED_CONTENT.sub("", text)
    return re.sub(
        r"\\head\s*\{([^{}]*(?:Introduction|Conclusion|References|Appendix)[^{}]*)\}",
        lambda match: rf"\section{{{match.group(1)}}}",
        text,
        flags=re.IGNORECASE,
    )


def strip_source_abstract(text: str) -> str:
    parts = source_abstract_parts(text)
    if not parts:
        return text
    start, end, _ = parts
    return text[:start] + text[end:]


def strip_bibliography(text: str) -> str:
    text = BIBLIOGRAPHY_ENVIRONMENT.sub("", text)
    text = AMSTEX_BIBLIOGRAPHY_ENVIRONMENT.sub("", text)
    text = re.sub(r"\\bibliographystyle\s*\{[^{}]*\}", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\\bibliography\s*\{[^{}]*\}", "", text, flags=re.IGNORECASE)
    headings = [
        match
        for pattern in (BIBLIOGRAPHY_HEADING, MANUAL_BIBLIOGRAPHY_HEADING)
        if (match := pattern.search(text))
    ]
    if not headings:
        return text
    start = min(match.start() for match in headings)
    end = bibliography_section_end(text, start)
    return text[:start] + text[end:]


def bibliography_section_end(text: str, start: int) -> int:
    candidates = [match.start() for match in STRUCTURAL_POST_BIBLIOGRAPHY.finditer(text, start + 1)]
    page_break = re.compile(r"(?im)^[ \t]*\\newpage\b")
    for match in page_break.finditer(text, start + 1):
        following = text[match.end() : match.end() + 300]
        if re.search(r"(?i)\b(?:Table\s+\d+|Figure\s+Captions?|Appendix)\b", following):
            candidates.append(match.start())
    return min(candidates) if candidates else len(text)


def split_document_source(text: str) -> tuple[str, str]:
    begin = ACTIVE_BEGIN_DOCUMENT.search(text)
    if not begin:
        amstex = AMSTEX_DOCUMENT_START.search(text)
        if amstex:
            end = AMSTEX_DOCUMENT_END.search(text, amstex.end())
            body_end = end.start() if end else len(text)
            return text[: amstex.start()], text[amstex.end() : body_end]
        end = ACTIVE_END_DOCUMENT.search(text)
        return "", text[: end.start()] if end else text
    end = ACTIVE_END_DOCUMENT.search(text, begin.end())
    body = text[begin.end() : end.start()] if end else text[begin.end() :]
    if end:
        body += trailing_scientific_appendix(text[end.end() :])
    return text[: begin.start()], body


def trailing_scientific_appendix(tail: str) -> str:
    marker = re.search(r"(?im)^[ \t]*\\(?:appendix\b|(?:section|chapter)\*?\s*\{)", tail)
    if not marker:
        return ""
    if ACTIVE_BEGIN_DOCUMENT.search(tail[: marker.start()]):
        return ""
    appendix = tail[marker.start() :]
    heading = re.search(r"\\(?:section|chapter)\*?\s*\{[^{}]*Appendix", appendix, re.IGNORECASE)
    heading = heading or re.match(
        r"\\(?:section|chapter)\*?\s*\{", appendix.lstrip(), re.IGNORECASE
    )
    words = re.findall(r"[A-Za-z]{3,}", strip_comments_outside_literals(appendix))
    return "\n" + appendix if heading and len(words) >= 20 else ""


def prepare_source(source: str) -> str:
    text = normalize_source_control_bytes(legacy.strip_iffalse_blocks(source))
    text = strip_noncontent_source(text)
    text = legacy.strip_huge_preamble_before_macro_expansion(text)
    text = legacy.strip_known_malformed_preamble(text)
    preamble, body = split_document_source(text)
    body = legacy.drop_balanced_argument_commands(body, BODY_METADATA_COMMAND)
    body = strip_source_abstract(body)
    body = strip_page_layout_metadata(body)
    body = cleanup_case.normalize_manual_sections(body)
    body = cleanup_case.strip_front_matter_residue(body)
    body = legacy.normalize_custom_section_commands(body)
    body = table_case.protect_formal_tables(body, preamble)
    body = expand_retrieval_macros(body)
    body = expand_retrieval_macros(body, preamble)
    body = strip_declared_graphic_calls(body, preamble)
    body = strip_nonsemantic_markup(body).replace(r"\ensuremathTEMP", r"\ensuremath")
    body = strip_page_layout_metadata(body)
    body = normalize_semantic_aliases(body)
    body = drop_unresolved_comment_commands(body)
    body = strip_bibliography(body)
    body = strip_table_of_contents(body)
    body = strip_figure_caption_sections(body)
    body = strip_custom_figure_calls(body)
    body = protect_inline_code_runs(body)
    body = OVERFULL_DRAFT_CONDITIONAL.sub("", body)
    body = unwrap_text_styles(body)
    body = re.sub(r"\\(?:noindent|indent)\b", "", body)
    body = strip_comments_outside_literals(body)
    body = strip_source_abstract(body)
    body = strip_layout_outside_formal_content(body)
    body = legacy.RE_BODY_METADATA_COMMANDS.sub("", body)
    return body.strip()


def strip_custom_figure_calls(text: str) -> str:
    """Drop source-specific figure macros after macro expansion has retained calls."""
    text = strip_figbox_calls(text)
    text = strip_graphic_wrappers(text)
    pattern = re.compile(r"\\fig(?![A-Za-z])")
    for match in reversed(list(pattern.finditer(text))):
        cursor = skip_optional_table_argument(text, match.end())
        parsed = read_macro_args(text, cursor, 2)
        if parsed:
            _, end = parsed
            text = text[: match.start()] + text[end:]
    graphics = re.compile(
        r"\\(?:epsfig|psfig|epsfbox|epsffile|includegraphics)\*?\b", re.IGNORECASE
    )
    for match in reversed(list(graphics.finditer(text))):
        cursor = skip_optional_table_argument(text, match.end())
        parsed = read_macro_args(text, cursor, 1)
        if parsed:
            _, end = parsed
            text = text[: match.start()] + text[end:]
    return strip_empty_graphic_wrappers(text)


def strip_declared_graphic_calls(text: str, definitions: str) -> str:
    graphic = re.compile(r"\\(?:includegraphics|epsfig|psfig|epsfbox|epsffile)\b", re.IGNORECASE)
    in_scope = re.compile(r"\\begin\{(?:tabular|algorithm|verbatim|lstlisting)\}", re.IGNORECASE)
    wrappers = {
        (name, nargs)
        for _, _, name, nargs, body in retrieval_macros(definitions)
        if 1 <= nargs <= 5 and graphic.search(body) and not in_scope.search(body)
    }
    for name, nargs in wrappers:
        pattern = re.compile(re.escape(name) + r"(?![A-Za-z])")
        for match in reversed(list(pattern.finditer(text))):
            parsed = read_macro_args(text, match.end(), nargs)
            if parsed:
                text = text[: match.start()] + text[parsed[1] :]
    return text


def strip_figbox_calls(text: str) -> str:
    pattern = re.compile(r"\\figbox(?![A-Za-z])", re.IGNORECASE)
    for match in reversed(list(pattern.finditer(text))):
        cursor = skip_optional_table_argument(text, match.end())
        parsed = read_macro_args(text, cursor, 4)
        if not parsed:
            continue
        args, end = parsed
        replacement = args[0] if args[1].strip().lower() == "table" else ""
        text = text[: match.start()] + replacement + text[end:]
    return text


def strip_empty_graphic_wrappers(text: str) -> str:
    pattern = re.compile(r"\\resizebox(?:\*)?", re.IGNORECASE)
    for match in reversed(list(pattern.finditer(text))):
        parsed = read_macro_args(text, match.end(), 3)
        if parsed and not parsed[0][2].strip():
            text = text[: match.start()] + text[parsed[1] :]
    return text


def protect_inline_code_runs(text: str) -> str:
    pattern = re.compile(r"\\texttt\s*\{")
    runs, cursor = [], 0
    while match := pattern.search(text, cursor):
        close = legacy.find_matching_brace(text, match.end() - 1)
        if close < 0:
            cursor = match.end()
            continue
        end, bodies = close + 1, [text[match.end() : close]]
        while True:
            separator = re.match(
                r"(?:\s|\{\\(?:small|footnotesize|scriptsize|tiny)\s+\\par\})*", text[end:]
            )
            next_start = end + separator.end()
            following = pattern.match(text, next_start)
            if not following:
                break
            next_close = legacy.find_matching_brace(text, following.end() - 1)
            if next_close < 0:
                break
            bodies.append(text[following.end() : next_close])
            end = next_close + 1
        if len(bodies) >= 2:
            runs.append((match.start(), end, bodies))
        cursor = end
    for start, end, bodies in reversed(runs):
        block = "\\begin{lyxcode}\n" + "\n".join(bodies) + "\n\\end{lyxcode}"
        text = text[:start] + block + text[end:]
    return text


def strip_graphic_wrappers(text: str) -> str:
    pattern = re.compile(r"\\resizebox(?:\*)?", re.IGNORECASE)
    for match in reversed(list(pattern.finditer(text))):
        parsed = read_macro_args(text, match.end(), 3)
        if parsed and re.search(
            r"\\(?:includegraphics|epsfig|psfig)\b", parsed[0][2], re.IGNORECASE
        ):
            text = text[: match.start()] + text[parsed[1] :]
    return text


def strip_figure_caption_sections(text: str) -> str:
    heading = re.compile(
        r"\\(?:section|subsection|subsubsection)\*?\s*\{\s*(?:list\s+of\s+)?"
        r"figure(?:s|\s+captions?)?\s*\}",
        re.IGNORECASE,
    )
    section = re.compile(r"\\(?:section|subsection|subsubsection)\*?\s*\{")
    for match in reversed(list(heading.finditer(text))):
        following = section.search(text, match.end())
        end = following.start() if following else len(text)
        text = text[: match.start()] + text[end:]
    plain_heading = re.compile(
        r"(?im)^\s*(?:\{?\\(?:bf|large|Large)\s*)?(?:list\s+of\s+)?"
        r"Figure\s+Captions?\s*[.:}]?\s*$"
    )
    for match in reversed(list(plain_heading.finditer(text))):
        following = section.search(text, match.end())
        end = following.start() if following else len(text)
        text = text[: match.start()] + text[end:]
    return text


def strip_table_of_contents(text: str) -> str:
    heading = re.compile(
        r"\\(?:section|subsection)\*?\s*\{\s*Table\s+of\s+Contents\s*\}", re.IGNORECASE
    )
    section = re.compile(r"\\(?:section|subsection)\*?\s*\{")
    for match in reversed(list(heading.finditer(text))):
        following = section.search(text, match.end())
        end = following.start() if following else len(text)
        text = text[: match.start()] + text[end:]
    return text


def strip_page_layout_metadata(text: str) -> str:
    names = re.compile(
        r"\\(pagestyle|thispagestyle|markboth|markright|markleft|fancyhead|fancyfoot)\b"
    )
    for match in reversed(list(names.finditer(text))):
        count = 2 if match.group(1).lower() == "markboth" else 1
        parsed = read_macro_args(text, match.end(), count)
        if parsed:
            _, end = parsed
            text = text[: match.start()] + text[end:]
    return text


def strip_nonsemantic_markup(text: str) -> str:
    text = legacy.drop_balanced_argument_commands(text, re.compile(r"\\index\s*\{"))
    text = re.sub(
        r"\\(?:protect|xspace|tipaencoding|singlespacing(?:plus(?:plus)?)?|normalspacing|"
        r"nice(?:one|two)spacing|nolinebreak|linebreak|nopagebreak|normalfont|bfseries)(?![A-Za-z])",
        " ",
        text,
    )
    text = re.sub(r"\\(?:it|bf|rm|sf|tt|sl)\b(?=\s)", " ", text)
    return re.sub(r"[ \t]+", " ", text)


def strip_layout_outside_formal_content(text: str) -> str:
    protected: dict[str, str] = {}
    targets = MATH_ENVS | {
        "table",
        "table*",
        "tabular",
        "tabular*",
        "longtable",
        "tabbing",
        "description",
        "description*",
    }
    targets |= CODE_ENVS | TEXT_EXAMPLE_ENVS
    spans = [(start, end) for start, end, _ in environment_spans(text, targets)]
    spans.extend(match.span() for match in legacy.RE_MATH_SPAN.finditer(text))
    for index, (start, end) in enumerate(sorted(legacy.merged_spans(spans), reverse=True)):
        token = f"LAYOUTSPAN{index:06d}TOKEN"
        protected[token] = text[start:end]
        text = text[:start] + token + text[end:]
    text = strip_direct_layout_commands(text)
    for token, content in protected.items():
        text = text.replace(token, content)
    return text


def normalize_semantic_aliases(text: str) -> str:
    aliases = {
        r"\\evOper\s*\\?": "evolution operator",
        r"\\FPoper\s*\\?": "Perron-Frobenius operator",
        r"\\dzeta\s*s?": "dynamical zeta functions",
        r"\\fd(?![A-Za-z])\s*s?": "Fredholm determinants",
    }
    for pattern, replacement in aliases.items():
        text = re.sub(pattern, replacement, text)
    return text


def strip_comments_outside_literals(text: str) -> str:
    masked = legacy.RE_COMMENT_LINE.sub(lambda match: " " * len(match.group(0)), text)
    spans = [(match.start(), match.end()) for match in legacy.RE_VERBATIM_ENV.finditer(masked)]
    spans.extend((match.start(), match.end()) for match in legacy.RE_VERB_COMMAND.finditer(masked))
    protected = {}
    for index, (start, end) in enumerate(sorted(legacy.merged_spans(spans), reverse=True)):
        token = f"LITERALSPAN{index:06d}TOKEN"
        protected[token] = text[start:end]
        text = text[:start] + token + text[end:]
    text = re.sub(r"(?m)^[ \t]*%[^\n]*(?:\n|$)", "", text)
    text = legacy.RE_COMMENT_LINE.sub("", text)
    for token, literal in protected.items():
        text = text.replace(token, literal)
    return text


def unwrap_text_styles(text: str) -> str:
    previous = None
    while previous != text:
        previous = text
        text = legacy.unwrap_argument_command_pattern(text, TEXT_STYLE_COMMAND, block=False)
        text = OLD_TEXT_FONT_BRACED_GROUP.sub(r"{\1}", text)
        text = OLD_TEXT_FONT_GROUP.sub(r"{\1}", text)
    return text


def drop_unresolved_comment_commands(text: str) -> str:
    for match in reversed(list(UNRESOLVED_COMMENT_COMMAND.finditer(text))):
        close = legacy.find_matching_brace(text, match.end() - 1)
        if close >= 0:
            text = text[: match.start()] + text[close + 1 :]
    return text


def environment_spans(text: str, targets: set[str]) -> list[tuple[int, int, str]]:
    stack: list[tuple[str, int]] = []
    spans = []
    for match in ENV_TOKEN.finditer(text):
        env = match.group(2).lower()
        if match.group(1).lower() == "begin":
            stack.append((env, match.start()))
            continue
        index = next((i for i in range(len(stack) - 1, -1, -1) if stack[i][0] == env), None)
        if index is None:
            continue
        _, start = stack[index]
        del stack[index:]
        if env in targets:
            spans.append((start, match.end(), env))
    return outermost_spans(spans)


def outermost_spans(spans: list[tuple[int, int, str]]) -> list[tuple[int, int, str]]:
    selected = []
    for span in sorted(spans, key=lambda value: (value[0], -value[1])):
        if selected and span[0] < selected[-1][1]:
            continue
        selected.append(span)
    return selected


def latex_fence(label: str, source: str) -> str:
    return f"\n\n{source.strip()}\n\n"


def formal_token(index: int) -> str:
    return f"⟬{index:06d}⟭"


def render_table_block(block: str) -> str:
    if TABLE_OUT_OF_SCOPE_CONTENT.search(block):
        return ""
    tabbing_spans = environment_spans(block, {"tabbing"})
    if tabbing_spans:
        caption = clean_table_caption(block)
        rendered = [
            render_tabbing_block(block[start:end]).strip() for start, end, _ in tabbing_spans
        ]
        parts = [f"*Table: {caption}*"] if caption else []
        parts.extend(item for item in rendered if item)
        return "\n\n" + "\n\n".join(parts) + "\n\n"
    if table_case.should_preserve_source(block):
        caption = clean_table_caption(block)
        source_table = fallback_table_markdown(table_case.source_table_content(block))
        parts = [f"*Table: {caption}*"] if caption else []
        parts.append(source_table)
        return "\n\n" + "\n\n".join(parts) + "\n\n"
    verbatim = table_verbatim_markdown(block)
    if verbatim:
        return f"\n\n{verbatim}\n\n"
    manual = preferred_manual_tables(block)
    if manual:
        caption = clean_table_caption(block)
        parts = [f"*Table: {caption}*"] if caption else []
        if not all(valid_markdown_table(table) for table in manual):
            parts.append(fallback_table_markdown(table_case.source_table_content(block)))
            return "\n\n" + "\n\n".join(parts) + "\n\n"
        return "\n\n" + "\n\n".join(parts + manual) + "\n\n"
    pandoc_table = pandoc_table_markdown(block)
    if pandoc_table:
        return f"\n\n{pandoc_table}\n\n"
    caption = clean_table_caption(block)
    fragments = [
        block[start:end]
        for start, end, _ in environment_spans(block, {"tabular", "tabular*", "longtable"})
    ]
    if not fragments and TABULAR_BEGIN.search(block):
        fragments = [block]
    tables = [table_to_markdown(fragment) for fragment in fragments]
    tables = [table for table in tables if table]
    if not tables:
        description = description_table_markdown(block)
        if description:
            return (
                f"\n\n*Table: {caption}*\n\n{description}\n\n"
                if caption
                else f"\n\n{description}\n\n"
            )
        fallback = legacy.table_fragment_text(block)
        tables = [fallback_table_markdown(fallback)] if fallback else []
    parts = [f"*Table: {caption}*"] if caption else []
    parts.extend(tables)
    return "\n\n" + "\n\n".join(parts) + "\n\n" if parts else ""


def clean_table_caption(block: str) -> str:
    captions = raw_latex_captions(block)
    if not captions:
        return ""
    caption = legacy.RE_LABEL_COMMAND.sub("", captions[0])
    return clean_table_cell(caption)


def valid_markdown_table(table: str) -> bool:
    if not table.lstrip().startswith("|"):
        return True
    for line in table.splitlines():
        opening = len(re.findall(r"(?<!\\)\{", line))
        closing = len(re.findall(r"(?<!\\)\}", line))
        if opening != closing:
            return False
    return not bool(re.search(r"(?<!\\)\b(?:[A-Z][A-Z-]+|[a-z]{1,3})\}", table))


def preferred_manual_tables(block: str) -> list[str]:
    fragile = re.compile(r"\\(?:multirow|shortstack|parbox|fbox|char\d+|bordermatrix)\b")
    if fragile.search(block):
        return []
    fragments = [
        block[start:end]
        for start, end, _ in environment_spans(block, {"tabular", "tabular*", "longtable"})
    ]
    if not fragments or any(len(TABULAR_BEGIN.findall(fragment)) > 1 for fragment in fragments):
        return []
    rendered = [table_to_markdown(fragment) for fragment in fragments]
    return rendered if all(rendered) else []


def table_verbatim_markdown(block: str) -> str:
    environments = {"verbatim", "verbatim*", "alltt", "lstlisting", "acmlisting", "verbcode", "ce"}
    spans = environment_spans(block, environments)
    if not spans:
        return ""
    parts = [render_verbatim_block(env, block[start:end]).strip() for start, end, env in spans]
    return "\n\n".join(part for part in parts if part)


def description_table_markdown(block: str) -> str:
    text = legacy.table_fragment_text(block)
    items = re.findall(r"- \*\*[^*]*:\*\*\s*(.*?)(?=\n\s*- \*\*|\Z)", text, re.DOTALL)
    cleaned = [re.sub(r"\s+", " ", item).strip() for item in items]
    cleaned = [re.sub(r"\s*\d+(?:cm|mm|pt)\s+\d+(?:cm|mm|pt)\s*$", "", item) for item in cleaned]
    return "\n".join(f"- {item}" for item in cleaned if item)


def pandoc_table_markdown(block: str) -> str:
    if not PANDOC_COMPLEX_TABLE.search(block):
        return ""
    candidate = strip_table_rules(block)
    rendered = legacy.convert_pandoc(candidate)
    rendered = re.sub(r":::\s*(?:turn)?", "", rendered or "")
    if not rendered or not (MARKDOWN_TABLE.search(rendered) or PANDOC_GRID_TABLE.search(rendered)):
        return ""
    if PANDOC_TABLE_RESIDUE.search(rendered):
        return ""
    if rendered.count("{") != rendered.count("}") or any(
        line.count("{") != line.count("}") for line in rendered.splitlines()
    ):
        return ""
    source_tokens = set(FORMAL_TOKEN_RE.findall(block))
    rendered_tokens = set(FORMAL_TOKEN_RE.findall(rendered))
    if not source_tokens.issubset(rendered_tokens):
        return ""
    return clean_output_spacing(rendered)


def tabular_body(fragment: str) -> str:
    match = TABULAR_BEGIN.search(fragment)
    if not match:
        return ""
    cursor = match.end()
    argument_count = 2 if match.group(1).lower() == "tabular*" else 1
    for _ in range(argument_count):
        cursor = skip_optional_table_argument(fragment, cursor)
        cursor = skip_required_table_argument(fragment, cursor)
    end = fragment.lower().rfind(rf"\end{{{match.group(1).lower()}}}")
    return fragment[cursor : end if end >= cursor else len(fragment)]


def skip_optional_table_argument(text: str, cursor: int) -> int:
    cursor = skip_space(text, cursor)
    if cursor < len(text) and text[cursor] == "[":
        close = matching_delimiter(text, cursor, "[", "]")
        return close + 1 if close >= 0 else cursor
    return cursor


def skip_required_table_argument(text: str, cursor: int) -> int:
    cursor = skip_space(text, cursor)
    if cursor < len(text) and text[cursor] == "{":
        close = legacy.find_matching_brace(text, cursor)
        return close + 1 if close >= 0 else cursor
    return cursor


def skip_space(text: str, cursor: int) -> int:
    while cursor < len(text) and text[cursor].isspace():
        cursor += 1
    return cursor


def matching_delimiter(text: str, start: int, opening: str, closing: str) -> int:
    depth = 0
    for index in range(start, len(text)):
        if text[index] == opening and (index == 0 or text[index - 1] != "\\"):
            depth += 1
        elif text[index] == closing and (index == 0 or text[index - 1] != "\\"):
            depth -= 1
            if depth == 0:
                return index
    return -1


def split_table_level(text: str, separator: str) -> list[str]:
    parts, start, braces, math = [], 0, 0, False
    index = 0
    while index < len(text):
        char = text[index]
        if char == "$" and (index == 0 or text[index - 1] != "\\"):
            math = not math
        elif not math and char == "{":
            braces += 1
        elif not math and char == "}":
            braces = max(0, braces - 1)
        unescaped = index == 0 or text[index - 1] != "\\"
        if not math and braces == 0 and unescaped and text.startswith(separator, index):
            parts.append(text[start:index])
            index += len(separator)
            if separator == r"\\" and index < len(text) and text[index] == "[":
                close = matching_delimiter(text, index, "[", "]")
                index = close + 1 if close >= 0 else index
            start = index
            continue
        index += 1
    parts.append(text[start:])
    return parts


def table_to_markdown(fragment: str) -> str:
    body = table_case.normalize_body(strip_table_rules(tabular_body(fragment)))
    if len(TABULAR_BEGIN.findall(fragment)) > 1:
        return fallback_table_markdown(body)
    body = flatten_nested_tabular(body)
    rows = []
    for raw_row in split_table_level(body, r"\\"):
        cells = [clean_table_cell(cell) for cell in split_table_level(raw_row, "&")]
        cells = [cell for cell in cells if cell or len(cells) > 1]
        if any(cells):
            rows.append(cells)
    if not rows:
        return ""
    rows = merge_table_continuation_rows(rows)
    width = max(len(row) for row in rows)
    rows = [row + [""] * (width - len(row)) for row in rows]
    header, data = table_header_and_data(rows, width)
    lines = [markdown_table_row(header), markdown_table_row(["---"] * width)]
    lines.extend(markdown_table_row(row) for row in data)
    rendered = "\n".join(lines)
    if re.search(r"\\(?:multicolumn|multirow|begin|end)\b", rendered):
        return ""
    return rendered


def merge_table_continuation_rows(rows: list[list[str]]) -> list[list[str]]:
    merged = []
    for row in rows:
        previous = merged[-1] if merged else []
        continuation = (
            len(row) >= 3
            and len(previous) == len(row)
            and bool(row[0])
            and not row[1]
            and row[2].lstrip().startswith("(")
            and bool(previous[0])
            and bool(previous[1])
            and bool(previous[2])
            and row[0][:1].islower()
            and previous[0][:1].islower()
        )
        if not continuation:
            merged.append(row)
            continue
        for index, value in enumerate(row):
            if value:
                previous[index] = f"{previous[index]} {value}".strip()
    return merged


def strip_table_rules(text: str) -> str:
    text = re.sub(
        r"\\(?:hline|toprule|midrule|bottomrule|tableline)\b", "\n", text, flags=re.IGNORECASE
    )
    text = re.sub(r"\\cline\s*\{[^{}]*\}", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"\\(?:endfirsthead|endhead|endfoot|endlastfoot)\b", r"\\", text)
    return text


def clean_table_cell(cell: str) -> str:
    cell = table_case.strip_cell_spacing(cell)
    cell = flatten_nested_tabular(cell)
    cell = unwrap_spanning_cell(cell)
    cell = re.sub(r"\\(?:multicolumn|multirow)\s*\{[^{}]*\}\s*\{[^{}]*\}\s*", "", cell)
    cell = legacy.RE_LABEL_COMMAND.sub("", cell)
    cell = re.sub(r"\{\s*\\(?:small|footnotesize|scriptsize|tiny)\s+([^{}]*)\}", r"\1", cell)
    cell = re.sub(
        r"\\(?:centering|raggedright|raggedleft|small|footnotesize|scriptsize)\b", " ", cell
    )
    cell = re.sub(r"\\(?:vspace|hspace)\*?\s*\{[^{}]*\}", " ", cell)
    cell = re.sub(r"\\vbox\s+to\s+[^{}\s]+\s*\{\s*\}", "", cell)
    cell = unwrap_text_styles(cell)
    cell = normalize_direct_text_styles(cell)
    for _ in range(2):
        cell = re.sub(r"\{\s*(\$[^$]*\$[^{}]*)\}", r"\1", cell)
    cell = re.sub(r"^\s*\{\s*([^{}]+)\}(?=\\[A-Za-z]+|$)", r"\1", cell)
    cell = cell.replace(r"\&", "&")
    cell = re.sub(r"^\s*\[[\d.]+(?:ex|em|pt|mm|cm)?\]\s*", "", cell)
    cell = cell.replace("\n", " ").replace("|", r"\|")
    return re.sub(r"\s+", " ", cell).strip(" {}")


def flatten_nested_tabular(cell: str) -> str:
    spans = environment_spans(cell, {"tabular", "tabular*", "longtable"})
    for start, end, _ in reversed(spans):
        text = legacy.table_fragment_text(cell[start:end])
        replacement = "<br>".join(line.strip() for line in text.splitlines() if line.strip())
        cell = cell[:start] + replacement + cell[end:]
    return cell


def unwrap_spanning_cell(cell: str) -> str:
    pattern = re.compile(r"\\(?:multicolumn|multirow)\s*\{[^{}]*\}\s*\{[^{}]*\}\s*\{")
    match = pattern.search(cell)
    if not match:
        return cell
    close = legacy.find_matching_brace(cell, match.end() - 1)
    if close < 0:
        return cell
    return cell[: match.start()] + cell[match.end() : close] + cell[close + 1 :]


def table_header_and_data(rows: list[list[str]], width: int) -> tuple[list[str], list[list[str]]]:
    first = rows[0]
    words = sum(len(re.findall(r"[A-Za-z]{2,}", cell)) for cell in first)
    numbers = sum(len(re.findall(r"(?<![A-Za-z])\d", cell)) for cell in first)
    if words and (words >= numbers or bool(re.search(r"[A-Za-z]", first[0]))):
        return first, rows[1:]
    return [f"Column {index}" for index in range(1, width + 1)], rows


def markdown_table_row(cells: list[str]) -> str:
    return "| " + " | ".join(cells) + " |"


def fallback_table_markdown(text: str) -> str:
    rows = [line.rstrip() for line in text.splitlines() if line.strip()]
    if not rows:
        return ""
    return "```text\n" + "\n".join(rows) + "\n```"


def raw_latex_captions(block: str) -> list[str]:
    captions = []
    position = 0
    while match := legacy.RE_CAPTION_COMMAND.search(block, position):
        close = legacy.find_matching_brace(block, match.end() - 1)
        if close < 0:
            break
        captions.append(block[match.end() : close])
        position = close + 1
    return captions


def render_figure_block(block: str, theorem_envs: dict[str, str]) -> str:
    return figure_case.render_embedded_content(
        block, lambda body: render_formal_body(body, theorem_envs)
    )


def render_formal_block(env: str, block: str, theorem_envs: dict[str, str]) -> str:
    if env == FORMAL_RAW_TABLE_ENV:
        return latex_fence("", table_case.decode_formal_table(block))
    if env.startswith("table") or env.startswith("tabular") or env == "longtable":
        return render_table_block(block)
    if env.startswith("figure"):
        return render_figure_block(block, theorem_envs)
    if env in theorem_envs:
        return render_named_formal_block(env, block, theorem_envs)
    if env in {"ex", "exo", "subex"}:
        return render_named_formal_block(env, block, theorem_envs)
    if env == "tabbing":
        return render_tabbing_block(block)
    if env.startswith("description"):
        return render_description_block(block, theorem_envs)
    if env in TEXT_EXAMPLE_ENVS:
        return render_text_example_block(env, block)
    if env in {"algorithm", "algorithm*", "algorithmic", "program"} or "algo" in env:
        return render_named_formal_block(env, block, theorem_envs)
    if env.lower().startswith("program"):
        return render_custom_program_block(env, block)
    if env == "avm":
        return latex_fence("", block)
    if env in {"picture", "pspicture"}:
        return ""
    if env in CODE_ENVS:
        return render_verbatim_block(env, block)
    return latex_fence("", clean_math_presentation(block))


def render_named_formal_block(env: str, block: str, theorem_envs: dict[str, str]) -> str:
    pattern = re.compile(rf"\\begin\s*\{{{re.escape(env)}\}}(?:\[([^\]]*)\])?", re.IGNORECASE)
    match = pattern.search(block)
    end = re.search(rf"\\end\s*\{{{re.escape(env)}\}}\s*$", block, re.IGNORECASE)
    body = block[match.end() : end.start()] if match and end else block
    name = theorem_envs.get(env, env.replace("*", "").replace("_", " ").title())
    if env == "nemma" and body.lstrip().startswith("{"):
        start = body.index("{")
        close = legacy.find_matching_brace(body, start)
        body = body[close + 1 :] if close >= 0 else body
    if match and match.group(1):
        name += f" ({clean_table_cell(match.group(1))})"
    if "algo" in env or env in {"algorithm", "algorithm*", "algorithmic", "program"}:
        if re.search(r"\\(?:ForEach|For|While|If|Else|Begin|SetVline)\b", body):
            return f"\n\n### {name}\n\n{body.strip()}\n\n"
    return f"\n\n### {name}\n\n{render_formal_body(body, theorem_envs)}\n\n"


def render_formal_body(body: str, theorem_envs: dict[str, str]) -> str:
    table_envs = {"table", "table*", "tabular", "tabular*", "longtable"}
    formal_envs = table_envs | MATH_ENVS | CODE_ENVS | TEXT_EXAMPLE_ENVS
    formal_envs |= {"tabbing", "description", "description*", "ex", "exo", "subex"} | set(
        theorem_envs
    )
    spans = outermost_spans(environment_spans(body, formal_envs))
    rendered_blocks = {}
    for start, end, env in reversed(spans):
        rendered = render_formal_block(env, body[start:end], theorem_envs)
        token = f"INNERFORMAL{len(rendered_blocks):06d}TOKEN"
        rendered_blocks[token] = rendered
        body = body[:start] + f"\n{token}\n" + body[end:]
    body = render_inline_footnotes(source_preserving_prose(body))
    for token, rendered in rendered_blocks.items():
        body = body.replace(token, rendered)
    return body


def render_inline_footnotes(text: str) -> str:
    pattern = re.compile(r"\\footnote(?:\s*\[[^\]\n]*\])?\s*\{")
    for match in reversed(list(pattern.finditer(text))):
        close = legacy.find_matching_brace(text, match.end() - 1)
        if close >= 0:
            body = clean_footnote_body(text[match.end() : close])
            text = text[: match.start()] + f" (Footnote: {body})" + text[close + 1 :]
    return text


def clean_footnote_body(body: str) -> str:
    body = legacy.RE_LABEL_COMMAND.sub("", body)
    body = re.sub(r"\{\s*\}", "", body)
    return source_preserving_prose(body).replace("\n\n", " ").strip()


def render_tabbing_block(block: str) -> str:
    return tabbing_case.render(block, clean_tex_formatted_code)


def render_description_block(block: str, theorem_envs: dict[str, str]) -> str:
    body = description_body(block)
    children: dict[str, str] = {}
    spans = [
        span
        for span in environment_spans(body, {"description", "description*"})
        if 0 < span[1] - span[0] < len(body)
    ]
    for start, end, _ in reversed(spans):
        child = body[start:end]
        if description_body(child) == child:
            continue
        token = f"DESCRIPTIONNEST{len(children):06d}TOKEN"
        children[token] = render_description_block(child, theorem_envs).strip()
        body = body[:start] + f"\n{token}\n" + body[end:]
    items = description_items(body)
    if not items:
        return source_preserving_prose(body)
    rendered = [render_description_item(label, content, children) for label, content in items]
    return "\n\n" + "\n".join(item for item in rendered if item) + "\n\n"


def description_body(block: str) -> str:
    start = re.search(r"\\begin\{description\*?\}", block, re.IGNORECASE)
    ends = list(re.finditer(r"\\end\{description\*?\}", block, re.IGNORECASE))
    end = ends[-1] if ends else None
    return (
        block[start.end() : end.start()] if start and end and end.start() >= start.end() else block
    )


def description_items(text: str) -> list[tuple[str, str]]:
    matches = list(re.finditer(r"\\item\b", text))
    items = []
    for index, match in enumerate(matches):
        cursor = skip_space(text, match.end())
        label = ""
        if cursor < len(text) and text[cursor] == "[":
            close = matching_delimiter(text, cursor, "[", "]")
            if close >= 0:
                label, cursor = text[cursor + 1 : close], close + 1
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        items.append((label, text[cursor:end]))
    return items


def render_description_item(label: str, content: str, children: dict[str, str]) -> str:
    label = clean_description_label(label)
    nested = []
    for token, child in children.items():
        if token in content:
            content = content.replace(token, "")
            nested.append(child)
    content = clean_description_content(content)
    prefix = f"- **{label}:**" if label else "-"
    rendered = (
        prefix
        if not content
        else f"{prefix} {content}"
        if "\n" not in content
        else f"{prefix}\n{indent_markdown(content, 2)}"
    )
    nested_text = "\n".join(indent_markdown(child, 2) for child in nested)
    return f"{rendered}\n{nested_text}" if nested_text else rendered


def clean_description_label(text: str) -> str:
    text = unwrap_text_styles(text)
    text = re.sub(r"\\(?:small|footnotesize|scriptsize|tiny|normalsize)\b", "", text)
    text = text.replace(r"{[}", "[").replace(r"{]}", "]").replace(r"\_", "_")
    text = re.sub(r"\\(?:par|noindent|indent)\b", "", text).replace("~", " ")
    text = re.sub(r"[{}]", "", text)
    return re.sub(r"\s+", " ", text).strip(" *:")


def clean_description_content(text: str) -> str:
    empty_group = (
        r"~?\s*\{\s*(?:\\(?:small|footnotesize|scriptsize|tiny|normalsize)\s*)?(?:\\par\s*)?\}"
    )
    previous = None
    while text != previous:
        previous = text
        text = re.sub(empty_group, "", text)
    text = source_preserving_prose(text).replace("~", " ")
    for _ in range(3):
        text = text.replace(r"{[}", "[").replace(r"{]}", "]")
        text = re.sub(r"\{\s*\[\s*\}", "[", text)
        text = re.sub(r"\{\s*\]\s*\}", "]", text)
        text = re.sub(r"\{\s*([\[(][^{}\\$]*?)\s*\}", r"\1", text)
    text = re.sub(r"\[\s+", "[", text)
    text = re.sub(r"\s+\]", "]", text)
    text = re.sub(r"(?m)^\s*[{}~]+\s*$", "", text)
    return clean_output_spacing(text)


def indent_markdown(text: str, spaces: int) -> str:
    prefix = " " * spaces
    return "\n".join(prefix + line if line else line for line in text.splitlines())


def render_verbatim_block(env: str, block: str) -> str:
    body = environment_body(block, env)
    if env == "listing":
        body = re.sub(r"^\s*(?:\[[^\]\n]*\])?(?:\{[^{}\n]*\})?", "", body)
    if env in TEX_FORMATTED_CODE_ENVS:
        body = clean_tex_formatted_code(body)
    return f"\n\n```text\n{body.strip()}\n```\n\n"


def render_custom_program_block(env: str, block: str) -> str:
    body = environment_body(block, env)
    parsed = read_macro_args(body, 0, 2)
    title = ""
    if parsed:
        args, end = parsed
        title = re.sub(r"[{}]", "", clean_table_cell(args[1]))
        body = body[end:]
    body = clean_tex_formatted_code(body)
    heading = f"### {title}\n\n" if title else ""
    return f"\n\n{heading}```text\n{body.strip()}\n```\n\n"


def render_text_example_block(env: str, block: str) -> str:
    body = clean_tex_formatted_code(environment_body(block, env))
    body = "\n".join(line.strip() for line in body.splitlines() if line.strip())
    return f"\n\n```text\n{body}\n```\n\n" if body else ""


def environment_body(block: str, env: str) -> str:
    start = re.search(rf"\\begin\{{{re.escape(env)}\}}", block, re.IGNORECASE)
    end = re.search(rf"\\end\{{{re.escape(env)}\}}\s*$", block, re.IGNORECASE)
    return block[start.end() : end.start()] if start and end else block


def clean_tex_formatted_code(text: str) -> str:
    text = unwrap_text_styles(text)
    text = unwrap_code_font_groups(text)
    text = decode_verb_commands(text)
    text = re.sub(r"\\(?:small|footnotesize|scriptsize|tiny|normalsize)\b", "", text)
    text = text.replace(r"\~{}", "CODELITERALTILDETOKEN")
    text = re.sub(r"\\\\(?:\s*\[[^\]\n]*\])?[ \t]*(?:\r?\n)?", "\n", text)
    text = re.sub(r"\\par\b", "\n", text)
    for _ in range(3):
        text = text.replace(r"{[}", "[").replace(r"{]}", "]")
    text = text.replace(r"\_", "_").replace(r"\#", "#")
    text = text.replace(r"\%", "%").replace(r"\&", "&")
    text = text.replace(r"\{", "{").replace(r"\}", "}")
    text = text.replace("{*}", "*").replace("~", " ")
    text = text.replace("CODELITERALTILDETOKEN", "~")
    text = re.sub(r"\{\s*\}", "", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def decode_verb_commands(text: str) -> str:
    pattern = re.compile(r"\\verb(\S)(.*?)\1", re.DOTALL)
    return pattern.sub(lambda match: match.group(2), text)


def unwrap_code_font_groups(text: str) -> str:
    pattern = re.compile(r"\{\\(?:small|footnotesize|scriptsize|tiny|normalsize)\s*")
    for _ in range(12):
        matches = list(pattern.finditer(text))
        if not matches:
            break
        for match in reversed(matches):
            close = legacy.find_matching_brace(text, match.start())
            if close >= 0:
                text = text[: match.start()] + text[match.end() : close] + text[close + 1 :]
    return text


def replace_spans(
    text: str,
    spans: list[tuple[int, int, str]],
    theorem_envs: dict[str, str],
    blocks: dict[str, str] | None = None,
) -> tuple[str, dict[str, str]]:
    blocks = {} if blocks is None else blocks
    for start, end, env in reversed(spans):
        token = formal_token(len(blocks))
        blocks[token] = render_formal_block(env, text[start:end], theorem_envs)
        text = text[:start] + f"\n\n{token}\n\n" + text[end:]
    return text, blocks


def protect_inline_math(text: str, blocks: dict[str, str]) -> str:
    def replacement(match: re.Match) -> str:
        token = formal_token(len(blocks))
        blocks[token] = clean_inline_math_presentation(match.group(0))
        return token

    return legacy.RE_MATH_SPAN.sub(replacement, text)


def clean_math_presentation(text: str) -> str:
    """Remove only size switches that have no mathematical meaning."""
    text = MATH_PRESENTATION_COMMAND.sub("", text)
    text = unwrap_ensuremath_wrappers(text)
    text = text.replace(r"\EuScript", r"\mathcal")
    return text.replace(r"\Bbb", r"\mathbb")


def unwrap_ensuremath_wrappers(text: str) -> str:
    pattern = re.compile(r"\\ensuremath\s*\{")
    for _ in range(8):
        matches = list(pattern.finditer(text))
        if not matches:
            break
        for match in reversed(matches):
            close = legacy.find_matching_brace(text, match.end() - 1)
            if close >= 0:
                text = text[: match.start()] + text[match.end() : close] + text[close + 1 :]
    return text


def clean_inline_math_presentation(text: str) -> str:
    text = clean_math_presentation(text)
    if text.startswith("$$"):
        return text
    return re.sub(r"\s+", " ", text).strip()


def protect_inline_verbatim(text: str, blocks: dict[str, str]) -> str:
    def replacement(match: re.Match) -> str:
        token = formal_token(len(blocks))
        blocks[token] = f"`{match.group(2).strip()}`"
        return token

    return legacy.RE_VERB_COMMAND.sub(replacement, text)


def protect_semantic_commands(text: str, blocks: dict[str, str]) -> str:
    pattern = re.compile(r"\\[A-Z][A-Z0-9]{1,}(?![A-Za-z])")

    def replacement(match: re.Match) -> str:
        token = formal_token(len(blocks))
        blocks[token] = f"`{match.group(0)}`"
        return token

    return pattern.sub(replacement, text)


def protect_citation_commands(text: str, blocks: dict[str, str]) -> str:
    matches = list(legacy.RE_CITE_FAMILY_COMMAND.finditer(text))
    matches.extend(CUSTOM_CITATION_COMMAND.finditer(text))
    matches.extend(NAMED_CITATION_COMMAND.finditer(text))
    unique = {(match.start(), match.end()): match for match in matches}
    for match in sorted(unique.values(), key=lambda value: value.start(), reverse=True):
        token = formal_token(len(blocks))
        blocks[token] = match.group(0)
        text = text[: match.start()] + token + text[match.end() :]
    return text


def protect_reference_commands(text: str, blocks: dict[str, str]) -> str:
    matches = list(legacy.RE_REF_FAMILY_COMMAND.finditer(text))
    matches.extend(CUSTOM_REFERENCE_COMMAND.finditer(text))
    matches.extend(legacy.RE_LABEL_COMMAND.finditer(text))
    for match in sorted(matches, key=lambda value: value.start(), reverse=True):
        token = formal_token(len(blocks))
        blocks[token] = match.group(0)
        text = text[: match.start()] + token + text[match.end() :]
    return text


def protect_plain_numeric_references(text: str, blocks: dict[str, str]) -> str:
    pattern = re.compile(
        r"\b(?:subcases?|cases?|theorems?|lemmas?|propositions?|equations?|sections?)\s+"
        r"\d+(?:\.\d+)+\.?",
        re.IGNORECASE,
    )
    for match in reversed(list(pattern.finditer(text))):
        token = formal_token(len(blocks))
        blocks[token] = match.group(0)
        text = text[: match.start()] + token + text[match.end() :]
    return text


def protect_remaining_macro_uses(text: str, source: str, blocks: dict[str, str]) -> str:
    signatures = remaining_macro_signatures(source, text)
    for name, (nargs, body) in signatures.items():
        pattern = re.compile(re.escape(name) + r"(?![A-Za-z])")
        for match in reversed(list(pattern.finditer(text))[:300]):
            if nargs:
                parsed = read_macro_args(text, match.end(), nargs)
                if not parsed:
                    continue
                args, end = parsed
            else:
                args = []
                end = match.end()
            token = formal_token(len(blocks))
            invocation = text[match.start() : end]
            expanded = body
            for index, argument in enumerate(args, 1):
                expanded = expanded.replace(f"#{index}", argument)
            evidence = invocation if not expanded.strip() else f"{invocation} = {expanded.strip()}"
            blocks[token] = (
                f"`{evidence[:500]}`"
                if "\n" not in evidence
                else latex_fence("### Formal Source", evidence)
            )
            text = text[: match.start()] + token + text[end:]
    return text


def remaining_macro_signatures(source: str, text: str) -> dict[str, tuple[int, str]]:
    definitions = {}
    for _, _, name, nargs, body in retrieval_macros(source):
        definitions[name] = (nargs, body)
    used = set(re.findall(r"\\[A-Za-z]+", text))
    semantic = re.compile(r"[A-Za-z]{2,}|[$&_^]|\\(?:frac|rightarrow|longrightarrow|begin)\b")
    optional_names = optional_argument_macro_names(source)
    return {
        name: (nargs, body)
        for name, (nargs, body) in definitions.items()
        if name not in optional_names
        and name in used
        and semantic.search(body)
        and len(body) <= 1000
    }


def protect_footnotes(text: str, blocks: dict[str, str]) -> str:
    pattern = re.compile(r"\\footnote(?:\s*\[[^\]\n]*\])?\s*\{")
    for match in reversed(list(pattern.finditer(text))):
        close = legacy.find_matching_brace(text, match.end() - 1)
        if close == -1:
            continue
        body = clean_footnote_body(text[match.end() : close])
        token = formal_token(len(blocks))
        blocks[token] = f" (Footnote: {body})"
        text = text[: match.start()] + token + text[close + 1 :]
    return text


def protect_ensuremath(text: str, blocks: dict[str, str]) -> str:
    matches = list(re.finditer(r"\\ensuremath\s*\{", text))
    for match in reversed(matches):
        close = legacy.find_matching_brace(text, match.end() - 1)
        if close < 0:
            continue
        body = clean_math_presentation(text[match.end() : close])
        prefix = text[: match.start()]
        inside_math = len(re.findall(r"(?<!\\)\$", prefix)) % 2 == 1
        if inside_math:
            replacement = "{" + body + "}"
        else:
            replacement = formal_token(len(blocks))
            blocks[replacement] = f"${body}$"
        text = text[: match.start()] + replacement + text[close + 1 :]
    return text


def restore_blocks(text: str, blocks: dict[str, str]) -> str:
    for _ in range(8):
        before = text
        for token, block in reversed(list(blocks.items())):
            text = text.replace(token, block)
        if text == before or not FORMAL_TOKEN_RE.search(text):
            break
    return text


def protect_plain_formal_blocks(text: str, blocks: dict[str, str]) -> str:
    def replacement(match: re.Match) -> str:
        token = formal_token(len(blocks))
        blocks[token] = latex_fence("", clean_math_presentation(match.group(0)))
        return f"\n\n{token}\n\n"

    def pseudocode_replacement(match: re.Match) -> str:
        token = formal_token(len(blocks))
        blocks[token] = latex_fence("### Algorithm or Procedure", match.group(0))
        return f"\n\n{token}\n\n"

    text = PLAIN_FORMAL_BLOCK.sub(replacement, text)
    text = CUSTOM_DERIVATION_BLOCK.sub(replacement, text)
    text = CUSTOM_DISPLAY_COMMAND_BLOCK.sub(replacement, text)
    text = CUSTOM_PAIRED_BLOCK.sub(replacement, text)
    text = LEGACY_DISPLAY_BLOCK.sub(replacement, text)
    text = BRACKET_DISPLAY_BLOCK.sub(replacement, text)
    text = PSEUDOCODE_BLOCK.sub(pseudocode_replacement, text)
    return protect_fragile_dollar_displays(text, blocks)


def decode_encoded_code(value: str) -> str:
    replacements = {
        "LINEBREAKCHAR": "\n",
        "BACKSLASHCHAR": "\\",
        "PERCENTCHAR": "%",
        "LEFTBRACECHAR": "{",
        "RIGHTBRACECHAR": "}",
    }
    for encoded, literal in replacements.items():
        value = value.replace(encoded, literal)
    return value.strip()


def protect_encoded_code_blocks(text: str, blocks: dict[str, str]) -> str:
    def replacement(match: re.Match) -> str:
        token = formal_token(len(blocks))
        decoded = decode_encoded_code(match.group(1))
        blocks[token] = f"\n\n### Source Example\n\n```text\n{decoded}\n```\n\n"
        return f"\n\n{token}\n\n"

    return ENCODED_CODE_BLOCK.sub(replacement, text)


def protect_fragile_dollar_displays(text: str, blocks: dict[str, str]) -> str:
    spans = [
        match.span()
        for match in FRAGILE_DOLLAR_DISPLAY.finditer(text)
        if FRAGILE_DISPLAY_MACRO.search(match.group(0))
    ]
    for start, end in reversed(spans):
        token = formal_token(len(blocks))
        blocks[token] = latex_fence("", text[start:end])
        text = text[:start] + f"\n\n{token}\n\n" + text[end:]
    return text


def protect_custom_bracket_blocks(text: str, blocks: dict[str, str]) -> str:
    stack: list[tuple[str, int]] = []
    spans = []
    for match in CUSTOM_BRACKET_TOKEN.finditer(text):
        name, marker = match.groups()
        if marker == "[":
            stack.append((name, match.start()))
            continue
        index = next((i for i in range(len(stack) - 1, -1, -1) if stack[i][0] == name), None)
        if index is not None:
            _, start = stack[index]
            del stack[index:]
            spans.append((start, match.end(), "formal"))
    for start, end, _ in reversed(outermost_spans(spans)):
        token = formal_token(len(blocks))
        blocks[token] = latex_fence("### Formal Definition", text[start:end])
        text = text[:start] + f"\n\n{token}\n\n" + text[end:]
    return text


def normalize_references(text: str) -> str:
    return text


def convert_prose(source: str) -> tuple[str, str, list[str]]:
    return source_preserving_prose(source), "source_preserving", []


def source_preserving_prose(source: str) -> str:
    text = legacy.normalize_raw_section_commands(source)
    text = legacy.normalize_manual_numbered_headings(text)
    text = legacy.normalize_report_style_headings(text)
    text = legacy.RE_RAW_BEGIN_LIST_ENV.sub("\n", text)
    text = legacy.RE_RAW_END_LIST_ENV.sub("\n", text)
    text = re.sub(
        r"\\begin\{(?:mylist|list)\}(?:\s*\{[^{}]*\}){0,2}", "\n", text, flags=re.IGNORECASE
    )
    text = re.sub(r"\\end\{(?:mylist|list)\}", "\n", text, flags=re.IGNORECASE)
    text = legacy.RE_ITEM_COMMAND.sub("\n- ", text)
    text = legacy.unwrap_preconversion_text_formatting(text)
    text = normalize_direct_text_styles(text)
    text = strip_direct_layout_commands(text)
    text = normalize_inline_math_spans(text)
    return join_direct_prose_lines(text)


def normalize_inline_math_spans(text: str) -> str:
    def replacement(match: re.Match) -> str:
        value = match.group(0)
        return value if value.startswith("$$") else clean_inline_math_presentation(value)

    return legacy.RE_MATH_SPAN.sub(replacement, text)


def normalize_direct_text_styles(text: str) -> str:
    size = r"(?:\\(?:small|footnotesize|scriptsize|tiny|normalsize|large|Large)\s*)*"
    styles = (
        (rf"\{{{size}\\(?:em|it|sl)\s+([^{{}}]*)\}}", r"*\1*"),
        (rf"\{{{size}\\(?:bf)\s+([^{{}}]*)\}}", r"**\1**"),
        (rf"\{{{size}\\(?:tt)\s+([^{{}}]*)\}}", r"`\1`"),
    )
    previous = None
    while text != previous:
        previous = text
        for pattern, replacement in styles:
            text = re.sub(pattern, replacement, text)
    return text


def strip_direct_layout_commands(text: str) -> str:
    text = re.sub(r"\\(?:begin|end)\{titlepage\}", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"\\(?:hbadness|vbadness|hfuzz|vfuzz)\s*=\s*[-+]?\d+(?:\.\d+)?(?:pt)?", " ", text)
    text = legacy.unwrap_centerline_commands(text)
    text = re.sub(r"\\begin\{(?:center|flushleft|flushright|quote|quotation)\}", "\n", text)
    text = re.sub(r"\\end\{(?:center|flushleft|flushright|quote|quotation)\}", "\n", text)
    text = re.sub(r"\\begin\{multicols\*?\}\s*\{[^{}]*\}", "\n", text)
    text = re.sub(r"\\end\{multicols\*?\}", "\n", text)
    text = re.sub(r"\\begin\{minipage\}(?:\[[^\]]*\])?\s*\{[^{}]*\}", "\n", text)
    text = re.sub(r"\\end\{minipage\}", "\n", text)
    text = re.sub(r"\\(?:par|smallskip|medskip|bigskip)\b", "\n\n", text)
    text = re.sub(r"\\newline\b", " ", text)
    text = re.sub(
        r"\\(?:newpage|clearpage|pagebreak|eject|vfill|vfil|noindent|indent|centering|raggedright|raggedleft)\b",
        " ",
        text,
    )
    text = re.sub(r"\\(?:vspace|hspace|kern|mkern)\*?\s*\{[^{}]*\}", " ", text)
    text = re.sub(r"\\(?:vskip|hskip)\s*[-+]?\s*[\d.]+(?:true)?(?:pt|mm|cm|em|ex)\b", " ", text)
    text = re.sub(
        r"\\(?:base)?lineskip\s*=\s*(?:[\d.]+\s*(?:true)?(?:pt|mm|cm|em|ex)|[\d.]*\\baselineskip)",
        " ",
        text,
    )
    text = re.sub(r"\\enlargethispage\s*\{[^{}]*\}|\\document\b", " ", text)
    text = re.sub(
        r"\\rule(?:\s*\[[^\]]*\])?\s*\{[^{}]*\}\s*\{[^{}]*\}|\\hrulefill\b|\\hrule\b", " ", text
    )
    text = re.sub(r"\\\\(?:\s*\[[^\]\n]*\])?", "\n", text)
    text = re.sub(r"\\(?:setcounter|addtocounter|setlength)\s*\{[^{}]*\}\s*\{[^{}]*\}", " ", text)
    text = re.sub(r"\\pagenumbering\s*\{[^{}]*\}", " ", text)
    text = re.sub(
        r"\\(?:figrule|border|cbstart|cbend|qtreecenterfalse|qtreecentertrue|strich|unskip|kill|qed)\b",
        " ",
        text,
    )
    text = re.sub(r"\\end\{quote\}", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\\LABEL\s*\{[^{}]*\}\s*\{[^{}]*\}", " ", text)
    text = re.sub(r"\\rnc\s*\{[^{}]*\}\s*\{[^{}]*\}", " ", text)
    text = re.sub(r"\\if\s*([A-Za-z])\s*\{\1\}", " ", text)
    text = re.sub(r"\\fi\b", " ", text)
    text = re.sub(
        r"\\(?:small|footnotesize|scriptsize|tiny|normalsize|large|Large|LARGE|huge|Huge)\b",
        " ",
        text,
    )
    text = re.sub(
        r"\\(?:protect|leavevmode|relax|sloppy|fussy|draft|findemo|widetext|hfill|break)\b",
        " ",
        text,
    )
    text = re.sub(
        r"(?m)^\s*\\(?:maketitle|tableofcontents|listoffigures|listoftables)\s*$", "", text
    )
    text = re.sub(r"(?m)^\s*\{\s*\}\s*$", "", text)
    return re.sub(r"[ \t]+", " ", text)


def join_direct_prose_lines(text: str) -> str:
    output, paragraph = [], []

    def flush() -> None:
        if paragraph:
            output.append(" ".join(paragraph).strip())
            paragraph.clear()

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            flush()
            continue
        if re.match(r"^(?:#{1,6}\s|[-*+]\s|\d+[.)]\s|```|⟬\d{6}⟭$)", line):
            flush()
            indent = raw_line[: len(raw_line) - len(raw_line.lstrip())]
            output.append(indent + line)
            continue
        paragraph.append(line)
    flush()
    return "\n\n".join(part for part in output if part).strip()


def strip_heading_label(title: str) -> str:
    return re.sub(r"\s+(?:h|sec|chap|part):[A-Za-z0-9:._-]+\s*$", "", title).strip()


def demote_false_headings(markdown: str, source: str) -> str:
    titles = {
        legacy.normalized_title_text(strip_heading_label(title))
        for title in legacy.source_section_titles(source)
    }
    output = []
    for line in markdown.splitlines():
        match = re.match(r"^(#{1,6})\s+(.+)$", line)
        if not match:
            output.append(line)
            continue
        title = strip_heading_label(match.group(2))
        normalized = legacy.normalized_title_text(title)
        if normalized in titles and not re.fullmatch(r"\d{6,10}", normalized):
            output.append(f"{match.group(1)} {title}")
        else:
            output.append(f"**{title.strip()}**")
    text = "\n".join(output)
    return re.sub(r"(?m)^#{1,6}\s*(\d{6,10})\s*$", r"ArXiv reference: \1", text)


def source_title_text(source: str) -> str:
    source = strip_comments_outside_literals(source)
    title = explicit_source_title(source) or amstex_source_title(source)
    if not title:
        title = prominent_front_matter_title(source)
    return clean_source_title(title)


def explicit_source_title(source: str) -> str:
    boundary = source_title_boundary(source)
    candidates = []
    for command in SOURCE_TITLE_COMMANDS:
        for start, value in braced_command_values(source, command):
            if (
                start > boundary
                or source_title_definition(source, start)
                or not source_title_candidate_active(source, start)
            ):
                continue
            value = expand_title_footnote_marks(value, source)
            expanded = expand_retrieval_macros(value, source[:start])
            cleaned = clean_source_title(expanded)
            if plausible_source_title(cleaned):
                candidates.append((source_title_command_rank(command), start, cleaned))
    return min(candidates, default=(0, 0, ""), key=lambda item: (-item[0], item[1]))[2]


def braced_command_values(source: str, command: str) -> list[tuple[int, str]]:
    pattern = re.compile(rf"\\{re.escape(command)}(?![A-Za-z@])")
    values = []
    for match in pattern.finditer(source):
        cursor = skip_source_space(source, match.end())
        if cursor < len(source) and source[cursor] == "[":
            cursor = matching_source_delimiter(source, cursor, "[", "]") + 1
            cursor = skip_source_space(source, cursor)
        if cursor >= len(source) or source[cursor] != "{":
            continue
        close = matching_source_delimiter(source, cursor, "{", "}")
        if close >= 0:
            values.append((match.start(), source[cursor + 1 : close]))
    return values


def matching_source_delimiter(text: str, start: int, opening: str, closing: str) -> int:
    if start < 0 or start >= len(text) or text[start] != opening:
        return -1
    depth = 1
    for index in range(start + 1, len(text)):
        if source_character_escaped(text, index):
            continue
        if text[index] == opening:
            depth += 1
        elif text[index] == closing:
            depth -= 1
            if depth == 0:
                return index
    return -1


def source_character_escaped(text: str, index: int) -> bool:
    backslashes = 0
    index -= 1
    while index >= 0 and text[index] == "\\":
        backslashes += 1
        index -= 1
    return backslashes % 2 == 1


def skip_source_space(source: str, cursor: int) -> int:
    while cursor >= 0 and cursor < len(source) and source[cursor].isspace():
        cursor += 1
    return cursor


def source_title_definition(source: str, start: int) -> bool:
    prefix = source[max(0, start - 40) : start]
    return bool(re.search(r"\\(?:re)?newcommand\s*\{?\s*$|\\(?:g?def|let)\s*$", prefix))


def source_title_candidate_active(source: str, start: int) -> bool:
    definitions = retrieval_macros(source[:start])
    latest = {name: (position, nargs, body) for position, _, name, nargs, body in definitions}
    for name, (position, nargs, body) in latest.items():
        if nargs != 1:
            continue
        pattern = re.compile(re.escape(name) + r"(?![A-Za-z])")
        for match in reversed(list(pattern.finditer(source, position, start))):
            parsed = read_macro_args(source, match.end(), 1)
            if not parsed or parsed[1] <= start or source_title_definition(source, match.start()):
                continue
            activity = source_title_wrapper_activity(body, source[: match.start()])
            if activity is False:
                return False
            break
    return True


def source_title_wrapper_activity(body: str, definitions: str) -> bool | None:
    compact = re.sub(r"\s+", "", body)
    if not compact:
        return False
    if compact in {"#1", "{#1}"}:
        return True
    match = re.fullmatch(
        r"\\ifthenelse\{\\equal\{(\\[A-Za-z]+)\}\{([^{}]+)\}\\?\}"
        r"\{([^{}]*)\}\{([^{}]*)\}",
        compact,
    )
    if not match:
        return None
    constants = {
        name: value.strip()
        for _, _, name, nargs, value in retrieval_macros(definitions)
        if nargs == 0 and re.fullmatch(r"\s*[^{}]+\s*", value)
    }
    if match.group(1) not in constants:
        return None
    branch = match.group(3) if constants[match.group(1)] == match.group(2) else match.group(4)
    return "#1" in branch


def source_title_command_rank(command: str) -> int:
    return {"title": 5, "articletitle": 4, "Name": 4, "mytitle": 3, "cbb": 2}[command]


def source_title_boundary(source: str) -> int:
    content_start = source_content_start(source)
    patterns = (
        r"\\begin\s*\{abstract\}",
        r"\\abstracts?\b",
        r"\\section\*?\s*\{",
        r"\\chapter\*?\s*\{",
        r"\\head(?:ing)?\b",
    )
    content = source[content_start:]
    positions = [
        content_start + match.start()
        for pattern in patterns
        if (match := re.search(pattern, content, re.IGNORECASE))
    ]
    return min(positions, default=min(len(source), 100_000))


def source_content_start(source: str) -> int:
    match = re.search(r"\\begin\s*\{document\}|^[ \t]*\\document\b", source, re.MULTILINE)
    return match.end() if match else 0


def amstex_source_title(source: str) -> str:
    match = re.search(r"\\title\b(.*?)\\endtitle\b", source, re.DOTALL | re.IGNORECASE)
    return match.group(1) if match and match.start() <= source_title_boundary(source) else ""


def clean_source_title(title: str) -> str:
    if not title:
        return ""
    title = strip_publication_notice_from_title(title)
    title = title.replace("%", " ")
    title = normalize_title_small_caps(title)
    title = re.split(r"\\(?:author|date)(?![A-Za-z@])", title, maxsplit=1)[0]
    title = re.sub(r"\\tex\s*\{\\\\\}", " ", title)
    title = re.sub(r"\$\s*~\s*\$", " ", title)
    title = legacy.drop_balanced_argument_commands(
        title, re.compile(r"\\(?:footnote|thanks|titlenote)\s*\{")
    )
    title = drop_small_title_notes(title)
    title = re.sub(r"\\\\\s*\[[^\]\n]*\]", " ", title)
    title = re.sub(r"\\(?:footnotemark|footnotesize)(?:\s*\[[^\]\n]*\])?", " ", title)
    title = re.sub(r"\\space\b", " ", title)
    title = title.replace(r"\-", "").replace("~", " ")
    title = re.sub(r"\\(?=\s)", "", title)
    title = re.sub(r"\\hspace\*?\s*\{\s*-[^{}]*\}", "", title)
    title = legacy.drop_balanced_argument_commands(
        title, re.compile(r"\\(?:vspace|hspace|raisebox)\*?\s*\{")
    )
    title = unwrap_text_styles(title)
    title = re.sub(r"\\rightline\s*(?:\{[^{}]*\}|[^\\\n]*)", "", title)
    title = re.sub(r"\\(?:vspace|vskip|hspace|hskip)\*?\s*(?:\{[^{}]*\}|[-.\d]+\w*)", " ", title)
    title = re.sub(r"\\hrule(?:\s+height\s*[-.\d]+\w*)?", " ", title)
    title = re.sub(r"\\(?:begin|end)\s*\{[^{}]*\}", " ", title)
    title = re.sub(
        r"\\(?:centerline|normalsize|small|large|Large|LARGE|huge|Huge|"
        r"sixteenbf|eighteenbf|titlefont|bfseries)\b",
        "",
        title,
    )
    title = re.sub(r"\\(?:rm|bf|it|sc|tt|sl|em)\b", "", title)
    title = title.replace(r"\\", " ").replace("{", "").replace("}", "")
    return decode_title_latex(legacy.clean_metadata_text(title))


def normalize_title_small_caps(title: str) -> str:
    patterns = (r"\{\s*\\sc\s+([^{}]+)\}", r"\\textsc\s*\{([^{}]+)\}")
    for pattern in patterns:
        title = re.sub(pattern, lambda match: match.group(1).upper(), title)
    return title


def decode_title_latex(title: str) -> str:
    protected = {}

    def protect(match: re.Match) -> str:
        token = f"TEXMDTITLEMATH{len(protected):04d}TOKEN"
        protected[token] = match.group(0)
        return token

    masked = legacy.RE_MATH_SPAN.sub(protect, title)
    try:
        decoded = legacy.LatexNodes2Text().latex_to_text(masked)
    except Exception:
        decoded = masked
    for token, value in protected.items():
        decoded = decoded.replace(token, value)
    decoded = re.sub(r"\bTeX\s+macs\b", "TeXmacs", decoded)
    return " ".join(decoded.split())


def strip_publication_notice_from_title(title: str) -> str:
    separator = re.search(r"\\mbox\s*\{\s*\}\s*\\\\", title)
    if not separator:
        return title
    prefix = title[: separator.start()]
    if re.search(r"\b(?:appeared|to appear|proceedings)\b", prefix, re.IGNORECASE):
        return title[separator.end() :]
    return title


def drop_small_title_notes(title: str) -> str:
    patterns = (
        re.compile(r"\{\s*\\small\s+Note\b", re.IGNORECASE),
        re.compile(r"\{\s*\\footnotesize\b", re.IGNORECASE),
    )
    for pattern in patterns:
        for match in reversed(list(pattern.finditer(title))):
            close = matching_source_delimiter(title, match.start(), "{", "}")
            if close >= 0:
                title = title[: match.start()] + title[close + 1 :]
    return title


def expand_title_footnote_marks(title: str, source: str) -> str:
    pattern = re.compile(r"\\footnotemark\s*\[([^\]]+)\]")

    def replacement(match: re.Match) -> str:
        body = numbered_footnote_text(source, match.group(1))
        cleaned = clean_source_title(body).rstrip(". ") if body else ""
        return f" [{cleaned}]" if 0 < len(cleaned.split()) <= 8 else ""

    return pattern.sub(replacement, title)


def numbered_footnote_text(source: str, number: str) -> str:
    pattern = re.compile(rf"\\footnotetext\s*\[\s*{re.escape(number)}\s*\]\s*\{{")
    match = pattern.search(source)
    if not match:
        return ""
    opening = match.end() - 1
    close = matching_source_delimiter(source, opening, "{", "}")
    return source[opening + 1 : close] if close >= 0 else ""


def plausible_source_title(title: str) -> bool:
    words = re.findall(r"[A-Za-zÀ-ÿ]{2,}", title)
    rejected = re.compile(r"^(?:abstract|references|bibliography|contents)$", re.IGNORECASE)
    return 1 <= len(words) <= 40 and len(title) <= 500 and not rejected.fullmatch(title.strip())


def prominent_front_matter_title(source: str) -> str:
    start, boundary = source_content_start(source), source_title_boundary(source)
    scan_end = max(boundary, min(len(source), start + 50_000))
    candidates = prominent_title_candidates(source, start, scan_end, boundary)
    if not candidates:
        return ""
    best = max(candidates, key=lambda item: (item[2], -item[0]))
    joined = join_adjacent_title_candidates(source, best, candidates)
    return joined


def prominent_title_candidates(
    source: str, start: int, end: int, boundary: int
) -> list[tuple[int, int, int, str]]:
    patterns = (
        re.compile(r"\\(?:textbf|bfseries)\s*\{"),
        re.compile(r"\{\s*(?:\\(?:LARGE|Large|large|huge|Huge|sixteenbf|eighteenbf|bf|sc)\b\s*)+"),
    )
    candidates = []
    for pattern in patterns:
        for match in pattern.finditer(source, start, end):
            if match.start() > boundary and not inside_title_container(source, match.start()):
                continue
            opening = source.find("{", match.start(), match.end())
            close = matching_source_delimiter(source, opening, "{", "}")
            if close < 0 or close > end:
                continue
            raw = source[opening + 1 : close]
            title = clean_source_title(raw)
            score = prominent_title_score(source, match.start(), close, raw, title)
            if score >= 3 and plausible_source_title(title):
                candidates.append((match.start(), close + 1, score, title))
    return deduplicate_title_candidates(candidates)


def prominent_title_score(source: str, start: int, end: int, raw: str, title: str) -> int:
    context = source[max(0, start - 40) : min(len(source), end + 20)]
    score = 0
    score += 5 if re.search(r"\\(?:LARGE|huge|Huge|eighteenbf)\b", context) else 0
    score += 3 if re.search(r"\\(?:Large|large|sixteenbf)\b", context) else 0
    score += 1 if re.search(r"\\(?:textbf|bf|bfseries)\b", context) else 0
    score += 3 if inside_title_container(source, start) else 0
    score += 1 if title.isupper() and len(title.split()) >= 4 else 0
    if re.search(
        r"\b(?:department|university|institute|email|e-mail|special report)\b", title, re.IGNORECASE
    ):
        score -= 6
    if len(re.findall(r"[A-Za-z]{2,}", title)) < 3:
        score -= 3
    return score


def inside_title_container(source: str, position: int) -> bool:
    prefix = source[:position]
    begin = max(prefix.rfind(r"\begin{center}"), prefix.rfind(r"\begin{titlepage}"))
    end = max(prefix.rfind(r"\end{center}"), prefix.rfind(r"\end{titlepage}"))
    return begin > end


def deduplicate_title_candidates(
    candidates: list[tuple[int, int, int, str]],
) -> list[tuple[int, int, int, str]]:
    best = {}
    for candidate in candidates:
        key = legacy.normalized_title_text(candidate[3])
        if key not in best or candidate[2] > best[key][2]:
            best[key] = candidate
    return list(best.values())


def join_adjacent_title_candidates(
    source: str,
    best: tuple[int, int, int, str],
    candidates: list[tuple[int, int, int, str]],
) -> str:
    selected = [best]
    for candidate in sorted(candidates):
        if candidate[0] <= best[0] or candidate[0] - selected[-1][1] > 400:
            continue
        gap = source[selected[-1][1] : candidate[0]]
        subtitle = selected[-1][3].rstrip().endswith(":") and candidate[2] >= 3
        if (candidate[2] < best[2] - 1 and not subtitle) or title_gap_has_person_metadata(gap):
            continue
        selected.append(candidate)
    return " ".join(candidate[3] for candidate in selected)


def title_gap_has_person_metadata(gap: str) -> bool:
    return bool(
        re.search(
            r"\\author\b|\b(?:by|department|university|institute|email)\b", gap, re.IGNORECASE
        )
    )


def source_metadata_header(source: str) -> str:
    title = cleanup_case.clean_title(source_title_text(source)) or "Untitled"
    parts = [f"# {title}", ""]
    abstract = source_abstract_markdown(source)
    if abstract:
        parts.extend(["## Abstract", abstract, ""])
    return "\n".join(parts)


def source_abstract_markdown(source: str) -> str:
    source = strip_comments_outside_literals(source)
    parts = source_abstract_parts(source)
    if not parts:
        return ""
    start, _, abstract = parts
    preamble = source[:start]
    abstract = expand_abstract_macro(abstract, preamble)
    abstract = expand_retrieval_macros(abstract, preamble)
    abstract = normalize_semantic_aliases(abstract)
    abstract = drop_unresolved_comment_commands(abstract)
    abstract = strip_comments_outside_literals(abstract)
    abstract = re.sub(r"\\maketitle(?![A-Za-z])", "", abstract)
    abstract = remove_environment_spans(abstract, {"picture", "pspicture"})
    abstract = legacy.RE_LABEL_COMMAND.sub("", abstract)
    abstract = unwrap_text_styles(abstract)
    abstract = re.sub(r"\\(?:it|bf|rm|small|normalsize)\b", "", abstract)
    blocks: dict[str, str] = {}
    abstract = protect_today_commands(abstract, blocks)
    abstract = protect_citation_commands(abstract, blocks)
    abstract = protect_reference_commands(abstract, blocks)
    abstract = protect_inline_math(abstract, blocks)
    abstract = protect_remaining_macro_uses(abstract, source, blocks)
    abstract = protect_semantic_commands(abstract, blocks)
    rendered = legacy.convert_fallback_preserving_math(abstract, legacy.convert_pylatexenc)
    return legacy.RE_LABEL_COMMAND.sub("", restore_blocks(rendered or abstract, blocks)).strip()


def expand_abstract_macro(abstract: str, definitions: str) -> str:
    call = re.fullmatch(r"\s*(\\[A-Za-z]+)\s*", abstract)
    if not call:
        return abstract
    matches = [
        macro
        for macro in retrieval_macros(definitions)
        if macro[2] == call.group(1) and macro[3] == 0
    ]
    return matches[-1][4] if matches and len(matches[-1][4]) <= 10000 else abstract


def repair_split_decimal_emphasis(markdown: str) -> str:
    pattern = re.compile(r"\*\*([^*]{0,500}?)(\d)\*\*\s*\n+\s*(\d+)([.,])")
    markdown = pattern.sub(
        lambda match: f"{match.group(1)}{match.group(2)}.{match.group(3)}{match.group(4)}", markdown
    )
    split_value = re.compile(r"\*\*((?:\d+\.)+\d+\.\s+[^*\n]{3,300}?)\*\*\s*\n+\s*(\d{3})(?=[,;])")
    return split_value.sub(r"\1 .\2", markdown)


def repair_split_numbered_prose(markdown: str) -> str:
    markdown = re.sub(
        r"\b(Theorem|Lemma|Proposition|Corollary)\s*\n+\s*\*\*(\d+(?:\.\d+)+\.[^*]*)\*\*",
        r"\1 \2",
        markdown,
    )
    markdown = re.sub(
        r"\b(equation\s*\(\d+)\*\*\s*\n+\s*(\d+\):)", r"\1.\2", markdown, flags=re.IGNORECASE
    )
    return re.sub(r"(\b(?:equation|Theorem|Lemma)?\s*\(\d+)\n+\s*(\d+\))", r"\1.\2", markdown)


def clean_output_spacing(text: str) -> str:
    text = remove_residual_captions(text)
    text = strip_standalone_layout_braces(text)
    text = re.sub(
        r"\\hfill\s*\\rule(?:\s*\[[^\]]*\])?\s*\{[^{}]*\}\s*\{[^{}]*\}\s*\\vspace\s*\{[^{}]*\}",
        "",
        text,
    )
    text = re.sub(r"\\centerline\*([^*\n]+)\*", r"\1", text)
    text = re.sub(r"`?<!--\s*-->`?(?:\{=html\})?", "", text)
    text = re.sub(r"\b([A-Z]{2,})\s+-complete\b", r"\1-complete", text)
    text = re.sub(r":\s*\n\s*is given by:", " is given by:", text, flags=re.IGNORECASE)
    text = re.sub(r"^\s*(?:\{\s*)+\}?\s*$|^\s*\\textbf\s*\{\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"(?m)^\s*\\let\\[A-Za-z@]+.*$", "", text)
    text = re.sub(r"(?m)^\s*-?\s*sep\s+\S+\s*\{?bibdata\}?\s*$", "", text, flags=re.IGNORECASE)
    text = re.sub(r"(?mi)^\s*use if there are several authors[^\n]*$", "", text)
    text = re.sub(r"([A-Za-z][À-ÿ])\s+([a-z])(?=[a-z])", r"\1\2", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def remove_residual_captions(text: str) -> str:
    pattern = re.compile(r"\\caption\*?(?:\s*\[[^\]]*\])?\s*\{", re.IGNORECASE)
    for match in reversed(list(pattern.finditer(text))):
        close = legacy.find_matching_brace(text, match.end() - 1)
        if close >= 0:
            text = text[: match.start()] + text[close + 1 :]
    return text


def strip_standalone_layout_braces(text: str) -> str:
    output, fenced, displayed = [], False, False
    math_env = re.compile(r"\\(?:begin|end)\{(?:equation|align|gather|multline|displaymath)")
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            fenced = not fenced
        if not fenced:
            displayed ^= line.count("$$") % 2 == 1
            displayed |= bool(
                re.search(r"\\\[|\\begin\{(?:equation|align|gather|multline|displaymath)", line)
            )
        if not fenced and not displayed and re.fullmatch(r"\s*[{}\]]\s*", line):
            continue
        output.append(line)
        if not fenced and (r"\]" in line or (math_env.search(line) and r"\end{" in line)):
            displayed = False
    return "\n".join(output)


def normalize_final_structure(text: str) -> str:
    text = re.sub(r"\\LABEL\s*\{[^{}]*\}\s*\{[^{}]*\}", "", text)
    text = re.sub(r"\{\s*\\refstepcounter\s*\{[^{}]*\}\s*", "", text)
    text = re.sub(r"\\refstepcounter\s*\{[^{}]*\}", "", text)
    text = re.sub(r"(?m)^-\s*\}\s*", "- ", text)
    text = re.sub(r"\\(?:section|subsection|subsubsection|paragraph)\*?\s*\{\s*\}", "\n", text)
    text = re.sub(
        r"\\begin\{(?:myitemize|mylist|list|slide\*?|examples)\}(?:\s*\{[^{}]*\}){0,2}",
        "\n",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"\\end\{(?:myitemize|mylist|list|slide\*?|examples)\}", "\n", text, flags=re.IGNORECASE
    )
    text = re.sub(r"\\(?:begin|end)\{tt\}", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"\\item\b", "\n- ", text)
    text = re.sub(r"(?m)^-\s*$\n?", "", text)
    text = re.sub(r"(?mi)^#{1,6}\s+Tables?\s*$\n?", "", text)
    text = re.sub(r"(?mi)^\s*(?:\\?(?:begin|end)\{)?table\*?(?:\})?\s*$\n?", "", text)
    text = re.sub(r"(?m)^([IVX]+[.)]?\s+[A-Z][^\n]{3,})$", r"# \1", text)
    text = re.sub(r"(?mi)^\s*(Acknowledg(?:e)?ments?|Preface)\s*$", r"## \1", text)
    text = re.sub(r"(?m)^(#{1,6}\s+[^\n]*?)\$\$\s*$", r"\1", text)
    text = re.sub(
        r"(?m)^(#{1,6}\s+[^\n]*[A-Za-z]+-[A-Za-z]*[À-ÿ])\s+([a-z])(?=\b)",
        r"\1\2",
        text,
    )
    text = re.sub(r"(?mi)^\s*\{?\s*APPENDIX\s*\}?\s*$", "# Appendix", text)
    text = re.sub(r"(?mi)^\*Proof\\?/?\s*:?\s*\*\s*$", "**Proof**", text)
    text = re.sub(r"(?m)^\*\*([A-Z][A-Z0-9 /&-]{0,24})\*\*$", r"## \1", text)
    text = re.sub(r"\\begin\{keywords?\}\s*", "Keywords: ", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*\\end\{keywords?\}", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\\(?:begin|end)\{article\}", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\\PARstart\s*\{([^{}])\}\s*\{([^{}]+)\}", r"\1\2", text)
    return legacy.normalize_raw_section_commands(text)


def strip_markdown_bibliography(text: str) -> str:
    heading = MARKDOWN_BIBLIOGRAPHY_HEADING.search(text)
    return text[: heading.start()] if heading else text


def strip_coordinate_artifacts(text: str) -> str:
    coordinate = re.compile(r"\(-?\d+,-?\d+\)")

    def keep_line(line: str) -> bool:
        matches = coordinate.findall(line)
        if len(matches) < 3:
            return True
        if re.search(r"\b(?:appears in|copyright|arxiv|cs\.[A-Z]{2}/\d)", line, re.IGNORECASE):
            return False
        remainder = coordinate.sub("", line)
        remainder = re.sub(r"[\s,;:{}\[\]()|\\-]", "", remainder)
        return bool(re.search(r"[A-Za-z]", remainder)) or len(remainder) > 20

    return "\n".join(line for line in text.splitlines() if keep_line(line))


def render_retrieval_document(source: str) -> tuple[str, str, list[str], str]:
    theorem_envs = theorem_environment_names(source)
    prepared = prepare_source(source)
    targets = BASE_FORMAL_ENVS | set(theorem_envs) | custom_formal_environment_names(source)
    blocks: dict[str, str] = {}
    protected = protect_encoded_code_blocks(prepared, blocks)
    protected = protect_citation_commands(protected, blocks)
    protected = protect_reference_commands(protected, blocks)
    protected = protect_today_commands(protected, blocks)
    protected = protect_plain_numeric_references(protected, blocks)
    protected = protect_custom_bracket_blocks(protected, blocks)
    figure_targets = {env for env in targets if env.startswith("figure")}
    figure_spans = environment_spans(protected, figure_targets)
    protected, blocks = replace_spans(protected, figure_spans, theorem_envs, blocks)
    protected = protect_plain_formal_blocks(protected, blocks)
    math_spans = environment_spans(protected, MATH_ENVS)
    protected, blocks = replace_spans(protected, math_spans, theorem_envs, blocks)
    table_targets = {
        env for env in targets if env.startswith(("table", "tabular")) or env == "longtable"
    }
    table_spans = environment_spans(protected, table_targets)
    protected, blocks = replace_spans(protected, table_spans, theorem_envs, blocks)
    formal_targets = targets - MATH_ENVS - figure_targets - table_targets
    spans = environment_spans(protected, formal_targets)
    protected, blocks = replace_spans(protected, spans, theorem_envs, blocks)
    protected = protect_footnotes(protected, blocks)
    protected = protect_ensuremath(protected, blocks)
    protected = protect_inline_verbatim(protected, blocks)
    protected = protect_inline_math(protected, blocks)
    protected = normalize_references(protected)
    markdown, method, warnings = convert_prose(protected)
    markdown = demote_false_headings(markdown, protected)
    markdown = restore_blocks(markdown, blocks)
    markdown = repair_split_decimal_emphasis(markdown)
    markdown = repair_split_numbered_prose(markdown)
    if FORMAL_TOKEN_RE.search(markdown):
        warnings.append("unresolved_formal_placeholder_raw_fallback")
        markdown = restore_blocks(source_preserving_prose(protected), blocks)
        method = "source_preserving"
    markdown = legacy.RE_LABEL_COMMAND.sub("", markdown)
    markdown = normalize_final_structure(markdown)
    markdown = strip_markdown_bibliography(markdown)
    combined = source_metadata_header(source) + markdown
    combined = strip_coordinate_artifacts(combined)
    combined = re.sub(r"(?mi)^\s*Introduction\s*$", "# Introduction", combined)
    combined = re.sub(r"(?m)^\s*(\d{1,2}\s+[A-Z][A-Za-z' -]{10,})\s*$", r"## \1", combined)
    document = clean_output_spacing(combined) + "\n"
    return document, method, warnings, prepared


def protect_today_commands(text: str, blocks: dict[str, str]) -> str:
    """Keep ``\\today`` source-native and deterministic."""
    pattern = re.compile(r"\\today(?![A-Za-z])")
    for match in reversed(list(pattern.finditer(text))):
        token = formal_token(len(blocks))
        blocks[token] = match.group(0)
        text = text[: match.start()] + token + text[match.end() :]
    return text
