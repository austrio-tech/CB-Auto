import re
from pathlib import Path
from typing import NamedTuple

_STOP_WORDS = {
    "what", "is", "the", "a", "an", "how", "do", "i", "my", "your", "can",
    "you", "me", "for", "of", "in", "on", "at", "to", "and", "or", "with",
    "that", "this", "it", "be", "are", "was", "were", "have", "has", "had",
    "will", "would", "could", "should", "about", "tell", "show", "get", "us",
}


class _Section(NamedTuple):
    label: str   # "filename/heading" — used for scoring
    content: str # already-stripped text


_sections: list[_Section] = []


def _strip_markdown(text: str) -> str:
    """Remove pipe-table separators and collapse table rows into compact lines."""
    lines = []
    for line in text.splitlines():
        s = line.strip()
        if re.match(r"^\|[-| :]+\|$", s):      # |---|---| separator rows
            continue
        if s.startswith("|") and s.endswith("|"):
            cells = [c.strip() for c in s[1:-1].split("|") if c.strip()]
            lines.append(" | ".join(cells))
        else:
            lines.append(line)
    # Collapse 3+ consecutive blank lines into 1
    text = "\n".join(lines)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def load_knowledge_base(kb_folder: str = "K_B") -> None:
    global _sections
    _sections = []
    folder = Path(kb_folder)
    if not folder.exists():
        return

    for md_file in sorted(folder.glob("*.md")):
        raw = md_file.read_text(encoding="utf-8")
        cleaned = _strip_markdown(raw)
        # Split into sections on ## headings
        parts = re.split(r"(?=\n## )", cleaned)
        for part in parts:
            part = part.strip()
            if not part:
                continue
            first_line = part.splitlines()[0]
            heading = re.sub(r"^#+\s*", "", first_line).strip()
            label = f"{md_file.stem} {heading}".lower()
            _sections.append(_Section(label=label, content=part))


def get_relevant_kb(question: str, top_n: int = 4) -> str:
    """Return only the KB sections most relevant to the question."""
    if not _sections:
        return "(no knowledge base loaded)"

    if not question.strip():
        return "\n\n---\n\n".join(s.content for s in _sections)

    words = {
        w.lower() for w in re.findall(r"\b\w+\b", question)
        if w.lower() not in _STOP_WORDS and len(w) > 2
    }

    scored = sorted(
        _sections,
        key=lambda s: sum(1 for w in words if w in s.label + " " + s.content.lower()),
        reverse=True,
    )

    return "\n\n---\n\n".join(s.content for s in scored[:top_n])
