#!/usr/bin/env python3
"""dirstat: Fast directory statistics analyzer. Zero dependencies."""

import os
import sys
import argparse
from collections import defaultdict


def human(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"


def scan(root: str, exclude: set[str]) -> tuple[list[tuple], dict, int, int]:
    """Returns (files, ext_stats, total_size, total_count)"""
    files = []
    ext_stats: dict[str, list] = defaultdict(list)
    total_size = 0
    total_count = 0

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in exclude]
        for fname in filenames:
            fpath = os.path.join(dirpath, fname)
            try:
                size = os.path.getsize(fpath)
            except OSError:
                continue
            ext = os.path.splitext(fname)[1].lower() or "(no ext)"
            files.append((size, fpath))
            ext_stats[ext].append(size)
            total_size += size
            total_count += 1

    return files, ext_stats, total_size, total_count


def bar(fraction: float, width: int = 20) -> str:
    filled = round(fraction * width)
    return "█" * filled + "░" * (width - filled)


def cmd_summary(args):
    exclude = set(args.exclude.split(",")) if args.exclude else {".git", "__pycache__", "node_modules", ".venv"}
    files, ext_stats, total_size, total_count = scan(args.path, exclude)

    print(f"\n  Path   : {os.path.abspath(args.path)}")
    print(f"  Files  : {total_count:,}")
    print(f"  Size   : {human(total_size)}")
    print(f"  Types  : {len(ext_stats)}\n")

    print(f"  {'Extension':<14} {'Files':>7}  {'Size':>10}  {'% size':<22}")
    print("  " + "-" * 60)

    sorted_ext = sorted(ext_stats.items(), key=lambda x: -sum(x[1]))
    for ext, sizes in sorted_ext[: args.top]:
        count = len(sizes)
        sz = sum(sizes)
        pct = sz / total_size if total_size else 0
        print(f"  {ext:<14} {count:>7}  {human(sz):>10}  {bar(pct)} {pct*100:.1f}%")

    if len(sorted_ext) > args.top:
        rest = sorted_ext[args.top :]
        rest_size = sum(sum(s) for _, s in rest)
        rest_count = sum(len(s) for _, s in rest)
        pct = rest_size / total_size if total_size else 0
        print(f"  {'(others)':<14} {rest_count:>7}  {human(rest_size):>10}  {bar(pct)} {pct*100:.1f}%")
    print()


def cmd_largest(args):
    exclude = set(args.exclude.split(",")) if args.exclude else {".git", "__pycache__", "node_modules", ".venv"}
    files, _, total_size, _ = scan(args.path, exclude)
    files.sort(reverse=True)

    print(f"\n  Top {args.n} largest files in {os.path.abspath(args.path)}\n")
    print(f"  {'Size':>10}   Path")
    print("  " + "-" * 70)
    root_abs = os.path.abspath(args.path)
    for size, fpath in files[: args.n]:
        rel = os.path.relpath(fpath, root_abs)
        print(f"  {human(size):>10}   {rel}")
    print()


def cmd_tree(args):
    exclude = set(args.exclude.split(",")) if args.exclude else {".git", "__pycache__", "node_modules", ".venv"}

    def _tree(path, prefix="", depth=0):
        if depth > args.depth:
            return
        try:
            entries = sorted(os.scandir(path), key=lambda e: (not e.is_dir(), e.name.lower()))
        except PermissionError:
            return
        entries = [e for e in entries if e.name not in exclude]
        for i, entry in enumerate(entries):
            connector = "└── " if i == len(entries) - 1 else "├── "
            if entry.is_dir():
                try:
                    n = sum(1 for _ in os.scandir(entry.path))
                except PermissionError:
                    n = "?"
                print(f"{prefix}{connector}{entry.name}/  [{n} items]")
                extension = "    " if i == len(entries) - 1 else "│   "
                _tree(entry.path, prefix + extension, depth + 1)
            else:
                try:
                    size = human(entry.stat().st_size)
                except OSError:
                    size = "?"
                print(f"{prefix}{connector}{entry.name}  ({size})")

    print(f"\n{os.path.abspath(args.path)}/")
    _tree(args.path)
    print()


def main():
    p = argparse.ArgumentParser(
        prog="dirstat",
        description="Fast directory statistics analyzer. Zero dependencies.",
    )
    p.add_argument("--version", action="version", version="dirstat 1.0.0")
    sub = p.add_subparsers(dest="cmd", required=True)

    def add_common(sp):
        sp.add_argument("path", nargs="?", default=".", help="Directory to analyze (default: .)")
        sp.add_argument("--exclude", help="Comma-separated dir names to skip")

    sp = sub.add_parser("summary", help="File type breakdown with sizes")
    add_common(sp)
    sp.add_argument("--top", type=int, default=15, help="Show top N extensions")

    sp = sub.add_parser("largest", help="List largest files")
    add_common(sp)
    sp.add_argument("-n", type=int, default=20, help="Number of files to show")

    sp = sub.add_parser("tree", help="Visual directory tree with sizes")
    sp.add_argument("path", nargs="?", default=".", help="Directory (default: .)")
    sp.add_argument("--depth", type=int, default=3, help="Max depth")
    sp.add_argument("--exclude", help="Comma-separated dir names to skip")

    args = p.parse_args()
    {"summary": cmd_summary, "largest": cmd_largest, "tree": cmd_tree}[args.cmd](args)


if __name__ == "__main__":
    main()
