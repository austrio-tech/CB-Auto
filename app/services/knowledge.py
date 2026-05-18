from pathlib import Path

_kb_cache: str = ""


def load_knowledge_base(kb_folder: str = "K_B") -> str:
    global _kb_cache
    folder = Path(kb_folder)
    if not folder.exists():
        _kb_cache = ""
        return _kb_cache

    parts: list[str] = []
    for md_file in sorted(folder.glob("*.md")):
        content = md_file.read_text(encoding="utf-8")
        parts.append(f"### {md_file.stem}\n\n{content}")

    _kb_cache = "\n\n---\n\n".join(parts)
    return _kb_cache


def get_knowledge_base() -> str:
    return _kb_cache
