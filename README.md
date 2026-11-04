Mollana
=======

An Urdu Unicode text editor built on one idea: **type in Roman, read in Urdu**.
Roman words convert to Arabic-script Urdu as you write, with a suggestion list,
Nastaliq shaping, and spell checking.

The editor widget and the transliteration engine are separate packages —
[`pyraya`](https://pypi.org/project/pyraya/) and
[`romanalfaz`](https://pypi.org/project/romanalfaz/). This repository is the
application: the window, the file tree, projects, preferences, and dictionaries.

Requirements
------------

* Python 3.13
* [uv](https://docs.astral.sh/uv/)

Running
-------

```bash
uv sync
uv run mollana
# or
uv run python -m mollana
```

Either form works from any directory. Development commands:

| Action                  | Command                              |
| ----------------------- | ------------------------------------ |
| Lint                    | `uv run ruff check .`                |
| Type-check              | `uv run pyrefly check`               |
| Layer contracts         | `uv run lint-imports`                |
| Tests                   | `uv run pytest`                      |
| Regenerate UI/resources | `uv run python scripts/compileUI.py` |

Features
--------

* Roman-to-Urdu conversion with ranked suggestions, committed with a keystroke
* Right-to-left paragraphs with a Nastaliq font stack
* Spell-check underlines against the bundled dictionary, plus words you teach it
* Multiple documents in tabs, with a file tree over any folder
* Projects: a folder that declares itself one with `.mollana/workspace.toml`
* Dark and light themes

Status
------

Alpha, `0.2.0a1`.

License
-------

MIT. See `LICENSE.txt`.

(c) Copyright RoXimn 2013. All rights reserved.
