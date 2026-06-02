#!/usr/bin/env python3
"""
dirstat - directory statistics at a glance

    dirstat summary              # breakdown by file type
    dirstat largest -n 20        # 20 biggest files
    dirstat tree --depth 2       # visual tree
    dirstat dupes                # find duplicate files
"""

import os
import sys
import argparse
import hashlib
from collections import defaultdict


# dirs that rarely contain interesting user files
DEFAULT_EXCLUDE = {".git", "__pycache__", "node_modules", ".venv", "venv",
                   ".tox", ".mypy_cache", ".pytest_cache", "dist", "build",
                   ".DS_Store"}


def human(n: float) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(n) < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"


def parse_exclude(s: str | None) -> set[str]:
    if not s:
        return DEFAULT_EXCLUDE.copy()
    return set(s.split(","))


def walk(root: str, exclude: set[str]):
    """Yield (path, size) for every readable file under root."""
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in exclude]
        for fname in filenames:
            fpath = os.path.join(dirpath, fname)
            try:
                yield fpath, os.path.getsize(fpath)
            except OSError:
                pass


def bar(fraction: float, width: int = 18) -> str:
    filled = round(max(0.0, min(1.0, fraction)) * width)
    return "▓" * filled + "░" * (width - filled)


# ---------------------------------------------------------------------------

def cmd_summary(args):
    exclude = parse_exclude(args.exclude)
    ext_sizes: dict[str, list[int]] = defaultdict(list)
    total_size = 0

    for fpath, size in walk(args.path, exclude):
        ext = os.path.splitext(fpath)[1].lower() or "(none)"
        ext_sizes[ext].append(size)
        total_size += size

    total_files = sum(len(v) for v in ext_sizes.values())

    if total_files == 0:
        sys.exit("no files found (check --exclude?)")

    print(f"\n  {os.path.abspath(args.path)}")
    print(f"  {total_files:,} files  ·  {human(total_size)}\n")

    sorted_ext = sorted(ext_sizes.items(), key=lambda x: -sum(x[1]))
    top = sorted_ext[: args.top]
    rest = sorted_ext[args.top :]

    col = max(len(e) for e, _ in top) + 1 if top else 10
    print(f"  {'ext':<{col}}  {'files':>7}  {'size':>9}  chart")
    print(f"  {'-'*col}  {'-------'}  {'-'*9}  " + "-" * 22)

    def _row(ext, sizes):
        sz = sum(sizes)
        pct = sz / total_size if total_size else 0
        print(f"  {ext:<{col}}  {len(sizes):>7}  {human(sz):>9}  {bar(pct)} {pct*100:4.1f}%")

    for ext, sizes in top:
        _row(ext, sizes)

    if rest:
        all_rest_sizes = [s for _, sv in rest for s in sv]
        _row("(others)", all_rest_sizes)

    print()


def cmd_largest(args):
    exclude = parse_exclude(args.exclude)
    files = sorted(walk(args.path, exclude), key=lambda x: -x[1])

    root = os.path.abspath(args.path)
    print(f"\n  {args.n} largest files in {root}\n")
    print(f"  {'size':>9}   path")
    print(f"  {'-'*9}   {'-'*50}")

    for fpath, size in files[: args.n]:
        try:
            rel = os.path.relpath(fpath, root)
        except ValueError:
            rel = fpath
        print(f"  {human(size):>9}   {rel}")
    print()


def cmd_tree(args):
    exclude = parse_exclude(args.exclude)

    def _scan_size(path: str) -> int:
        total = 0
        try:
            for entry in os.scandir(path):
                if entry.name in exclude:
                    continue
                if entry.is_dir(follow_symlinks=False):
                    total += _scan_size(entry.path)
                else:
                    try:
                        total += entry.stat().st_size
                    except OSError:
                        pass
        except PermissionError:
            pass
        return total

    def _tree(path: str, prefix: str = "", depth: int = 0):
        if depth > args.depth:
            return
        try:
            entries = sorted(os.scandir(path), key=lambda e: (not e.is_dir(), e.name.lower()))
        except PermissionError:
            return
        entries = [e for e in entries if e.name not in exclude]
        for i, entry in enumerate(entries):
            last = i == len(entries) - 1
            conn = "└── " if last else "├── "
            ext  = "    " if last else "│   "
            if entry.is_dir(follow_symlinks=False):
                sz = _scan_size(entry.path) if args.sizes else None
                suffix = f"  ({human(sz)})" if sz is not None else ""
                print(f"{prefix}{conn}{entry.name}/{suffix}")
                _tree(entry.path, prefix + ext, depth + 1)
            else:
                try:
                    sz = entry.stat().st_size
                    suffix = f"  ({human(sz)})"
                except OSError:
                    suffix = ""
                print(f"{prefix}{conn}{entry.name}{suffix}")

    root = os.path.abspath(args.path)
    print(f"\n{root}/")
    _tree(args.path)
    print()


def cmd_dupes(args):
    """Find files with identical content (by SHA-1 of first 64KB + size)."""
    exclude = parse_exclude(args.exclude)

    def fingerprint(path: str, size: int) -> str:
        h = hashlib.sha1()
        h.update(str(size).encode())
        try:
            with open(path, "rb") as f:
                h.update(f.read(65536))
        except OSError:
            pass
        return h.hexdigest()

    # group by size first — cheap pre-filter
    by_size: dict[int, list[str]] = defaultdict(list)
    for fpath, size in walk(args.path, exclude):
        by_size[size].append(fpath)

    groups: dict[str, list[str]] = defaultdict(list)
    for size, paths in by_size.items():
        if len(paths) < 2:
            continue
        for p in paths:
            groups[fingerprint(p, size)].append(p)

    found = {fp: ps for fp, ps in groups.items() if len(ps) >= 2}

    if not found:
        print("no duplicates found")
        return

    root = os.path.abspath(args.path)
    total_waste = 0
    for fp, paths in sorted(found.items(), key=lambda x: -len(x[1])):
        size = os.path.getsize(paths[0])
        waste = size * (len(paths) - 1)
        total_waste += waste
        print(f"\n  {human(size)} × {len(paths)}  (wasting {human(waste)})")
        for p in paths:
            try:
                rel = os.path.relpath(p, root)
            except ValueError:
                rel = p
            print(f"    {rel}")

    print(f"\n  total reclaimable: {human(total_waste)}")


# ---------------------------------------------------------------------------

def main():
    p = argparse.ArgumentParser(
        prog="dirstat",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--version", action="version", version="1.1.0")
    sub = p.add_subparsers(dest="cmd", required=True, metavar="command")

    def add_path(sp):
        sp.add_argument("path", nargs="?", default=".", metavar="DIR")
        sp.add_argument("--exclude", metavar="DIRS",
                        help="comma-separated dir names to skip "
                             "(default: .git,__pycache__,node_modules,…)")

    sp = sub.add_parser("summary", help="file type breakdown")
    add_path(sp)
    sp.add_argument("--top", type=int, default=15, metavar="N",
                    help="show top N extensions (default: 15)")

    sp = sub.add_parser("largest", help="list largest files")
    add_path(sp)
    sp.add_argument("-n", type=int, default=20, metavar="N")

    sp = sub.add_parser("tree", help="visual directory tree")
    sp.add_argument("path", nargs="?", default=".", metavar="DIR")
    sp.add_argument("--depth", type=int, default=3)
    sp.add_argument("--sizes", action="store_true",
                    help="show directory sizes (slower)")
    sp.add_argument("--exclude", metavar="DIRS")

    sp = sub.add_parser("dupes", help="find duplicate files")
    add_path(sp)

    args = p.parse_args()
    {"summary": cmd_summary, "largest": cmd_largest,
     "tree":    cmd_tree,    "dupes":   cmd_dupes}[args.cmd](args)


if __name__ == "__main__":
    main()
