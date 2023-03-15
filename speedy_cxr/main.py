import os
import sys
import pydicom
import numpy as np
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QSizePolicy, QScrollArea, QPushButton, QHBoxLayout, \
    QVBoxLayout, QSlider, QWidget, QFileDialog, QCheckBox, QToolBar, QAction, QStyle, QSpacerItem, QMessageBox
from PyQt5.QtGui import QImage, QPixmap, QPainter
from PyQt5.QtCore import Qt, QSettings, pyqtSignal
from pydicom.pixel_data_handlers.util import apply_modality_lut, apply_voi_lut
import csv


class WindowedLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._image = None
        self._window_center = None
        self._window_width = None

    image_updated = pyqtSignal()

    def set_image(self, image):
        self._image = image
        self.update()

    def set_window_center(self, value):
        self._window_center = value
        self.update()

    def paintEvent(self, event):
        if self._image is None:
            super().paintEvent(event)
            return

        if self._window_width is None:
            self._window_width = 255
        if self._window_center is None:
            self._window_center = 127

        # Apply windowing transformation to the image
        lo = self._window_center - self._window_width // 2
        hi = self._window_center + self._window_width // 2
        image = np.clip(self._image, lo, hi)
        image = (image - lo) * 255 // (hi - lo)
        image = np.uint8(image)

        # Convert the image to a QImage and display it
        height, width = image.shape
        bytes_per_line = width
        qimage = QImage(image.data.tobytes(), width, height, bytes_per_line, QImage.Format_Grayscale8)
        pixmap = QPixmap.fromImage(qimage)
        painter = QPainter(pixmap)
        # painter.drawText(10, 20, f"Window Center: {self._window_center}")
        painter.end()
        self.setPixmap(pixmap)
        self.image_updated.emit()

        # Call the base class method
        super().paintEvent(event)


class MainWindow(QMainWindow):
    def __init__(self, dir_path):
        super().__init__()
        self.default_directory = '.'
        self.zoom = 1.0
        self.current_index = 0
        self.nav_toolbar = QToolBar(self)
        next_icon = self.style().standardIcon(QStyle.SP_ArrowForward)
        prev_icon = self.style().standardIcon(QStyle.SP_ArrowBack)
        self.prevAction = QAction(prev_icon, "&Back", self)
        self.nextAction = QAction(next_icon, "&Next", self)
        self.window_center_label = QLabel("Window Center:")
        self.window_center_slider = QSlider(Qt.Horizontal)

        self.dir_path = dir_path
        self.file_list = sorted([f for f in os.listdir(self.dir_path) if f.endswith('.dcm')])
        self.viewed_values = {f: False for f in self.file_list}

        # Load the checkbox values from CSV file
        self.checkbox_values = {}
        loaded = self.load_from_csv()
        if loaded:
            self.restore_from_saved_state()

        # Load the current DICOM file
        self.load_file()

        # Create a WindowedLabel to display the image
        self.label = WindowedLabel(self)
        self.label.setScaledContents(True)
        self.label.set_image(self.image)

        main_layout = QVBoxLayout()
        main_layout.addLayout(self.create_image_layout())
        # Create a scroll area widget and set its layout
        scroll_widget = QWidget(self)
        scroll_widget.setLayout(main_layout)
        # Create a scroll area and add the scroll widget to it
        scroll_area = QScrollArea(self)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        self.setCentralWidget(scroll_area)
        self.setMinimumSize(self.label.size())

        self.create_file_toolbar()

        self.create_window_slider()
        # main_layout.addLayout(self.create_window_slider())

        self.checkbox_toolbar = QToolBar(self)
        checkboxes = self.create_checkboxes()
        self.set_checkbox_toolbar(checkboxes)

        self.create_image_toolbar()

        self.create_navigation_toolbar()

        # Connect the keyboard events to navigate images
        self.keyPressEvent = self.handle_key_press_event

        # Connect the sliders to update the windowing parameters
        self.window_center_slider.valueChanged.connect(self.on_window_center_changed)

        # Connect the nav buttons to their functions and to reset the windowing parameters
        self.nextAction.triggered.connect(self.reset_window_center_slider)
        self.prevAction.triggered.connect(self.reset_window_center_slider)
        self.prevAction.triggered.connect(self.previous_image)
        self.nextAction.triggered.connect(self.next_image)

        self.label.image_updated.connect(self.resize_after_image_changed)


    def create_image_layout(self):
        image_layout = QHBoxLayout()
        image_layout.addWidget(self.label)
        return image_layout

    def create_checkboxes(self):
        checkboxes = []
        filename = self.file_list[self.current_index]
        # for i in range(5):
        consolidation_checkbox = QCheckBox("Consolidation", self)
        consolidation_checkbox.setObjectName("consolidation_checkbox")
        consolidation_checkbox.setChecked(bool(self.checkbox_values.get(filename, False)))
        consolidation_checkbox.stateChanged.connect(self.on_consolidation_changed)
        checkboxes.append(consolidation_checkbox)
        return checkboxes

    def set_checkbox_toolbar(self, checkboxes):
        checkbox_layout = QVBoxLayout()
        viewed_label = QLabel(self)
        viewed_label.setAlignment(Qt.AlignHCenter)
        viewed_label.setObjectName("viewed_label")
        viewed_label.setText("Prev. Viewed: " + ("Yes" if self.is_image_viewed() else "No"))
        checkbox_layout.addWidget(viewed_label)
        spacer_item = QSpacerItem(0, 25, QSizePolicy.Fixed, QSizePolicy.Minimum)
        checkbox_layout.addItem(spacer_item)
        checkbox_heading = QLabel(self)
        checkbox_heading.setAlignment(Qt.AlignHCenter)
        checkbox_heading.setText("FINDINGS")
        checkbox_layout.addWidget(checkbox_heading)

        for checkbox in checkboxes:
            checkbox_layout.addWidget(checkbox)

        checkbox_widget = QWidget(self)
        checkbox_widget.setLayout(checkbox_layout)
        checkbox_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        # Create a toolbar to hold the checkbox widget
        self.checkbox_toolbar.addWidget(checkbox_widget)
        self.checkbox_toolbar.setStyleSheet("QToolBar QLabel { font-weight: bold; }")
        self.addToolBar(Qt.RightToolBarArea, self.checkbox_toolbar)

    def create_window_slider(self):
        # Create sliders for window center
        self.window_center_slider.setValue(127)
        self.window_center_slider.setRange(1, 255)
        # slider_layout = QVBoxLayout()
        # window_center_layout = QHBoxLayout()
        # Create a label for the window center slider and add the label + slider to the layout
        # window_center_layout.addWidget(self.window_center_label)
        # window_center_layout.addWidget(self.window_center_slider)
        # # Add the layout to the parent slider layout
        # slider_layout.addLayout(window_center_layout)
        # return slider_layout

    def create_file_toolbar(self):
        # Add a button to the toolbar to save checkbox values to CSV file
        self.file_tool_bar = QToolBar(self)
        saveicon = self.style().standardIcon(QStyle.SP_DialogSaveButton)
        self.saveAction = QAction(saveicon, "&Save", self)
        self.file_tool_bar.addAction(self.saveAction)
        # exiticon = self.style().standardIcon(QStyle.SP_DialogCloseButton)
        # self.exitAction = QAction(exiticon, "&Exit", self)
        # self.file_tool_bar.addAction(self.exitAction)
        self.addToolBar(Qt.TopToolBarArea, self.file_tool_bar)
        self.saveAction.triggered.connect(self.save_to_csv)

    def create_image_toolbar(self):
        # Add buttons to invert the image and to rotate by 90 degrees
        invert_button = QPushButton("Invert", self)
        invert_button.clicked.connect(self.invert_image)
        rotate_button = QPushButton("Rotate 90°", self)
        rotate_button.clicked.connect(self.rotate_image)
        self.image_toolbar = QToolBar(self)
        self.image_toolbar.addWidget(invert_button)
        self.image_toolbar.addWidget(rotate_button)
        self.image_toolbar.addWidget(self.window_center_label)
        self.image_toolbar.addWidget(self.window_center_slider)

        # Create buttons for zoom in and zoom out
        zoom_in_button = QPushButton("Zoom In", self)
        zoom_in_button.clicked.connect(self.zoom_in)
        zoom_out_button = QPushButton("Zoom Out", self)
        zoom_out_button.clicked.connect(self.zoom_out)
        # Add the buttons to the toolbar
        self.image_toolbar.addWidget(zoom_in_button)
        self.image_toolbar.addWidget(zoom_out_button)

        self.addToolBar(Qt.TopToolBarArea, self.image_toolbar)

    def create_navigation_toolbar(self):
        # Add buttons to navigate to previous and next image
        self.nav_toolbar = QToolBar(self)
        self.nav_toolbar.addAction(self.prevAction)
        self.nav_toolbar.addAction(self.nextAction)
        self.addToolBar(Qt.TopToolBarArea, self.nav_toolbar)

    def restore_from_saved_state(self):
        # Check for saved settings and restore last viewed file
        settings = QSettings('MyApp', 'DicomViewer')
        if settings.contains('last_file') and settings.contains('last_index'):
            last_file = settings.value('last_file')
            last_index = settings.value('last_index')
            self.current_index = self.file_list.index(last_file) if last_file in self.file_list else last_index

        # Create a new file list that puts unviewed files after the current file
        unviewed_files = [f for f in self.file_list[self.current_index + 1:] if not self.viewed_values[f]]
        viewed_files = [f for f in self.file_list[:self.current_index + 1] if not self.viewed_values[f]]
        if len(unviewed_files) == 0:
            QMessageBox.information(self, "All Images Viewed", "You have viewed all the images.")
        else:
            self.file_list = unviewed_files + viewed_files

    def reset_window_center_slider(self):
        self.window_center_slider.setValue(127)

    def load_file(self):
        file_path = os.path.join(self.dir_path, self.file_list[self.current_index])

        try:
            # Read the DICOM file
            ds = pydicom.dcmread(file_path)
            self.image = ds.pixel_array
            self.image = apply_modality_lut(self.image, ds)
            self.image = apply_voi_lut(self.image.astype(int), ds, 0)

            # Convert the pixel array to an 8-bit integer array
            if ds.BitsStored != 8:
                _min = np.amin(self.image)
                _max = np.amax(self.image)
                self.image = (self.image - _min) * 255.0 / (_max - _min)
                self.image = np.uint16(self.image)
        except Exception as e:
            # Handle the exception (e.g. display an error message)
            QMessageBox.critical(self, "Error", f"Failed to load file:\n{str(e)}", QMessageBox.Ok,
                                 setDefaultButton=QMessageBox.Ok)
            self.next_image(prev_failed=True)

    def previous_image(self):
        self.viewed_values[self.file_list[self.current_index]] = True

        # Save current file and index
        self.save_settings()

        # Load previous file
        self.current_index -= 1
        if self.current_index < 0:
            self.current_index = len(self.file_list) - 1
        self.load_file()

        self.zoom = 1.0
        self.label._window_center = None
        self.label._window_width = None

        # Update the image
        self.label.set_image(self.image)
        self.setWindowTitle(f"Dicom Viewer - {self.file_list[self.current_index]}")

        # Set the checkbox value for the current file
        self.set_checkbox_value()

        viewed_label = self.findChild(QLabel, "viewed_label")
        viewed_label.setText("Viewed: " + ("Yes" if self.is_image_viewed() else "No"))

    def next_image(self, prev_failed=False):
        if not prev_failed:
            self.viewed_values[self.file_list[self.current_index]] = True
        else:
            self.viewed_values[self.file_list[self.current_index]] = "FAILED"

        # Save current file and index
        self.save_settings()
        # Find the index of the next unviewed file
        next_unviewed_index = (self.current_index + 1) % len(self.file_list)
        while next_unviewed_index != self.current_index and self.viewed_values[self.file_list[next_unviewed_index]]:
            next_unviewed_index = (next_unviewed_index + 1) % len(self.file_list)

        if next_unviewed_index == self.current_index:
            # All images have been viewed
            QMessageBox.information(self, "All Images Viewed", "You have viewed all the images.")
            self.current_index += 1
            if self.current_index >= len(self.file_list):
                self.current_index = 0
            self.load_file()
        else:
            self.current_index = next_unviewed_index
            self.load_file()

        self.zoom = 1.0
        self.label._window_center = None
        self.label._window_width = None

        # Update the image display
        self.label.set_image(self.image)
        self.setWindowTitle(f"Dicom Viewer - {self.file_list[self.current_index]}")

        # Set the checkbox value for the current file
        self.set_checkbox_value()

        viewed_label = self.findChild(QLabel, "viewed_label")
        viewed_label.setText("Viewed: " + ("Yes" if self.is_image_viewed() else "No"))

    def is_image_viewed(self):
        filename = self.file_list[self.current_index]
        return self.viewed_values.get(filename, False)

    def resize_after_image_changed(self):
        # This slot is called when the image_changed signal is emitted
        # It will resize the widget after the image has been changed
        self.resizeEvent(None)

    def set_checkbox_value(self):
        # Get the checkbox widget for the current file
        filename = self.file_list[self.current_index]
        consolidation_checkbox = self.findChild(QCheckBox, "consolidation_checkbox")

        # Set the checkbox value based on the stored value
        checkbox_value = self.checkbox_values.get(filename, False)
        consolidation_checkbox.setChecked(checkbox_value)

    def invert_image(self):
        # Invert the image and update the display
        self.image = 255 - self.image
        self.label.set_image(self.image)

    def rotate_image(self):
        # Rotate the image by 90 degrees and update the display
        self.image = np.rot90(self.image)
        self.label.set_image(self.image)

    def on_window_center_changed(self, value):
        self.label.set_window_center(value)

    def resizeEvent(self, event):
        if self.label.pixmap() is None:
            return

        # Calculate the optimal zoom level and set it to the WindowedLabel
        image_size = self.label.pixmap().size()
        # window_size = event.size()
        window_size = self.size()
        nav_toolbar_height = self.nav_toolbar.height()
        image_toolbar_height = self.image_toolbar.height()
        top_toolbar_height = nav_toolbar_height if nav_toolbar_height > image_toolbar_height else image_toolbar_height

        self.zoom_level = min(
            (window_size.width() - self.checkbox_toolbar.width() - 25) / image_size.width(),
            (window_size.height() - top_toolbar_height - 25) / image_size.height()
        ) * self.zoom
        self.label.setFixedSize(self.zoom_level * image_size)

        # Call the base class method
        super().resizeEvent(event)

    def handle_key_press_event(self, event):
        if event.key() == Qt.Key_Left:
            self.previous_image()
        elif event.key() == Qt.Key_Right:
            self.next_image()
        else:
            super().keyPressEvent(event)

    def save_settings(self):
        # Save current file and index
        settings = QSettings('MyApp', 'DicomViewer')
        settings.setValue('last_file', self.file_list[self.current_index])
        settings.setValue('last_index', self.current_index)

    def save_to_csv(self):

        # file_name, _ = QFileDialog.getSaveFileName(self, "Save File", "", "CSV Files (*.csv)")
        file_dialog = QFileDialog(self, 'Save Progress to CSV File', self.default_directory, 'CSV Files (*.csv)')
        # file_dialog.setOption(QFileDialog.DontUseNativeDialog, True)
        file_dialog.setAcceptMode(QFileDialog.AcceptSave)
        file_dialog.selectFile('*.csv')
        file_dialog.selectFile('untitled.csv')

        if file_dialog.exec_() == QFileDialog.Accepted:
            selected_file = file_dialog.getSaveFileName()
            self.default_directory = file_dialog.directory().path()
            with open(selected_file, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['filename', 'viewed', 'consolidation'])

                for filename in self.file_list:
                    # Get the checkbox values for the file
                    viewed = self.viewed_values.get(filename, False)
                    if viewed != "FAILED":
                        consolidation = self.checkbox_values.get(filename, False)
                    else:
                        consolidation = "FAIL"

                    # Write the checkbox values to the CSV file
                    writer.writerow([filename, viewed, consolidation])

    def load_from_csv(self):
        msg_box = QMessageBox()
        msg_box.setText("Do you want to load previous progress or create a new output file?")
        load_button = msg_box.addButton("Load", QMessageBox.AcceptRole)
        new_button = msg_box.addButton("New", QMessageBox.RejectRole)
        msg_box.setDefaultButton(load_button)
        msg_box.exec_()

        if msg_box.clickedButton() == load_button:
            file_dialog = QFileDialog(self, 'Open previously saved CSV File', self.default_directory, 'CSV Files (*.csv)')
            # file_dialog.setOption(QFileDialog.DontUseNativeDialog, True)
            file_dialog.setFileMode(QFileDialog.ExistingFile)
            file_dialog.selectFile('*.csv')

            if file_dialog.exec_() == QFileDialog.Accepted:
                selected_file = file_dialog.selectedFiles()[0]
                self.default_directory = file_dialog.directory().path()
                with open(selected_file, 'r') as file:
                    reader = csv.reader(file)
                    next(reader)  # Skip the header row
                    for row in reader:
                        filename = row[0]
                        viewed = row[1]
                        viewed = True if viewed == 'True' else False
                        consolidation = row[2]
                        consolidation = True if consolidation == 'True' else False
                        self.checkbox_values[filename] = consolidation
                        self.viewed_values[filename] = viewed
                return True
            else:
                return False
        elif msg_box.clickedButton() == new_button:
            return False

    def on_consolidation_changed(self, state):
        filename = self.file_list[self.current_index]
        self.checkbox_values[filename] = bool(state)
        settings = QSettings('MyApp', 'DicomViewer')
        settings.setValue(filename, state)

    def zoom_in(self):
        self.zoom *= 1.1
        self.resizeEvent(None)

    def zoom_out(self):
        self.zoom /= 1.1
        self.resizeEvent(None)

    def closeEvent(self, event):
        # Ask the user if they want to save before closing
        reply = QMessageBox.question(self, 'Save Changes?', 'Do you want to save changes before closing?',
                                     QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                                     setDefaultButton=QMessageBox.Cancel)
        if reply == QMessageBox.Yes:
            self.save_to_csv()
        elif reply == QMessageBox.Cancel:
            event.ignore()
            return

        event.accept()


def main():
    app = QApplication(sys.argv)
    load_msg_box = QMessageBox()
    load_msg_box.setText("Welcome to Speedy CXR")
    load_msg_box.setInformativeText("Please select the directory containing the DICOM files")
    ok_button = load_msg_box.addButton("Ok", QMessageBox.AcceptRole)
    cancel_button = load_msg_box.addButton("Cancel", QMessageBox.RejectRole)
    load_msg_box.setDefaultButton(ok_button)
    load_msg_box.exec_()

    if load_msg_box.clickedButton() == ok_button:
        # Use QFileDialog to select a directory
        dir_path = QFileDialog.getExistingDirectory(None, "Select DICOM directory")
        if dir_path:
            window = MainWindow(dir_path)
            window.show()
        sys.exit(app.exec_())
    elif load_msg_box.clickedButton() == cancel_button:
        sys.exit()


if __name__ == '__main__':
    main()
