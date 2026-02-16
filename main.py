import os
import sys
from PyQt6 import QtGui, QtWidgets
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMessageBox, QFileDialog
from main_window import Ui_mainWindow


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
        self.image_path = None
        self.cats_visible = False

        self.folderPathSelectorButton.clicked.connect(self.select_folder)
        self.nextButton.clicked.connect(self.next_image)
        self.prevButton.clicked.connect(self.prev_image)
        self.addCatButton.clicked.connect(self.add_category)
        self.delCatButton.clicked.connect(self.del_category)

        self.setWindowIcon(QIcon("app_icon.ico"))

        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.imageLabel.setScaledContents(False)
        self.imageLabel.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)

        self.prevButton.setEnabled(False)
        self.nextButton.setEnabled(False)

        self.toggle_categories()
        self.update_status_bar()

    def toggle_categories(self, visible: bool = False):
        self.cats_visible =  visible

        self.addCatButton.setVisible(self.cats_visible)
        self.delCatButton.setVisible(self.cats_visible)
        self.catListComboBox.setVisible(self.cats_visible)

    def update_status_bar(self):
        if len(self.files) == 0:
            status_text = ""
        elif self.original_pixmap is None:
            file_name = os.path.basename(self.image_path)
            status_text = f'Image: {self.curr_file + 1} of {len(self.files)} | File: {file_name} | Invalid image'
        else:
            file_name = os.path.basename(self.image_path)
            orig_width = self.original_pixmap.width()
            orig_height = self.original_pixmap.height()
            status_text = f'Image: {self.curr_file + 1} of {len(self.files)} | File: {file_name} | Orig: {orig_width}x{orig_height}'
        self.statusbar.showMessage(status_text)

    def add_btns_for_categories(self):
        '''Adds buttons to the grid layout for each category'''
        rows = int(len(self.folders)/7 + 1)
        position = [(i, j) for i in range(rows) for j in range(7)]

        for i in range(self.buttonsGridLayout.count())[::-1]:
            self.buttonsGridLayout.itemAt(i).widget().deleteLater()

        for position, category in zip(position, self.folders):
            button = QtWidgets.QPushButton(category)
            lambda_ = self.create_lambda(category)

            button.clicked.connect(lambda_)
            button.setFixedSize(100, 35)
            self.buttonsGridLayout.addWidget(button, *position)

    def create_lambda(self, category):
        '''Creates lambda function for each button'''
        return lambda: self.move_to_category(category)

    def move_to_category(self, category):
        '''Moves current file to the given category'''
        if len(self.files) == 0:
            return

        file_name = self.files[self.curr_file]

        path_to_file = os.path.join(self.folder, file_name)
        path_to_dest = os.path.join(self.folder, category, file_name)
        try:
            os.rename(path_to_file, path_to_dest)
        except Exception as e:
            QMessageBox.warning(self, "Move Failed",
                                f"Could not move {file_name} to {category}:\n{e}")
            return

        if self.curr_file < len(self.files)-1:
            self.curr_file += 1
            self.display_image()
        else:
            self.reset_state()

    def reset_state(self):
        '''Rests state to initial state'''
        self.folder = None
        self.folders = []
        self.files = []
        self.curr_file = 0
        self.imageLabel.clear()
        self.imageLabel.setText('Nothing here... Just both of us...')
        self.folderPathSelectorButton.setText('Select Folder')
        self.catListComboBox.clear()
        self.add_btns_for_categories()
        self.catListComboBox.setPlaceholderText('Categories')
        self.image_loaded = False
        self.original_pixmap = None
        self.image_path = None
        self.toggle_categories(False)
        self.update_status_bar()
        self._update_nav_buttons()

    def reset_image(self, label="No images found."):
        self.files = []
        self.curr_file = 0
        self.imageLabel.clear()
        self.imageLabel.setText(label)
        self.catListComboBox.clear()
        self.catListComboBox.setPlaceholderText('Categories')
        self.add_btns_for_categories()
        self.image_loaded = False
        self.original_pixmap = None
        self.image_path = None
        self.toggle_categories(False)
        self.update_status_bar()
        self._update_nav_buttons()

    def _update_nav_buttons(self):
        has_files = len(self.files) > 0
        self.prevButton.setEnabled(has_files and self.curr_file > 0)
        self.nextButton.setEnabled(has_files and self.curr_file < len(self.files) - 1)

    def display_image(self):
        '''Loads image from the current file and displays it scaled to fit'''
        if len(self.files) == 0:
            self.reset_image()
            return
        self.image_path = os.path.join(self.folder, self.files[self.curr_file])
        self.original_pixmap = QtGui.QPixmap(self.image_path)
        if self.original_pixmap.isNull():
            self.original_pixmap = None
            self.image_loaded = False
            self.imageLabel.clear()
            file_name = os.path.basename(self.image_path)
            self.imageLabel.setText(f"Unable to load image: {file_name}")
            self.update_status_bar()
            self._update_nav_buttons()
            return
        self._scale_image()
        self.update_status_bar()
        self._update_nav_buttons()
        self.image_loaded = True

    def _scale_image(self):
        '''Scales the cached original_pixmap to fit the scroll area viewport'''
        if self.original_pixmap is None:
            return
        viewport_size = self.scrollArea.viewport().size()

        scaled_pixmap = self.original_pixmap.scaled(viewport_size, Qt.AspectRatioMode.KeepAspectRatio,
                                       Qt.TransformationMode.SmoothTransformation)

        final_pixmap = QtGui.QPixmap(viewport_size)
        final_pixmap.fill(Qt.GlobalColor.black)

        painter = QtGui.QPainter(final_pixmap)
        x_offset = (viewport_size.width() - scaled_pixmap.width()) // 2
        y_offset = (viewport_size.height() - scaled_pixmap.height()) // 2
        painter.drawPixmap(x_offset, y_offset, scaled_pixmap)
        painter.end()

        self.imageLabel.setPixmap(final_pixmap)

    def resizeEvent(self, event):
        if self.image_loaded:
            self._scale_image()
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
        image_formats = ['jpg', 'png', 'jpeg', 'gif', 'bmp',
                         'webp', 'ico', 'tiff', 'tif']
        for item in os.listdir(self.folder):
            if os.path.isfile(os.path.join(self.folder, item)):
                if item.split(".")[-1].lower() in image_formats:
                    self.files.append(item)
            else:
                self.folders.append(item)
        self.set_categories()

        if len(self.files) != 0:
            self.display_image()
        else:
            self.reset_image("No images found.")

    def next_image(self):
        '''Shows the next image'''
        if self.curr_file < len(self.files):
            self.curr_file += 1
            if self.curr_file == len(self.files):
                self.curr_file = len(self.files) - 1
            self.display_image()

    def prev_image(self):
        '''Shows the previous image'''
        if self.curr_file >= 0 and self.curr_file < len(self.files):
            if self.curr_file > 0:
                self.curr_file -= 1
            else:
                self.curr_file = 0
            self.display_image()

    def add_category(self):
        '''Adds new category with the name of the text of combobox'''
        category = self.catListComboBox.currentText()
        if category in self.folders or not category:
            return
        os.makedirs(os.path.join(self.folder, category))
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

    def open_file(self):
        '''Opens selected file in the default program'''
        if self.fileNameButton.text() == "FileName":
            QMessageBox.information(self, "Error",
                                    "Please select a folder first")
            return
        os.startfile(f'{self.folder}/{self.fileNameButton.text()}')


if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
