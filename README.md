# dirstat

Fast **directory statistics** analyzer. Zero dependencies — pure Python stdlib.

See file type breakdown, sizes, and largest files at a glance.

## Install

```bash
curl -O https://raw.githubusercontent.com/yangming-zhang/dirstat/main/dirstat.py
python dirstat.py --help
```

## Commands

| Command | Description |
|---------|-------------|
| `summary` | File type breakdown with sizes and bar chart |
| `largest` | List largest files |
| `tree`    | Visual directory tree with file sizes |

## Usage

```bash
# File type breakdown for current directory
python dirstat.py summary

# Analyze a specific path, show top 20 extensions
python dirstat.py summary /path/to/project --top 20

# List 10 largest files
python dirstat.py largest -n 10 /path/to/project

# Directory tree (depth 2)
python dirstat.py tree --depth 2

# Exclude custom directories
python dirstat.py summary . --exclude ".git,dist,build"
```

## Example output

```
  Path   : /home/user/myproject
  Files  : 1,842
  Size   : 47.3 MB
  Types  : 23

  Extension       Files        Size  % size
  ------------------------------------------------------------
  .py              824      8.2 MB  ████████░░░░░░░░░░░░ 41.2%
  .json            312      6.1 MB  ██████░░░░░░░░░░░░░░ 30.5%
  .md               58      1.4 MB  █░░░░░░░░░░░░░░░░░░░  7.0%
  .txt              96      0.9 MB  █░░░░░░░░░░░░░░░░░░░  4.5%
  ...
```

## Options

- `--exclude` — comma-separated directory names to skip (default: `.git,__pycache__,node_modules,.venv`)
- `--top N` — show top N extensions in summary (default: 15)
- `--depth N` — max depth for tree view (default: 3)

## Requirements

- Python 3.9+
- No third-party packages

## License

MIT
