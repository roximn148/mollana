# ******************************************************************************
# Copyright (c) 2026 RoXimn <roximn148@gmail.com>
# This source code is licensed under the MIT license found in the
# LICENSE.txt file in the root directory of this source tree.
# ******************************************************************************

"""The main window: menus and tab wiring, and nothing else.

Every decision about documents, projects, and dictionaries belongs to
:mod:`mollana.editor`; every decision about the buffer belongs to PyRaya. This
class translates user intent into calls on those two and reports back.
"""

# ******************************************************************************
from pathlib import Path

from pyraya import PyRaya
from PySide6.QtCore import QSize, QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QDialog, QFileDialog, QMainWindow, QMenu, QMessageBox
from romanalfaz.engine import Vocabulary

from mollana.editor.dictionaries import DictionaryStore
from mollana.editor.document import Document
from mollana.editor.project import Project
from mollana.editor.recent import RecentFiles
from mollana.editor.session import Session
from mollana.infra.logging import getLogger
from mollana.infra.meta import Rx
from mollana.infra.settings import RSettings
from mollana.ui.learn_dialog import LearnWordDialog, prefillFor
from mollana.ui.mainwindowui import MainWindowUi

# ******************************************************************************
FILE_FILTER: str = "Text files (*.txt *.md *.tex *.csv *.json *.toml);;All files (*)"
"""Filter offered by the open and save dialogs."""

RECENT_MENU_TITLE: str = "Recent Files"


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
        self._dictionaryLoaded = False
        self._savedDictionaryWords: dict[str, int] = {}
        self.autoSaveTimer = QTimer(self)
        self.autoSaveTimer.setInterval(self.settings.Main.AutoSaveInterval * 60_000)
        self.autoSaveTimer.timeout.connect(self.flushDictionaries)
        self.autoSaveTimer.start()

        self.recent = RecentFiles(
            paths=self.settings.Main.RecentFiles,
            limit=self.settings.Main.RecentMaxCount,
        )

        self.recentMenu = QMenu(RECENT_MENU_TITLE, self)
        self.ui.menuFile.insertMenu(self.ui.actionQuit, self.recentMenu)

        self._connectActions()
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
        ui.actionNewProject.triggered.connect(self.onNewProject)
        ui.actionOpenProject.triggered.connect(self.onOpenProject)
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

        ui.actionWordWrap.toggled.connect(self.onWordWrap)
        ui.actionSpellChecker.toggled.connect(self.onSpellChecker)

        ui.tbwEditors.tabCloseRequested.connect(self.onTabCloseRequested)
        ui.tbwEditors.currentChanged.connect(self.onTabChanged)
        ui.trvExplorer.fileActivated.connect(self.onFileActivated)

    # **************************************************************************
    # Documents
    # **************************************************************************
    def openDocument(self, document: Document, text: str = "") -> Document:
        """Add ``document`` to the session and open its tab."""
        self.session.add(document)
        editor = self.ui.tbwEditors.bind(document, text)
        editor.setAddWordHandler(self.openLearnDialog)
        self._loadActiveDictionary(editor)
        editor.setSpellCheckEnabled(self.ui.actionSpellChecker.isChecked())
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

        Both icons are greyed while no document is open, and each one is
        greyed when its service is off for the active editor.
        """
        editor = self.ui.tbwEditors.activeEditor()
        spell = editor is not None and editor.isSpellCheckEnabled()
        assist = editor is not None and editor.isAssistEnabled()
        self.ui.lblSpellCheck.setEnabled(spell)
        self.ui.lblAssist.setEnabled(assist)
        spellMode = QIcon.Mode.Normal if spell else QIcon.Mode.Disabled
        assistMode = QIcon.Mode.Normal if assist else QIcon.Mode.Disabled
        self.ui.lblSpellCheck.setPixmap(self.ui.iconSpellCheck.pixmap(QSize(16, 16), spellMode))
        self.ui.lblAssist.setPixmap(self.ui.iconAssist.pixmap(QSize(16, 16), assistMode))

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
                prefill,
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
        """Browse a folder without converting it into a project."""
        folder = QFileDialog.getExistingDirectory(self, "Open Folder")
        if not folder:
            return
        self.ui.trvExplorer.setRoot(folder)
        self.statusBar().showMessage(f"Browsing {folder}", 4000)

    # **************************************************************************
    def onFileActivated(self, path: str) -> None:
        """Open a file double-clicked in the explorer."""
        self.openPath(path)

    # **************************************************************************
    def onSave(self) -> None:
        """Save the active document in place."""
        document = self.session.active
        if document is None:
            return
        if document.path is None:
            self.onSaveAs()
            return
        self.saveDocument(document)

    # **************************************************************************
    def onSaveAs(self) -> None:
        """Save the active document under a new path."""
        document = self.session.active
        if document is None:
            return
        suggested = str(document.path) if document.path else document.displayName
        fileName, _ = QFileDialog.getSaveFileName(self, "Save As", suggested, FILE_FILTER)
        if not fileName:
            return
        self.saveDocument(document, Path(fileName))

    # **************************************************************************
    def saveDocument(self, document: Document, path: Path | None = None) -> bool:
        """Write ``document``'s buffer to disk and refresh its title."""
        editor = self.ui.tbwEditors.editorFor(document.id)
        if editor is None:
            return False
        try:
            written = document.save(editor.toPlainText(), path)
        except (OSError, ValueError) as error:
            QMessageBox.warning(self, "Save", f"Cannot save:\n{error}")
            return False

        self.ui.tbwEditors.refreshTitle(document)
        self._updateTitle()
        self.recent.add(written)
        self._rebuildRecentMenu()
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
        """Keep the session's active index in step with the tab bar."""
        if index >= 0:
            self.session.activeIndex = index
        self._updateTitle()

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

        self.ui.tbwEditors.removeDocument(document.id)
        self.session.close(document.id)
        self._updateTitle()

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
            return self.saveDocument(document)
        return True

    # **************************************************************************
    # Projects
    # **************************************************************************
    def onNewProject(self) -> None:
        """Convert a chosen folder into a project."""
        folder = QFileDialog.getExistingDirectory(self, "Choose a folder to convert into a project")
        if not folder:
            return
        root = Path(folder)
        if Project.isProject(root):
            QMessageBox.information(self, "New Project", f"{root} is already a project.")
            self.openProject(root)
            return
        self.openProject(root, create=True)

    # **************************************************************************
    def onOpenProject(self) -> None:
        """Open a folder that already declares itself a project."""
        folder = QFileDialog.getExistingDirectory(self, "Open Project")
        if not folder:
            return
        root = Path(folder)
        if not Project.isProject(root):
            QMessageBox.warning(
                self,
                "Open Project",
                f"{root} is not a project.\nUse File > New Project to convert it.",
            )
            return
        self.openProject(root)

    # **************************************************************************
    def openProject(self, root: Path, create: bool = False) -> None:
        """Attach a project to the session and open its declared documents."""
        try:
            project = Project.create(root) if create else Project.open(root)
        except (OSError, ValueError) as error:
            QMessageBox.warning(self, "Project", f"Cannot open {root}:\n{error}")
            return

        self.session.project = project
        self.ui.trvExplorer.setRoot(project.root)
        for path in project.documentPaths:
            if path.is_file():
                self.openPath(path)
        self._updateTitle()
        self.statusBar().showMessage(f"Project {project.name}", 4000)

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
    def _callEditor(self, method: str) -> None:
        """Call ``method`` on the active editor, if there is one."""
        editor = self.ui.tbwEditors.activeEditor()
        if editor is not None:
            getattr(editor, method)()

    # **************************************************************************
    # Chrome
    # **************************************************************************
    def _updateTitle(self) -> None:
        """Compose the window title from the project and active document."""
        parts = [Rx.ApplicationTitle]
        if self.session.project is not None:
            parts.append(self.session.project.name)
        document = self.session.active
        if document is not None:
            marker = "*" if document.dirty else ""
            parts.append(f"{marker}{document.displayName}")
        self.setWindowTitle(" - ".join(parts))
        self.refreshEditorStatus()

    # **************************************************************************
    def _rebuildRecentMenu(self) -> None:
        """Rebuild the recent-files submenu from the current list."""
        self.recentMenu.clear()
        paths = self.recent.existing()
        if not paths:
            empty = self.recentMenu.addAction("No recent files")
            empty.setEnabled(False)
            return
        for path in paths:
            action = self.recentMenu.addAction(str(path))
            action.triggered.connect(lambda checked=False, target=path: self.openPath(target))
        self.recentMenu.addSeparator()
        self.recentMenu.addAction("Clear Recent", self.onClearRecent)

    # **************************************************************************
    def onClearRecent(self) -> None:
        """Forget every recent path."""
        self.recent.clear()
        self._rebuildRecentMenu()

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
            "<li>Some icons by "
            '<a href="https://invent.kde.org/frameworks/oxygen-icons">Oxygen Icons</a>'
            ", licensed under "
            '<a href="https://www.gnu.org/licenses/lgpl-3.0.en.html">'
            "GNU Lesser General Public License v3.0</a> License.</li>"
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
        """Offer to save unsaved documents, persist state, then close."""
        for document in self.session.dirtyDocuments:
            self.selectDocument(document)
            if not self.confirmClose(document):
                event.ignore()
                return

        self.settings.Main.RecentFiles = [Path(path) for path in self.recent.paths]
        self.settings.save()
        self.autoSaveTimer.stop()
        self.flushDictionaries()
        event.accept()


# ******************************************************************************
