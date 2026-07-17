"""Internal helpers extracted from ClaimSpy retrieval v136."""


import contextlib
import contextvars
import html
import io
import os
import re
import subprocess
import unicodedata
from pathlib import Path

import pypandoc
from pylatexenc.latex2text import LatexNodes2Text

PS_SIGNATURES = [
    "%!PS", "%%BoundingBox", "/Times-Roman", "/Helvetica", "%%Page:",
    "%%EOF", "/F0 ", " SF(", " SF (", "/TeXDict", "/FontType",
    "/BitMaps", "/BuildChar", "/FontMatrix", "/@startdoc",
]

HTML_SIGNATURES = ["<!DOCTYPE", "<html", "<HTML", "<body", "<BODY"]

BINARY_SIGNATURES = [" TeX output ", "ustar"]

SUPPORT_FILE_SUFFIXES = (".sty", ".cls", ".bst", ".bib", ".bbl", ".clo")

PANDOC_TIMEOUT_SECONDS = int(os.environ.get("PANDOC_TIMEOUT_SECONDS", "30"))

RE_NEWCOMMAND = re.compile(
    r"\\(?:re)?newcommand\s*\{?(\\[a-zA-Z]+)\}?"
    r"(?:\[(\d+)\])?(?:\[[^\]]*\])?\s*\{",
    re.DOTALL,
)

RE_DEF = re.compile(r"\\(?:gdef|edef|xdef|def)\s*(\\[a-zA-Z]+)\s*((?:#\d){0,3})\s*\{", re.DOTALL)

RE_DEFINE = re.compile(r"\\(?:re)?define\s*(\\[a-zA-Z]+)\s*((?:#\d){0,3})\s*\{", re.DOTALL)

RE_COMMENT_LINE = re.compile(r"(?<!\\)%.*$", re.MULTILINE)

RE_FILE_HEADER = re.compile(r"^={16,}\nFILE:\s*(.*?)\n={16,}\n", re.MULTILINE)

RE_IFFALSE_BLOCK = re.compile(r"\\iffalse\b.*?\\fi\b", re.DOTALL)

RE_NEWTHEOREM_COMMAND = re.compile(r"\\newtheorem\s*\{", re.DOTALL)

RE_INPUT_BRACED_NAME = re.compile(r"\\(?:input|include)\s*\{([^}]+)\}")

RE_INPUT_BARE_NAME = re.compile(r"\\input\s+([^\s{}]+)")

RE_USEPACKAGE_COMMAND = re.compile(r"\\usepackage(?:\[[^\]\n]*\])?\s*\{([^{}]+)\}")

RE_DOCUMENTSTYLE_COMMAND = re.compile(r"\\documentstyle(?:\[([^\]\n]*)\])?\s*\{([^{}]+)\}")

RE_BIBLIOGRAPHY_COMMAND = re.compile(r"\\bibliography\s*\{([^{}]+)\}")

RE_GRAPHICS_COMMAND = re.compile(
    r"\\(?:includegraphics|epsfig|psfig)\*?"
    r"(?:\[[^\]]{0,300}\])?\s*\{([^{}]{0,1000})\}",
    re.IGNORECASE,
)

RE_GRAPHICS_INPUT = re.compile(
    r"\\input\s*\{?([A-Za-z0-9_./:-]+\.(?:pstex_t|pstex|ps|eps|fig|pic|idraw))\}?",
    re.IGNORECASE,
)

RE_EPSFBOX_COMMAND = re.compile(
    r"\\(?:epsfbox|epsffile)\s*\{([^{}]{0,1000})\}",
    re.IGNORECASE,
)

RE_EPSFBOX_BARE_COMMAND = re.compile(
    r"\\(?:epsfbox|epsffile)\s*([A-Za-z0-9_./:-]+\.(?:eps|ps|pdf|png|jpg|jpeg))",
    re.IGNORECASE,
)

RE_EPSF_SIZE_COMMAND = re.compile(r"\\epsf[xy]size\s*=?\s*[-.\w]+", re.IGNORECASE)

RE_HBOX_FIGURE_WRAPPER = re.compile(r"\\hbox\{\s*(\[Figure omitted:[^\]\n]+\])\s*\}", re.IGNORECASE)

RE_PST_ENV = re.compile(r"\\begin\{pspicture\}.*?\\end\{pspicture\}", re.DOTALL | re.IGNORECASE)

RE_LGRINDFILE_COMMAND = re.compile(r"\\lgrindfile\s*\{([^{}]+)\}")

RE_VERBATIM_ENV = re.compile(r"\\begin\{(verbatim|Verbatim|lstlisting|alltt)\}(.*?)\\end\{\1\}", re.DOTALL)

RE_VERB_COMMAND = re.compile(r"\\verb\*?(.)(.*?)\1", re.DOTALL)

RE_FIGURE_ENV = re.compile(r"\\begin\{figure\*?\}(?:\[[^\]\n]*\])?(.*?)\\end\{figure\*?\}", re.DOTALL)

RE_CAPTION_COMMAND = re.compile(r"\\caption(?:\[[^\]\n]*\])?\s*\{", re.DOTALL)

RE_LABEL_COMMAND = re.compile(r"\\label\s*\{([^{}]*)\}")

RE_PLAIN_PICTURE_ENV = re.compile(r"\\beginpicture\b.*?\\endpicture\b", re.DOTALL)

RE_PICTURE_TEXT_COMMAND = re.compile(
    r"\\(?:makebox|framebox|dashbox)\s*(?:\([^)]{0,120}\))?(?:\[[^\]\n]{0,120}\])?\s*\{",
    re.DOTALL,
)

RE_FORMATTING_ARGUMENT_COMMAND = re.compile(
    r"\\(?:ensuremath|mathit|mathrm|mathbf|mathsf|mathtt|text|textrm|textmd|mbox|operatorname)\*?\s*\{",
    re.DOTALL,
)

RE_ESCAPED_ENSUREMATH_COMMAND = re.compile(r"\\ensuremath\s*\{(.*?)\\\}", re.DOTALL)

RE_TEXT_FORMATTING_ARGUMENT_COMMAND = re.compile(
    r"\\(?:textsc|textit|textbf|emph|text|textrm|textmd|mbox|ensuremath)\*?\s*\{",
    re.DOTALL,
)

RE_XSPACE_COMMAND = re.compile(r"\\xspace\b")

RE_CUSTOM_SECTION_COMMAND = re.compile(
    r"\\(newsec|newsection|Section|SubSection|sect|subsect)\*?\s*\{",
    re.DOTALL,
)

RE_MULTI_BLANK = re.compile(r"\n{3,}")

RE_REPEAT_RULE = re.compile(r"^\s*[=\-*]{12,}\s*$", re.MULTILINE)

RE_STANDALONE_EQUALS_LINE = re.compile(r"(?m)^\s*=\s*$")

RE_MATH_SPAN = re.compile(
    r"\$\$.*?\$\$|\$[^$]{1,5000}\$|\\\(.*?\\\)|\\\[.*?\\\]",
    re.DOTALL,
)

RE_FENCED_CODE_BLOCK = re.compile(r"```.*?```", re.DOTALL)

RE_FALLBACK_MATH_ENV_BLOCK = re.compile(
    r"\\begin\{(equation\*?|align\*?|aligned\*?|eqnarray\*?|array|matrix|pmatrix|bmatrix|vmatrix|"
    r"cases|gather\*?|split|multline\*?|displaymath|math|avm)\}"
    r".*?\\end\{\1\}",
    re.DOTALL,
)

RE_FALLBACK_TABLE_BLOCK = re.compile(
    r"\\begin\{(tabular\*?)\}"
    r"(?:\[[^\]\n]*\])?(?:\{[^{}\n]*\}){0,2}"
    r".{0,50000}?\\end\{\1\}",
    re.DOTALL | re.IGNORECASE,
)

RE_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")

RE_BEGIN_DOCUMENT = re.compile(r"\\(?:begin\{document\}|begindocument)", re.IGNORECASE)

RE_END_DOCUMENT = re.compile(r"\\(?:end\{document\}|enddocument)", re.IGNORECASE)

RE_END_TOPMATTER = re.compile(r"\\endtopmatter", re.IGNORECASE)

RE_BODY_METADATA_COMMANDS = re.compile(
    r"\\(?:title|author|address|date|thanks|subjclass|email)"
    r"(?:\[[^\]]*\])?\{.*?\}|\\(?:maketitle|ratitle)\b",
    re.DOTALL,
)

RE_TEXT_NOISE_LINE = re.compile(
    r"^\s*(?:empty|amsppt|amsart|article|plain|roman|arabic|headings|year\d+|no\d+|=\d+|"
    r"[-=]?(?:\d+(?:\.\d+)?|\.\d+)(?:pt|mm|cm|in)|figure\s*=.*\.(?:ps|eps)|"
    r"th\s+(?:\d+(?:\.\d+)?|\.\d+)in|indent\s+\d+(?:\.\d+)?em|sentence.*ctr.*|"
    r"skip\s+\d+pt|#\d.*#\d.*|\[[^\]]*\]article)\s*$",
    re.MULTILINE,
)

RE_PANDOC_DIV_LINE = re.compile(r"^\s*:{2,}(?:\s+\S.*)?$", re.MULTILINE)

RE_MARKDOWN_LINEBREAK = re.compile(r"\\\s*$", re.MULTILINE)

RE_METADATA_STYLE = re.compile(r"\{\\(?:it|em|bf|tt|rm|sc)\s+([^{}]+)\}")

RE_METADATA_COMMAND = re.compile(r"\\(?:LaTeX|TeX|ldots|dots)\b")

RE_TEX_DIMENSION_NOISE = re.compile(r"(?<!\w)-?\.\d+pt(?!\w)")

RE_TEX_GLUE_NOISE = re.compile(r"\b(?:plus|minus)?\s*-?\d+(?:\.\d+)?truept\b")

RE_TRUEPT_LAYOUT_FRAGMENT = re.compile(
    r"\bto\s+\.\d+(?:true)?in|height\d+(?:\.\d+)?pt\s+width\.?\d+(?:\.\d+)?pt\s+\d+pt"
)

RE_CONVERTED_COMMAND_FRAGMENT = re.compile(
    r"\b(?:gindocument|ginabstract|ginverbatim|gincenter|ginequation|"
    r"gendocument|endcenter|endabstract|endverbatim)\b"
)

RE_DOCUMENTSTYLE_FRAGMENT = re.compile(r"\bstyle(?:\[[^\]\n]*\])?\s*\w+\b")

RE_FIGURE_INCLUDE_FRAGMENT = re.compile(
    r"figure\s*=\s*[^\s,\n]+(?:\.(?:ps|eps|idraw|fig))?"
    r"(?:,[A-Za-z_-]+=(?:[0-9.]+[A-Za-z]*|[yn]|true|false))*\s*",
    re.IGNORECASE,
)

RE_GRAPHICS_PLACEHOLDER = re.compile(r"<\s*g\s*r\s*a\s*p\s*h\s*i\s*c\s*s\s*>", re.IGNORECASE)

RE_BIB_STYLE_SPACING = re.compile(r"\.\d+em\s+plus\s+\.\d+em\s+minus\s+-?\.\d+em")

RE_STYLE_TOKEN_LINE = re.compile(r"^\s*(?:acl|aaai|named|fullname|natexlab|subject:\s*file\s*\d+)\s*$", re.IGNORECASE)

RE_INTERNAL_CITE_FRAGMENT = re.compile(
    r"(?:commapen-?\d+|cite[^\s]{0,30})?##?\d(?:##?\d)*\s*\(?internalciteb?[A-Za-z0-9:._-]*\)?",
    re.IGNORECASE,
)

RE_GRAPHICS_OPTION_FRAGMENT = re.compile(
    r"\bfile\s*=\s*[^\s,\n]+\.(?:ps|eps|pdf|png|jpg|jpeg)"
    r"(?:\s*,\s*[A-Za-z_-]+\s*=\s*[-\w. ]+)*",
    re.IGNORECASE,
)

RE_PANDOC_EMPTY_SPAN = re.compile(r"\[\]\{#[^}\n]*\}")

RE_PANDOC_REF_LINK_ATTR = re.compile(
    r"\[(.*?)\]\(#[^)]+\)\{reference-type=\"([^\"]+)\"\s+reference=\"([^\"]+)\"\}",
    re.DOTALL,
)

RE_XML_REF_LINE = re.compile(r"(?m)^\s*<ref>\s*")

RE_GENERIC_REF_TAG = re.compile(r"<ref>\s*([A-Za-z0-9:._-]+)?")

RE_GENERIC_CIT_TAG = re.compile(r"<cit\.?>")

RE_LATEX_INTERNAL_CITE = re.compile(
    r"\\def\\@commapen\{[^{}]*\}\\def\\citename##1\{[^{}]*\}\\@internalcite\s*\{([^{}]+)\}"
)

RE_AT_INTERNAL_CITE = re.compile(
    r"(?:\\def\\@commapen\{[^{}]*\}\\def\\citename##1\{[^{}]*\})?\\@internalcite\s*\{([^{}]+)\}"
)

RE_INTERNAL_CITEB_COMMAND = re.compile(r"\\@internalciteb?\{([^{}]+)\}")

RE_CITE_CONTROL_SEQUENCE = re.compile(
    r"\\(?:CiteListComma|CiteListSemicolon|CiteDelimsParens|CiteDelimsEmpty|leavevmode)\b"
)

RE_CITENAME_DEF_FRAGMENT = re.compile(r"\\def\\citename##1\{.{0,120}?\}", re.DOTALL)

RE_HTML_PICTURE_BLOCK = re.compile(
    r"<figure\b[^>]*>\s*(?:<div[^>]*>\s*){0,3}.*?class=[\"']picture[\"'].*?</figure>",
    re.DOTALL | re.IGNORECASE,
)

RE_HTML_FIGURE_BLOCK = re.compile(r"<figure\b[^>]*>.*?</figure>", re.DOTALL | re.IGNORECASE)

RE_HTML_FIGCAPTION = re.compile(r"<figcaption\b[^>]*>(.*?)</figcaption>", re.DOTALL | re.IGNORECASE)

RE_HTML_TAG = re.compile(r"<[^>]+>")

RE_RAW_LATEX_ATTRIBUTE = re.compile(r"`?\s*\\?\s*\{=latex\}`?")

RE_TEX_ERROR_MESSAGE = re.compile(r"\\(?:let\\errmessage|errmessage)\{[^{}]*\}")

RE_BBB_ERROR_PREFIX = re.compile(r"\\Bbb@")

RE_MATH_ENV_WRAPPER = re.compile(
    r"\\(?:begin|end)\{(?:equation\*?|eqnarray\*?|align\*?|aligned\*?|split|gather\*?|multline\*?|tabular\*?)\}"
    r"(?:\[[^\]\n]*\])?"
)

RE_MATH_LABEL_COMMAND = re.compile(r"\\(?:label|nonumber|notag)(?:\{[^{}]*\})?")

RE_THEOREM_BEGIN = re.compile(
    r"\\begin\s*\{\s*(theorem|lemma|lem|corollary|cor|proposition|prop|definition|defin|tef|"
    r"proof|proofqed|remark|rem|example|exa|claim|cla|scholium|sch|axiom|axi|conjecture|con|theor|teo)\*?\s*\}"
    r"(?:\s*\[[^\]]{0,200}\])?(?:\s*\{[^{}\n]{0,200}\})?",
    re.IGNORECASE,
)

RE_THEOREM_END = re.compile(
    r"\\end\s*\{\s*(?:theorem|lemma|lem|corollary|cor|proposition|prop|definition|defin|tef|"
    r"proof|proofqed|remark|rem|example|exa|claim|cla|scholium|sch|axiom|axi|conjecture|con|theor|teo)\*?\s*\}",
    re.IGNORECASE,
)

RE_CITE_COMMAND = re.compile(r"\\cite\s*(?:\[[^\]\n]*\])?\s*(?:\{([^{}\n]*)\}|([A-Za-z0-9:._-]+))")

RE_CITE_FAMILY_COMMAND = re.compile(
    r"\\(?:cite|citep|citet|citealp|citeauthor|citeyear|nocite)\*?"
    r"(?:\[[^\]]{0,200}\]){0,2}\s*\{([^{}]{0,1200})\}",
    re.DOTALL,
)

RE_REF_FAMILY_COMMAND = re.compile(r"\\(?:ref|eqref|pageref|autoref)\*?\s*\{([^{}\n]*)\}")

RE_RAW_SECTION_COMMAND = re.compile(r"\\(part|chapter|section|subsection|subsubsection|paragraph)\*?\s*\{", re.DOTALL)

RE_RAW_BEGIN_LIST_ENV = re.compile(r"\\begin\{(?:itemize|enumerate|description|romannum)\*?\}", re.IGNORECASE)

RE_RAW_END_LIST_ENV = re.compile(r"\\end\{(?:itemize|enumerate|description|romannum)\*?\}", re.IGNORECASE)

RE_RAW_OLD_LIST_ENV = re.compile(r"\\(?:begin|end)(?:list|description|enumerate|itemize|romannum)\b(?:\s*\\[A-Za-z]+\b|\s*\{[^{}\n]*\})*", re.IGNORECASE)

RE_RAW_PANDOC_SPAN_LIST_ENV = re.compile(r"\\(?:begin|end)<span>list[^<]*</span>", re.IGNORECASE)

RE_RAW_BEGIN_EXAMPLE_ENV = re.compile(
    r"\\begin\{(?:ex|subex|example|examples|lexample)\*?\}(?:\[[^\]\n]*\])?",
    re.IGNORECASE,
)

RE_RAW_END_EXAMPLE_ENV = re.compile(r"\\end\{(?:ex|subex|example|examples|lexample)\*?\}", re.IGNORECASE)

RE_COUNTER_COMMAND = re.compile(r"\\(?:addtocounter|setcounter|stepcounter)\s*\{[^{}\n]*\}(?:\s*\{[^{}\n]*\})?")

RE_ITEM_ESCAPED_LABEL_COMMAND = re.compile(r"\\item\s*\\\[([^\\\]\n]{0,200})\\\]")

RE_ITEM_LABEL_COMMAND = re.compile(r"\\item\s*\[([^\]\n]{0,200})\]")

RE_ITEM_COMMAND = re.compile(r"\\item(?:\[[^\]\n]*\])?")

RE_MATHRM_WORD_COMMAND = re.compile(r"\\mathrm([A-Za-z]{2,})")

RE_TEX_SPACING_COMMAND = re.compile(r"\\rule(?:\[[^\]\n]*\])?\{[^{}\n]*\}\{[^{}\n]*\}")

RE_TEX_HORIZONTAL_SKIP = re.compile(r"\\hskip\s*[-.\d]+\\?unitlength")

RE_EMPTY_DISPLAY_MATH = re.compile(r"\$\$\s*\$\$")

RE_MARKDOWN_DISPLAY_BLOCK = re.compile(r"\$\$(.*?)\$\$", re.DOTALL)

RE_ORPHAN_WRAPPED_DISPLAY_MATH = re.compile(r"(?<!\$)\$\s*(\$\$.*?\$\$)\s*\$(?!\$)", re.DOTALL)

RE_SINGLE_COLUMN_ARRAY_DISPLAY = re.compile(
    r"\$\$\s*\\begin\{array\}\{c\}(.*?)\\end\{array\}\s*\$\$",
    re.DOTALL,
)

RE_QUANTUM_CIRCUIT_ARRAY_BLOCK = re.compile(
    r"\$\$\s*\\begin\{array\}\{[^{}\n]*\}(.*?)\\end\{array\}\.?\s*\$\$",
    re.DOTALL,
)

MATH_IDENTIFIER_TOKEN = (
    r"(?:[A-Zα-ωΑ-ΩℓℒℤℝℂΠψγτλ]"
    r"(?:_[A-Za-z0-9+\-α-ωΑ-Ω]+)?[̃~]?(?:,[a-z])?|[a-z]_[A-Za-z0-9+\-α-ωΑ-Ω]+(?:,[a-z])?)"
)

MATH_SHORT_VARIABLE_TOKEN = r"[a-rt-z]"

MATH_SHORT_VARIABLE_PREFIXES = ("any", "as", "each", "solution", "solutions", "vectors", "where", "Where")

MATH_TEXT_PREFIXES = (
    "a", "and", "any", "as", "associate", "by", "defined by", "each", "for",
    "from", "function", "functions", "in", "length", "let", "Let", "matrix",
    "matrices", "of", "operator", "operators", "solution", "solutions",
    "space", "spaces", "the", "The", "to", "vector", "vectors", "where",
    "Where", "with", "Since", "since",
)

MATH_TEXT_SUFFIXES = (
    "and", "are", "be", "by", "for", "from", "has", "have", "in",
    "if", "is", "of", "stand", "stands", "tend", "tends", "the", "to", "where", "with",
)

RE_TEX_DISPLAY_SPACING_COMMAND = re.compile(
    r"\\\[\s*[-+]?\d+(?:\.\d+)?\s*(?:ex|em|pt|cm|mm|in)\s*(?:\\\]|\])"
)

RE_TEX_DISPLAY_MATH_BLOCK = re.compile(r"\\\[(.*?)\\\]", re.DOTALL)

RE_TABLE_ALIGNMENT_ONLY_LINE = re.compile(r"^\s*[clrld]{3,}\s*$")

RE_PICTURE_COORD = re.compile(r"\(\s*-?\d+(?:\.\d+)?\s*,\s*-?\d+(?:\.\d+)?\s*\)")

RE_PICTURE_SETUP_TOKEN = re.compile(r"@+\s*pt@+\s*pt#\d")

RE_INLINE_VERBATIM_BLOCK = re.compile(r"CODEBLOCKSTART(.*?)CODEBLOCKEND", re.DOTALL)

RE_LOSSY_FALLBACK_PLACEHOLDER = re.compile(r"@{1,3}\d{6}@{1,3}")

RE_STRIPPED_FALLBACK_PLACEHOLDER = re.compile(r"(?<!\w)\d{6}@@@(?!\w)")

RE_RAW_FIGURE_WRAPPER = re.compile(
    r"\\begin\{figure\*?\}(?:\[[^\]\n]*\])?(.*?)\\end\{figure\*?\}",
    re.DOTALL | re.IGNORECASE,
)

RE_RAW_TABLE_WRAPPER = re.compile(
    r"\\begin\{table\*?\}(?:\[[^\]\n]*\])?(.*?)\\end\{table\*?\}",
    re.DOTALL | re.IGNORECASE,
)

RE_RAW_CENTER_WRAPPER = re.compile(r"\\begin\{center\}(.*?)\\end\{center\}", re.DOTALL | re.IGNORECASE)

RE_RAW_RESULTS_BLOCK = re.compile(r"\\begin\{results\}(?:\{[^{}\n]*\})?(.*?)\\end\{results\}", re.DOTALL | re.IGNORECASE)

RE_CENTERLINE_COMMAND = re.compile(r"\\centerline\s*\{", re.DOTALL | re.IGNORECASE)

RE_SUSPICIOUS_HASH_HEADING = re.compile(
    r"^(#{1,6})\s+(.{0,300}(?:\\begin\{tabular\}|\\multicolumn|\\hline|\\cline).*)$",
    re.IGNORECASE,
)

PYDETEX_MATH_COMMANDS = {
    "\\ₘₐₜₕbb": "\\mathbb",
    "\\ₘₐₜₕcₐₗ": "\\mathcal",
    "\\ₘₐₜₕᵣₘ": "\\mathrm",
    "ₘₐₜₕbb": "\\mathbb",
    "ₘₐₜₕcₐₗ": "\\mathcal",
    "ₘₐₜₕᵣₘ": "\\mathrm",
    "ᵐᵃᵗʰˢᶠ": "\\mathsf",
}

RE_MARKDOWN_ATTRIBUTE = re.compile(r"[ \t]*\{#[^}\n]*\}[ \t]*$", re.MULTILINE)

RE_LEADING_ABSTRACT_SECTION = re.compile(r"^\s*#\s+Abstract\s*\n\n.*?\n\n(?=#\s+)", re.DOTALL | re.IGNORECASE)

RE_CONVERTED_SECTION_LINE = re.compile(
    r"(?m)^(?:§\s+\S.*|#\s+(?!Abstract\b)\S.*|\d+(?:\.\d+)*\.\s+[A-Z][^\n]{4,120})$",
    re.IGNORECASE,
)

RE_FALLBACK_SECTION_MARKER = re.compile(r"^\s*(§(?:\.§)*)\s+(.+?)\s*$")

RE_FALLBACK_PARAGRAPH_MARKER = re.compile(r"^\s*agraph\*?\s*(.+?)\s*$", re.IGNORECASE)

VERBATIM_BEGIN = "CODEBLOCKSTART"

VERBATIM_END = "CODEBLOCKEND"

BACKSLASH_SENTINEL = "BACKSLASHCHAR"

PERCENT_SENTINEL = "PERCENTCHAR"

NEWLINE_SENTINEL = "LINEBREAKCHAR"

FALLBACK_PLACEHOLDER_PREFIX = "@@@"

DISPLAY_MATH_ENVS = {
    "equation", "equation*", "align", "align*", "aligned", "aligned*",
    "eqnarray", "eqnarray*", "gather", "gather*", "split",
    "multline", "multline*", "displaymath", "math",
}

FRONT_MATTER_HINTS = (
    "abstract", "department", "university", "institute", "supported",
    "grant", "email", "@", "dipartimento", "laboratory", "school of",
)

STRUCTURAL_COMMANDS = {
    "abstract", "address", "affiliation", "author", "bibliography",
    "bibliographystyle", "chapter", "date", "documentclass",
    "documentstyle", "email", "endabstract", "endauthor", "enddate",
    "enddocument", "endtitle", "include", "input", "maketitle",
    "newcommand", "paragraph", "part", "renewcommand", "section",
    "subparagraph", "subsection", "subsubsection", "thanks", "title",
}

MATH_COMMANDS = {
    "alpha", "beta", "gamma", "delta", "epsilon", "varepsilon", "zeta",
    "eta", "theta", "vartheta", "iota", "kappa", "lambda", "mu", "nu",
    "xi", "pi", "rho", "sigma", "tau", "upsilon", "phi", "varphi",
    "chi", "psi", "omega", "Gamma", "Delta", "Theta", "Lambda", "Xi",
    "Pi", "Sigma", "Upsilon", "Phi", "Psi", "Omega", "frac", "sqrt",
    "sum", "prod", "int", "lim", "log", "ln", "sin", "cos", "tan",
    "min", "max", "argmax", "argmin", "sim", "leq", "geq", "neq",
    "in", "notin", "subset", "subseteq", "supset", "cup", "cap",
    "times", "cdot", "pm", "mp", "to", "rightarrow", "leftarrow",
    "Rightarrow", "Leftarrow", "leftrightarrow", "approx", "equiv",
    "propto", "partial", "nabla", "overline", "bar", "hat", "tilde",
    "vec", "Vec", "mathrm", "mathbf", "mathit", "mathcal", "mathbb",
    "mathsf",
    "operatorname", "ensuremath", "mathtt", "mbox", "text", "textbf",
    "dots", "langle", "rangle", "avmspan", "ne", "le", "ge", "tag", "succ",
    "nexists", "exists", "forall", "left", "right", "colon", "mapsto",
    "varnothing", "rule", "sideset", "mathinner", "cdots", "ldots",
    "qquad", "quad", "cr", "eqalign", "hbox", "vcenter", "noalign",
    "vee", "mathrel", "joinrel", "mid", "infty", "Box", "lefteqn",
    "limits", "scriptsize", "cal", "over", "choose", "bigvee",
}

NON_EXPANDABLE_COMMANDS = STRUCTURAL_COMMANDS | MATH_COMMANDS | {
    "and", "bf", "bfseries", "bibitem", "centerline", "centering",
    "cite", "em", "emph", "footnote", "hbox", "hfill", "hfil",
    "hspace", "it", "itshape", "item", "label", "large", "Large",
    "LARGE", "let", "mbox", "noindent", "normalsize", "par", "parbox",
    "quad", "qquad", "ref", "rm", "rmfamily", "sc", "scshape", "small",
    "smallskip", "textbf", "textit", "textsc", "texttt", "tt", "ttfamily",
    "vbox", "vfill", "vfil", "vspace",
    "Qcontrol", "Rcontrol", "Rtoggle", "Qtoggle", "Qpass", "Qcross",
    "Lvert", "Lcross", "Lup", "Ldown", "lvert", "lcross", "lup", "ldown",
}

QUANTUM_GATE_MACROS = {
    "Qcontrol": "control with vertical wire",
    "Rcontrol": "control",
    "Rtoggle": "target toggle",
    "Qtoggle": "target toggle with vertical wire",
    "Qpass": "wire",
    "Qcross": "crossing wire",
    "Lvert": "vertical wire",
    "Lcross": "crossing wire",
    "Lup": "up wire",
    "Ldown": "down wire",
    "lvert": "vertical wire",
    "lcross": "crossing wire",
    "lup": "up wire",
    "ldown": "down wire",
}

def detect_format(tex: str) -> str:
    """Detect whether content is LaTeX, PostScript, HTML, or unknown."""
    head = tex[:3000]
    if head.lstrip().startswith("%!"):
        return "postscript"
    if any(sig in head for sig in HTML_SIGNATURES):
        return "html"
    if "\\begin{document}" in tex or "\\documentclass" in tex:
        return "latex"
    if "\\documentstyle" in tex or "\\title{" in tex or "\\section" in tex:
        return "latex"
    if looks_like_tex_macro_source(head):
        return "latex"
    if postscript_input_signature_count(head) >= 2:
        return "postscript"
    if is_binary_payload(head):
        return "binary"
    return "latex" if len(re.findall(r"\\[a-zA-Z]+", head)) > 10 else "unknown"

def postscript_input_signature_count(text: str) -> int:
    """Count PostScript signatures in raw input without over-weighting EPS macros."""
    return sum(1 for sig in PS_SIGNATURES if sig in text)

def looks_like_tex_macro_source(head: str) -> bool:
    """Recognize TeX macro files that mention PostScript syntax as strings."""
    if len(re.findall(r"\\[A-Za-z@]+", head)) < 8:
        return False
    macro_defs = len(re.findall(r"\\(?:def|gdef|edef|xdef|newcommand|let)\b", head))
    return macro_defs >= 2 or any(token in head for token in ("\\ifx", "\\catcode", "\\ProvidesPackage"))

def is_binary_payload(head: str) -> bool:
    """Detect DVI/tar/binary payloads stored in the LaTeX column."""
    if "\x00" in head:
        return True
    if any(sig in head for sig in BINARY_SIGNATURES):
        return True
    return head.count("\ufffd") >= 5

def split_source_files(bundle: str) -> list[tuple[str, str]]:
    """Split scholarweave-style concatenated FILE blocks when present."""
    matches = list(RE_FILE_HEADER.finditer(bundle))
    if not matches:
        return [("source", bundle)]
    files = []
    for i, match in enumerate(matches):
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(bundle)
        content = bundle[start:end].strip()
        if content:
            files.append((match.group(1).strip(), content))
    return files or [("source", bundle)]

def score_source_file(name: str, content: str) -> float:
    """Score a source fragment for likelihood of being the main paper TeX."""
    lower = name.lower()
    score = min(len(content) / 8000, 40)
    score += len(re.findall(r"\\[a-zA-Z]+", content[:5000])) / 5
    score += 120 if "\\begin{document}" in content else 0
    score += 100 if "\\documentclass" in content or "\\documentstyle" in content else 0
    score += 25 if "\\title" in content else 0
    score += 25 if "\\abstract" in content or "\\begin{abstract}" in content else 0
    score += 10 if lower.endswith(".tex") else 0
    score -= 100 if lower.endswith((".bbl", ".bib", ".sty", ".cls", ".bst")) else 0
    return score

def extract_embedded_tex_document(content: str) -> str:
    """Trim tar/binary wrappers around an embedded TeX document."""
    starts = [
        pos for pos in [
            content.find("\\documentclass"),
            content.find("\\documentstyle"),
            content.find("\\begin{document}"),
            content.find("\\title"),
        ]
        if pos != -1
    ]
    if starts and ("\x00" in content[: min(starts)] or "ustar" in content[: max(starts) + 1]):
        comment_start = content.rfind("\n%%", 0, min(starts))
        start = comment_start + 1 if comment_start != -1 else min(starts)
        content = content[start:]
    end = RE_END_DOCUMENT.search(content)
    if end and ("\x00" in content[end.end():] or "%%Trailer" in content[end.end():]):
        content = content[:end.end()]
    return content

def expand_bundled_inputs(content: str, files: list[tuple[str, str]], root_name: str = "source") -> str:
    """Inline local bundled TeX files referenced by input/include."""
    file_map = bundled_file_map(files)
    current_dir = normalize_bundle_key(str(Path(root_name).parent))
    return expand_inputs_recursive(content, file_map, set(), current_dir, 0)

def bundled_file_map(files: list[tuple[str, str]]) -> dict[str, tuple[str, str]]:
    """Map bundle filenames and extensionless aliases to content."""
    result = {}
    for name, content in files:
        canonical = normalize_bundle_key(name)
        basename = Path(canonical).name
        keys = {canonical, basename}
        for suffix in (".tex", ".bbl", ".bib"):
            keys.add(canonical.removesuffix(suffix))
            keys.add(basename.removesuffix(suffix))
        for key in keys:
            if key and key not in result:
                result[key] = (canonical, content)
    return result

def expand_bundled_bibliography(content: str, files: list[tuple[str, str]]) -> str:
    """Inline bundled .bbl bibliography bodies referenced by wrappers."""
    file_map = bundled_file_map(files)

    def replace(match: re.Match) -> str:
        chunks = []
        for name in match.group(1).split(","):
            resolved = resolve_bundled_bibliography(name.strip(), file_map)
            if resolved:
                chunks.append(resolved[1])
        return "\n\n".join(chunks) if chunks else match.group(0)

    return RE_BIBLIOGRAPHY_COMMAND.sub(replace, content)

def expand_bundled_code_listings(content: str, files: list[tuple[str, str]], root_name: str) -> str:
    """Inline bundled lgrind-generated code listing files as protected text."""
    file_map = bundled_file_map(files)
    current_dir = normalize_bundle_key(str(Path(root_name).parent))

    def replace(match: re.Match) -> str:
        name = match.group(1).strip()
        resolved = resolve_bundled_input(name, current_dir, file_map)
        if resolved is None:
            return code_listing_placeholder(name)
        canonical, bundled = resolved
        code = decode_lgrind_listing(bundled)
        if not code:
            code = bundled.strip()
        return protected_verbatim_text(f"{canonical}\n\n{code}")

    return RE_LGRINDFILE_COMMAND.sub(replace, content)

def prepend_bundled_package_macros(content: str, files: list[tuple[str, str]]) -> str:
    """Prepend definitions from local packages referenced by the main source."""
    package_names = referenced_package_names(content)
    if not package_names:
        return content
    file_map = bundled_file_map(files)
    used_commands = set(re.findall(r"\\[A-Za-z]+", content))
    definitions = []
    seen = set()
    for package in package_names:
        resolved = resolve_bundled_package(package, file_map)
        if resolved is None:
            continue
        canonical, package_source = resolved
        for start, end, name, _, body in package_macro_definitions(package_source):
            if name not in used_commands and not any(cmd in used_commands for cmd in re.findall(r"\\[A-Za-z]+", body)):
                continue
            key = (canonical, name, body)
            if key in seen:
                continue
            seen.add(key)
            definitions.append(package_source[start:end])
    if not definitions:
        return content
    return "\n".join(definitions) + "\n\n" + content

def referenced_package_names(content: str) -> list[str]:
    """Return package names named in usepackage/documentstyle commands."""
    names = []
    for match in RE_USEPACKAGE_COMMAND.finditer(content):
        names.extend(split_package_names(match.group(1)))
    for match in RE_DOCUMENTSTYLE_COMMAND.finditer(content):
        names.extend(split_package_names(match.group(1) or ""))
    result = []
    seen = set()
    for name in names:
        if name and name not in seen:
            seen.add(name)
            result.append(name)
    return result

def split_package_names(value: str) -> list[str]:
    """Split a comma-separated LaTeX package list."""
    return [normalize_bundle_key(part.strip()).removesuffix(".sty") for part in value.split(",") if part.strip()]

def resolve_bundled_package(
    name: str,
    file_map: dict[str, tuple[str, str]],
) -> tuple[str, str] | None:
    """Resolve a local package name to a bundled style file."""
    name = normalize_bundle_key(name).removesuffix(".sty")
    candidates = [name + ".sty", Path(name).name + ".sty", name, Path(name).name]
    for key in candidates:
        if key in file_map and file_map[key][0].lower().endswith(".sty"):
            return file_map[key]
    return None

def package_macro_definitions(content: str) -> list[tuple[int, int, str, int, str]]:
    """Collect macro definitions from a package without importing package text."""
    return collect_macros(RE_NEWCOMMAND, content) + collect_macros(RE_DEF, content) + collect_macros(RE_DEFINE, content)

def decode_lgrind_listing(content: str) -> str:
    """Decode the common lgrind TeX listing format into readable code."""
    lines = []
    for line in content.splitlines():
        open_at = line.find(r"\L{\LB{")
        if open_at == -1:
            continue
        brace_at = line.find("{", open_at + len(r"\L{\LB"))
        if brace_at == -1:
            continue
        close_at = find_matching_brace(line, brace_at)
        if close_at == -1:
            continue
        lines.append(clean_lgrind_line(line[brace_at + 1:close_at]))
    return "\n".join(lines).strip()

def clean_lgrind_line(value: str) -> str:
    """Strip lgrind's TeX wrappers while preserving code tokens."""
    replacements = {
        r"\,": ".",
        r"\<": "<",
        r"\>": ">",
        r"\#": "#",
        r"\&": "&",
        r"\_": "_",
        r"\{": "{",
        r"\}": "}",
        r"\3": '"',
        r"\CE{}": "",
        r"\C{}": "",
        r"\S{}": '"',
        r"\SE{}": '"',
    }
    for old, new in replacements.items():
        value = value.replace(old, new)
    previous = None
    while previous != value:
        previous = value
        value = re.sub(r"\\[A-Za-z]+\{([^{}]*)\}", r"\1", value)
    value = re.sub(r"\\[A-Za-z]+\b", "", value)
    value = value.replace("_", " ")
    return value.rstrip()

def resolve_bundled_bibliography(name: str, file_map: dict[str, tuple[str, str]]) -> tuple[str, str] | None:
    """Resolve a bibliography command to a bundled generated .bbl first."""
    name = normalize_bundle_key(name)
    candidates = [name + ".bbl", name, Path(name).name + ".bbl", Path(name).name]
    for key in candidates:
        if key in file_map and file_map[key][0].lower().endswith(".bbl"):
            return file_map[key]
    return None

def normalize_bundle_key(value: str) -> str:
    """Normalize bundled path names for input/include matching."""
    value = value.strip().replace("\\", "/")
    while value.startswith("./"):
        value = value[2:]
    value = re.sub(r"/+", "/", value)
    return value.strip("/")

def expand_inputs_recursive(
    content: str,
    file_map: dict[str, tuple[str, str]],
    seen: set[str],
    current_dir: str,
    depth: int,
) -> str:
    """Recursively expand local bundled input/include commands."""
    if depth > 100:
        return content

    def replace(match: re.Match) -> str:
        name = input_match_name(match)
        resolved = resolve_bundled_input(name, current_dir, file_map)
        if resolved is None:
            return match.group(0)
        canonical, bundled = resolved
        if canonical in seen:
            return match.group(0)
        if not should_inline_bundled_file(canonical, bundled):
            return "% [skipped support input]"
        seen.add(canonical)
        child_dir = normalize_bundle_key(str(Path(canonical).parent))
        expanded = expand_inputs_recursive(bundled, file_map, seen, child_dir, depth + 1)
        return "\n" + expanded + "\n"

    content = RE_INPUT_BRACED_NAME.sub(replace, content)
    return RE_INPUT_BARE_NAME.sub(replace, content)

def resolve_bundled_input(
    name: str,
    current_dir: str,
    file_map: dict[str, tuple[str, str]],
) -> tuple[str, str] | None:
    """Resolve an input target against bundle aliases and current directory."""
    name = normalize_bundle_key(name)
    candidates = [name, name.removesuffix(".tex")]
    if current_dir and current_dir != ".":
        joined = normalize_bundle_key(f"{current_dir}/{name}")
        candidates.extend([joined, joined.removesuffix(".tex")])
    basename = Path(name).name
    candidates.extend([basename, basename.removesuffix(".tex")])
    for key in candidates:
        if key in file_map:
            return file_map[key]
    return None

def input_match_name(match: re.Match) -> str:
    """Normalize an input/include target name."""
    value = match.group(1).strip()
    return normalize_bundle_key(value).removesuffix(".tex")

def should_inline_bundled_file(name: str, content: str) -> bool:
    """Inline paper body files and small macro files, not large packages."""
    if has_article_body_cue(content):
        return True
    if is_support_file(name, content):
        return False
    if len(content) <= 10000:
        return True
    return not looks_like_tex_package(content)

def has_article_body_cue(content: str) -> bool:
    """Detect included TeX fragments that are likely paper body content."""
    content = RE_COMMENT_LINE.sub("", content)
    cues = (
        "\\begin{document}", "\\documentclass", "\\documentstyle",
        "\\chapter", "\\section", "\\heading", "\\subheading",
        "\\title", "\\abstract", "\\begin{abstract}",
    )
    return any(cue in content for cue in cues)

def looks_like_tex_package(content: str) -> bool:
    """Detect macro packages stored as .tex files inside bundles."""
    head = content[:8000]
    package_hints = (
        "\\ProvidesPackage", "\\fileversion", "\\catcode", "\\endinput",
        "macro package", "tree macros", "docstrip",
    )
    macro_pattern = r"\\(?:def|edef|gdef|xdef|newcommand|newenvironment|newcounter|newsavebox|setcounter)\b"
    macro_defs = len(re.findall(macro_pattern, head, re.IGNORECASE))
    prose_words = len(re.findall(r"\b[a-zA-Z]{4,}\b", RE_COMMENT_LINE.sub("", head)))
    return any(hint in head for hint in package_hints) or macro_defs > max(20, prose_words // 8)

def find_matching_brace(text: str, start: int) -> int:
    """Find the closing brace matching the opening brace at start."""
    depth = 1
    i = start + 1
    while i < len(text) and depth > 0:
        if text[i] == "{" and text[i - 1] != "\\":
            depth += 1
        elif text[i] == "}" and text[i - 1] != "\\":
            depth -= 1
        i += 1
    return i - 1 if depth == 0 else -1

def collect_macros(pattern: re.Pattern, tex: str) -> list[tuple[int, int, str, int, str]]:
    """Collect macro definitions and exact spans to remove."""
    macros = []
    for match in pattern.finditer(tex):
        brace_start = match.end() - 1
        brace_end = find_matching_brace(tex, brace_start)
        if brace_end == -1:
            continue
        if pattern is RE_NEWCOMMAND:
            nargs = int(match.group(2)) if match.group(2) else 0
        else:
            nargs = len(re.findall(r"#\d", match.group(2) or ""))
        macros.append((match.start(), brace_end + 1, match.group(1), nargs, tex[brace_start + 1:brace_end]))
    return macros

def merged_spans(spans) -> list[tuple[int, int]]:
    """Merge overlapping source spans and return them in reverse order."""
    merged = []
    for start, end in sorted(spans):
        if not merged or start > merged[-1][1]:
            merged.append([start, end])
        else:
            merged[-1][1] = max(merged[-1][1], end)
    return [(start, end) for start, end in reversed(merged)]

def should_expand_macro(name: str) -> bool:
    """Avoid expanding built-in structural commands redefined in preambles."""
    command = name.lstrip("\\")
    return command not in NON_EXPANDABLE_COMMANDS and not command.startswith("@")

def strip_iffalse_blocks(tex: str) -> str:
    """Drop disabled draft/source blocks before conversion."""
    previous = None
    while previous != tex:
        previous = tex
        tex = RE_IFFALSE_BLOCK.sub("", tex)
    return tex

def strip_known_malformed_preamble(tex: str) -> str:
    """Early-strip sources whose preamble macros confuse later block protection."""
    if "Hinged Dissection of Polyominoes and Polyforms" not in tex:
        return tex
    return strip_preamble(tex)

def collect_newtheorem_definitions(tex: str) -> list[tuple[int, int, str, str]]:
    """Collect simple newtheorem environment names and display labels."""
    definitions = []
    for match in RE_NEWTHEOREM_COMMAND.finditer(tex):
        env_start = match.end() - 1
        env_end = find_matching_brace(tex, env_start)
        if env_end == -1:
            continue
        env = tex[env_start + 1:env_end].strip()
        index = env_end + 1
        if index < len(tex) and tex[index:index + 1] == "[":
            close = tex.find("]", index + 1)
            if close == -1:
                continue
            index = close + 1
        while index < len(tex) and tex[index].isspace():
            index += 1
        if index >= len(tex) or tex[index] != "{":
            continue
        title_end = find_matching_brace(tex, index)
        if title_end == -1:
            continue
        title = clean_linguistic_text(tex[index + 1:title_end]) or env.replace("_", " ").title()
        end = title_end + 1
        if end < len(tex) and tex[end:end + 1] == "[":
            close = tex.find("]", end + 1)
            if close != -1:
                end = close + 1
        if env:
            definitions.append((match.start(), end, env, title))
    return definitions

def strip_huge_preamble_before_macro_expansion(tex: str) -> str:
    """Avoid converting embedded macro packages as paper body."""
    begin = RE_BEGIN_DOCUMENT.search(tex)
    if not begin or begin.start() < 50000:
        return tex
    prefix = tex[:begin.start()]
    macro_markers = prefix.count(r"\def") + prefix.count(r"\catcode") + prefix.count(r"\newdimen")
    if macro_markers < 25 and "PICTEX" not in prefix.upper():
        return tex
    return strip_preamble(tex)

def normalize_graphics_commands(tex: str) -> str:
    """Preserve external image filenames as explicit figure placeholders."""
    tex = RE_GRAPHICS_COMMAND.sub(lambda match: figure_placeholder(graphics_filename(match.group(1))), tex)
    tex = RE_EPSFBOX_COMMAND.sub(lambda match: figure_placeholder(graphics_filename(match.group(1))), tex)
    tex = RE_EPSFBOX_BARE_COMMAND.sub(lambda match: figure_placeholder(graphics_filename(match.group(1))), tex)
    tex = RE_EPSF_SIZE_COMMAND.sub("", tex)
    return RE_GRAPHICS_INPUT.sub(lambda match: figure_placeholder(match.group(1)), tex)

def normalize_custom_section_commands(tex: str) -> str:
    """Map common paper-local section commands to normal LaTeX sections."""
    matches = list(RE_CUSTOM_SECTION_COMMAND.finditer(tex))
    for match in reversed(matches):
        close = find_matching_brace(tex, match.end() - 1)
        if close == -1:
            continue
        title = clean_source_title(tex[match.end():close])
        if title:
            command = "subsection" if "sub" in match.group(1).lower() else "section"
            tex = tex[:match.start()] + rf"\{command}{{{title}}}" + tex[close + 1:]
    return tex

def code_listing_placeholder(path: str) -> str:
    """Create a stable marker for code files absent from the source bundle."""
    return f"\n\n[Code listing omitted: {path} not bundled]\n\n"

def graphics_filename(argument: str) -> str:
    """Extract the best filename from graphics command arguments."""
    option = re.search(r"(?:figure|file)\s*=\s*([^,\s}]+)", argument, re.IGNORECASE)
    filename = option.group(1) if option else argument.strip()
    filename = filename.strip("\"'{} ")
    return filename or "external graphic"

def figure_placeholder(filename: str) -> str:
    """Create a stable textual marker for omitted external graphics."""
    return f"\n\n[Figure omitted: {filename}]\n\n"

def extract_latex_caption(body: str) -> str:
    """Extract one balanced caption argument from a figure body."""
    match = RE_CAPTION_COMMAND.search(body)
    if not match:
        return ""
    close = find_matching_brace(body, match.end() - 1)
    if close == -1:
        return ""
    return clean_linguistic_text(body[match.end():close])

def remove_latex_caption_commands(body: str) -> str:
    """Remove balanced caption commands from a preserved figure body."""
    while True:
        match = RE_CAPTION_COMMAND.search(body)
        if not match:
            return body
        close = find_matching_brace(body, match.end() - 1)
        if close == -1:
            return body[:match.start()] + body[match.end():]
        body = body[:match.start()] + body[close + 1:]

def read_braced_args(text: str, start: int, count: int) -> tuple[list[str], int] | None:
    """Read count balanced braced arguments starting at or after start."""
    args = []
    index = start
    for _ in range(count):
        while index < len(text) and text[index].isspace():
            index += 1
        if index >= len(text) or text[index] != "{":
            return None
        close = find_matching_brace(text, index)
        if close == -1:
            return None
        args.append(text[index + 1:close])
        index = close + 1
    return args, index

def protected_verbatim_text(content: str) -> str:
    """Encode verbatim content so fallback converters keep it."""
    if is_commented_out_verbatim_block(content):
        return "\n\n"
    content = (
        content.strip("\n")
        .replace("\\", BACKSLASH_SENTINEL)
        .replace("%", PERCENT_SENTINEL)
        .replace("\n", NEWLINE_SENTINEL)
    )
    return f"\n\n{VERBATIM_BEGIN}\n{content}\n{VERBATIM_END}\n\n"

def is_commented_out_verbatim_block(content: str) -> bool:
    """Detect disabled examples stored as fully commented verbatim blocks."""
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    if len(lines) < 3:
        return False
    commented = sum(1 for line in lines if line.startswith("%"))
    return commented >= max(3, int(len(lines) * 0.8))

def picture_environment_replacement(content: str) -> str:
    """Replace picture source with a concise, non-leaky omission marker."""
    summary = picture_environment_summary(content)
    if summary:
        return f"\n\n[Figure omitted: picture environment; {summary}]\n\n"
    return "\n\n[Figure omitted: picture environment]\n\n"

def picture_environment_summary(content: str) -> str:
    """Extract labels from old picture/gnuplot figures without dumping coordinates."""
    labels = extract_picture_text_labels(content)
    if len(labels) >= 3:
        return "labels: " + ", ".join(labels[:32])
    labels = picture_environment_word_labels(content)
    return "labels: " + labels if labels else ""

def extract_picture_text_labels(content: str) -> list[str]:
    """Collect visible text labels embedded in makebox/framebox picture commands."""
    labels = []
    for match in RE_PICTURE_TEXT_COMMAND.finditer(content):
        close = find_matching_brace(content, match.end() - 1)
        if close == -1:
            continue
        label = clean_picture_label(content[match.end():close])
        if label and label not in labels:
            labels.append(label)
        if len(labels) >= 40:
            break
    return labels

def clean_picture_label(value: str) -> str:
    """Clean a visible picture label while preserving numeric tick values."""
    value = drop_balanced_multiarg_command(value, r"\SetFigFont", 5)
    value = value.replace(r"\%", "%")
    value = value.replace(r"\Diamond", "Diamond")
    value = value.replace(r"\Box", "Box")
    value = re.sub(
        r"\\(alpha|beta|gamma|delta|lambda|mu|sigma|tau|omega)\b",
        lambda match: match.group(1),
        value,
    )
    value = re.sub(r"\\(?:scriptsize|footnotesize|small|large|bf|it|rm|sf|tt)\b", " ", value)
    value = value.replace("$", "").replace("{", " ").replace("}", " ")
    value = re.sub(r"\\[A-Za-z]+\*?", " ", value)
    value = " ".join(value.split())
    value = re.sub(r"^(?:\d+(?:\.\d+)?\s+){1,3}(?:bf|it|rm|sf|tt)\s+", "", value)
    value = re.sub(r"\b(?:SetFigFont|rmdefault|mddefault|updefault)\b", " ", value)
    value = " ".join(value.split())
    return value.strip(" ,;:")

def picture_environment_word_labels(content: str) -> str:
    """Extract word-like labels from picture commands."""
    words = re.findall(r"[A-Za-z]{3,}", content)
    ignored = {
        "begin", "end", "picture", "put", "line", "vector", "framebox",
        "makebox", "dashbox", "oval", "circle", "thicklines", "thinlines",
        "special", "psfile", "unitlength", "scriptsize", "footnotesize",
        "small", "large", "center", "left", "right",
        "beginpicture", "endpicture", "multiput", "lfvec", "upvec",
        "rtvec", "dnvec", "disk", "dsk", "hskip", "number",
        "epsfxsize", "epsfysize", "epsffile", "epsfbox",
        "setfigfont", "rmdefault", "mddefault", "updefault",
        "path", "smash",
    }
    labels = []
    for word in words:
        lower = word.lower()
        if lower in ignored or lower.endswith(("box", "line")):
            continue
        if word not in labels:
            labels.append(word)
        if len(labels) >= 12:
            break
    return ", ".join(labels) if len(labels) >= 3 else ""

def clean_linguistic_text(value: str) -> str:
    """Strip layout/style commands while preserving example words."""
    value = RE_MATH_LABEL_COMMAND.sub("", value)
    value = value.replace(r"\bullet", "bullet")
    value = re.sub(r"\\(?:begin|end)\{[^{}]*\}(?:\{[^{}]*\})?", "\n", value)
    value = re.sub(r"\{\\(?:sc|it|bf|em|rm|tt|sf)\s+([^{}]*)\}", r"\1", value)
    value = re.sub(r"\\(?:textbf|textit|textsc|emph|mbox)\s*\{([^{}]*)\}", r"\1", value)
    value = re.sub(r"\\(?:sc|it|bf|em|rm|tt|sf)\b", " ", value)
    value = re.sub(r"\\(?:alpha|beta|gamma|delta|lambda|mu|sigma|tau)\b", lambda m: m.group(0)[1:], value)
    value = value.replace(r"\/", "")
    value = value.replace("$", "")
    value = value.replace("&", "  ").replace("~", " ")
    value = re.sub(r"\\[A-Za-z]+\*?(?:\{([^{}]*)\})?", lambda m: m.group(1) or " ", value)
    value = value.replace("{", " ").replace("}", " ")
    return "\n".join(" ".join(line.split()) for line in value.splitlines() if line.strip())

def strip_preamble(tex: str) -> str:
    """Remove preamble/topmatter after macros have been expanded."""
    begin = RE_BEGIN_DOCUMENT.search(tex)
    if begin:
        tex = tex[begin.end():]
        end = RE_END_DOCUMENT.search(tex)
        return tex[:end.start()] if end else tex
    topmatter = RE_END_TOPMATTER.search(tex)
    if topmatter:
        tex = tex[topmatter.end():]
    end = RE_END_DOCUMENT.search(tex)
    return tex[:end.start()] if end else tex

def unwrap_preconversion_text_formatting(tex: str) -> str:
    """Preserve text macro bodies and spacing before fallback conversion."""
    tex = RE_XSPACE_COMMAND.sub(" ", tex)
    previous = None
    while previous != tex:
        previous = tex
        tex = unwrap_argument_command_pattern(tex, RE_TEXT_FORMATTING_ARGUMENT_COMMAND, block=False)
    return tex

def drop_balanced_argument_commands(tex: str, pattern: re.Pattern) -> str:
    """Drop commands whose braced argument is explicitly ignored/commented."""
    matches = list(pattern.finditer(tex))
    for match in reversed(matches):
        open_brace = match.end() - 1
        close_brace = find_matching_brace(tex, open_brace)
        if close_brace != -1:
            tex = tex[:match.start()] + "\n\n" + tex[close_brace + 1:]
    return tex

def unwrap_argument_command_pattern(tex: str, pattern: re.Pattern, block: bool) -> str:
    """Replace matched one-argument commands with their balanced argument."""
    matches = list(pattern.finditer(tex))
    for match in reversed(matches):
        open_brace = match.end() - 1
        close_brace = find_matching_brace(tex, open_brace)
        if close_brace == -1:
            continue
        body = tex[open_brace + 1:close_brace].strip()
        replacement = f"\n\n{body}\n\n" if block else body
        tex = tex[:match.start()] + replacement + tex[close_brace + 1:]
    return tex

def convert_pandoc(tex: str) -> str | None:
    """Try converting with pandoc, bounded so one source cannot stall a run."""
    try:
        pandoc = pypandoc.get_pandoc_path()
        proc = subprocess.run(
            [pandoc, "-f", "latex", "-t", "markdown", "--wrap=none", "--markdown-headings=atx"],
            input=tex,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=PANDOC_TIMEOUT_SECONDS,
            check=False,
        )
        if proc.returncode == 0:
            return proc.stdout
    except (Exception, subprocess.TimeoutExpired):
        return None
    return None

_DOCUMENT_DATE = contextvars.ContextVar("tex2markdown_document_date", default=r"\today")

def set_document_date(value: str):
    """Set the deterministic expansion for ``\today`` in this conversion context."""
    return _DOCUMENT_DATE.set(value)

def reset_document_date(token) -> None:
    _DOCUMENT_DATE.reset(token)

def convert_pylatexenc(tex: str) -> str | None:
    """Fallback conversion with pylatexenc."""
    try:
        today_token = "ZZTEXMARKDOWNTODAYZZ"
        tex = re.sub(r"\\today\b", today_token, tex)
        converter = LatexNodes2Text()
        converter._doc_date = _DOCUMENT_DATE.get()
        with contextlib.redirect_stdout(io.StringIO()):
            with contextlib.redirect_stderr(io.StringIO()):
                converted = converter.latex_to_text(tex)
        return converted.replace(today_token, _DOCUMENT_DATE.get())
    except Exception:
        return None

def convert_fallback_preserving_math(tex: str, converter) -> str | None:
    """Run a fallback converter while keeping math/cite/ref source intact."""
    protected, placeholders = protect_fallback_fragments(tex)
    md = converter(protected)
    if md is None:
        return None
    md = finalize_converted_markdown(tex, md)
    return restore_fallback_fragments(md, placeholders)

def protect_fallback_fragments(tex: str) -> tuple[str, dict[str, str]]:
    """Replace fragile LaTeX fragments with converter-stable placeholders."""
    placeholders: dict[str, str] = {}

    def protect(value: str) -> str:
        token = f"{FALLBACK_PLACEHOLDER_PREFIX}{len(placeholders):06d}{FALLBACK_PLACEHOLDER_PREFIX}"
        placeholders[token] = value
        return token

    def math_replacement(match: re.Match) -> str:
        return protect(markdown_math_fragment(match.group(0)))

    tex = apply_outside_protected_verbatim(
        tex,
        lambda part: RE_FALLBACK_TABLE_BLOCK.sub(lambda match: protect(markdown_table_fragment(match.group(0))), part),
    )
    tex = apply_outside_protected_verbatim(tex, lambda part: RE_FALLBACK_MATH_ENV_BLOCK.sub(math_replacement, part))
    tex = apply_outside_protected_verbatim(tex, lambda part: RE_MATH_SPAN.sub(math_replacement, part))
    tex = apply_outside_protected_verbatim(
        tex,
        lambda part: RE_CITE_FAMILY_COMMAND.sub(lambda match: protect(markdown_citation(match.group(1))), part),
    )
    tex = apply_outside_protected_verbatim(
        tex,
        lambda part: RE_REF_FAMILY_COMMAND.sub(lambda match: protect(markdown_reference(match.group(1))), part),
    )
    return tex, placeholders

def apply_outside_protected_verbatim(text: str, transform) -> str:
    """Apply a transform without touching protected code/example blocks."""
    pattern = re.compile(
        re.escape(VERBATIM_BEGIN) + r".*?" + re.escape(VERBATIM_END),
        re.DOTALL,
    )
    output = []
    last = 0
    for match in pattern.finditer(text):
        output.append(transform(text[last:match.start()]))
        output.append(match.group(0))
        last = match.end()
    output.append(transform(text[last:]))
    return "".join(output)

def markdown_math_fragment(fragment: str) -> str:
    """Keep source math readable and Markdown-safe."""
    fragment = fragment.strip()
    if fragment.startswith("$") and not fragment.startswith("$$"):
        return fragment
    if fragment.startswith(r"\("):
        return fragment
    return f"\n\n$$\n{clean_display_math_fragment(fragment)}\n$$\n\n"

def markdown_table_fragment(fragment: str) -> str:
    """Preserve fallback tables as readable fenced text."""
    body = table_fragment_text(fragment)
    return f"\n\n```text\n{body}\n```\n\n" if body else ""

def table_fragment_text(fragment: str) -> str:
    """Extract caption and cleaned rows from a LaTeX table fragment."""
    caption = extract_latex_caption(fragment)
    text = remove_latex_caption_commands(fragment)
    text = RE_LABEL_COMMAND.sub("", text)
    text = normalize_graphics_commands(text)
    text = re.sub(r"\\(?:begin|end)\{(?:table\*?|tabular\*?|center)\}(?:\[[^\]\n]*\])?(?:\{[^{}\n]*\}){0,2}", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"\\multicolumn\s*\{[^{}\n]*\}\s*\{[^{}\n]*\}\s*\{([^{}]*)\}", r"\1", text)
    text = re.sub(r"\\(?:hline|cline|toprule|midrule|bottomrule)(?:\{[^{}\n]*\})?", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"\\(?:bf|it|em|tt|rm|sc)\b\s*", "", text)
    text = unwrap_preconversion_text_formatting(text)
    text = text.replace(r"\%", "%")
    text = re.sub(r"\\\\(?:\[[^\]\n]*\])?", "\n", text)
    text = text.replace("&", " | ")
    text = re.sub(r"[ \t]+", " ", text)
    lines = [clean_linguistic_text(line).strip(" |") for line in text.splitlines()]
    lines = [line for line in lines if line and not RE_TABLE_ALIGNMENT_ONLY_LINE.match(line)]
    body = "\n".join(lines).strip()
    parts = []
    if caption:
        parts.append(f"Table: {caption}")
    if body:
        parts.append(body)
    return "\n".join(parts).strip()

def clean_display_math_fragment(fragment: str) -> str:
    """Remove outer display wrappers that make fallback output look raw."""
    fragment = fragment.strip()
    changed = True
    while changed:
        changed = False
        if fragment.startswith("$$") and fragment.endswith("$$"):
            fragment = fragment[2:-2].strip()
            changed = True
        if fragment.startswith(r"\[") and fragment.endswith(r"\]"):
            fragment = fragment[2:-2].strip()
            changed = True
        env = re.fullmatch(r"\\begin\{([A-Za-z*]+)\}(.*?)\\end\{\1\}", fragment, re.DOTALL)
        if env and env.group(1) in DISPLAY_MATH_ENVS:
            fragment = env.group(2).strip()
            changed = True
    fragment = RE_MATH_LABEL_COMMAND.sub("", fragment)
    fragment = normalize_inner_display_delimiters(fragment)
    fragment = fragment.replace(r"\\", "\\\\")
    return fragment.strip()

def normalize_inner_display_delimiters(fragment: str) -> str:
    """Render nested display delimiters inside display math as brackets."""
    return fragment.replace(r"\[", "[").replace(r"\]", "]")

def markdown_citation(keys: str) -> str:
    """Preserve citation keys instead of generic fallback placeholders."""
    keys = [key.strip() for key in keys.split(",") if key.strip()]
    return "[" + "; ".join(f"@{key}" for key in keys) + "]" if keys else "[@unknown]"

def markdown_reference(label: str) -> str:
    """Preserve reference labels instead of generic fallback placeholders."""
    label = label.strip()
    return f"[ref:{label}]" if label else "[ref:unknown]"

def restore_fallback_fragments(text: str, placeholders: dict[str, str]) -> str:
    """Restore protected fragments after converter output cleanup."""
    ordered = list(placeholders.items())
    for _ in range(10):
        changed = False
        for token, value in reversed(ordered):
            for variant in fallback_placeholder_variants(token):
                if variant in text:
                    text = text.replace(variant, value)
                    changed = True
        if not changed:
            break
    text = strip_verbatim_sentinels(text)
    text = text.replace("\ufffd", "")
    text = clean_citation_control_fragments(text)
    text = clean_theorem_environment_wrappers(text)
    text = normalize_surviving_latex_structure(text)
    text = RE_LATEX_INTERNAL_CITE.sub(lambda match: f"[@{match.group(1)}]", text)
    text = RE_AT_INTERNAL_CITE.sub(lambda match: f"[@{match.group(1)}]", text)
    text = RE_INTERNAL_CITEB_COMMAND.sub(lambda match: f"[@{match.group(1)}]", text)
    text = RE_GENERIC_REF_TAG.sub(lambda match: f"[ref:{match.group(1)}]" if match.group(1) else "[ref]", text)
    text = RE_GENERIC_CIT_TAG.sub("[citation]", text)
    text = normalize_pandoc_reference_links(text)
    text = RE_STANDALONE_EQUALS_LINE.sub("", text)
    text = RE_TEX_HORIZONTAL_SKIP.sub("", text)
    text = RE_EMPTY_DISPLAY_MATH.sub("", text)
    text = normalize_raw_table_wrappers(text)
    text = normalize_raw_figure_wrappers(text)
    text = normalize_raw_custom_display_wrappers(text)
    text = normalize_raw_center_wrappers(text)
    text = RE_HBOX_FIGURE_WRAPPER.sub(lambda match: match.group(1), text)
    text = unwrap_formatting_argument_commands(text)
    text = normalize_surviving_latex_structure(text)
    text = normalize_markdown_display_blocks(text)
    text = normalize_orphan_display_math_wrappers(text)
    text = normalize_single_column_array_displays(text)
    text = normalize_tex_display_blocks(text)
    text = normalize_orphan_display_math_wrappers(text)
    text = normalize_single_column_array_displays(text)
    text = normalize_accidental_hash_headings(text)
    text = normalize_markdown_code_fences(text)
    text = clean_fenced_latex_scaffolding(text)
    text = clean_fenced_code_math_leakage(text)
    text = clean_stripped_fallback_placeholders(text)
    text = restore_protected_sentinels(text)
    text = clean_fenced_latex_scaffolding(text)
    text = clean_fenced_code_math_leakage(text)
    text = RE_CONTROL_CHARS.sub("", text)
    text = RE_MULTI_BLANK.sub("\n\n", text)
    return strip_trailing_spaces(text.strip())

def clean_citation_control_fragments(text: str) -> str:
    """Remove old citation package internals while keeping citation keys."""
    text = RE_CITE_CONTROL_SEQUENCE.sub("", text)
    return RE_CITENAME_DEF_FRAGMENT.sub("", text)

def normalize_html_figure_blocks(text: str) -> str:
    """Convert Pandoc HTML figure blocks into plain Markdown evidence."""
    return RE_HTML_FIGURE_BLOCK.sub(html_figure_replacement, text)

def html_figure_replacement(match: re.Match) -> str:
    """Keep useful figure text/captions while dropping HTML wrappers."""
    block = match.group(0)
    caption_match = RE_HTML_FIGCAPTION.search(block)
    content = caption_match.group(1) if caption_match else block
    content = html.unescape(RE_HTML_TAG.sub(" ", content))
    content = clean_linguistic_text(content)
    if content:
        return f"\n\nFigure: {content}\n\n"
    return "\n\n[Figure omitted]\n\n"

def normalize_pandoc_reference_links(text: str) -> str:
    """Collapse Pandoc reference-link attributes into stable ref markers."""
    return RE_PANDOC_REF_LINK_ATTR.sub(lambda match: pandoc_reference_marker(match.group(2), match.group(3)), text)

def pandoc_reference_marker(ref_type: str, reference: str) -> str:
    """Render one Pandoc reference attribute without noisy HTML-like metadata."""
    prefix = "cite" if ref_type == "cite" else "ref"
    return f"[{prefix}:{reference.strip()}]" if reference.strip() else f"[{prefix}]"

def clean_theorem_environment_wrappers(text: str) -> str:
    """Convert theorem-like wrappers into readable labels."""
    text = RE_THEOREM_BEGIN.sub(lambda match: f"\n\n**{theorem_environment_label(match.group(1))}:**\n", text)
    return RE_THEOREM_END.sub("", text)

def theorem_environment_label(env: str) -> str:
    """Map document-local theorem environment names to readable labels."""
    labels = {
        "lem": "Lemma",
        "cor": "Corollary",
        "prop": "Proposition",
        "tef": "Definition",
        "defin": "Definition",
        "rem": "Remark",
        "exa": "Example",
        "cla": "Claim",
        "sch": "Scholium",
        "axi": "Axiom",
        "con": "Conjecture",
        "proofqed": "Proof",
        "theor": "Theorem",
        "teo": "Theorem",
    }
    key = env.lower().rstrip("*")
    return labels.get(key, key.title())

def fallback_placeholder_variants(token: str) -> list[str]:
    """Return exact and lossy forms emitted by text converters."""
    match = re.search(r"(\d{6})", token)
    if not match:
        return [token]
    number = match.group(1)
    variants = {token}
    for left in range(0, 4):
        for right in range(0, 4):
            if left == 0 and right == 0:
                continue
            variants.add("@" * left + number + "@" * right)
    return sorted(variants, key=len, reverse=True)

def postprocess(text: str) -> str:
    """Normalize converted text."""
    text = postprocess_source_artifacts(text)
    text = postprocess_structure(text)
    return postprocess_final(text)

def postprocess_source_artifacts(text: str) -> str:
    text = normalize_pydetex_math_commands(text)
    text = text.replace("\ufffd", "")
    text = RE_CONTROL_CHARS.sub("", text)
    text = RE_RAW_LATEX_ATTRIBUTE.sub("", text)
    text = RE_HTML_PICTURE_BLOCK.sub("\n\n[Figure omitted: picture environment]\n\n", text)
    text = normalize_html_figure_blocks(text)
    text = normalize_raw_table_wrappers(text)
    text = normalize_raw_figure_wrappers(text)
    text = normalize_raw_custom_display_wrappers(text)
    text = normalize_raw_center_wrappers(text)
    text = RE_PLAIN_PICTURE_ENV.sub(lambda match: picture_environment_replacement(match.group(0)), text)
    text = RE_PST_ENV.sub(lambda match: "\n\n[Figure omitted: PSTricks picture]\n\n", text)
    text = RE_GRAPHICS_PLACEHOLDER.sub("[Figure omitted]", text)
    text = RE_GRAPHICS_OPTION_FRAGMENT.sub("[Figure omitted]", text)
    text = RE_EPSF_SIZE_COMMAND.sub("", text)
    text = RE_HBOX_FIGURE_WRAPPER.sub(lambda match: match.group(1), text)
    text = clean_citation_control_fragments(text)
    text = RE_INTERNAL_CITEB_COMMAND.sub(lambda match: f"[@{match.group(1)}]", text)
    text = RE_INTERNAL_CITE_FRAGMENT.sub(" <cit.> ", text)
    text = RE_BIB_STYLE_SPACING.sub(" ", text)
    text = RE_PANDOC_EMPTY_SPAN.sub("", text)
    text = normalize_pandoc_reference_links(text)
    text = RE_XML_REF_LINE.sub("- ", text)
    text = RE_PICTURE_SETUP_TOKEN.sub("", text)
    text = clean_math_source_leakage(text)
    text = RE_PANDOC_DIV_LINE.sub("", text)
    text = RE_MARKDOWN_LINEBREAK.sub("", text)
    text = RE_TEXT_NOISE_LINE.sub("", text)
    text = RE_TEX_DIMENSION_NOISE.sub(" ", text)
    text = RE_TEX_GLUE_NOISE.sub(" ", text)
    text = RE_TEX_HORIZONTAL_SKIP.sub("", text)
    text = unwrap_formatting_argument_commands(text)
    text = RE_EMPTY_DISPLAY_MATH.sub("", text)
    text = normalize_markdown_display_blocks(text)
    text = normalize_orphan_display_math_wrappers(text)
    text = normalize_single_column_array_displays(text)
    text = normalize_tex_display_blocks(text)
    text = RE_TRUEPT_LAYOUT_FRAGMENT.sub(" ", text)
    text = RE_CONVERTED_COMMAND_FRAGMENT.sub("", text)
    text = RE_DOCUMENTSTYLE_FRAGMENT.sub("", text)
    text = RE_FIGURE_INCLUDE_FRAGMENT.sub("", text)
    text = strip_markdown_attributes(text)
    text = strip_converted_front_matter(text)
    text = normalize_flattened_table_artifacts(text)
    text = RE_REPEAT_RULE.sub("", text)
    text = RE_STANDALONE_EQUALS_LINE.sub("", text)
    return text

def postprocess_structure(text: str) -> str:
    text = clean_theorem_environment_wrappers(text)
    text = strip_artifact_lines(text)
    text = RE_MULTI_BLANK.sub("\n\n", text)
    text = strip_trailing_spaces(text)
    text = normalize_fallback_markup(text)
    text = normalize_surviving_latex_structure(text)
    text = normalize_math_identifier_spacing(text)
    text = restore_inline_verbatim_blocks(text)
    text = restore_verbatim_blocks(text)
    text = normalize_tex_display_blocks(text)
    text = normalize_orphan_display_math_wrappers(text)
    text = normalize_single_column_array_displays(text)
    text = strip_verbatim_sentinels(text)
    text = normalize_surviving_latex_structure(text)
    text = normalize_math_identifier_spacing(text)
    text = normalize_markdown_code_fences(text)
    text = clean_fenced_latex_scaffolding(text)
    text = clean_fenced_code_math_leakage(text)
    return text

def postprocess_final(text: str) -> str:
    text = reflow_paragraphs(text.strip())
    text = merge_soft_wrapped_blocks(text)
    text = unwrap_formatting_argument_commands(text)
    text = normalize_tex_display_blocks(text)
    text = normalize_orphan_display_math_wrappers(text)
    text = normalize_single_column_array_displays(text)
    text = unwrap_formatting_argument_commands(text)
    text = normalize_math_identifier_spacing(text)
    text = normalize_orphan_escaped_brackets(text)
    text = normalize_flattened_table_artifacts(text)
    text = normalize_accidental_hash_headings(text)
    text = normalize_markdown_code_fences(text)
    text = clean_fenced_latex_scaffolding(text)
    text = clean_fenced_code_math_leakage(text)
    text = restore_protected_sentinels(text)
    text = clean_fenced_latex_scaffolding(text)
    return clean_fenced_code_math_leakage(text)

def normalize_pydetex_math_commands(text: str) -> str:
    """Undo PyDetex subscript-spelled TeX command names."""
    for bad, good in PYDETEX_MATH_COMMANDS.items():
        text = text.replace(bad, good)
    return text

def normalize_flattened_table_artifacts(text: str) -> str:
    """Clean obvious tabular alignment leaks and collapsed row starts."""
    return "\n".join(normalize_flattened_table_line(line) for line in text.splitlines())

def normalize_raw_figure_wrappers(text: str) -> str:
    """Strip raw figure wrappers once the useful placeholder/caption is present."""
    return RE_RAW_FIGURE_WRAPPER.sub(raw_figure_replacement, text)

def normalize_raw_table_wrappers(text: str) -> str:
    """Strip raw table wrappers while preserving table body and caption."""
    text = RE_RAW_TABLE_WRAPPER.sub(raw_table_replacement, text)
    text = re.sub(r"\\begin\s*\{\s*table\*?\s*\}(?:\[[^\]\n]*\])?", "\n", text, flags=re.IGNORECASE)
    return re.sub(r"\\end\s*\{\s*table\*?\s*\}", "\n", text, flags=re.IGNORECASE)

def normalize_raw_custom_display_wrappers(text: str) -> str:
    """Clean custom display wrappers used for query/result examples."""
    text = RE_RAW_RESULTS_BLOCK.sub(lambda match: "\n\nResults:\n" + clean_custom_results_body(match.group(1)) + "\n", text)
    text = replace_balanced_caption_commands(text)
    replacements = {
        r"\\begin\{query\}": "\n\nQuery:\n",
        r"\\end\{query\}": "\n",
        r"\\begin\{dpy\}": "\n",
        r"\\end\{dpy\}": "\n",
        r"\\begin\{dpycol\}": "\n",
        r"\\end\{dpycol\}": "\n",
    }
    for old, new in replacements.items():
        text = re.sub(old, new, text, flags=re.IGNORECASE)
    return re.sub(r"\\begin\{results\}(?:\{[^{}\n]*\})?", "\n\nResults:\n", text, flags=re.IGNORECASE).replace(r"\end{results}", "\n")

def clean_custom_results_body(body: str) -> str:
    """Clean custom query-result rows without dropping cell values."""
    body = re.sub(r"\\(?:hline|cline)(?:\{[^{}\n]*\})?", "\n", body, flags=re.IGNORECASE)
    body = re.sub(r"\\\\(?:\[[^\]\n]*\])?", "\n", body)
    body = body.replace("&", " | ")
    body = re.sub(r"[ \t]+", " ", body)
    lines = [line.strip(" |") for line in body.splitlines()]
    return "\n".join(line for line in lines if line).strip()

def replace_balanced_caption_commands(text: str) -> str:
    """Render surviving balanced captions as readable text."""
    while True:
        match = RE_CAPTION_COMMAND.search(text)
        if not match:
            return text
        close = find_matching_brace(text, match.end() - 1)
        if close == -1:
            text = text[:match.start()] + "Caption: " + text[match.end():]
            continue
        caption = clean_linguistic_text(text[match.end():close])
        replacement = f"\n\nCaption: {caption}\n\n" if caption else "\n\n"
        text = text[:match.start()] + replacement + text[close + 1:]

def normalize_raw_center_wrappers(text: str) -> str:
    """Remove centering wrappers while preserving formulas/examples inside."""
    text = unwrap_centerline_commands(text)
    previous = None
    while previous != text:
        previous = text
        text = RE_RAW_CENTER_WRAPPER.sub(lambda match: "\n\n" + match.group(1).strip() + "\n\n", text)
    text = re.sub(r"\\(?:begin|end)\{center\}", "", text, flags=re.IGNORECASE)
    return text.replace(r"\begincenter", "").replace(r"\endcenter", "")

def unwrap_centerline_commands(text: str) -> str:
    """Remove old centerline wrappers while preserving their content."""
    for match in reversed(list(RE_CENTERLINE_COMMAND.finditer(text))):
        close = find_matching_brace(text, match.end() - 1)
        if close == -1:
            continue
        body = text[match.end():close].strip()
        text = text[:match.start()] + f"\n\n{body}\n\n" + text[close + 1:]
    return text

def raw_table_replacement(match: re.Match) -> str:
    """Keep table evidence while removing float/layout wrappers."""
    body = match.group(1)
    caption = extract_latex_caption(body)
    body = remove_latex_caption_commands(body)
    body = RE_LABEL_COMMAND.sub("", body)
    body = normalize_raw_center_wrappers(body)
    body = re.sub(r"\\begin\{minipage\}(?:\[[^\]\n]*\])?(?:\{[^{}\n]*\})?", "\n", body, flags=re.IGNORECASE)
    body = re.sub(r"\\end\{minipage\}", "\n", body, flags=re.IGNORECASE)
    body = re.sub(r"\\(?:centering|footnotesize|scriptsize|small|normalsize)\b", " ", body)
    body = re.sub(r"\\(?:vspace|hspace)\*?\s*\{[^{}\n]*\}", " ", body)
    body = re.sub(r"\\multicolumn\s*\{[^{}\n]*\}\s*\{[^{}\n]*\}\s*\{([^{}\n]*)\}", r"\1", body)
    body = re.sub(r"\\(?:hline|cline|toprule|midrule|bottomrule)(?:\{[^{}\n]*\})?", "\n", body, flags=re.IGNORECASE)
    body = body.replace(r"\fbox", "")
    body = "\n".join(line.strip() for line in body.splitlines() if line.strip() and line.strip() not in {"{", "}"})
    parts = [body]
    if caption:
        parts.append(f"Table: {caption}")
    return "\n\n" + "\n".join(part for part in parts if part).strip() + "\n\n"

def raw_figure_replacement(match: re.Match) -> str:
    """Keep figure placeholders and captions while removing LaTeX wrappers."""
    body = RE_RAW_CENTER_WRAPPER.sub(lambda center: center.group(1), match.group(1))
    caption = extract_latex_caption(body)
    body = remove_latex_caption_commands(body)
    body = RE_LABEL_COMMAND.sub("", body)
    body = normalize_graphics_commands(body)
    body = re.sub(r"\\(?:begin|end)\{center\}", "", body, flags=re.IGNORECASE)
    body = "\n".join(line.strip() for line in body.splitlines() if line.strip())
    parts = [body]
    if caption:
        parts.append(f"Figure: {caption}")
    return "\n\n" + "\n".join(part for part in parts if part).strip() + "\n\n"

def normalize_accidental_hash_headings(text: str) -> str:
    """Escape example/table lines that Markdown would misread as headings."""
    output = []
    for line in text.splitlines():
        match = RE_SUSPICIOUS_HASH_HEADING.match(line)
        if match:
            output.append(f"\\# {match.group(2)}")
        else:
            output.append(line)
    return "\n".join(output)

def clean_stripped_fallback_placeholders(text: str) -> str:
    """Remove fallback sentinels whose leading marker was stripped by a converter."""
    text = RE_LOSSY_FALLBACK_PLACEHOLDER.sub("", text)
    text = RE_STRIPPED_FALLBACK_PLACEHOLDER.sub("", text)
    return re.sub(r" {2,}", " ", text)

def restore_protected_sentinels(text: str) -> str:
    """Decode protected verbatim sentinels that bypassed marker restoration."""
    return (
        text.replace(BACKSLASH_SENTINEL, "\\")
        .replace(PERCENT_SENTINEL, "%")
        .replace(NEWLINE_SENTINEL, "\n")
    )

def normalize_flattened_table_line(line: str) -> str:
    """Normalize one table-like line without changing ordinary prose."""
    if RE_TABLE_ALIGNMENT_ONLY_LINE.match(line):
        return ""
    line = re.sub(r"(\bTable\s+\d)\s+[clrld]{3,}\s+(?=\S+\s*&)", r"\1 ", line)
    if " & " not in line and not re.search(r"\b[clrld]{3,}\s*&", line):
        return line
    line = re.sub(r"\b[clrld]{3,}\s*&\s*", "", line)
    line = re.sub(r"^\s*[clrld]{3,}\s+(?=\S+\s*&)", "", line)
    row_start = r"(?:d\([^)\n]{1,90}\)|E\$_\{\\mathrm|[A-Z][A-Za-z0-9/+*.-]{1,24}\s*&)"
    line = re.sub(rf"(?<=\d)\s+(?={row_start})", "\n", line)
    line = re.sub(rf"(?<=\))\s+(?={row_start})", "\n", line)
    line = re.sub(r"(?<=[A-Za-z])\s+(?=d\()", "\n", line)
    return line

def unwrap_formatting_argument_commands(text: str) -> str:
    """Drop formatting-only wrappers while preserving their text/math body."""
    text = RE_XSPACE_COMMAND.sub(" ", text)
    text = RE_ESCAPED_ENSUREMATH_COMMAND.sub(lambda match: clean_escaped_ensuremath_body(match.group(1)), text)
    previous = None
    while previous != text:
        previous = text
        text = unwrap_argument_command_pattern(text, RE_FORMATTING_ARGUMENT_COMMAND, block=False)
    return text

def clean_escaped_ensuremath_body(body: str) -> str:
    """Clean malformed ensuremath bodies closed as escaped braces."""
    body = body.replace(r"\ ", " ")
    body = re.sub(r"\\(?=[`',;:.])", "", body)
    return body.strip()

def normalize_markdown_display_blocks(text: str) -> str:
    """Clean display-math internals without touching inline prose math."""
    return RE_MARKDOWN_DISPLAY_BLOCK.sub(
        lambda match: "$$" + normalize_inner_display_delimiters(match.group(1)) + "$$",
        text,
    )

def normalize_orphan_display_math_wrappers(text: str) -> str:
    """Remove stray inline dollar wrappers around restored display math."""
    return RE_ORPHAN_WRAPPED_DISPLAY_MATH.sub(lambda match: match.group(1), text)

def normalize_single_column_array_displays(text: str) -> str:
    """Simplify one-column display arrays while preserving line breaks."""
    return RE_SINGLE_COLUMN_ARRAY_DISPLAY.sub(single_column_array_display_replacement, text)

def single_column_array_display_replacement(match: re.Match) -> str:
    """Render a ``{c}`` array display as plain multiline display math."""
    body = match.group(1).strip()
    lines = [clean_single_column_array_line(line) for line in re.split(r"\\\\", body)]
    lines = [line for line in lines if line]
    return "\n\n$$\n" + "\n".join(lines) + "\n$$\n\n" if lines else ""

def clean_single_column_array_line(line: str) -> str:
    """Clean one line from a single-column array without erasing math."""
    line = unwrap_formatting_argument_commands(line.strip())
    line = line.replace(r"\:", " ")
    line = line.replace(r"\;", " ")
    line = line.replace(r"\!", "")
    line = re.sub(r"\s+", " ", line)
    return line.strip()

def normalize_tex_display_blocks(text: str) -> str:
    """Convert surviving TeX display delimiters into Markdown display math."""
    text = RE_TEX_DISPLAY_SPACING_COMMAND.sub("", text)
    text = text.replace("$$}", "$$")

    def replacement(match: re.Match) -> str:
        body = normalize_inner_display_delimiters(match.group(1).strip())
        return f"\n\n$$\n{body}\n$$\n\n" if body else ""

    return RE_TEX_DISPLAY_MATH_BLOCK.sub(replacement, text)

def normalize_orphan_escaped_brackets(text: str) -> str:
    """Turn leftover display delimiters into literal brackets."""
    return text.replace(r"\[", "[").replace(r"\]", "]")

def clean_fenced_code_math_leakage(text: str) -> str:
    """Remove display-math wrapper leakage from preserved text examples."""
    def replacement(match: re.Match) -> str:
        block = match.group(0)
        if "$$" not in block and r"\]" not in block and r"\[" not in block:
            return block
        block = re.sub(r"(?m)^\s*\$\$\s*$", "", block)
        block = block.replace(r"\[", "[").replace(r"\]", "]")
        return RE_MULTI_BLANK.sub("\n\n", block)

    return RE_FENCED_CODE_BLOCK.sub(replacement, text)

def clean_fenced_latex_scaffolding(text: str) -> str:
    """Remove LaTeX drawing/layout scaffolding inside preserved figure blocks."""
    return RE_FENCED_CODE_BLOCK.sub(clean_one_fenced_latex_block, text)

def clean_one_fenced_latex_block(match: re.Match) -> str:
    """Clean one fenced block while preserving its evidence text."""
    block = match.group(0)
    if not any(token in block for token in (
        r"\begincenter", r"\endcenter", r"\setlength", r"\begingroup",
        r"\psfig", r"\epsfig", r"\epsfbox", r"\epsffile",
        r"\includegraphics", r"\pstree", r"\beginavm", r"\input",
        r"\hline", r"\multicolumn", r"\noalign", r"\hrule",
        r"\futurelet", r"\caption", r"\rule", r"\hfill",
        r"\hspace", r"\vspace", r"\newcommand",
        "PSTree:", "AVM span:",
    )):
        return block
    block = clean_fenced_caption_blocks(block)
    lines = block.splitlines()
    if len(lines) <= 2:
        return block
    cleaned = [lines[0]]
    for line in lines[1:-1]:
        normalized = clean_fenced_latex_line(line)
        if normalized is None:
            continue
        cleaned.append(normalized)
    cleaned.append(lines[-1])
    return "\n".join(cleaned)

def clean_fenced_caption_blocks(block: str) -> str:
    """Normalize multiline caption commands before line-oriented cleanup."""
    return re.sub(
        r"\\caption\[([^\]]{1,300})\]\s*",
        lambda match: f"Caption: {clean_linguistic_text(match.group(1))}. ",
        block,
        flags=re.DOTALL,
    )

def clean_fenced_latex_line(line: str) -> str | None:
    """Clean one line inside a preserved fenced figure/code block."""
    stripped = line.strip()
    if not stripped:
        return line
    if stripped in {r"\\", "\\"}:
        return None
    drop_prefixes = (
        r"\begincenter", r"\endcenter", r"\nopagebreak", r"\begingroup",
        r"\endgroup", r"\makeatletter", r"\makeatother",
    )
    if stripped.startswith(drop_prefixes):
        return None
    if re.match(r"\\(?:setlength|renewcommand|gdef|reset@font|fontfamily|fontseries|fontshape|fontsize|selectfont|ifx|fi|sbox|newsavebox)\b", stripped):
        return None
    if (
        re.match(r"\\(?:e?psfig(?:file)?|epsfbox|epsffile|includegraphics)\b|\\psfig(?=\S)|\\input\S+\.(?:ps|eps|eepic|pstex|fig|pdf|png|jpg|jpeg)", stripped)
        or re.search(r"\\(?:hbox)?\\?(?:e?psfig|psfig|epsfbox|epsffile|includegraphics)\b", stripped)
    ):
        placeholder = figure_placeholder_from_fenced_line(stripped)
        if placeholder:
            return placeholder
        cleaned = re.sub(r"\\hbox\s*\\?(?:e?psfig|psfig|epsfbox|epsffile|includegraphics)\b", "", line)
        cleaned = re.sub(
            r"\\(?:e?psfig|psfig|epsfbox|epsffile|includegraphics)\b"
            r"(?:\s*\[[^\]\n]*\])?(?:\s*\{[^{}\n]*\}|[A-Za-z0-9_./:-]+\.(?:ps|eps|pdf|png|jpg|jpeg))?",
            "",
            cleaned,
        )
        if not cleaned.strip() or r"\raisebox" in stripped:
            return None
        return cleaned.strip()
    line = line.replace(r"\pstree", "PSTree:")
    line = line.replace(r"\Tr", "Tree node:")
    line = re.sub(r"\\beginavm\\?", "AVM:", line)
    line = line.replace(r"\endavm", "")
    line = line.replace(r"\avmspan", "AVM span:")
    line = clean_fenced_caption_text(line)
    if line is None:
        return None
    line = clean_fenced_layout_text(line)
    if line is None:
        return None
    line = clean_fenced_table_text(line)
    if line is None:
        return None
    line = clean_fenced_tree_avm_text(line)
    return line

def clean_fenced_caption_text(line: str) -> str | None:
    """Render caption commands inside preserved evidence blocks."""
    if r"\caption" not in line:
        return line
    line = re.sub(
        r"\\caption(?:\[[^\]\n]*\])?\s*\{([^{}\n]*)\}",
        lambda match: f"Caption: {clean_linguistic_text(match.group(1))}",
        line,
    )
    line = re.sub(r"\\caption(?:\[[^\]\n]*\])?\s*", "Caption: ", line)
    line = re.sub(r"[ \t]+", " ", line).strip()
    return line or None

def clean_fenced_layout_text(line: str) -> str | None:
    """Remove drawing-only layout commands inside preserved evidence blocks."""
    if not any(token in line for token in (r"\rule", r"\hfill", r"\hspace", r"\vspace", r"\newcommand")):
        return line
    line = re.sub(r"\\newcommand\\[A-Za-z]+\s*", " ", line)
    line = re.sub(r"\\rule(\[ref:[^\]\n]+\])", r"\1", line)
    line = re.sub(r"\\(?:hfill|vfill)\b", " ", line)
    line = re.sub(r"\\[hv]space\*?(?:\s*\{[^{}\n]*\}|\\?\*?[-.\w]+)?", " ", line)
    line = re.sub(r"\\rule(?:\[[^\]\n]*\])?(?:\{[^{}\n]*\}){2}", " ", line)
    dimension = r"[-+]?\d*(?:\.\d+)?\s*(?:ex|em|pt|cm|mm|in)"
    rule_body = rf"(?:\\?[A-Za-z]+|{dimension})\s*{dimension}([A-Za-z0-9_()]+)?"
    line = re.sub(rf"\\rule(?:\[[^\]\n]*\])?{rule_body}", lambda match: f" {match.group(1) or ''} ", line)
    line = re.sub(rf"(?<!\\)\brule(?:\[[^\]\n]*\])?{rule_body}", lambda match: f" {match.group(1) or ''} ", line)
    line = re.sub(r"[ \t]+", " ", line).strip()
    return line or None

def clean_fenced_table_text(line: str) -> str | None:
    """Clean table layout commands inside preserved evidence blocks."""
    if not any(token in line for token in (
        r"\hline", "hline", r"\multicolumn", r"\cline", r"\sc",
        r"\bf", r"\em", r"\noalign", r"\hrule", r"\futurelet",
    )):
        return line
    line = re.sub(r"\\noalign\\ifnum0=`\\fi", " ", line)
    line = re.sub(r"\\(?:hrule|arrayrulewidth|futurelet|@height|@xhline|@tempa)\b", " ", line)
    line = re.sub(r"\\hline\b|(?<!\\)\bhline\b|\\cline\s*\{[^{}\n]*\}", " ", line)
    line = re.sub(
        r"\\multicolumn\s*\{?\d+\}?\s*\{[^{}\n]*\}\s*\{([^{}\n]*)\}",
        r"\1",
        line,
    )
    line = re.sub(
        r"\\multicolumn\s*\d+\s*[lcr|@{} ]+\s*(?:\\(?:em|bf|sc)\s*)?([^\\\n]+)",
        r"\1",
        line,
    )
    line = re.sub(r"\\(?:sc|bf|em|it|rm|sf)\b", " ", line)
    line = line.replace(r"\ ", " ")
    line = re.sub(r"[ \t]+", " ", line).strip()
    return line or None

def clean_fenced_tree_avm_text(line: str) -> str:
    """Make preserved PSTree/AVM figure text scannable without rendering it."""
    if not any(marker in line for marker in ("PSTree:", "Tree node:", "AVM:", "AVM span:")):
        return line
    line = re.sub(r"(?<!^)(PSTree:|Tree node:|AVM:|AVM span:)", r"\n\1", line)
    line = re.sub(r"\[levelsep=[^\]\n]*\]", "", line)
    line = re.sub(r"\[ref=[^\]\n]*\]", "", line)
    line = re.sub(r"\\mathit\s+([A-Za-z]+)", r"\1", line)
    line = re.sub(r"\\(?:mathit|em)\s*\{([^{}]*)\}", r"\1", line)
    line = re.sub(r"\\em\b", "", line)
    line = line.replace(r"\wedge", "and")
    line = line.replace(r"\vee", "or")
    line = line.replace(r"\@", "@")
    line = line.replace(r"\<", "<").replace(r"\>", ">")
    line = line.replace("{", " ").replace("}", " ")
    line = line.replace("AVM span:", "AVM span: ")
    line = re.sub(r"[ \t]+", " ", line)
    line = re.sub(r" *\n *", "\n", line)
    return line.strip()

def figure_placeholder_from_fenced_line(line: str) -> str | None:
    """Convert fenced graphics/include commands into concise placeholders."""
    match = re.search(
        r"(?:file=|\\(?:e?psfig(?:file)?|epsfbox|epsffile|input|includegraphics)"
        r"(?:\s*\[[^\]\n]*\])?\s*\{?)"
        r"([A-Za-z0-9_./:-]+\.(?:ps|eps|eepic|pstex|fig|pdf|png|jpg|jpeg))",
        line,
    )
    if not match:
        match = re.search(r"\\input([A-Za-z0-9_./:-]+\.(?:ps|eps|eepic|pstex|fig|pdf|png|jpg|jpeg))", line)
    if not match:
        return None
    return f"[Figure omitted: {match.group(1)}]"

def restore_inline_verbatim_blocks(text: str) -> str:
    """Restore protected code markers even if a converter inlined them."""
    if VERBATIM_BEGIN not in text:
        return text
    return RE_INLINE_VERBATIM_BLOCK.sub(lambda match: inline_code_block(match.group(1)), text)

def inline_code_block(content: str) -> str:
    """Decode one inline protected verbatim block into a fenced block."""
    content = (
        content.replace(BACKSLASH_SENTINEL, "\\")
        .replace(PERCENT_SENTINEL, "%")
        .replace(NEWLINE_SENTINEL, "\n")
        .strip()
    )
    return f"\n\n```text\n{content}\n```\n\n" if content else ""

def clean_math_source_leakage(text: str) -> str:
    """Remove TeX diagnostics/wrappers that survive inside converted math."""
    text = RE_TEX_ERROR_MESSAGE.sub("", text)
    text = RE_BBB_ERROR_PREFIX.sub(r"\\mathbb", text)
    text = RE_MATH_ENV_WRAPPER.sub("", text)
    text = RE_LATEX_INTERNAL_CITE.sub(lambda match: f"[@{match.group(1)}]", text)
    text = RE_AT_INTERNAL_CITE.sub(lambda match: f"[@{match.group(1)}]", text)
    text = RE_CITE_COMMAND.sub(lambda match: f"[{match.group(1) or match.group(2)}]", text)
    text = RE_GENERIC_REF_TAG.sub(lambda match: f"[ref:{match.group(1)}]" if match.group(1) else "[ref]", text)
    text = RE_GENERIC_CIT_TAG.sub("[citation]", text)
    text = RE_ITEM_COMMAND.sub("\n- ", text)
    text = RE_MATHRM_WORD_COMMAND.sub(lambda match: match.group(1), text)
    text = RE_TEX_SPACING_COMMAND.sub(" ", text)
    return RE_MATH_LABEL_COMMAND.sub("", text)

def strip_artifact_lines(text: str) -> str:
    """Drop standalone style tokens and coalesce picture-coordinate dumps."""
    output = []
    in_coordinate_dump = False
    for line in text.splitlines():
        if RE_STYLE_TOKEN_LINE.match(line):
            continue
        if is_picture_coordinate_line(line) or is_drawing_artifact_line(line):
            if not in_coordinate_dump:
                output.append("[Figure omitted: coordinate drawing]")
                in_coordinate_dump = True
            continue
        in_coordinate_dump = False
        output.append(line)
    return "\n".join(output)

def is_drawing_artifact_line(line: str) -> bool:
    """Detect raw drawing-program lines from figures."""
    stripped = line.strip()
    if not stripped:
        return False
    drawing_tokens = (
        "/Ellipse", "/Ligne", "/Arrow", " gsave ", " setgray",
        "\\setplotarea", "\\axis ", "\\!ifnextchar", "\\plot ",
        "\\setbox\\!picbox", "\\beginpicture", "\\endpicture",
    )
    return any(token in stripped for token in drawing_tokens)

def is_picture_coordinate_line(line: str) -> bool:
    """Detect lines that are mostly LaTeX picture coordinate/font dumps."""
    stripped = line.strip()
    if not stripped:
        return False
    coords = len(RE_PICTURE_COORD.findall(stripped))
    if coords >= 3:
        return True
    if coords >= 2 and is_mostly_picture_coordinates(stripped):
        return True
    if coords >= 1:
        picture_tokens = ["[lb]", "[rb]", "[lt]", "[rt]", "[b]", "[t]", "cmr", "rm", "<span", "</span>"]
        if coords >= 2 and any(token in stripped for token in picture_tokens):
            return True
    if coords >= 1 and len(stripped) > 80:
        return any(token in stripped for token in picture_tokens)
    return False

def is_mostly_picture_coordinates(line: str) -> bool:
    """Return true when non-coordinate residue is diagram syntax, not prose."""
    residue = RE_PICTURE_COORD.sub(" ", line)
    residue = re.sub(r"[-+*/=<>|()[\]{}.,:;_^\\\d\s]+", " ", residue)
    words = re.findall(r"[A-Za-z]{4,}", residue)
    if len(words) >= 3:
        return False
    return len(residue.strip()) <= max(20, len(line) // 3)

def normalize_fallback_markup(text: str) -> str:
    """Promote fallback converter section/paragraph markers to Markdown."""
    return "\n".join(normalize_fallback_line(line) for line in text.splitlines())

def normalize_surviving_latex_structure(text: str) -> str:
    """Convert raw structural LaTeX left by fallback converters."""
    text = normalize_raw_section_commands(text)
    text = normalize_manual_numbered_headings(text)
    text = normalize_report_style_headings(text)
    text = normalize_quantum_gate_macros(text)
    text = normalize_quantum_circuit_arrays(text)
    text = normalize_surviving_semantic_macros(text)
    text = normalize_recovered_theory_names(text)
    text = normalize_xy_matrix_macros(text)
    text = normalize_raw_graphics_scaffolding(text)
    text = normalize_raw_feature_structure_envs(text)
    text = normalize_procedure_labels(text)
    text = normalize_collapsed_tag_bullets(text)
    text = normalize_inline_numbered_lists(text)
    text = normalize_raw_list_and_bibliography_wrappers(text)
    text = normalize_raw_layout_commands(text)
    text = RE_LABEL_COMMAND.sub("", text)
    text = RE_COUNTER_COMMAND.sub("", text)
    text = RE_RAW_BEGIN_EXAMPLE_ENV.sub("\n\nExample:\n", text)
    text = RE_RAW_END_EXAMPLE_ENV.sub("\n", text)
    text = RE_RAW_PANDOC_SPAN_LIST_ENV.sub("\n", text)
    text = RE_RAW_OLD_LIST_ENV.sub("\n", text)
    text = RE_RAW_BEGIN_LIST_ENV.sub("\n", text)
    text = RE_RAW_END_LIST_ENV.sub("\n", text)
    text = RE_ITEM_ESCAPED_LABEL_COMMAND.sub(lambda match: f"\n- {clean_linguistic_text(match.group(1))}: ", text)
    text = RE_ITEM_LABEL_COMMAND.sub(lambda match: f"\n- {clean_linguistic_text(match.group(1))}: ", text)
    text = RE_ITEM_COMMAND.sub("\n- ", text)
    text = RE_CITE_FAMILY_COMMAND.sub(lambda match: markdown_citation(match.group(1)), text)
    text = RE_REF_FAMILY_COMMAND.sub(lambda match: markdown_reference(match.group(1)), text)
    return text

def normalize_quantum_gate_macros(text: str) -> str:
    """Render old local quantum-circuit picture macros as readable labels."""
    for name, label in QUANTUM_GATE_MACROS.items():
        text = re.sub(rf"\\{name}(?![A-Za-z])", f"[Quantum gate: {label}]", text)
    return text

def normalize_quantum_circuit_arrays(text: str) -> str:
    """Collapse display arrays made only of quantum gate labels."""
    return RE_QUANTUM_CIRCUIT_ARRAY_BLOCK.sub(quantum_circuit_array_replacement, text)

def quantum_circuit_array_replacement(match: re.Match) -> str:
    """Render a gate-only array as a concise circuit placeholder."""
    body = match.group(1)
    labels = re.findall(r"\[Quantum gate: ([^\]\n]+)\]", body)
    if not labels:
        return match.group(0)
    residue = re.sub(r"\[Quantum gate: [^\]\n]+\]", " ", body)
    residue = re.sub(r"\\+|[{}[\]().,;:\s]", " ", residue)
    if residue.strip():
        return match.group(0)
    return "\n\n[Quantum circuit: " + "; ".join(labels) + "]\n\n"

def normalize_math_identifier_spacing(text: str) -> str:
    """Repair fallback output that glues prose words to math identifiers."""
    return apply_outside_fenced_code(text, normalize_math_identifier_spacing_part)

def normalize_math_identifier_spacing_part(text: str) -> str:
    """Apply conservative prose/math spacing repairs to normal text."""
    prefix_pattern = "|".join(re.escape(prefix) for prefix in sorted(MATH_TEXT_PREFIXES, key=len, reverse=True))
    suffix_pattern = "|".join(re.escape(suffix) for suffix in sorted(MATH_TEXT_SUFFIXES, key=len, reverse=True))
    text = re.sub(
        rf"\b({prefix_pattern})({MATH_IDENTIFIER_TOKEN})((?:{suffix_pattern})\b|[∈=,.;:)\\[→≤≥<>^]|\s)",
        lambda match: f"{match.group(1)} {match.group(2)}{math_spacing_delimiter(match.group(3))}",
        text,
    )
    short_prefix_pattern = "|".join(
        re.escape(prefix) for prefix in sorted(MATH_SHORT_VARIABLE_PREFIXES, key=len, reverse=True)
    )
    text = re.sub(
        rf"\b({short_prefix_pattern})({MATH_SHORT_VARIABLE_TOKEN})((?:{suffix_pattern})\b|[∈=,.;:)\\[→≤≥<>^]|\s)",
        lambda match: f"{match.group(1)} {match.group(2)}{math_spacing_delimiter(match.group(3))}",
        text,
    )
    text = re.sub(r"(?<=[a-z])(?=[ℓℒℤℝℂΠ])", " ", text)
    text = re.sub(
        rf"\b({MATH_IDENTIFIER_TOKEN})((?:{suffix_pattern})\b)",
        lambda match: f"{match.group(1)} {match.group(2)}",
        text,
    )
    text = re.sub(r"(?<=[)∞ℤℝℂ])(?=(?:and|are|be|has|is|of|tend|tends|the|to|with)\b)", " ", text)
    return text

def math_spacing_delimiter(delimiter: str) -> str:
    """Keep word suffixes separated while leaving punctuation tight."""
    if delimiter.isspace():
        return delimiter
    if re.match(r"[A-Za-z]", delimiter):
        return " " + delimiter
    return delimiter

def apply_outside_fenced_code(text: str, transform) -> str:
    """Apply a transform without touching Markdown fenced code blocks."""
    output = []
    last = 0
    for match in RE_FENCED_CODE_BLOCK.finditer(text):
        output.append(transform(text[last:match.start()]))
        output.append(match.group(0))
        last = match.end()
    output.append(transform(text[last:]))
    return "".join(output)

def normalize_recovered_theory_names(text: str) -> str:
    """Clean wording around recovered theory/system-name macros."""
    return re.sub(r"\bwe\s+to\s+introduce\s+Dachs\b", "we introduce Dachs", text)

def normalize_raw_graphics_scaffolding(text: str) -> str:
    """Replace raw external-graphics scaffolding that escaped figure cleanup."""
    text = re.sub(
        r"\\psset[^\n.]{0,240}\\pstree(?:\[[^\]\n]*\])?\.?",
        " [Tree diagram omitted]. ",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(r"\\pstree(?:\[[^\]\n]*\])?\.?", "[Tree diagram omitted].", text, flags=re.IGNORECASE)
    text = re.sub(
        r"\\begincenter\s*\\(?:e?psfigfile)\s*=\s*([A-Za-z0-9_./:-]+\.(?:ps|eps|pdf|png|jpg|jpeg))[^\n]*\s*\\endcenter",
        lambda match: f"\n\n[Figure omitted: {match.group(1)}]\n\n",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"\\(?:e?psfigfile)\s*=\s*([A-Za-z0-9_./:-]+\.(?:ps|eps|pdf|png|jpg|jpeg))[^\n]*",
        lambda match: f"[Figure omitted: {match.group(1)}]",
        text,
        flags=re.IGNORECASE,
    )
    return text.replace(r"\begincenter", "").replace(r"\endcenter", "")

def normalize_raw_list_and_bibliography_wrappers(text: str) -> str:
    """Remove raw list/bibliography wrappers after item contents survive."""
    text = drop_balanced_multiarg_command(text, r"\addcontentsline", 3)
    text = re.sub(r"\\(?:begin|end)\s*\{\s*(?:enumerate|itemize|description)\s*\}", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"\\begin\s*\{\s*thebibliography\s*\}\s*\{[^{}\n]*\}", "\n\n# References\n\n", text, flags=re.IGNORECASE)
    text = re.sub(r"\\end\s*\{\s*thebibliography\s*\}", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\\bibitem\s*(?:\[[^\]\n]*\])?\s*\{([^{}\n]*)\}", lambda match: f"\n- [{match.group(1)}] ", text)
    text = re.sub(r"\\newblock\b", " ", text)
    return text

def normalize_raw_layout_commands(text: str) -> str:
    """Drop layout commands that survive outside useful math/source."""
    text = re.sub(r"\\(?:begin|end)\s*\{\s*flush(?:right|left)\s*\}", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"\\begin\s*\{\s*minipage\s*\}(?:\[[^\]\n]*\])?\s*\{[^{}\n]*\}", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"\\end\s*\{\s*minipage\s*\}", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"\\noalign\s*\{[^{}\n]*\}", " ", text)
    text = re.sub(r"\\(?:vfill|vfil|protect|smallskip|medskip|bigskip)\b", " ", text)
    text = re.sub(r"\\(?:vspace|hspace)\*?\s*\{[^{}\n]*\}", " ", text)
    text = re.sub(r"\\rule\s*\{[^{}\n]*\}\s*\{[^{}\n]*\}", " ", text)
    text = re.sub(r"\\(?:vspace|hspace)\*?\s*[-.\d]+(?:ex|em|pt|cm|mm|in)", " ", text)
    text = re.sub(r"\\rule\s*(?:\\?[A-Za-z]+|[-.\d]+(?:ex|em|pt|cm|mm|in))\s*[-.]?\d*(?:\.\d+)?(?:ex|em|pt|cm|mm|in)", " ", text)
    text = re.sub(r"\bhspace\*?[-.]?\d+(?:\.\d+)?(?:ex|em|pt|cm|mm|in)\b", " ", text)
    return text

def drop_balanced_multiarg_command(text: str, command: str, arg_count: int) -> str:
    """Drop a command with balanced braced arguments."""
    pattern = re.compile(re.escape(command) + r"(?![A-Za-z])")
    for match in reversed(list(pattern.finditer(text))):
        parsed = read_braced_args(text, match.end(), arg_count)
        if parsed:
            _, end = parsed
            text = text[:match.start()] + " " + text[end:]
    return text

def normalize_manual_numbered_headings(text: str) -> str:
    """Promote old manual numbered headings embedded in fallback prose."""
    text = re.sub(
        r"(?<![#\n])\s+(\d+\.\s+[A-Z][A-Z0-9,;:() \-]{18,160})(?=\s+\d+\.\d+\.)",
        lambda match: f"\n\n# {match.group(1).strip()}\n\n",
        text,
    )
    return re.sub(
        r"(?<![#\n])\s+(\d+\.\d+\.\s+[^.\n]{5,120}\.)",
        lambda match: f"\n\n## {clean_fallback_heading(match.group(1))}\n\n",
        text,
    )

def normalize_report_style_headings(text: str) -> str:
    """Promote report-style PART/CHAPTER markers emitted by fallbacks."""
    text = re.sub(
        r"(?m)^\s*PART:\s+(.{1,120}?)\s+CHAPTER:\s+(.{1,120})\s*$",
        lambda match: f"\n\n# Part: {clean_fallback_heading(match.group(1))}\n\n# {clean_fallback_heading(match.group(2))}\n",
        text,
    )
    text = re.sub(
        r"(?m)^\s*PART:\s+(.{1,120})\s*$",
        lambda match: f"\n\n# Part: {clean_fallback_heading(match.group(1))}\n",
        text,
    )
    return re.sub(
        r"(?m)^\s*CHAPTER:\s+(.{1,120})\s*$",
        lambda match: f"\n\n# {clean_fallback_heading(match.group(1))}\n",
        text,
    )

def normalize_surviving_semantic_macros(text: str) -> str:
    """Render common formal macros that survive conversion."""
    text = replace_two_arg_macro(text, "elem", lambda args: f"{args[0]} in {args[1]}")
    text = replace_two_arg_macro(text, "tuple", lambda args: f"<{args[0]}, {args[1]}>")
    text = replace_one_arg_macro(text, "tuple", lambda arg: f"<{arg}>")
    text = replace_unbraced_one_arg_macro(text, "tuple", lambda arg: f"<{arg}>")
    text = replace_one_arg_macro(text, "Mean", lambda arg: f"Mean({arg})")
    text = replace_one_arg_macro(text, "BE", lambda arg: f"BE({arg})" if arg else "BE")
    text = replace_one_arg_macro(text, "SynR", lambda arg: f"SynR({arg})" if arg else "SynR")
    text = replace_one_arg_macro(text, "SemKats", lambda arg: f"SemKats({arg})" if arg else "SemKats")
    replacements = {
        r"\Ld": "L_D",
        r"\SAT": "models",
        r"\AND": "and",
        r"\OR": "or",
        r"\NOT": "not",
        r"\IMPL": "=>",
        r"\EQUV": "<=>",
        r"\DEF": ":=",
        r"\tupled": "tuple_d",
    }
    for old, new in replacements.items():
        text = re.sub(re.escape(old) + r"(?![A-Za-z])", new, text)
    text = re.sub(r"([⟩>])(?=(?:where|is|and|or)\b)", r"\1 ", text)
    text = re.sub(r"\\beginarray(?:\[[^\]\n]*\])?(?:\{?[^\\\n ]*)?", "\n", text)
    text = re.sub(r"\\endarray", "\n", text)
    return text

def normalize_xy_matrix_macros(text: str) -> str:
    """Render inline XY-pic matrices as explicit diagram placeholders."""
    pattern = re.compile(r"\\xymatrix(?:@[A-Za-z0-9]+)?\s*\{")
    for match in reversed(list(pattern.finditer(text))):
        close = find_matching_brace(text, match.end() - 1)
        if close == -1:
            continue
        body = " ".join(text[match.end():close].split())
        replacement = f"[XY matrix: {body}]" if body else "[XY matrix]"
        text = text[:match.start()] + replacement + text[close + 1:]
    return re.sub(r"\\xymatrix(?:@[A-Za-z0-9]+)?", "XY matrix:", text)

def normalize_procedure_labels(text: str) -> str:
    """Split collapsed algorithm/procedure labels into list items."""
    labels = (
        "Input", "Output", "Algorithm", "Prediction", "Reduction", "Factoring",
        "Lemma Table Lookup", "Subsumption", "Answer Lookup",
    )
    label_pattern = "|".join(re.escape(label) for label in labels)
    text = re.sub(rf"(?<!\n)(?:\\-\s*|\s+-\s*)({label_pattern}):", r"\n- \1:", text)
    return re.sub(rf"(?m)^\\-\s*({label_pattern}):", r"- \1:", text)

def normalize_inline_numbered_lists(text: str) -> str:
    """Split paragraphs that contain multiple inline numbered list markers."""
    paragraphs = text.split("\n\n")
    return "\n\n".join(split_inline_numbered_list_paragraph(part) for part in paragraphs)

def split_inline_numbered_list_paragraph(paragraph: str) -> str:
    """Split one paragraph only when it clearly contains a collapsed list."""
    markers = re.findall(r"(?:^|\s)([1-9]\d?\.)\s+(?=[A-Z])", paragraph)
    if len(markers) < 2:
        return paragraph
    return re.sub(r"\s+([1-9]\d?\.)\s+(?=[A-Z])", r"\n\1 ", paragraph)

def normalize_collapsed_tag_bullets(text: str) -> str:
    """Split long tagset paragraphs containing many ``- TAG:`` entries."""
    pattern = re.compile(r"\s+-\s+([A-Z][A-Z0-9]{1,12}:)")
    if len(pattern.findall(text)) < 20:
        return text
    return pattern.sub(lambda match: f"\n- {match.group(1)}", text)

def replace_one_arg_macro(text: str, name: str, render) -> str:
    """Replace balanced one-argument macro uses."""
    pattern = re.compile(rf"\\{re.escape(name)}(?![A-Za-z])\s*\{{")
    for match in reversed(list(pattern.finditer(text))):
        close = find_matching_brace(text, match.end() - 1)
        if close == -1:
            continue
        arg = text[match.end():close].strip()
        text = text[:match.start()] + render(arg) + text[close + 1:]
    return text

def replace_two_arg_macro(text: str, name: str, render) -> str:
    """Replace balanced two-argument macro uses."""
    pattern = re.compile(rf"\\{re.escape(name)}(?![A-Za-z])")
    for match in reversed(list(pattern.finditer(text))):
        parsed = read_braced_args(text, match.end(), 2)
        if not parsed:
            continue
        args, end = parsed
        text = text[:match.start()] + render([arg.strip() for arg in args]) + text[end:]
    return text

def replace_unbraced_one_arg_macro(text: str, name: str, render) -> str:
    r"""Replace simple unbraced semantic macro uses such as ``\tuple\cdots``."""
    pattern = re.compile(rf"\\{re.escape(name)}(?![A-Za-z])\s*(\\[A-Za-z]+|[A-Za-z0-9_.-]+)")
    for match in reversed(list(pattern.finditer(text))):
        text = text[:match.start()] + render(match.group(1).strip()) + text[match.end():]
    return text

def normalize_raw_feature_structure_envs(text: str) -> str:
    """Make surviving typed feature-structure wrappers readable."""
    def begin_replacement(match: re.Match) -> str:
        label = clean_linguistic_text(match.group(1) or "").strip()
        return f"[{label} " if label else "["

    def convert_part(part: str) -> str:
        part = re.sub(r"\\begin\{tfs\}(?:\{([^{}\n]*)\})?", begin_replacement, part, flags=re.IGNORECASE)
        part = re.sub(r"\\end\{tfs\}", "]", part, flags=re.IGNORECASE)
        return re.sub(
            r"\$\$\s*\\begin\{avm\}(.*?)\\end\{avm\}\s*\$\$",
            lambda match: fenced_avm_replacement(match.group(1)),
            part,
            flags=re.DOTALL | re.IGNORECASE,
        )

    return apply_outside_fenced_code(text, convert_part)

def fenced_avm_replacement(body: str) -> str:
    """Render a surviving AVM display as readable evidence text."""
    body = clean_avm_display_body(body)
    return f"\n\n```text\nAVM:\n{body}\n```\n\n" if body else ""

def clean_avm_display_body(body: str) -> str:
    """Clean AVM matrix notation without erasing feature/value content."""
    body = unwrap_formatting_argument_commands(body)
    replacements = {
        r"\avmspan": "AVM span:",
        r"\@": "@",
        r"\<": "<",
        r"\>": ">",
        r"\langle": "<",
        r"\rangle": ">",
        r"\wedge": "and",
        r"\vee": "or",
    }
    for old, new in replacements.items():
        body = body.replace(old, new)
    body = re.sub(r"\\(?:mathtt|mathit|mathrm|texttt|text)\s+([A-Za-z0-9_/-]+)", r"\1", body)
    body = re.sub(r"\\(?:mathtt|mathit|mathrm|texttt|text)\s*\{([^{}]*)\}", r"\1", body)
    body = re.sub(r"\$([^$\n]{1,120})\$", r"\1", body)
    body = body.replace("\\\\", "\n")
    body = re.sub(r"[{}]", " ", body)
    body = body.replace("&", " : ")
    body = re.sub(r"[ \t]+", " ", body)
    body = re.sub(r" *\n *", "\n", body)
    return "\n".join(line.strip() for line in body.splitlines() if line.strip())

def normalize_raw_section_commands(text: str) -> str:
    """Promote surviving balanced section commands to Markdown headings."""
    matches = list(RE_RAW_SECTION_COMMAND.finditer(text))
    for match in reversed(matches):
        close = find_matching_brace(text, match.end() - 1)
        if close == -1:
            continue
        raw_title = text[match.end():close]
        title = clean_source_title(raw_title) or clean_math_heading_title(raw_title)
        if not title:
            continue
        level = {
            "part": 1,
            "chapter": 1,
            "section": 1,
            "subsection": 2,
            "subsubsection": 3,
            "paragraph": 4,
        }.get(match.group(1).lower(), 2)
        heading = f"\n\n{'#' * level} {title}\n\n"
        text = text[:match.start()] + heading + text[close + 1:]
    return text

def clean_math_heading_title(title: str) -> str:
    """Keep math-only section titles instead of dropping the heading."""
    title = RE_MATH_LABEL_COMMAND.sub("", title)
    title = title.replace("$", "").replace("\\", "")
    title = title.replace("{", " ").replace("}", " ")
    return " ".join(title.split()).strip(" .")

def normalize_fallback_line(line: str) -> str:
    """Normalize one fallback-converted structural line."""
    section = RE_FALLBACK_SECTION_MARKER.match(line)
    if section:
        level = min(section.group(1).count("§"), 6)
        return f"{'#' * level} {clean_fallback_heading(section.group(2))}"
    paragraph = RE_FALLBACK_PARAGRAPH_MARKER.match(line)
    if paragraph:
        return f"### {clean_fallback_heading(paragraph.group(1))}"
    return line

def clean_fallback_heading(value: str) -> str:
    """Clean a fallback heading label without changing its meaning."""
    value = " ".join(value.strip(" .").split())
    return value[:1].upper() + value[1:] if value else value

def restore_verbatim_blocks(text: str) -> str:
    """Restore protected verbatim blocks as fenced code."""
    if VERBATIM_BEGIN not in text:
        return text
    return restore_verbatim_lines(text.splitlines())

def restore_verbatim_lines(lines: list[str]) -> str:
    """Restore protected verbatim markers line by line."""
    output, code, in_code = [], [], False
    for line in lines:
        if line.strip() == VERBATIM_BEGIN:
            in_code, code = True, []
        elif line.strip() == VERBATIM_END and in_code:
            output.extend(["```text", *restore_code_lines(code), "```"])
            in_code = False
        elif in_code:
            code.append(line)
        else:
            output.append(line)
    if in_code:
        output.extend(["```text", *restore_code_lines(code), "```"])
    return "\n".join(output)

def restore_code_lines(lines: list[str]) -> list[str]:
    """Decode protected backslashes inside a code block."""
    output = []
    for line in lines:
        decoded = line.replace(BACKSLASH_SENTINEL, "\\").replace(PERCENT_SENTINEL, "%")
        output.extend(decoded.split(NEWLINE_SENTINEL))
    return output

def normalize_markdown_code_fences(text: str) -> str:
    """Repair repeated or unterminated fenced text blocks."""
    output = []
    in_code = False
    for line in text.splitlines():
        stripped = line.strip()
        if in_code and re.match(r"#{1,6}\s+\S", stripped):
            output.extend(["```", ""])
            in_code = False
        if stripped.startswith("```"):
            if in_code and stripped != "```":
                output.extend(["```", ""])
                output.append(line)
                continue
            in_code = not in_code
        output.append(line)
    if in_code:
        output.append("```")
    return "\n".join(output)

def strip_verbatim_sentinels(text: str) -> str:
    """Remove protected-code markers left behind by lossy converters."""
    text = text.replace(VERBATIM_BEGIN, "")
    text = text.replace(VERBATIM_END, "")
    return text.replace(BACKSLASH_SENTINEL, "\\")

def strip_converted_front_matter(text: str) -> str:
    """Drop converted title/author/abstract blocks already in metadata."""
    text = RE_LEADING_ABSTRACT_SECTION.sub("", text)
    text = strip_leading_abstract_paragraph(text)
    match = RE_CONVERTED_SECTION_LINE.search(text[:5000])
    if not match or match.start() < 20:
        return text
    prefix = text[:match.start()]
    if looks_like_converted_front_matter(prefix) or looks_like_short_citation_prefix(prefix):
        return text[match.start():]
    return text

def looks_like_converted_front_matter(prefix: str) -> bool:
    """Detect title/author/affiliation blocks before the real body."""
    compact = normalize_for_search(prefix).lower()
    return len(prefix) < 3500 and any(hint in compact for hint in FRONT_MATTER_HINTS)

def looks_like_short_citation_prefix(prefix: str) -> bool:
    """Detect stray citation-key lists before the first section."""
    compact = " ".join(prefix.split())
    if len(compact) > 1200 or len(compact.split()) > 60:
        return False
    sentence_marks = compact.count(".") + compact.count("?") + compact.count("!")
    citationish = len(re.findall(r"[A-Za-z]+[-+][A-Za-z0-9]+|\w+:\d+", compact))
    return sentence_marks < 2 and citationish >= 2

def strip_leading_abstract_paragraph(text: str) -> str:
    """Remove converted title/abstract prose when no abstract env survived."""
    normalized = normalize_for_search(text[:3000]).lower()
    abstract_at = normalized.find("abstract.")
    if abstract_at == -1:
        abstract_at = normalized.find("\nabstract\n")
    if abstract_at == -1:
        return text
    next_para = text.find("\n\n", abstract_at)
    if next_para == -1 or next_para > 3500:
        return text
    if normalized[abstract_at:next_para].strip().rstrip(".") == "abstract":
        second_para = text.find("\n\n", next_para + 2)
        if second_para != -1 and second_para < 3500:
            return text[second_para + 2:]
    return text[next_para + 2:]

def strip_markdown_attributes(text: str) -> str:
    """Remove pandoc reference attributes without scanning every character."""
    if "{#" not in text:
        return text
    return "\n".join(strip_markdown_attribute_line(line) for line in text.splitlines())

def strip_markdown_attribute_line(line: str) -> str:
    """Remove a trailing Pandoc-style attribute from one line."""
    if "{#" not in line:
        return line
    return RE_MARKDOWN_ATTRIBUTE.sub("", line)

def strip_trailing_spaces(text: str) -> str:
    """Strip trailing horizontal whitespace without regex backtracking."""
    return "\n".join(line.rstrip(" \t") for line in text.splitlines())

def reflow_paragraphs(text: str) -> str:
    """Join converter-introduced hard wraps inside prose paragraphs."""
    return "\n\n".join(reflow_one_paragraph(part) for part in text.split("\n\n"))

def reflow_one_paragraph(paragraph: str) -> str:
    """Reflow a paragraph only when it looks like prose, not code or math."""
    lines = [line.strip() for line in paragraph.splitlines() if line.strip()]
    if len(lines) < 2 or not should_reflow_lines(lines):
        return paragraph.strip()
    return " ".join(lines)

def should_reflow_lines(lines: list[str]) -> bool:
    """Return true for ordinary prose lines wrapped by source formatting."""
    joined = " ".join(lines)
    if re.match(r"^(?:\d+\.|[A-Z]\.)\s+\S", lines[0].strip()):
        return False
    if any(is_structural_line(line) for line in lines):
        return False
    if len(re.findall(r"[A-Za-z]", joined)) < max(20, len(joined) // 5):
        return False
    codeish = sum(1 for line in lines if re.search(r"\b(?:In|Out)\[\d+\]|[/{}]{3,}|^\s*[A-Za-z0-9_.-]+\s*=", line))
    return codeish == 0

def is_structural_line(line: str) -> bool:
    """Identify lines that should keep their own Markdown/text layout."""
    stripped = line.strip()
    return (
        stripped.startswith(("#", "§", "-", "*", "+", ">", "|", "$", "\\", "```"))
        or stripped.endswith("\\")
    )

def merge_soft_wrapped_blocks(text: str) -> str:
    """Merge prose blocks split by blank lines at physical line breaks."""
    merged = []
    pending = []
    for block in text.split("\n\n"):
        if is_soft_wrap_block(block):
            pending.append(block.strip())
            if ends_sentence(block):
                flush_pending(merged, pending)
            continue
        flush_pending(merged, pending)
        merged.append(block.strip())
    flush_pending(merged, pending)
    return "\n\n".join(part for part in merged if part)

def is_soft_wrap_block(block: str) -> bool:
    """Identify one-line prose fragments caused by blank-line wrapping."""
    stripped = block.strip()
    if "\n" in stripped or is_structural_line(stripped):
        return False
    if re.match(r"^\s*(?:\d+\.){2,}\s+\S", stripped):
        return True
    if re.search(r"\b(?:In|Out)\[\d+\]|[/{}]{3,}|[=<>]{2,}", stripped):
        return False
    words = stripped.split()
    return 2 <= len(words) <= 18 and bool(re.search(r"[A-Za-z]{3}", stripped))

def ends_sentence(block: str) -> bool:
    """Detect when a soft-wrapped prose sentence/paragraph likely ends."""
    return block.strip().endswith((".", "?", "!", '."', '."', ".)", ".'"))

def flush_pending(merged: list[str], pending: list[str]) -> None:
    """Append pending soft-wrapped prose to merged output."""
    if pending:
        merged.append(" ".join(pending))
        pending.clear()

def normalize_for_search(text: str) -> str:
    """Normalize styled Unicode letters before keyword checks."""
    return unicodedata.normalize("NFKD", text)

def source_section_titles(tex: str) -> list[str]:
    """Extract source section titles with enough cleanup for coverage checks."""
    titles = []
    for match in re.finditer(r"\\(chapter|section|subsection|subsubsection)\*?\s*\{", tex):
        close = find_matching_brace(tex, match.end() - 1)
        if close == -1:
            continue
        title = clean_source_title(tex[match.end():close])
        if len(title) >= 4:
            titles.append(title)
    return titles

def clean_source_title(title: str) -> str:
    """Convert a TeX title argument into searchable plain text."""
    title = re.sub(r"\\(?:protect|mbox|centerline)\b", " ", title)
    title = re.sub(r"\\(?:the)?(?:chapter|section|subsection|subsubsection)\b", " ", title)
    title = re.sub(r"\\(?:sf|rm|bf|it|em|sc|large|Large|small|normalsize)\b", " ", title)
    title = re.sub(r"\\\s+", " ", title)
    title = title.replace("{", " ").replace("}", " ")
    title = re.sub(r"\$[^$]*\$", " ", title)
    try:
        title = LatexNodes2Text().latex_to_text(title)
    except Exception:
        title = re.sub(r"\\[A-Za-z]+", " ", title)
    title = " ".join(title.replace("\n", " ").split())
    return title.strip(" .")

def section_title_hits(titles: list[str], md: str) -> tuple[int, int]:
    """Count how many source section titles appear in converted text."""
    haystack = normalized_title_text(md)
    late_haystack = normalized_title_text(md[len(md) // 3:])
    normalized = [normalized_title_text(title) for title in titles]
    normalized = [title for title in normalized if len(title) >= 4]
    hits = sum(1 for title in normalized if title in haystack)
    tail = normalized[-min(3, len(normalized)):]
    tail_hits = sum(1 for title in tail if title in late_haystack)
    return hits, tail_hits

def normalized_title_text(text: str) -> str:
    """Normalize text for loose section-title matching."""
    text = normalize_for_search(text).lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())

def finalize_converted_markdown(tex: str, md: str) -> str:
    """Apply postprocessing plus source-aware structural repairs."""
    md = postprocess(md)
    return promote_plain_source_headings(tex, md)

def promote_plain_source_headings(tex: str, md: str) -> str:
    """Promote standalone source section titles emitted as plain text."""
    titles = {normalized_title_text(title): title for title in source_section_titles(tex)}
    if not titles:
        return md
    output = []
    for line in md.splitlines():
        stripped = line.strip()
        key = normalized_title_text(stripped)
        if key in titles and not stripped.startswith("#"):
            level = heading_level_for_title(titles[key])
            output.append(f"{'#' * level} {stripped}")
        else:
            output.append(line)
    return "\n".join(output)

def heading_level_for_title(title: str) -> int:
    """Choose a Markdown heading level for a source title."""
    return 2 if re.match(r"^\d+(?:\.\d+)*\.?\s+", title) else 1

def clean_metadata_text(text: str) -> str:
    """Clean simple LaTeX markup in metadata fields."""
    text = RE_METADATA_STYLE.sub(r"\1", text)
    text = RE_METADATA_COMMAND.sub(lambda m: m.group(0).lstrip("\\"), text)
    text = text.replace(r"\_", "_")
    text = text.replace(r"\&", "&")
    text = normalize_surviving_latex_structure(text)
    return " ".join(text.strip().split())

def is_support_file(name: str, content: str) -> bool:
    """Return true for TeX support files that are not article bodies."""
    lower = name.lower()
    has_body = has_article_body_cue(content)
    if lower.endswith(SUPPORT_FILE_SUFFIXES):
        return not has_body
    return lower.endswith(".tex") and not has_body and looks_like_tex_package(content)
