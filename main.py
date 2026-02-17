from __future__ import annotations

import os
import sys
from functools import partial
from pathlib import Path

if sys.platform == "win32":
    os.environ["QT_MEDIA_BACKEND"] = "windows"
elif sys.platform == "darwin":
    os.environ["QT_MEDIA_BACKEND"] = "darwin"
elif sys.platform == "linux":
    os.environ["QT_MEDIA_BACKEND"] = "gstreamer"

from PyQt6 import QtGui, QtWidgets
from PyQt6.QtCore import Qt, QTimer, QUrl
from PyQt6.QtGui import QCloseEvent, QIcon, QKeySequence, QResizeEvent, QShortcut
from PyQt6.QtMultimedia import QAudioOutput, QMediaMetaData, QMediaPlayer
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtWidgets import QFileDialog, QMessageBox, QStackedWidget
from send2trash import send2trash

from constants import MAX_IMAGE_DIMENSION, MEDIA_FORMATS, VIDEO_FORMATS
from main_window import Ui_mainWindow
from themes.theme_manager import ThemeManager


class MainWindow(QtWidgets.QMainWindow, Ui_mainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setupUi(self)
        self.folder: Path | None = None
        self.folders: list[str] = []
        self.files: list[str] = []
        self.curr_file: int = 0
        self.image_loaded: bool = False
        self.original_pixmap: QtGui.QPixmap | None = None
        self.media_path: Path | None = None
        self.media_type: str | None = None
        self.cats_visible: bool = False
        self.video_resolution: QtGui.QSize | None = None

        self.folderPathSelectorButton.clicked.connect(self.select_folder)
        self.nextButton.clicked.connect(self.next_image)
        self.prevButton.clicked.connect(self.prev_image)
        self.addCatButton.clicked.connect(self.add_category)
        self.delCatButton.clicked.connect(self.del_category)

        QShortcut(QKeySequence(Qt.Key.Key_Right), self, self.next_image)
        QShortcut(QKeySequence(Qt.Key.Key_Left), self, self.prev_image)
        QShortcut(QKeySequence("Ctrl+O"), self, self.select_folder)
        QShortcut(QKeySequence(Qt.Key.Key_Space), self, self._toggle_playback)
        QShortcut(QKeySequence(Qt.Key.Key_Delete), self, self.delete_file)

        app_dir = Path(__file__).parent
        self.setWindowIcon(QIcon(str(app_dir / "app_icon.ico")))

        delete_icon = self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_DialogDiscardButton)
        self.deleteFileButton.setIcon(delete_icon)
        self.deleteFileButton.clicked.connect(self.delete_file)
        self.deleteFileButton.setEnabled(False)

        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.imageLabel.setScaledContents(False)
        self.imageLabel.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)

        # Set up stacked widget for image/video display
        self.verticalLayout.removeWidget(self.imageLabel)

        self.mediaStack = QStackedWidget()
        self.mediaStack.addWidget(self.imageLabel)  # page 0: image

        self._setup_video_container()  # creates videoContainer as page 1
        self.mediaStack.addWidget(self.videoContainer)

        self.verticalLayout.addWidget(self.mediaStack)

        # Persistent media player
        self.mediaPlayer = QMediaPlayer()
        self.audioOutput = QAudioOutput()
        self.mediaPlayer.setAudioOutput(self.audioOutput)
        self.mediaPlayer.setVideoOutput(self.videoWidget)

        self.seekSlider.sliderMoved.connect(self.mediaPlayer.setPosition)
        self.mediaPlayer.playbackStateChanged.connect(self._on_playback_state_changed)
        self.mediaPlayer.durationChanged.connect(self._on_duration_changed)
        self.mediaPlayer.positionChanged.connect(self._on_position_changed)
        self.mediaPlayer.errorOccurred.connect(self._on_player_error)
        self.mediaPlayer.metaDataChanged.connect(self._on_metadata_changed)

        self.prevButton.setEnabled(False)
        self.nextButton.setEnabled(False)

        self._resize_timer = QTimer()
        self._resize_timer.setSingleShot(True)
        self._resize_timer.setInterval(50)
        self._resize_timer.timeout.connect(self._scale_image)

        self.folderPathSelectorButton.setToolTip("Select a folder of media files to sort (Ctrl+O)")
        self.prevButton.setToolTip("Previous file (Left arrow)")
        self.nextButton.setToolTip("Next file (Right arrow)")
        self.addCatButton.setToolTip("Add a new category folder")
        self.delCatButton.setToolTip("Delete the selected category")
        self.deleteFileButton.setToolTip("Delete current file (Delete key)")

        self.toggle_categories()
        self.update_status_bar()

    def _setup_video_container(self) -> None:
        self.videoContainer = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(self.videoContainer)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.videoWidget = QVideoWidget()
        layout.addWidget(self.videoWidget, stretch=1)

        self.videoControlsWidget = QtWidgets.QWidget()
        self.videoControlsWidget.setObjectName("videoControlsWidget")
        controls = QtWidgets.QHBoxLayout(self.videoControlsWidget)
        controls.setContentsMargins(4, 4, 4, 4)

        self.playPauseButton = QtWidgets.QPushButton("\u25b6")
        self.playPauseButton.setObjectName("playPauseButton")
        self.playPauseButton.setMinimumWidth(40)
        self.playPauseButton.clicked.connect(self._toggle_playback)
        controls.addWidget(self.playPauseButton)

        self.seekSlider = QtWidgets.QSlider(Qt.Orientation.Horizontal)
        self.seekSlider.setRange(0, 0)
        controls.addWidget(self.seekSlider, stretch=1)

        self.timeLabel = QtWidgets.QLabel("0:00 / 0:00")
        self.timeLabel.setMinimumWidth(100)
        self.timeLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        controls.addWidget(self.timeLabel)

        self.muteButton = QtWidgets.QPushButton("\U0001f50a")
        self.muteButton.setObjectName("muteButton")
        self.muteButton.setMinimumWidth(40)
        self.muteButton.setCheckable(True)
        self.muteButton.clicked.connect(self._toggle_mute)
        controls.addWidget(self.muteButton)

        layout.addWidget(self.videoControlsWidget)

    def _toggle_playback(self) -> None:
        if self.mediaPlayer.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.mediaPlayer.pause()
        elif self.mediaPlayer.source().isValid():
            self.mediaPlayer.play()

    def _toggle_mute(self) -> None:
        muted = self.muteButton.isChecked()
        self.audioOutput.setMuted(muted)
        self.muteButton.setText("\U0001f507" if muted else "\U0001f50a")

    def _on_playback_state_changed(self, state: QMediaPlayer.PlaybackState) -> None:
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.playPauseButton.setText("\u23f8")
        else:
            self.playPauseButton.setText("\u25b6")

    def _on_duration_changed(self, duration: int) -> None:
        self.seekSlider.setRange(0, duration)
        self._update_time_label(self.mediaPlayer.position(), duration)

    def _on_position_changed(self, position: int) -> None:
        self.seekSlider.setValue(position)
        self._update_time_label(position, self.mediaPlayer.duration())

    def _on_metadata_changed(self) -> None:
        resolution = self.mediaPlayer.metaData().value(QMediaMetaData.Key.Resolution)
        if resolution and resolution.isValid():
            self.video_resolution = resolution
            self.update_status_bar()

    def _on_player_error(self, error: QMediaPlayer.Error, message: str) -> None:
        self._stop_video()
        self.mediaStack.setCurrentWidget(self.imageLabel)
        file_name = self.media_path.name if self.media_path else "unknown"
        self.imageLabel.setText(f"Unable to play video: {file_name}\n{message}")

    def _update_time_label(self, position_ms: int, duration_ms: int) -> None:
        def fmt(ms: int) -> str:
            s = max(0, ms // 1000)
            return f"{s // 60}:{s % 60:02d}"

        self.timeLabel.setText(f"{fmt(position_ms)} / {fmt(duration_ms)}")

    def _is_video(self, filename: str) -> bool:
        return Path(filename).suffix.lower().lstrip(".") in VIDEO_FORMATS

    def _stop_video(self) -> None:
        self.mediaPlayer.stop()
        self.mediaPlayer.setSource(QUrl())

    def _play_video(self) -> None:
        self.mediaStack.setCurrentWidget(self.videoContainer)
        self.mediaPlayer.setSource(QUrl.fromLocalFile(str(self.media_path)))
        self.mediaPlayer.play()

    def toggle_categories(self, visible: bool = False) -> None:
        self.cats_visible = visible

        self.addCatButton.setVisible(self.cats_visible)
        self.delCatButton.setVisible(self.cats_visible)
        self.catListComboBox.setVisible(self.cats_visible)

    def update_status_bar(self) -> None:
        if len(self.files) == 0:
            status_text = ""
        elif self.media_type == "video":
            file_name = self.media_path.name
            if self.video_resolution and self.video_resolution.isValid():
                res = f"Orig: {self.video_resolution.width()}x{self.video_resolution.height()}"
            else:
                res = "Video"
            status_text = f"File: {self.curr_file + 1} of {len(self.files)} | File: {file_name} | {res}"
        elif self.original_pixmap is None:
            file_name = self.media_path.name
            status_text = f"File: {self.curr_file + 1} of {len(self.files)} | File: {file_name} | Invalid image"
        else:
            file_name = self.media_path.name
            orig_width = self.original_pixmap.width()
            orig_height = self.original_pixmap.height()
            status_text = f"File: {self.curr_file + 1} of {len(self.files)} | File: {file_name} | Orig: {orig_width}x{orig_height}"
        self.statusbar.showMessage(status_text)

    def add_btns_for_categories(self) -> None:
        """Adds buttons to the grid layout for each category"""
        for i in range(self.buttonsGridLayout.count())[::-1]:
            self.buttonsGridLayout.itemAt(i).widget().deleteLater()

        button_width = 100
        spacing = self.buttonsGridLayout.spacing() or 6
        available_width = (
            self.centralwidget.width()
            - self.gridLayout.contentsMargins().left()
            - self.gridLayout.contentsMargins().right()
        )
        cols = max(1, available_width // (button_width + spacing))

        for idx, category in enumerate(self.folders):
            row = idx // cols
            col = idx % cols
            button = QtWidgets.QPushButton(category)
            button.setObjectName("categoryButton")
            button.clicked.connect(partial(self.move_to_category, category))
            button.setMinimumWidth(button_width)
            button.setFixedHeight(35)
            self.buttonsGridLayout.addWidget(button, row, col)

    def move_to_category(self, category: str) -> None:
        """Moves current file to the given category"""
        if len(self.files) == 0:
            return

        self._stop_video()

        file_name = self.files[self.curr_file]

        path_to_file = self.folder / file_name
        path_to_dest = self.folder / category / file_name
        try:
            path_to_file.rename(path_to_dest)
        except OSError as e:
            QMessageBox.warning(self, "Move Failed", f"Could not move {file_name} to {category}:\n{e}")
            return

        self.files.pop(self.curr_file)
        self._advance_after_removal()

    def delete_file(self) -> None:
        """Sends current file to the system recycle bin"""
        if not self.files:
            return

        self._stop_video()

        file_name = self.files[self.curr_file]
        file_path = self.folder / file_name

        confirm = QMessageBox.question(
            self,
            "Delete File",
            f"Move '{file_name}' to the recycle bin?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )

        if confirm != QMessageBox.StandardButton.Yes:
            return

        try:
            send2trash(str(file_path))
        except OSError as e:
            QMessageBox.warning(self, "Delete Failed", f"Could not delete {file_name}:\n{e}")
            return

        self.files.pop(self.curr_file)
        self._advance_after_removal()

    def _advance_after_removal(self) -> None:
        """Adjusts curr_file index and refreshes display after a file is removed from the list."""
        if not self.files:
            self.reset_state()
        elif self.curr_file >= len(self.files):
            self.curr_file = len(self.files) - 1
            self.display_media()
        else:
            self.display_media()

    def reset_state(self) -> None:
        """Resets state to initial state"""
        self.folder = None
        self.folders = []
        self.folderPathSelectorButton.setText("Select Folder")
        self.reset_image("Nothing here... Just both of us...")

    def reset_image(self, label: str = "No media files found.") -> None:
        self._stop_video()
        self.mediaStack.setCurrentWidget(self.imageLabel)
        self.files = []
        self.curr_file = 0
        self.imageLabel.clear()
        self.imageLabel.setText(label)
        self.catListComboBox.clear()
        self.catListComboBox.setPlaceholderText("Categories")
        self.add_btns_for_categories()
        self.image_loaded = False
        self.original_pixmap = None
        self.media_path = None
        self.media_type = None
        self.toggle_categories(False)
        self.update_status_bar()
        self._update_nav_buttons()

    def _update_nav_buttons(self) -> None:
        has_files = len(self.files) > 0
        self.prevButton.setEnabled(has_files and self.curr_file > 0)
        self.nextButton.setEnabled(has_files and self.curr_file < len(self.files) - 1)
        self.deleteFileButton.setEnabled(has_files)

    def display_media(self) -> None:
        """Loads current file and displays it (image or video)"""
        if len(self.files) == 0:
            self.reset_image()
            return

        self._stop_video()
        self.video_resolution = None
        self.media_path = self.folder / self.files[self.curr_file]

        if self._is_video(self.files[self.curr_file]):
            self.media_type = "video"
            self.original_pixmap = None
            self.image_loaded = False
            self._play_video()
        else:
            self.media_type = "image"
            self._display_image()

        self.update_status_bar()
        self._update_nav_buttons()

    def _display_image(self) -> None:
        """Loads image from the current file and displays it scaled to fit"""
        self.mediaStack.setCurrentWidget(self.imageLabel)
        reader = QtGui.QImageReader(str(self.media_path))
        reader.setAutoTransform(True)
        size = reader.size()
        if size.isValid() and (size.width() > MAX_IMAGE_DIMENSION or size.height() > MAX_IMAGE_DIMENSION):
            reader.setScaledSize(
                size.scaled(MAX_IMAGE_DIMENSION, MAX_IMAGE_DIMENSION, Qt.AspectRatioMode.KeepAspectRatio)
            )
        image = reader.read()
        if image.isNull():
            self.original_pixmap = None
            self.image_loaded = False
            self.imageLabel.clear()
            self.imageLabel.setText(f"Unable to load image: {self.media_path.name}")
            return
        self.original_pixmap = QtGui.QPixmap.fromImage(image)
        self._scale_image()
        self.image_loaded = True

    def _scale_image(self) -> None:
        """Scales the cached original_pixmap to fit the scroll area viewport"""
        if self.original_pixmap is None:
            return
        viewport_size = self.scrollArea.viewport().size()
        scaled = self.original_pixmap.scaled(
            viewport_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        )
        self.imageLabel.setPixmap(scaled)

    def resizeEvent(self, event: QResizeEvent | None) -> None:
        if self.image_loaded:
            self._resize_timer.start()
        super().resizeEvent(event)

    def closeEvent(self, event: QCloseEvent | None) -> None:
        self._resize_timer.stop()
        self._stop_video()
        event.accept()

    def set_categories(self) -> None:
        """Sets the categories to the folders in the current folder"""
        self.catListComboBox.clear()
        self.catListComboBox.addItems(self.folders)
        self.add_btns_for_categories()

    def get_folder_content(self) -> None:
        """Gets the content of current folder"""
        self.curr_file = 0
        self.files = []
        self.folders = []
        for entry in sorted(self.folder.iterdir(), key=lambda p: p.name):
            if entry.is_file():
                ext = entry.suffix.lower().lstrip(".")
                if ext in MEDIA_FORMATS:
                    self.files.append(entry.name)
            else:
                self.folders.append(entry.name)
        self.set_categories()

        if self.files:
            self.display_media()
        else:
            self.reset_image("No media files found.")

    def next_image(self) -> None:
        """Shows the next file"""
        if self.curr_file < len(self.files) - 1:
            self.curr_file += 1
            self.display_media()

    def prev_image(self) -> None:
        """Shows the previous file"""
        if self.curr_file > 0:
            self.curr_file -= 1
            self.display_media()

    def add_category(self) -> None:
        """Adds new category with the name of the text of combobox"""
        category = self.catListComboBox.currentText().strip()
        if not category or category in self.folders:
            return

        invalid_chars = set('/\\:*?"<>|')
        found = [c for c in category if c in invalid_chars]
        if found:
            QMessageBox.warning(self, "Invalid Name", f"Category name cannot contain: {' '.join(found)}")
            return

        try:
            (self.folder / category).mkdir(parents=True)
        except OSError as e:
            QMessageBox.warning(self, "Create Failed", f"Could not create category '{category}':\n{e}")
            return

        self.folders.append(category)
        self.set_categories()

    def del_category(self) -> None:
        """Deletes selected category.
        All files will be returned to the main folder"""
        category = self.catListComboBox.currentText()
        if category not in self.folders or not category:
            return
        del_dialog_message = (
            f"Are you sure to delete {category} category?\nAll files in this category will be moved to main folder"
        )

        confirmation = QMessageBox.question(
            self,
            "Delete Category",
            del_dialog_message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if confirmation == QMessageBox.StandardButton.Yes:
            category_path = self.folder / category
            failures: list[str] = []

            for entry in category_path.iterdir():
                try:
                    entry.rename(self.folder / entry.name)
                except OSError as e:
                    failures.append(f"{entry.name}: {e}")

            if failures:
                QMessageBox.warning(
                    self,
                    "Move Errors",
                    f"Could not move {len(failures)} file(s) back to the main folder. "
                    f"Category '{category}' was not removed.\n\n" + "\n".join(failures),
                )
                self.get_folder_content()
                return

            try:
                category_path.rmdir()
            except OSError:
                QMessageBox.warning(self, "Delete Failed", f"Could not remove folder '{category}' (not empty).")

            self.get_folder_content()

    def select_folder(self) -> None:
        """Opens folder selection dialog and sets the folder path"""
        self.files = []
        folder_str = QFileDialog.getExistingDirectory(self, "Select Folder")
        if not folder_str:
            return
        self.folder = Path(folder_str)
        self.folderPathSelectorButton.setText(self.folder.name)
        self.toggle_categories(True)
        self.get_folder_content()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")

    theme = ThemeManager(app)
    theme.follow_system()

    window = MainWindow()
    window.show()
    sys.exit(app.exec())
