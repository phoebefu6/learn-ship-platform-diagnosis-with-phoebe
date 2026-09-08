"""Build and execute the course notebooks from cell-marked .py sources.

    python3 analysis/nbgen.py notebooks/src/a1_data_map.py   # -> notebooks/a1_data_map.ipynb (executed)
    python3 analysis/nbgen.py --all

A source file is plain Python with `# %% [markdown]` and `# %%` cell markers, so it runs as a
script too. Execution happens with cwd = notebooks/, the same place a learner opens them.
"""
from __future__ import annotations

import sys
from pathlib import Path

import nbformat
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "notebooks" / "src"
OUT = ROOT / "notebooks"


def parse(src: Path) -> nbformat.NotebookNode:
    nb = nbformat.v4.new_notebook()
    nb.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
    cells, kind, buf = [], None, []

    def flush() -> None:
        text = "\n".join(buf).strip("\n")
        if not text:
            return
        if kind == "md":
            lines = [ln[2:] if ln.startswith("# ") else ln.lstrip("#") for ln in text.splitlines()]
            cells.append(nbformat.v4.new_markdown_cell("\n".join(lines).strip()))
        else:
            cells.append(nbformat.v4.new_code_cell(text))

    for line in src.read_text().splitlines():
        if line.startswith("# %% [markdown]"):
            flush(); kind, buf = "md", []
        elif line.startswith("# %%"):
            flush(); kind, buf = "code", []
        elif kind is not None:
            buf.append(line)
    flush()
    nb.cells = cells
    return nb


def build(src: Path) -> Path:
    out = OUT / (src.stem + ".ipynb")
    if out.exists():
        out.unlink()  # a failed run must leave NO notebook behind, never a stale passing one
    nb = parse(src)
    client = NotebookClient(nb, timeout=900, kernel_name="python3", resources={"metadata": {"path": str(OUT)}})
    client.execute()
    nbformat.write(nb, out)
    return out


if __name__ == "__main__":
    targets = sorted(SRC.glob("*.py")) if "--all" in sys.argv else [Path(a) for a in sys.argv[1:]]
    for t in targets:
        print("executing", t.name, "...", flush=True)
        print("  ->", build(t))
