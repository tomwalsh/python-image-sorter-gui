import os
import sys
from PyQt6 import QtGui, QtWidgets
from PyQt6.QtGui import QIcon, QShortcut, QKeySequence
from PyQt6.QtCore import Qt, QTimer, QUrl
from PyQt6.QtWidgets import QMessageBox, QFileDialog, QStackedWidget
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from main_window import Ui_mainWindow

IMAGE_FORMATS = {'jpg', 'png', 'jpeg', 'gif', 'bmp', 'webp', 'ico', 'tiff', 'tif'}
VIDEO_FORMATS = {'mp4', 'avi', 'mov', 'mkv', 'webm', 'wmv', 'flv', 'm4v', 'mpg', 'mpeg'}
MEDIA_FORMATS = IMAGE_FORMATS | VIDEO_FORMATS


class MainWindow(QtWidgets.QMainWindow, Ui_mainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.folder = None
        self.folders = []
        self.files = []
        self.curr_file = 0
        self.image_loaded = False
        self.original_pixmap = None
        self.media_path = None
        self.media_type = None
        self.cats_visible = False

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

        app_dir = os.path.dirname(os.path.abspath(__file__))
        self.setWindowIcon(QIcon(os.path.join(app_dir, "app_icon.ico")))

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

    def _setup_video_container(self):
        self.videoContainer = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(self.videoContainer)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.videoWidget = QVideoWidget()
        layout.addWidget(self.videoWidget, stretch=1)

        controls = QtWidgets.QHBoxLayout()
        controls.setContentsMargins(4, 2, 4, 2)

        self.playPauseButton = QtWidgets.QPushButton("Play")
        self.playPauseButton.setFixedWidth(60)
        self.playPauseButton.clicked.connect(self._toggle_playback)
        controls.addWidget(self.playPauseButton)

        self.seekSlider = QtWidgets.QSlider(Qt.Orientation.Horizontal)
        self.seekSlider.setRange(0, 0)
        controls.addWidget(self.seekSlider, stretch=1)

        self.timeLabel = QtWidgets.QLabel("0:00 / 0:00")
        self.timeLabel.setFixedWidth(100)
        self.timeLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        controls.addWidget(self.timeLabel)

        self.muteButton = QtWidgets.QPushButton("Mute")
        self.muteButton.setFixedWidth(50)
        self.muteButton.setCheckable(True)
        self.muteButton.clicked.connect(self._toggle_mute)
        controls.addWidget(self.muteButton)

        layout.addLayout(controls)

    def _toggle_playback(self):
        if self.mediaPlayer.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.mediaPlayer.pause()
        elif self.mediaPlayer.source().isValid():
            self.mediaPlayer.play()

    def _toggle_mute(self):
        self.audioOutput.setMuted(self.muteButton.isChecked())

    def _on_playback_state_changed(self, state):
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.playPauseButton.setText("Pause")
        else:
            self.playPauseButton.setText("Play")

    def _on_duration_changed(self, duration):
        self.seekSlider.setRange(0, duration)
        self._update_time_label(self.mediaPlayer.position(), duration)

    def _on_position_changed(self, position):
        self.seekSlider.setValue(position)
        self._update_time_label(position, self.mediaPlayer.duration())

    def _on_player_error(self, error, message):
        self._stop_video()
        self.mediaStack.setCurrentWidget(self.imageLabel)
        file_name = os.path.basename(self.media_path) if self.media_path else "unknown"
        self.imageLabel.setText(f"Unable to play video: {file_name}\n{message}")

    def _update_time_label(self, position_ms, duration_ms):
        def fmt(ms):
            s = max(0, ms // 1000)
            return f"{s // 60}:{s % 60:02d}"
        self.timeLabel.setText(f"{fmt(position_ms)} / {fmt(duration_ms)}")

    def _is_video(self, filename):
        return filename.rsplit('.', 1)[-1].lower() in VIDEO_FORMATS

    def _stop_video(self):
        self.mediaPlayer.stop()
        self.mediaPlayer.setSource(QUrl())

    def _play_video(self):
        self.mediaStack.setCurrentWidget(self.videoContainer)
        self.mediaPlayer.setSource(QUrl.fromLocalFile(self.media_path))
        self.mediaPlayer.play()

    def toggle_categories(self, visible: bool = False):
        self.cats_visible = visible

        self.addCatButton.setVisible(self.cats_visible)
        self.delCatButton.setVisible(self.cats_visible)
        self.catListComboBox.setVisible(self.cats_visible)

    def update_status_bar(self):
        if len(self.files) == 0:
            status_text = ""
        elif self.media_type == 'video':
            file_name = os.path.basename(self.media_path)
            status_text = f'File: {self.curr_file + 1} of {len(self.files)} | File: {file_name} | Video'
        elif self.original_pixmap is None:
            file_name = os.path.basename(self.media_path)
            status_text = f'File: {self.curr_file + 1} of {len(self.files)} | File: {file_name} | Invalid image'
        else:
            file_name = os.path.basename(self.media_path)
            orig_width = self.original_pixmap.width()
            orig_height = self.original_pixmap.height()
            status_text = f'File: {self.curr_file + 1} of {len(self.files)} | File: {file_name} | Orig: {orig_width}x{orig_height}'
        self.statusbar.showMessage(status_text)

    def add_btns_for_categories(self):
        '''Adds buttons to the grid layout for each category'''
        for i in range(self.buttonsGridLayout.count())[::-1]:
            self.buttonsGridLayout.itemAt(i).widget().deleteLater()

        button_width = 100
        spacing = self.buttonsGridLayout.spacing() or 6
        available_width = self.centralwidget.width() - self.gridLayout.contentsMargins().left() - self.gridLayout.contentsMargins().right()
        cols = max(1, available_width // (button_width + spacing))

        for idx, category in enumerate(self.folders):
            row = idx // cols
            col = idx % cols
            button = QtWidgets.QPushButton(category)
            button.clicked.connect(self.create_lambda(category))
            button.setFixedSize(button_width, 35)
            self.buttonsGridLayout.addWidget(button, row, col)

    def create_lambda(self, category):
        '''Creates lambda function for each button'''
        return lambda: self.move_to_category(category)

    def move_to_category(self, category):
        '''Moves current file to the given category'''
        if len(self.files) == 0:
            return

        self._stop_video()

        file_name = self.files[self.curr_file]

        path_to_file = os.path.join(self.folder, file_name)
        path_to_dest = os.path.join(self.folder, category, file_name)
        try:
            os.rename(path_to_file, path_to_dest)
        except Exception as e:
            QMessageBox.warning(self, "Move Failed",
                                f"Could not move {file_name} to {category}:\n{e}")
            return

        self.files.pop(self.curr_file)

        if len(self.files) == 0:
            self.reset_state()
        elif self.curr_file >= len(self.files):
            self.curr_file = len(self.files) - 1
            self.display_media()
        else:
            self.display_media()

    def delete_file(self):
        '''Sends current file to the system recycle bin'''
        if not self.files:
            return

        file_name = self.files[self.curr_file]
        file_path = os.path.join(self.folder, file_name)

        confirm = QMessageBox.question(
            self, "Delete File",
            f"Move '{file_name}' to the recycle bin?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes)

        if confirm != QMessageBox.StandardButton.Yes:
            return

        try:
            send2trash(os.path.normpath(file_path))
        except Exception as e:
            QMessageBox.warning(self, "Delete Failed",
                                f"Could not delete {file_name}:\n{e}")
            return

        self.files.pop(self.curr_file)
        if not self.files:
            self.reset_state()
        elif self.curr_file >= len(self.files):
            self.curr_file = len(self.files) - 1
            self.display_image()
        else:
            self.display_image()

    def reset_state(self):
        '''Resets state to initial state'''
        self.folder = None
        self.folders = []
        self.folderPathSelectorButton.setText('Select Folder')
        self.reset_image('Nothing here... Just both of us...')

    def reset_image(self, label="No media files found."):
        self._stop_video()
        self.mediaStack.setCurrentWidget(self.imageLabel)
        self.files = []
        self.curr_file = 0
        self.imageLabel.clear()
        self.imageLabel.setText(label)
        self.catListComboBox.clear()
        self.catListComboBox.setPlaceholderText('Categories')
        self.add_btns_for_categories()
        self.image_loaded = False
        self.original_pixmap = None
        self.media_path = None
        self.media_type = None
        self.toggle_categories(False)
        self.update_status_bar()
        self._update_nav_buttons()

    def _update_nav_buttons(self):
        has_files = len(self.files) > 0
        self.prevButton.setEnabled(has_files and self.curr_file > 0)
        self.nextButton.setEnabled(has_files and self.curr_file < len(self.files) - 1)
        self.deleteFileButton.setEnabled(has_files)

    def display_media(self):
        '''Loads current file and displays it (image or video)'''
        if len(self.files) == 0:
            self.reset_image()
            return

        self._stop_video()
        self.media_path = os.path.join(self.folder, self.files[self.curr_file])

        if self._is_video(self.files[self.curr_file]):
            self.media_type = 'video'
            self.original_pixmap = None
            self.image_loaded = False
            self._play_video()
        else:
            self.media_type = 'image'
            self._display_image()

        self.update_status_bar()
        self._update_nav_buttons()

    def _display_image(self):
        '''Loads image from the current file and displays it scaled to fit'''
        self.mediaStack.setCurrentWidget(self.imageLabel)
        self.original_pixmap = QtGui.QPixmap(self.media_path)
        if self.original_pixmap.isNull():
            self.original_pixmap = None
            self.image_loaded = False
            self.imageLabel.clear()
            file_name = os.path.basename(self.media_path)
            self.imageLabel.setText(f"Unable to load image: {file_name}")
            return
        self._scale_image()
        self.image_loaded = True

    def _scale_image(self):
        '''Scales the cached original_pixmap to fit the scroll area viewport'''
        if self.original_pixmap is None:
            return
        viewport_size = self.scrollArea.viewport().size()

        scaled_pixmap = self.original_pixmap.scaled(viewport_size, Qt.AspectRatioMode.KeepAspectRatio,
                                       Qt.TransformationMode.SmoothTransformation)

        final_pixmap = QtGui.QPixmap(viewport_size)
        final_pixmap.fill(self.palette().color(QtGui.QPalette.ColorRole.Window))

        painter = QtGui.QPainter(final_pixmap)
        x_offset = (viewport_size.width() - scaled_pixmap.width()) // 2
        y_offset = (viewport_size.height() - scaled_pixmap.height()) // 2
        painter.drawPixmap(x_offset, y_offset, scaled_pixmap)
        painter.end()

        self.imageLabel.setPixmap(final_pixmap)

    def resizeEvent(self, event):
        if self.image_loaded:
            self._resize_timer.start()
        super().resizeEvent(event)

    def set_categories(self):
        '''Sets the categories to the folders in the current folder'''
        self.catListComboBox.clear()
        self.catListComboBox.addItems(self.folders)
        self.add_btns_for_categories()

    def get_folder_content(self):
        '''Gets the content of current folder'''
        self.curr_file = 0
        self.files = []
        self.folders = []
        for item in os.listdir(self.folder):
            if os.path.isfile(os.path.join(self.folder, item)):
                if item.rsplit('.', 1)[-1].lower() in MEDIA_FORMATS:
                    self.files.append(item)
            else:
                self.folders.append(item)
        self.set_categories()

        if len(self.files) != 0:
            self.display_media()
        else:
            self.reset_image("No media files found.")

    def next_image(self):
        '''Shows the next file'''
        if self.curr_file < len(self.files) - 1:
            self.curr_file += 1
            self.display_media()

    def prev_image(self):
        '''Shows the previous file'''
        if self.curr_file > 0:
            self.curr_file -= 1
            self.display_media()

    def add_category(self):
        '''Adds new category with the name of the text of combobox'''
        category = self.catListComboBox.currentText().strip()
        if not category or category in self.folders:
            return

        invalid_chars = set('/\\:*?"<>|')
        found = [c for c in category if c in invalid_chars]
        if found:
            QMessageBox.warning(self, "Invalid Name",
                                f"Category name cannot contain: {' '.join(found)}")
            return

        try:
            os.makedirs(os.path.join(self.folder, category))
        except OSError as e:
            QMessageBox.warning(self, "Create Failed",
                                f"Could not create category '{category}':\n{e}")
            return

        self.folders.append(category)
        self.set_categories()

    def del_category(self):
        '''Deletes selected category.
        All files will be returned to the main folder'''
        category = self.catListComboBox.currentText()
        if category not in self.folders or not category:
            return
        delDialogMessage = f'''Are you sure to delete {category} category?
        All files in this category will be moved to main folder'''

        confirmation = QMessageBox.question(
            self, "Delete Category", delDialogMessage,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No)

        if confirmation == QMessageBox.StandardButton.Yes:
            category_path = os.path.join(self.folder, category)

            for file in os.listdir(category_path):
                os.rename(os.path.join(category_path, file),
                          os.path.join(self.folder, file))

            os.rmdir(os.path.join(self.folder, category))
            self.folders.remove(category)
            self.set_categories()

    def select_folder(self):
        '''Opens folder selection dialog and sets the folder path'''
        self.files = []
        self.folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if not self.folder:
            return
        self.folderPathSelectorButton.setText(os.path.basename(self.folder))
        self.toggle_categories(True)
        self.get_folder_content()



if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
