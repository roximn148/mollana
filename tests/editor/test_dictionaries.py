# ******************************************************************************
# Copyright (c) 2026 RoXimn <roximn148@gmail.com>
# This source code is licensed under the MIT license found in the
# LICENSE.txt file in the root directory of this source tree.
# ******************************************************************************

"""The user-dictionary store: catalogue, active selection, and both merges."""

# ******************************************************************************
from pathlib import Path

import pytest

from mollana.editor.dictionaries import (
    DEFAULT_ID,
    DictionaryStore,
    formatVocabulary,
    parseVocabulary,
)


# ******************************************************************************
def test_ensureDefaultCreatesCatalogueAndFile(tmp_path: Path) -> None:
    store = DictionaryStore(tmp_path)
    entry = store.ensureDefault()
    assert entry is not None
    assert entry.id == DEFAULT_ID
    assert store.pathOf(DEFAULT_ID).is_file()
    assert store.indexPath.is_file()
    assert store.activeId() == DEFAULT_ID


# ******************************************************************************
def test_ensureDefaultIsIdempotent(tmp_path: Path) -> None:
    store = DictionaryStore(tmp_path)
    store.ensureDefault()
    store.ensureDefault()
    assert len(store.entries()) == 1


# ******************************************************************************
def test_createAndActivateNamedDictionary(tmp_path: Path) -> None:
    store = DictionaryStore(tmp_path)
    store.ensureDefault()
    store.create('legal', 'Legal Terms', description='court vocabulary')
    assert store.find('legal') is not None

    store.setActive('legal')
    assert store.activeId() == 'legal'


# ******************************************************************************
def test_createRejectsDuplicateId(tmp_path: Path) -> None:
    store = DictionaryStore(tmp_path)
    store.ensureDefault()
    store.create('legal', 'Legal Terms')
    with pytest.raises(ValueError):
        store.create('legal', 'Another')


# ******************************************************************************
def test_activateUnknownDictionaryRaises(tmp_path: Path) -> None:
    store = DictionaryStore(tmp_path)
    store.ensureDefault()
    with pytest.raises(KeyError):
        store.setActive('missing')


# ******************************************************************************
def test_writeKeepsTheLargerFrequency(tmp_path: Path) -> None:
    store = DictionaryStore(tmp_path)
    store.ensureDefault()
    store.write(DEFAULT_ID, {'کتاب': 10})
    store.write(DEFAULT_ID, {'کتاب': 2, 'علم': 1})

    words = store.read(DEFAULT_ID)
    assert words == {'کتاب': 10, 'علم': 1}


# ******************************************************************************
def test_mergeSumsFrequencies(tmp_path: Path) -> None:
    store = DictionaryStore(tmp_path)
    store.ensureDefault()
    store.create('legal', 'Legal Terms')
    store.write(DEFAULT_ID, {'کتاب': 1, 'علم': 4})
    store.write('legal', {'کتاب': 2})

    total = store.merge('legal', DEFAULT_ID)

    assert total == 2
    assert store.read(DEFAULT_ID) == {'کتاب': 3, 'علم': 4}


# ******************************************************************************
def test_writeIsIdempotentAcrossSaves(tmp_path: Path) -> None:
    store = DictionaryStore(tmp_path)
    store.ensureDefault()
    store.write(DEFAULT_ID, {'علم': 7})
    store.write(DEFAULT_ID, {'علم': 7})
    assert store.read(DEFAULT_ID) == {'علم': 7}


# ******************************************************************************
def test_parseVocabularySkipsJunkAndSumsDuplicates() -> None:
    text = 'کتاب$2\n\nعلم$3\nکتاب$1\nbroken\nnofrequency$\n'
    assert parseVocabulary(text) == {'کتاب': 3, 'علم': 3}


# ******************************************************************************
def test_formatVocabularyIsSorted() -> None:
    assert formatVocabulary({'b': 2, 'a': 1}) == 'a$1\nb$2\n'

# ******************************************************************************
