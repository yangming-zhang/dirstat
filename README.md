# dirstat

Directory statistics without the guesswork.

```
$ python dirstat.py summary ~/projects/myapp

  /home/user/projects/myapp
  3,241 files  ·  128.4 MB

  ext             files      size  chart
  ----------      -------  ------  ----------------------
  .py              1,204    18.2 MB  ▓▓▓▓▓▓░░░░░░░░░░░░  14.2%
  .json              487    42.1 MB  ▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░  32.8%
  .png               201    35.7 MB  ▓▓▓▓▓▓▓▓▓▓▓░░░░░░░  27.8%
  ...
```

## Setup

```bash
curl -O https://raw.githubusercontent.com/yangming-zhang/dirstat/main/dirstat.py
python dirstat.py --help
```

Python 3.9+, zero dependencies.

## Commands

```
summary   file type breakdown by count and size
largest   list the N biggest files
tree      visual directory tree with file sizes
dupes     find duplicate files (by content)
```

## Usage

```bash
# What's eating space in this repo?
python dirstat.py summary .

# Show top 30 extensions instead of 15
python dirstat.py summary . --top 30

# 10 biggest files
python dirstat.py largest -n 10 /some/path

# Tree, 2 levels deep, with directory sizes
python dirstat.py tree --depth 2 --sizes

# Find duplicates
python dirstat.py dupes ~/Downloads

# Ignore extra directories
python dirstat.py summary . --exclude ".git,dist,coverage"
```

## `dupes` output

```
  3.4 MB × 3  (wasting 6.8 MB)
    assets/hero.png
    public/images/hero.png
    backup/hero_copy.png
```

It uses SHA-1 of the first 64KB + file size as a fingerprint, which catches the common case (identical files) without reading every byte of every large file.

## Default excludes

`.git`, `__pycache__`, `node_modules`, `.venv`, `venv`, `.tox`, `.mypy_cache`, `dist`, `build`

Override with `--exclude` to add your own (replaces the defaults, so include any you still want).

## License

MIT
