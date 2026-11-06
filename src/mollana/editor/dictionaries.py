# ******************************************************************************
# Copyright (c) 2026 RoXimn <roximn148@gmail.com>
# This source code is licensed under the MIT license found in the
# LICENSE.txt file in the root directory of this source tree.
# ******************************************************************************

"""The store of user dictionaries.

Dictionaries live in application data, never in a project. One is active for the
whole process; the widget's shared dictionary is that one.

Two different merges exist and they are not interchangeable:

* :meth:`DictionaryStore.write` **keeps the larger frequency** of a word already
  on disk. Saving is idempotent, so a repeated save cannot inflate counts, and
  two running instances cannot silently drop each other's words.
* :meth:`DictionaryStore.merge` **sums** frequencies, matching the
  ``romanalfaz merge`` command line. Merging two vocabularies deliberately
  rewards words present in both.
"""

# ******************************************************************************
import tomllib
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import tomlkit

# ******************************************************************************
INDEX_FILENAME: str = "dictionaries.toml"
"""Catalogue of the dictionaries in the store."""

DEFAULT_ID: str = "default"
"""Identifier of the dictionary that always exists."""

DEFAULT_NAME: str = "Default"
"""Display name of the dictionary that always exists."""

SUFFIX: str = ".sym"
"""Extension of a SymSpell vocabulary file (``word$frequency`` per line)."""


# ******************************************************************************
@dataclass
class DictionaryEntry:
    """One dictionary in the store."""

    id: str
    name: str
    filename: str
    description: str = ""
    modified: str = ""


# ******************************************************************************
def parseVocabulary(text: str) -> dict[str, int]:
    """Read ``word$frequency`` lines, summing duplicate words and skipping junk."""
    words: dict[str, int] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or "$" not in line:
            continue
        word, _, frequency = line.rpartition("$")
        try:
            value = int(frequency)
        except ValueError:
            continue
        if word:
            words[word] = words.get(word, 0) + value
    return words


# ******************************************************************************
def formatVocabulary(words: Mapping[str, int]) -> str:
    """Render ``words`` as ``word$frequency`` lines, sorted by word."""
    return "".join(f"{word}${words[word]}\n" for word in sorted(words))


# ******************************************************************************
class DictionaryStore:
    """Named user dictionaries in one folder, with an indexed active one."""

    # **************************************************************************
    def __init__(self, root: Path) -> None:
        self.root = root

    # **************************************************************************
    @property
    def indexPath(self) -> Path:
        """Path of the catalogue file."""
        return self.root / INDEX_FILENAME

    # **************************************************************************
    def pathOf(self, dictionaryId: str) -> Path:
        """Path of the vocabulary file for ``dictionaryId``."""
        entry = self.find(dictionaryId)
        filename = entry.filename if entry is not None else f"{dictionaryId}{SUFFIX}"
        return self.root / filename

    # **************************************************************************
    def entries(self) -> list[DictionaryEntry]:
        """Every catalogued dictionary, in catalogue order."""
        if not self.indexPath.is_file():
            return []
        data = tomllib.loads(self.indexPath.read_text(encoding="utf-8"))
        entries = []
        for item in data.get("dictionaries", []):
            entries.append(
                DictionaryEntry(
                    id=str(item.get("id", "")),
                    name=str(item.get("name", "")),
                    filename=str(item.get("filename", "")),
                    description=str(item.get("description", "")),
                    modified=str(item.get("modified", "")),
                )
            )
        return entries

    # **************************************************************************
    def find(self, dictionaryId: str) -> DictionaryEntry | None:
        """Return the catalogue entry for ``dictionaryId``, or ``None``."""
        for entry in self.entries():
            if entry.id == dictionaryId:
                return entry
        return None

    # **************************************************************************
    def activeId(self) -> str:
        """Identifier of the active dictionary, defaulting to the default one."""
        if not self.indexPath.is_file():
            return DEFAULT_ID
        data = tomllib.loads(self.indexPath.read_text(encoding="utf-8"))
        return str(data.get("active", DEFAULT_ID))

    # **************************************************************************
    def setActive(self, dictionaryId: str) -> None:
        """Make ``dictionaryId`` the active dictionary.

        Raises:
            KeyError: no such dictionary exists.
        """
        if self.find(dictionaryId) is None:
            raise KeyError(f"No such dictionary: {dictionaryId}")
        self._writeIndex(entries=self.entries(), active=dictionaryId)

    # **************************************************************************
    def ensureDefault(self) -> DictionaryEntry:
        """Create the catalogue and the default dictionary if either is missing."""
        self.root.mkdir(parents=True, exist_ok=True)
        entry = self.find(DEFAULT_ID)
        if entry is None:
            entry = self.create(DEFAULT_ID, DEFAULT_NAME)
        elif not self.pathOf(DEFAULT_ID).is_file():
            self.pathOf(DEFAULT_ID).write_text("", encoding="utf-8", newline="")
        return entry

    # **************************************************************************
    def create(self, dictionaryId: str, name: str, description: str = "") -> DictionaryEntry:
        """Add a named dictionary, creating its (empty) vocabulary file.

        Raises:
            ValueError: the identifier is empty or already catalogued.
        """
        if not dictionaryId:
            raise ValueError("A dictionary needs a non-empty identifier.")
        if self.find(dictionaryId) is not None:
            raise ValueError(f"Dictionary already exists: {dictionaryId}")

        self.root.mkdir(parents=True, exist_ok=True)
        entry = DictionaryEntry(
            id=dictionaryId,
            name=name,
            filename=f"{dictionaryId}{SUFFIX}",
            description=description,
            modified=datetime.now().isoformat(timespec="seconds"),
        )
        self.pathOf(entry.id).write_text("", encoding="utf-8", newline="")
        self._writeIndex(entries=[*self.entries(), entry], active=self.activeId())
        return entry

    # **************************************************************************
    def read(self, dictionaryId: str) -> dict[str, int]:
        """Load the vocabulary of ``dictionaryId``, empty when absent."""
        path = self.pathOf(dictionaryId)
        if not path.is_file():
            return {}
        return parseVocabulary(path.read_text(encoding="utf-8"))

    # **************************************************************************
    def write(self, dictionaryId: str, words: Mapping[str, int]) -> None:
        """Persist ``words``, keeping the larger frequency of any word on disk."""
        merged = self.read(dictionaryId)
        for word, frequency in words.items():
            merged[word] = max(merged.get(word, 0), frequency)

        path = self.pathOf(dictionaryId)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(formatVocabulary(merged), encoding="utf-8", newline="")
        self._touch(dictionaryId)

    # **************************************************************************
    def merge(self, sourceId: str, targetId: str) -> int:
        """Add every word of ``sourceId`` into ``targetId``, summing frequencies.

        Returns:
            Number of vocabulary entries in the target afterwards.

        Raises:
            KeyError: either dictionary is not catalogued.
        """
        for dictionaryId in (sourceId, targetId):
            if self.find(dictionaryId) is None:
                raise KeyError(f"No such dictionary: {dictionaryId}")

        source = self.read(sourceId)
        target = self.read(targetId)
        for word, frequency in source.items():
            target[word] = target.get(word, 0) + frequency

        self.pathOf(targetId).write_text(formatVocabulary(target), encoding="utf-8", newline="")
        self._touch(targetId)
        return len(target)

    # **************************************************************************
    def _touch(self, dictionaryId: str) -> None:
        """Record that ``dictionaryId`` changed."""
        entries = self.entries()
        for entry in entries:
            if entry.id == dictionaryId:
                entry.modified = datetime.now().isoformat(timespec="seconds")
        self._writeIndex(entries=entries, active=self.activeId())

    # **************************************************************************
    def _writeIndex(self, entries: list[DictionaryEntry], active: str) -> None:
        """Write the catalogue file."""
        self.root.mkdir(parents=True, exist_ok=True)
        document = tomlkit.document()
        document["active"] = active
        catalogue = tomlkit.aot()
        for entry in entries:
            item = tomlkit.table()
            item["id"] = entry.id
            item["name"] = entry.name
            item["filename"] = entry.filename
            item["description"] = entry.description
            item["modified"] = entry.modified
            catalogue.append(item)
        document["dictionaries"] = catalogue
        self.indexPath.write_text(tomlkit.dumps(document), encoding="utf-8", newline="")


# ******************************************************************************
