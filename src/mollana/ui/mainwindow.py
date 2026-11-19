# ******************************************************************************
# Copyright (c) 2026 RoXimn <roximn148@gmail.com>
# This source code is licensed under the MIT license found in the
# LICENSE.txt file in the root directory of this source tree.
# ******************************************************************************

"""The main window: menus and tab wiring, and nothing else.

Every decision about documents, folders, and dictionaries belongs to
:mod:`mollana.editor`; every decision about the buffer belongs to PyRaya. This
class translates user intent into calls on those two and reports back.
"""

# ******************************************************************************
import os
from pathlib import Path

from pyraya import PyRaya
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QDialog, QFileDialog, QMainWindow, QMenu, QMessageBox
from romanalfaz.engine import Vocabulary

from mollana.editor.dictionaries import DictionaryStore
from mollana.editor.document import Document
from mollana.editor.folder import RECOVERY_DIRNAME, Folder
from mollana.editor.recent import RecentFiles, RecentFolders
from mollana.editor.session import Session
from mollana.infra.logging import getLogger
from mollana.infra.meta import Rx
from mollana.infra.settings import RSettings
from mollana.ui.fonts import editorFont, gutterFont, resolveTypeface
from mollana.ui.learn_dialog import LearnWordDialog, prefillFor
from mollana.ui.mainwindowui import MainWindowUi, servicePixmap
from mollana.ui.theme import icon

# ******************************************************************************
FILE_FILTER: str = "Text files (*.txt *.md *.tex *.csv *.json *.toml);;All files (*)"
"""Filter offered by the open and save dialogs."""

RECENT_FILES_TITLE: str = "Recent Files"

RECENT_FOLDERS_TITLE: str = "Recent Folders"


# ******************************************************************************
class MainWindow(QMainWindow):
    """Application shell hosting the explorer and the editor tabs."""

    # **************************************************************************
    def __init__(
        self,
        session: Session,
        store: DictionaryStore,
        settings: RSettings,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.ui = MainWindowUi(self)

        self.session = session
        self.store = store
        self.settings = settings
        self.log = getLogger("ui")
        self._editorTypeface = resolveTypeface(self.settings.Appearances)
        self.log.debug(
            f"Editor typeface: {self._editorTypeface[0]!r} at {self._editorTypeface[1]}pt"
        )
        self._dictionaryLoaded = False
        self._savedDictionaryWords: dict[str, int] = {}
        self._activeDocumentId: str | None = None
        self._folderWarned = False
        self._restoring = False
        self._closing = False
        # Seed the toggle states before wiring: the handlers persist on change,
        # and a startup sync must not write the file back unchanged.
        self.ui.actionLineNumbers.setChecked(self.settings.Editor.LineNumbers)
        self.ui.actionAutoEnveloping.setChecked(self.settings.Editor.AutoEnveloping)
        self.autoSaveTimer = QTimer(self)
        self.autoSaveTimer.setInterval(self.settings.Main.AutoSaveInterval * 60_000)
        self.autoSaveTimer.timeout.connect(self.onAutoSave)
        self.autoSaveTimer.start()

        self.recent = RecentFiles(
            paths=self.settings.Main.RecentFiles,
            limit=self.settings.Main.RecentMaxCount,
        )
        self.recentFolders = RecentFolders(
            paths=self.settings.Main.RecentFolders,
            limit=self.settings.Main.RecentFoldersMaxCount,
        )

        self.recentFoldersMenu = QMenu(RECENT_FOLDERS_TITLE, self)
        self.recentFoldersMenu.menuAction().setIcon(icon("open-folder"))
        self.ui.menuFile.insertMenu(self.ui.actionSave, self.recentFoldersMenu)

        self.recentMenu = QMenu(RECENT_FILES_TITLE, self)
        self.recentMenu.menuAction().setIcon(icon("recent-files"))
        self.ui.menuFile.insertMenu(self.ui.actionSave, self.recentMenu)
        self.ui.menuFile.insertSeparator(self.ui.actionSave)

        self._connectActions()
        self._rebuildRecentFoldersMenu()
        self._rebuildRecentMenu()
        self._updateTitle()

    # **************************************************************************
    # Wiring
    # **************************************************************************
    def _connectActions(self) -> None:
        """Connect every menu action to its handler."""
        ui = self.ui
        ui.actionNew.triggered.connect(self.onNew)
        ui.actionOpen.triggered.connect(self.onOpen)
        ui.actionOpenFolder.triggered.connect(self.onOpenFolder)
        ui.actionCloseFolder.triggered.connect(self.onCloseFolder)
        ui.actionSave.triggered.connect(self.onSave)
        ui.actionSaveAs.triggered.connect(self.onSaveAs)
        ui.actionCloseTab.triggered.connect(self.onCloseTab)
        ui.actionQuit.triggered.connect(self.close)
        ui.actionAbout.triggered.connect(self.onAbout)

        ui.actionUndo.triggered.connect(lambda: self._callEditor("undo"))
        ui.actionRedo.triggered.connect(lambda: self._callEditor("redo"))
        ui.actionCut.triggered.connect(lambda: self._callEditor("cut"))
        ui.actionCopy.triggered.connect(lambda: self._callEditor("copy"))
        ui.actionPaste.triggered.connect(lambda: self._callEditor("paste"))
        ui.actionSelectAll.triggered.connect(lambda: self._callEditor("selectAll"))
        ui.actionFind.triggered.connect(self.onFind)
        ui.actionReplace.triggered.connect(self.onReplace)
        ui.actionFindNext.triggered.connect(lambda: self._callFindWidget("findNext"))
        ui.actionFindPrev.triggered.connect(lambda: self._callFindWidget("findPrev"))

        ui.actionWordWrap.toggled.connect(self.onWordWrap)
        ui.actionSpellChecker.toggled.connect(self.onSpellChecker)
        ui.actionAssistMode.toggled.connect(self.onAssistMode)
        ui.actionLineNumbers.toggled.connect(self.onLineNumbers)
        ui.actionAutoEnveloping.toggled.connect(self.onAutoEnveloping)

        ui.lblSpellCheck.clicked.connect(self.onSpellCheckClicked)
        ui.lblAssist.clicked.connect(self.onAssistModeClicked)

        ui.tbwEditors.tabCloseRequested.connect(self.onTabCloseRequested)
        ui.tbwEditors.currentChanged.connect(self.onTabChanged)
        ui.tbwEditors.tabMoved.connect(self.onTabMoved)
        ui.trvExplorer.fileActivated.connect(self.onFileActivated)

    # **************************************************************************
    # Documents
    # **************************************************************************
    def openDocument(self, document: Document, text: str = "") -> Document:
        """Add ``document`` to the session and open its tab."""
        self.session.add(document)
        self._record(document)
        editor = self.ui.tbwEditors.bind(document, text)
        editor.setFontFamily(self._editorTypeface[0])
        editor.setFontSize(self._editorTypeface[1])
        editor.setGutterFont(gutterFont(self._editorTypeface[1]))
        editor.setGutterEnabled(self.ui.actionLineNumbers.isChecked())
        editor.setAutoWrapEnabled(self.ui.actionAutoEnveloping.isChecked())
        editor.setAddWordHandler(self.openLearnDialog)
        self._loadActiveDictionary(editor)
        editor.setSpellCheckEnabled(self.ui.actionSpellChecker.isChecked())
        editor.setAssistEnabled(self.ui.actionAssistMode.isChecked())
        editor.modificationChanged.connect(
            lambda modified, documentId=document.id: self.onDocumentModified(documentId, modified)
        )
        editor.spellCheckChanged.connect(self.refreshEditorStatus)
        editor.assistModeChanged.connect(self.refreshEditorStatus)
        self.selectDocument(document)
        self._updateTitle()
        return document

    # **************************************************************************
    def refreshEditorStatus(self) -> None:
        """Show the active editor's service state on the status bar.

        Both icons are clickable while a document is open, and each one is
        faded when its service is off for the active editor; with no document
        open both are disabled and faded.
        """
        editor = self.ui.tbwEditors.activeEditor()
        spell = editor is not None and editor.isSpellCheckEnabled()
        assist = editor is not None and editor.isAssistEnabled()
        self.ui.lblSpellCheck.setEnabled(editor is not None)
        self.ui.lblAssist.setEnabled(editor is not None)
        self.ui.lblSpellCheck.setPixmap(servicePixmap(self.ui.iconSpellCheck, spell))
        self.ui.lblAssist.setPixmap(servicePixmap(self.ui.iconAssist, assist))

    # **************************************************************************
    def _loadActiveDictionary(self, editor: PyRaya) -> None:
        """Load the active dictionary into PyRaya's shared vocabulary once.

        PyRaya's vocabulary starts empty on every process; without this the
        words saved on the last close would never come back, and the next
        save would overwrite them with only this session's words.

        The words are added to a standalone ``Vocabulary`` and installed in
        one swap (``setLocalDictionary``). Adding them one by one to the
        live shared vocabulary would rebuild PyRaya's whole lookup index
        after every word — an already-attached Vocabulary recompiles on
        each mutation — which made the first file open take seconds for a
        stored dictionary of a few dozen words.
        """
        if self._dictionaryLoaded:
            return
        self._dictionaryLoaded = True
        stored = self.store.read(self.store.activeId())
        dictionary = Vocabulary()
        for word, count in stored.items():
            dictionary.add(word, count=count, isCompleted=True)
        editor.setLocalDictionary(dictionary)
        self._savedDictionaryWords = dict(stored)

    # **************************************************************************
    def openLearnDialog(self, trigger: str) -> str | None:
        """Open the Add Word entry with the window's one keyboard.

        The modal dialog cannot reach the dock, so the dock lends it the
        panel; the keyboard starts in the dock's own state, F2 toggles it
        inside the dialog, and the panel goes home when the dialog closes.

        Args:
            trigger: The word that opened the learn flow.

        Returns:
            The chosen Arabic word, or ``None`` when the dialog is cancelled.
        """
        prefill = prefillFor(trigger, self.ui.tbwEditors.activeEditor())
        panel, keyboardVisible = self.ui.dockKeyboard.detachPanel()
        dialog: LearnWordDialog | None = None
        try:
            dialog = LearnWordDialog(
                editorFont(*self._editorTypeface),
                prefill=prefill,
                hint=trigger,
                parent=self,
                keyboard=panel,
                keyboardVisible=keyboardVisible,
            )
            if dialog.exec() != QDialog.DialogCode.Accepted:
                return None
            return dialog.word() or None
        finally:
            if dialog is not None:
                dialog.takeKeyboard()
            self.ui.dockKeyboard.attachPanel(panel, keyboardVisible)

    # **************************************************************************
    def openPath(self, path: Path | str) -> Document | None:
        """Open a file, reusing its tab when it is already open."""
        filePath = Path(path)
        for document in self.session.documents:
            if document.path is not None and document.path.resolve() == filePath.resolve():
                self.selectDocument(document)
                return document

        try:
            document = Document.fromPath(filePath)
            text = document.read()
        except (OSError, UnicodeDecodeError) as error:
            QMessageBox.warning(self, "Open", f"Cannot open {filePath}:\n{error}")
            return None

        self.openDocument(document, text)
        self.recent.add(filePath)
        self._rebuildRecentMenu()
        return document

    # **************************************************************************
    def selectDocument(self, document: Document) -> None:
        """Make ``document`` the active tab."""
        self.session.activeIndex = self.session.indexOf(document.id)
        editor = self.ui.tbwEditors.editorFor(document.id)
        if editor is not None:
            self.ui.tbwEditors.setCurrentWidget(editor)
        self._updateTitle()

    # **************************************************************************
    def onFind(self) -> None:
        """Open the find bar over the active editor."""
        widget = self.ui.tbwEditors.activeFindWidget()
        if widget is not None:
            widget.openFind()

    # **************************************************************************
    def onReplace(self) -> None:
        """Open the replace row, or replace the match when it is showing."""
        widget = self.ui.tbwEditors.activeFindWidget()
        if widget is not None:
            widget.triggerReplace()

    # **************************************************************************
    def onNew(self) -> None:
        """Create an untitled document."""
        self.openDocument(Document())

    # **************************************************************************
    def onOpen(self) -> None:
        """Ask for files and open each of them."""
        files, _ = QFileDialog.getOpenFileNames(self, "Open", "", FILE_FILTER)
        for fileName in files:
            self.openPath(fileName)

    # **************************************************************************
    def onOpenFolder(self) -> None:
        """Ask for a folder and open its last session."""
        folder = QFileDialog.getExistingDirectory(self, "Open Folder")
        if not folder:
            return
        self.openFolder(Path(folder))

    # **************************************************************************
    def onCloseFolder(self) -> None:
        """Close the folder's tabs, keeping its session for next time."""
        self.closeFolder()

    # **************************************************************************
    def onFileActivated(self, path: str) -> None:
        """Open a file double-clicked in the explorer."""
        self.openPath(path)

    # **************************************************************************
    def onSave(self) -> None:
        """Save the active document in place, or ask where a new one goes."""
        document = self.session.active
        if document is None:
            return
        if document.isUntitled:
            self.onSaveAs()
            return
        self.saveDocument(document)

    # **************************************************************************
    def onSaveAs(self, document: Document | None = None) -> bool:
        """Save a document under a new path. Returns True when saved."""
        document = document if document is not None else self.session.active
        if document is None:
            return False
        if document.isUntitled:
            folder = self.session.folder
            base = folder.root if folder is not None else Path.home()
            suggested = str(base / f"{document.displayName}.txt")
        else:
            suggested = str(document.path)
        fileName, _ = QFileDialog.getSaveFileName(self, "Save As", suggested, FILE_FILTER)
        if not fileName:
            return False
        return self.saveDocument(document, Path(fileName))

    # **************************************************************************
    def saveDocument(self, document: Document, path: Path | None = None) -> bool:
        """Write ``document``'s buffer to disk and refresh its title."""
        editor = self.ui.tbwEditors.editorFor(document.id)
        if editor is None:
            return False
        wasUntitled = document.isUntitled
        oldRelative = self._relativeOf(document)
        try:
            written = document.save(editor.toPlainText(), path)
        except (OSError, ValueError) as error:
            QMessageBox.warning(self, "Save", f"Cannot save:\n{error}")
            return False

        self.ui.tbwEditors.refreshTitle(document)
        self._updateTitle()
        self.recent.add(written)
        self._rebuildRecentMenu()
        if wasUntitled:
            # The buffer now has a real home, so its recovery copy is obsolete.
            self._dropRecovery(document)
        folder = self.session.folder
        if oldRelative is not None and folder is not None:
            # The record still names the old path; the file itself was moved.
            newRelative = self._relativeOf(document)
            if newRelative is None:
                folder.forget(oldRelative)
            else:
                folder.move(oldRelative, newRelative)
            self._saveFolder()
        self._record(document)
        self.statusBar().showMessage(f"Saved {written}", 4000)
        return True

    # **************************************************************************
    def onDocumentModified(self, documentId: str, modified: bool) -> None:
        """Mirror the widget's modified flag into the document."""
        document = self.session.find(documentId)
        if document is None:
            return
        document.dirty = modified
        self.ui.tbwEditors.refreshTitle(document)
        self._updateTitle()

    # **************************************************************************
    def onTabChanged(self, index: int) -> None:
        """Track the active tab and remember where the caret was on the old one."""
        incoming: Document | None = None
        if index >= 0:
            documentId = self.ui.tbwEditors.documentIdAt(index)
            incoming = self.session.find(documentId) if documentId else None

        previous = self.session.find(self._activeDocumentId) if self._activeDocumentId else None
        if previous is not None and previous is not incoming:
            self._capturePosition(previous)

        if incoming is not None:
            self.session.activeIndex = self.session.indexOf(incoming.id)
            self._activeDocumentId = incoming.id
            self._capturePosition(incoming)
            if not (self._restoring or self._closing):
                self._saveFolder()
        self._updateTitle()

    # **************************************************************************
    def onTabMoved(self, fromIndex: int, toIndex: int) -> None:
        """Keep the recorded session in the same order as the visible tabs."""
        self.session.move(fromIndex, toIndex)
        folder = self.session.folder
        if folder is None:
            return
        ordered = [
            relative
            for position in range(self.ui.tbwEditors.count())
            if (relative := self._relativeOfDocumentAt(position)) is not None
        ]
        folder.reorder(ordered)
        self._saveFolder()

    # **************************************************************************
    def onCloseTab(self) -> None:
        """Close the tab the user asked to close."""
        self.onTabCloseRequested(self.ui.tbwEditors.currentIndex())

    # **************************************************************************
    def onTabCloseRequested(self, index: int) -> None:
        """Close a tab, offering to save unsaved changes first."""
        documentId = self.ui.tbwEditors.documentIdAt(index)
        if documentId is None:
            return
        document = self.session.find(documentId)
        if document is None:
            return
        if not self.confirmClose(document):
            return

        self._discardTab(document)

    # **************************************************************************
    def confirmClose(self, document: Document) -> bool:
        """Ask about unsaved changes. Returns True when the tab may close."""
        if not document.dirty:
            return True

        answer = QMessageBox.question(
            self,
            "Close",
            f"{document.displayName} has unsaved changes.",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
        )
        if answer == QMessageBox.StandardButton.Cancel:
            return False
        if answer == QMessageBox.StandardButton.Save:
            return self.onSaveAs(document) if document.isUntitled else self.saveDocument(document)
        return True

    # **************************************************************************
    # Folder sessions
    # **************************************************************************
    @property
    def folder(self) -> Folder | None:
        """The folder whose session is attached, or ``None``."""
        return self.session.folder

    # **************************************************************************
    def openFolder(self, root: Path) -> None:
        """Open ``root``, restoring the session it recorded last time.

        Opening a folder is a deliberate claim that this folder is one work
        unit, so it is the one action that creates ``.mollana/workspace.toml``.
        The previous folder is synced and closed first, with the usual prompts.
        """
        root = Path(root)
        if not root.is_dir():
            QMessageBox.warning(self, "Open Folder", f"{root} is not a folder.")
            return

        current = self.session.folder
        if current is not None and current.root.resolve() == root.resolve():
            self.ui.trvExplorer.setRoot(root)
            return
        if not self.closeFolder():
            return

        self._folderWarned = False
        try:
            folder = Folder.open(root) if Folder.isFolder(root) else Folder.create(root)
        except (FileNotFoundError, OSError) as error:
            self.log.warning(f"Cannot start a session in {root}: {error}")
            folder = Folder(root=root)
            self._reportFolderError(error, root)

        self.session.folder = folder
        self.ui.trvExplorer.setRoot(root)
        self._enterWorkingDirectory(root)
        self._restoreSession(folder)
        self.recentFolders.add(root)
        self._rebuildRecentFoldersMenu()
        self._updateTitle()
        self.statusBar().showMessage(f"Folder {root.name}", 4000)

    # **************************************************************************
    def closeFolder(self) -> bool:
        """Close the folder's tabs and detach it, keeping its session.

        Returns:
            ``True`` when the folder was closed or none was open, ``False``
            when a close prompt was cancelled.
        """
        folder = self.session.folder
        if folder is None:
            return True

        # Walking the tabs changes the active one; the record must keep the
        # file the user last looked at, not whichever tab was walked last.
        activeId = self._activeDocumentId
        self._closing = True
        cancelled = False
        try:
            for document in list(self.session.documents):
                self.selectDocument(document)
                wasUntitled = document.isUntitled
                if not self.confirmClose(document):
                    cancelled = True
                    break
                if wasUntitled and document.isUntitled:
                    # Discarded outright, so its recovery copy is dead weight.
                    self._dropRecovery(document)
                self.ui.tbwEditors.removeDocument(document.id)
                self.session.close(document.id)
        finally:
            self._closing = False
        if cancelled:
            previous = self.session.find(activeId) if activeId else None
            if previous is not None:
                self.selectDocument(previous)
            return False

        self._syncFolder()
        self._leaveWorkingDirectory()
        self.session.folder = None
        self._activeDocumentId = None
        self.ui.trvExplorer.setRoot(None)
        self._updateTitle()
        return True

    # **************************************************************************
    def _restoreSession(self, folder: Folder) -> None:
        """Open the files ``folder`` recorded, forgiving missing ones."""
        # Restoring must not write back over the very record it is reading:
        # opening each tab would otherwise overwrite the saved caret with 0.
        self._restoring = True
        try:
            self._replaySession(folder)
        finally:
            self._restoring = False

    # **************************************************************************
    def _replaySession(self, folder: Folder) -> None:
        """The restore itself, inside the ``_restoring`` guard."""
        for entry in folder.openFiles:
            path = folder.root / entry.path
            if entry.recovered:
                self._restoreRecovered(path, entry.title)
            elif path.is_file():
                self.openPath(path)
            else:
                self.log.info(f"Skipping missing session file: {path}")

        document = self._documentForRelative(folder.active) if folder.active is not None else None
        if document is None:
            document = self.session.documents[0] if self.session.documents else None
        if document is not None:
            self.selectDocument(document)
            self._restorePosition(document, folder.caret, folder.scroll)
        self._pruneRecovery(folder)

    # **************************************************************************
    def _restoreRecovered(self, path: Path, title: str | None) -> Document | None:
        """Reopen an auto-saved untitled buffer from its recovery file."""
        if not path.is_file():
            return None
        try:
            document = Document.fromPath(path)
            document.id = path.stem
            document.untitled = True
            document.title = title or "Untitled"
            text = document.read()
        except (OSError, UnicodeDecodeError) as error:
            self.log.warning(f"Cannot restore {path}: {error}")
            return None
        return self.openDocument(document, text)

    # **************************************************************************
    def _restorePosition(self, document: Document, caret: int, scroll: int) -> None:
        """Put the caret and the vertical scrollbar back where they were."""
        editor = self.ui.tbwEditors.editorFor(document.id)
        if editor is None:
            return
        length = len(editor.toPlainText())
        cursor = editor.textCursor()
        cursor.setPosition(max(0, min(caret, length)))
        editor.setTextCursor(cursor)
        editor.verticalScrollBar().setValue(max(0, scroll))

    # **************************************************************************
    def _documentForRelative(self, relative: str) -> Document | None:
        """Return the open document recorded under ``relative``, or ``None``."""
        for document in self.session.documents:
            if self._relativeOf(document) == relative:
                return document
        return None

    # **************************************************************************
    def _relativeOf(self, document: Document | None) -> str | None:
        """Return ``document``'s recorded path, or ``None`` when unrecorded."""
        folder = self.session.folder
        if folder is None or document is None or document.path is None:
            return None
        return folder.relativePath(document.path)

    # **************************************************************************
    def _relativeOfDocumentAt(self, index: int) -> str | None:
        """Return the recorded path of the tab at ``index``, or ``None``."""
        documentId = self.ui.tbwEditors.documentIdAt(index)
        return self._relativeOf(self.session.find(documentId)) if documentId else None

    # **************************************************************************
    def _record(self, document: Document) -> None:
        """Record an open file in the folder's session, live."""
        folder = self.session.folder
        if folder is None or self._restoring:
            return
        relative = self._relativeOf(document)
        if relative is None:
            return
        title = document.title if document.isUntitled else None
        if folder.record(relative, title=title) is not None:
            self._saveFolder()

    # **************************************************************************
    def _capturePosition(self, document: Document) -> None:
        """Remember ``document``'s caret and scroll on the folder's active record."""
        folder = self.session.folder
        if folder is None or self._restoring or self._closing:
            return
        relative = self._relativeOf(document)
        if relative is None:
            return
        editor = self.ui.tbwEditors.editorFor(document.id)
        if editor is None:
            return
        folder.setActive(
            relative,
            caret=editor.textCursor().position(),
            scroll=editor.verticalScrollBar().value(),
        )

    # **************************************************************************
    def _discardTab(self, document: Document) -> None:
        """Remove a tab and forget it in the folder's session."""
        self._dropRecovery(document)
        folder = self.session.folder
        relative = self._relativeOf(document)
        if folder is not None and relative is not None:
            folder.forget(relative)
            self._saveFolder()
        self.ui.tbwEditors.removeDocument(document.id)
        self.session.close(document.id)
        if self._activeDocumentId == document.id:
            self._activeDocumentId = None
        self._updateTitle()

    # **************************************************************************
    def _dropRecovery(self, document: Document) -> None:
        """Forget an untitled buffer's recovery record, then delete its file.

        The record goes first on purpose: a crash in between leaves an orphan
        file the next open prunes, never a record pointing at missing text.
        """
        folder = self.session.folder
        if folder is None:
            return
        path = folder.recoveryPath(document.id)
        relative = folder.relativePath(path)
        if relative is None or all(entry.path != relative for entry in folder.openFiles):
            return
        folder.forget(relative)
        self._saveFolder()
        try:
            path.unlink(missing_ok=True)
        except OSError as error:
            self.log.warning(f"Cannot remove recovery file {path}: {error}")

    # **************************************************************************
    def _syncFolder(self) -> None:
        """Reconcile the session with what is open, then write it."""
        folder = self.session.folder
        if folder is None:
            return
        for entry in list(folder.openFiles):
            if not (folder.root / entry.path).is_file():
                folder.forget(entry.path)
        self._saveFolder()

    # **************************************************************************
    def _saveFolder(self) -> None:
        """Write the session, warning once per folder when the write fails."""
        folder = self.session.folder
        if folder is None:
            return
        try:
            folder.save()
        except OSError as error:
            self._reportFolderError(error)

    # **************************************************************************
    def _reportFolderError(self, error: OSError, root: Path | None = None) -> None:
        """Warn once that this folder cannot record its session."""
        folder = self.session.folder
        rootName = (
            str(root)
            if root is not None
            else (str(folder.root) if folder is not None else "this folder")
        )
        self.log.warning(f"Cannot save the session in {rootName}: {error}")
        if self._folderWarned:
            return
        self._folderWarned = True
        QMessageBox.warning(
            self,
            "Folder",
            f"Mollana cannot save this folder's session in {rootName}:\n{error}\n\n"
            "Files still open and save normally, but the open set will not be restored.",
        )

    # **************************************************************************
    def _pruneRecovery(self, folder: Folder) -> None:
        """Delete recovery files that no session record claims."""
        recorded = {entry.path for entry in folder.openFiles if entry.recovered}
        recoveryDir = folder.manifestPath.parent / RECOVERY_DIRNAME
        if not recoveryDir.is_dir():
            return
        for path in recoveryDir.iterdir():
            relative = folder.relativePath(path)
            if relative is None or relative in recorded:
                continue
            try:
                path.unlink()
            except OSError as error:
                self.log.warning(f"Cannot prune recovery file {path}: {error}")

    # **************************************************************************
    def saveRecovery(self) -> None:
        """Auto-save every dirty untitled buffer into the folder's recovery folder."""
        folder = self.session.folder
        if folder is None:
            return
        for document in self.session.documents:
            if not document.isUntitled or not document.dirty:
                continue
            editor = self.ui.tbwEditors.editorFor(document.id)
            if editor is None:
                continue
            path = folder.recoveryPath(document.id)
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                temporary = path.with_name(path.name + ".tmp")
                temporary.write_text(editor.toPlainText(), encoding="utf-8", newline="")
                os.replace(temporary, path)
            except OSError as error:
                self._reportFolderError(error)
                continue
            relative = folder.relativePath(path)
            if relative is not None:
                folder.record(relative, title=document.title or "Untitled")
                self._saveFolder()

    # **************************************************************************
    def onAutoSave(self) -> None:
        """The periodic save: learned words plus untitled recovery buffers."""
        self.flushDictionaries()
        self.saveRecovery()

    # **************************************************************************
    def _enterWorkingDirectory(self, root: Path) -> None:
        """Make ``root`` the process working directory."""
        try:
            os.chdir(root)
        except OSError as error:
            self.log.warning(f"Cannot enter {root}: {error}")

    # **************************************************************************
    def _leaveWorkingDirectory(self) -> None:
        """Move out of the folder so Windows will let it be renamed or deleted."""
        try:
            os.chdir(Path.home())
        except OSError as error:
            self.log.warning(f"Cannot leave the folder: {error}")
            try:
                os.chdir(Path.home().anchor or ".")
            except OSError:
                pass

    # **************************************************************************
    # View and edit
    # **************************************************************************
    def onWordWrap(self, enabled: bool) -> None:
        """Apply the word-wrap toggle to every open editor."""
        self.ui.tbwEditors.setLineWrapEnabled(enabled)

    # **************************************************************************
    def onSpellChecker(self, enabled: bool) -> None:
        """Apply the spell-check toggle to every open editor."""
        self.ui.tbwEditors.setSpellCheckEnabled(enabled)

    # **************************************************************************
    def onAssistMode(self, enabled: bool) -> None:
        """Apply the assist-mode toggle to every open editor."""
        self.ui.tbwEditors.setAssistEnabled(enabled)

    # **************************************************************************
    def onLineNumbers(self, enabled: bool) -> None:
        """Apply the line-numbers toggle to every open editor, and remember it."""
        self.ui.tbwEditors.setLineNumbersEnabled(enabled)
        self.settings.Editor.LineNumbers = enabled
        self.settings.save()

    # **************************************************************************
    def onAutoEnveloping(self, enabled: bool) -> None:
        """Apply the auto-enveloping toggle to every open editor, and remember it."""
        self.ui.tbwEditors.setAutoEnvelopingEnabled(enabled)
        self.settings.Editor.AutoEnveloping = enabled
        self.settings.save()

    # **************************************************************************
    def onSpellCheckClicked(self) -> None:
        """Toggle spell checking through its menu action, like F5."""
        self.ui.actionSpellChecker.toggle()

    # **************************************************************************
    def onAssistModeClicked(self) -> None:
        """Toggle assist mode through its menu action, like F6."""
        self.ui.actionAssistMode.toggle()

    # **************************************************************************
    def _callEditor(self, method: str) -> None:
        """Call ``method`` on the active editor, if there is one."""
        editor = self.ui.tbwEditors.activeEditor()
        if editor is not None:
            getattr(editor, method)()

    # **************************************************************************
    def _callFindWidget(self, method: str) -> None:
        """Call ``method`` on the active tab's find bar, if there is one."""
        widget = self.ui.tbwEditors.activeFindWidget()
        if widget is not None:
            getattr(widget, method)()

    # **************************************************************************
    # Chrome
    # **************************************************************************
    def _updateTitle(self) -> None:
        """Compose the window title from the folder and the active document."""
        parts = [Rx.ApplicationTitle]
        folder = self.session.folder
        if folder is not None:
            parts.append(folder.root.name)
        document = self.session.active
        if document is not None:
            marker = "*" if document.dirty else ""
            parts.append(f"{marker}{document.displayName}")
        self.setWindowTitle(" - ".join(parts))
        self.refreshEditorStatus()

    # **************************************************************************
    def _rebuildRecentFoldersMenu(self) -> None:
        """Rebuild the recent-folders submenu from the current list."""
        self.recentFoldersMenu.clear()
        roots = self.recentFolders.existing()
        if not roots:
            empty = self.recentFoldersMenu.addAction("No recent folders")
            empty.setEnabled(False)
            return
        folderIcon = icon("open-folder")
        for root in roots:
            action = self.recentFoldersMenu.addAction(str(root))
            action.setIcon(folderIcon)
            action.triggered.connect(lambda checked=False, target=root: self.openFolder(target))
        self.recentFoldersMenu.addSeparator()
        clear = self.recentFoldersMenu.addAction("Clear Recent", self.onClearRecentFolders)
        clear.setIcon(icon("clear-recent"))

    # **************************************************************************
    def _rebuildRecentMenu(self) -> None:
        """Rebuild the recent-files submenu from the current list."""
        self.recentMenu.clear()
        paths = self.recent.existing()
        if not paths:
            empty = self.recentMenu.addAction("No recent files")
            empty.setEnabled(False)
            return
        fileIcon = icon("document")
        for path in paths:
            action = self.recentMenu.addAction(str(path))
            action.setIcon(fileIcon)
            action.triggered.connect(lambda checked=False, target=path: self.openPath(target))
        self.recentMenu.addSeparator()
        clear = self.recentMenu.addAction("Clear Recent", self.onClearRecent)
        clear.setIcon(icon("clear-recent"))

    # **************************************************************************
    def onClearRecent(self) -> None:
        """Forget every recent file."""
        self.recent.clear()
        self._rebuildRecentMenu()

    # **************************************************************************
    def onClearRecentFolders(self) -> None:
        """Forget every recent folder."""
        self.recentFolders.clear()
        self._rebuildRecentFoldersMenu()

    # **************************************************************************
    def onAbout(self) -> None:
        """Show the about box."""
        QMessageBox.about(
            self,
            f"{Rx.ApplicationTitle} - About",
            f"<h4>{Rx.ApplicationTitle} <tt>{Rx.ApplicationVersion}</tt><br>"
            f"{Rx.Copyright}</h4>"
            f"<p>{Rx.Licence}</p>"
            "<h4>Attributions</h4>"
            "<ul>"
            "<li>Icons by "
            '<a href="https://phosphoricons.com">Phosphor Icons</a>'
            ", licensed under the "
            '<a href="https://github.com/phosphor-icons/core">MIT License</a>.'
            "</li>"
            "</ul>",
        )

    # **************************************************************************
    # Shutdown
    # **************************************************************************
    def flushDictionaries(self) -> None:
        """Persist this run's learned words, merging them into the active file.

        ``DictionaryStore.write`` keeps the larger frequency of any word
        already on disk, so a second instance's words survive. PyRaya's own
        ``Vocabulary.save`` overwrites, which is why it is not used here.
        """
        dictionaryId = self.store.activeId()
        target = self.store.pathOf(dictionaryId)
        for editor in self.ui.tbwEditors.editors():
            getDictionary = getattr(editor, "localDictionary", None)
            if getDictionary is None:
                continue
            dictionary = getDictionary()
            if dictionary is None or not dictionary.isModified():
                continue
            words = {
                word: count
                for word, count in dictionary.counter.items()
                if word in dictionary.completed
            }
            if words == self._savedDictionaryWords:
                continue
            try:
                self.store.write(dictionaryId, words)
            except OSError as error:
                self.log.warning(f"Could not save dictionary {dictionaryId}: {error}")
            else:
                self._savedDictionaryWords = dict(words)
                self.log.info(f"Saved dictionary {dictionaryId} to {target}")
            break

    # **************************************************************************
    def closeEvent(self, event) -> None:
        """Offer to save unsaved documents, sync the folder, then close."""
        if self.session.folder is not None:
            self.saveRecovery()
            if not self.closeFolder():
                event.ignore()
                return
        else:
            activeId = self._activeDocumentId
            for document in self.session.dirtyDocuments:
                self.selectDocument(document)
                if not self.confirmClose(document):
                    previous = self.session.find(activeId) if activeId else None
                    if previous is not None:
                        self.selectDocument(previous)
                    event.ignore()
                    return

        self.settings.Main.RecentFiles = [Path(path) for path in self.recent.paths]
        self.settings.Main.RecentFolders = [Path(path) for path in self.recentFolders.paths]
        self.settings.save()
        self.autoSaveTimer.stop()
        self.flushDictionaries()
        event.accept()


# ******************************************************************************
