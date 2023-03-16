import os
import sys
import pydicom
import numpy as np
from PyQt6.QtWidgets import QApplication, QLabel, QMainWindow, QSizePolicy, QScrollArea, QPushButton, QHBoxLayout, \
    QVBoxLayout, QSlider, QWidget, QFileDialog, QCheckBox, QToolBar, QStyle, QSpacerItem, QMessageBox, QDialog, \
    QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QToolButton, QTextEdit, QMenu, QWidgetAction, QMenuBar, \
    QTreeView
from PyQt6.QtGui import QImage, QPixmap, QPainter, QAction, QIcon, QTransform, QImage, QPixmap, QNativeGestureEvent, \
    QTouchEvent, QWheelEvent
from PyQt6.QtCore import Qt, QSettings, pyqtSignal, QRectF, QEvent, QPoint, QPointF, pyqtSlot
from pydicom.pixel_data_handlers.util import apply_modality_lut, apply_voi_lut
import csv
from qimage2ndarray import array2qimage
from qt_material import apply_stylesheet, get_theme
import qtawesome as qta
import yaml
from PyQt6.QtCore import QTimer
import datetime
import shutil


class CustomGraphicsView(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__()
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setOptimizationFlag(QGraphicsView.OptimizationFlag.DontAdjustForAntialiasing, True)
        self.setOptimizationFlag(QGraphicsView.OptimizationFlag.DontSavePainterState, True)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.previous_size = None
        self.zoom = 1.0
        # self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        self.touch_points = []

        if isinstance(parent, MainWindow):
            parent.resized.connect(self.on_main_window_resized)

    def zoom_in(self):
        factor = 1.2
        self.zoom *= factor
        self.scale(factor, factor)

    def zoom_out(self):
        factor = 0.8
        self.zoom /= factor
        self.scale(factor, factor)

    def on_main_window_resized(self):
        if self.scene() and self.scene().items():
            self.fitInView(self.scene().items()[0].boundingRect(), Qt.AspectRatioMode.KeepAspectRatio)
            self.scale(self.zoom, self.zoom)


class MainWindow(QMainWindow):
    resized = pyqtSignal()

    def __init__(self, dir_path):
        super().__init__()
        # Set the initial window size
        self.resize(1200, 900)
        # Set the minimum window size
        # self.setMinimumSize(500, 300)
        self.default_directory = '.'
        self.current_index = 0
        self.setMouseTracking(True)
        self.setAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents, True)

        self.image_view = CustomGraphicsView(self)
        self.image_view.resize(self.size())

        qta.set_defaults(
            color=get_theme("dark_blue.xml")['primaryLightColor'],
            color_disabled=get_theme("dark_blue.xml")['secondaryDarkColor'],
            color_active=get_theme("dark_blue.xml")['primaryColor'],
        )

        # Icons
        self.icons = {
            'save': qta.icon("mdi.content-save-all"),
            'next': qta.icon("mdi.arrow-right-circle"),
            'prev': qta.icon("mdi.arrow-left-circle"),
            'ww': qta.icon("mdi.arrow-expand-horizontal"),
            'wc': qta.icon("mdi.format-horizontal-align-center"),
            'inv': qta.icon("mdi.invert-colors"),
            'rot_right': qta.icon("mdi.rotate-right"),
            'rot_left': qta.icon("mdi.rotate-left"),
            'zoom_in': qta.icon("mdi.magnify-plus"),
            'zoom_out': qta.icon("mdi.magnify-minus"),
            'exit': qta.icon("mdi.exit-to-app"),
            'reset_win': qta.icon("mdi.credit-card-refresh"),
            'viewed': qta.icon("mdi.checkbox-marked-circle", color="green", scale=2),
            'not_viewed': qta.icon("mdi.close-circle", color="red", scale=2)
        }

        self.dir_path = dir_path
        self.file_list = sorted([f for f in os.listdir(self.dir_path) if f.endswith('.dcm')])
        self.findings = self.open_findings_yml()
        self.viewed_values = {f: False for f in self.file_list}
        self.notes = {f: "" for f in self.file_list}
        self.checkbox_values = {f: {finding: False for finding in self.findings} for f in self.file_list}
        self.checkboxes = {}

        # Load the checkbox values from CSV file
        self.loaded_file, self.loaded = self.load_from_csv()
        if self.loaded:
            self.restore_from_saved_state()

        # Load the current DICOM file
        self.load_file()

        main_layout = QVBoxLayout()

        self.image_scene = QGraphicsScene(self)
        # Create a QGraphicsPixmapItem to hold the image
        self.pixmap_item = QGraphicsPixmapItem()
        self.image_scene.addItem(self.pixmap_item)
        self.image_view.setScene(self.image_scene)

        main_layout.addWidget(self.image_view)
        self.load_image()

        central_widget = QWidget(self)
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # Create the navigation toolbar
        self.file_tool_bar = QToolBar(self)
        self.exitAction = QAction(self.icons['exit'], "&Exit", self)
        self.file_tool_bar.addAction(self.exitAction)
        self.saveAction = QAction(self.icons['save'], "&Save", self)
        self.file_tool_bar.addAction(self.saveAction)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.file_tool_bar)

        self.checkbox_toolbar = QToolBar(self)
        self.create_checkboxes()
        self.set_checkbox_toolbar(self.checkboxes)

        textbox = QTextEdit()
        textbox.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        textbox.textChanged.connect(self.on_text_changed)
        text_action = QWidgetAction(self)
        text_action.setDefaultWidget(textbox)
        self.textbox_label = QLabel(self)
        self.textbox_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.textbox_label.setObjectName("Notes")
        self.textbox_label.setText("NOTES:")
        self.checkbox_toolbar.addWidget(self.textbox_label)
        self.checkbox_toolbar.addAction(text_action)

        # Create the image toolbar
        self.image_toolbar = QToolBar(self)
        self.invert_action = QAction(self.icons['inv'], "Invert Grayscale", self)
        self.invert_action.triggered.connect(self.invert_grayscale)
        self.image_toolbar.addAction(self.invert_action)
        self.rotate_left_action = QAction(self.icons['rot_left'], "Rotate 90° Left", self)
        self.rotate_left_action.triggered.connect(self.rotate_image_left)
        self.image_toolbar.addAction(self.rotate_left_action)
        self.rotate_right_action = QAction(self.icons['rot_right'], "Rotate 90° Right", self)
        self.rotate_right_action.triggered.connect(self.rotate_image_right)
        self.image_toolbar.addAction(self.rotate_right_action)

        # Create zoom buttons
        self.zoom_in_action = QAction(self.icons['zoom_in'], "Zoom In", self)
        self.zoom_out_action = QAction(self.icons['zoom_out'], "Zoom Out", self)
        self.zoom_in_action.triggered.connect(self.image_view.zoom_in)
        self.zoom_out_action.triggered.connect(self.image_view.zoom_out)
        self.image_toolbar.addAction(self.zoom_in_action)
        self.image_toolbar.addAction(self.zoom_out_action)

        # Create sliders for window center
        self.window_center_label = QAction(self.icons['wc'], "Window Center", self)
        self.window_width_label = QAction(self.icons['ww'], "Window Width", self)
        self.window_center_slider = QSlider(Qt.Orientation.Horizontal)
        self.window_width_slider = QSlider(Qt.Orientation.Horizontal)
        self.window_center_slider.setRange(1, 255)
        self.window_center_slider.setValue(127)
        self.window_width_slider.setRange(1, 450)
        self.window_width_slider.setValue(255)

        spacer = QSpacerItem(16, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        spacer_layout = QHBoxLayout()
        spacer_widget = QWidget()
        spacer_widget.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        spacer_widget.setLayout(spacer_layout)
        spacer_widget.layout().addItem(spacer)

        # Connect the nav buttons to their functions and to reset the windowing parameters
        self.image_toolbar.addSeparator()
        self.reset_window_action = QAction(self.icons['reset_win'], "Reset Windowing", self)
        self.reset_window_action.triggered.connect(self.reset_window_sliders)
        self.image_toolbar.addAction(self.reset_window_action)

        self.image_toolbar.addAction(self.window_center_label)
        self.image_toolbar.addWidget(self.window_center_slider)
        # self.image_toolbar.addWidget(spacer)
        self.image_toolbar.addAction(self.window_width_label)
        self.image_toolbar.addWidget(self.window_width_slider)
        self.image_toolbar.addWidget(spacer_widget)

        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.image_toolbar)

        # Add buttons to navigate to previous and next image
        self.nav_toolbar = QToolBar(self)
        self.prevAction = QAction(self.icons['prev'], "&Back", self)
        self.nextAction = QAction(self.icons['next'], "&Next", self)
        self.nav_toolbar.addAction(self.prevAction)
        self.nav_toolbar.addAction(self.nextAction)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.nav_toolbar)

        # Connections between buttons / sliders and their functions
        self.window_center_slider.valueChanged.connect(self.update_image)
        self.window_width_slider.valueChanged.connect(self.update_image)
        self.nextAction.triggered.connect(self.reset_window_sliders)
        self.prevAction.triggered.connect(self.reset_window_sliders)
        self.prevAction.triggered.connect(self.previous_image)
        self.nextAction.triggered.connect(self.next_image)
        self.saveAction.triggered.connect(self.save_to_csv)
        self.exitAction.triggered.connect(self.close)

        self.init_menus()

        # Backup progress just in case...
        self.backup_files = None
        self.timer = QTimer()
        self.timer.setInterval(10 * 60 * 1000)  # 10 minutes in milliseconds
        self.timer.timeout.connect(self.backup_file)
        self.timer.start()

    def backup_file(self, max_backups=5):

        current_file_path = os.path.abspath(__file__)
        backup_folder_path = os.path.dirname(os.path.dirname(current_file_path)) + "/backups"
        # Create the backup folder if it doesn't exist
        os.makedirs(backup_folder_path, exist_ok=True)

        if self.backup_files is None:
            self.backup_files = os.listdir(backup_folder_path)

        # Get the current time as a string
        current_time_str = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

        # Construct the backup file name
        backup_file_name = f"auto_backup_{current_time_str}.bak"

        # Get a list of existing backup files
        backup_files = sorted(
            [f for f in os.listdir(backup_folder_path) if os.path.isfile(os.path.join(backup_folder_path, f))])

        # If the number of backup files exceeds the maximum, delete the oldest one
        if len(backup_files) >= max_backups:
            os.remove(os.path.join(backup_folder_path, backup_files[0]))
            backup_files.pop(0)

        # Copy the original file to the backup folder with the new name
        self.save_csv(os.path.join(backup_folder_path, backup_file_name))

        # Add the new backup file name to the list
        self.backup_files.append(backup_file_name)

        return backup_files

    def wheelEvent(self, event: QWheelEvent):
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:  # check if Ctrl key is pressed
            delta = event.angleDelta().y()  # get the scroll direction
            if delta > 0:
                # increase window width
                self.window_width_slider.setValue(self.window_width_slider.value() + 10)
            elif delta < 0:
                # decrease window width
                self.window_width_slider.setValue(self.window_width_slider.value() - 10)
        elif event.modifiers() == Qt.KeyboardModifier.ShiftModifier:  # check if Shft key is pressed
            delta = event.angleDelta().y()  # get the scroll direction
            if delta > 0:
                # increase window width
                self.window_center_slider.setValue(self.window_center_slider.value() + 5)
            elif delta < 0:
                # decrease window width
                self.window_center_slider.setValue(self.window_center_slider.value() - 5)
        else:
            super().wheelEvent(event)

    def open_findings_yml(self):
        with open('./checkboxes.yml', 'r') as file:
            data = yaml.load(file, Loader=yaml.FullLoader)

        return data['checkboxes']

    def on_text_changed(self):
        textbox = self.sender()
        text_entered = textbox.toPlainText().replace("\n", " ").replace(",", ";")
        self.notes[self.file_list[self.current_index]] = text_entered

    def invert_grayscale(self):
        if self.image is not None:
            # Invert the image
            inverted_image = 255 - self.image

            # Update the QPixmap
            qimage = array2qimage(inverted_image)
            pixmap = QPixmap.fromImage(qimage)
            self.pixmap_item.setPixmap(pixmap)

            # Update the image attribute to store the inverted image
            self.image = inverted_image

    def rotate_image_right(self):
        print(self.window_width_slider.value(), self.window_center_slider.value())
        # Rotate the image by 90 degrees and update the display
        rotated_image = np.rot90(self.image)
        qimage = array2qimage(rotated_image)
        pixmap = QPixmap.fromImage(qimage)
        self.pixmap_item.setPixmap(pixmap)
        self.image = rotated_image
        print(self.window_width_slider.value(), self.window_center_slider.value())
        self.update_image()
        print(self.window_width_slider.value(), self.window_center_slider.value())

    def rotate_image_left(self):
        print(self.window_width_slider.value(), self.window_center_slider.value())
        # Rotate the image by 90 degrees and update the display
        rotated_image = np.rot90(self.image, k=-1)
        qimage = array2qimage(rotated_image)
        pixmap = QPixmap.fromImage(qimage)
        self.pixmap_item.setPixmap(pixmap)
        self.image = rotated_image
        print(self.window_width_slider.value(), self.window_center_slider.value())
        self.update_image()
        print(self.window_width_slider.value(), self.window_center_slider.value())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.resized.emit()

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
                self.image = np.uint8(self.image)
        except Exception as e:
            # Handle the exception (e.g. display an error message)
            QMessageBox.critical(self, "Error", f"Failed to load file:\n{str(e)}", QMessageBox.StandardButton.Ok,
                                 defaultButton=QMessageBox.StandardButton.Ok)
            self.next_image(prev_failed=True)

    def load_image(self):
        # Load the image
        qimage = array2qimage(self.image)
        self.pixmap = QPixmap.fromImage(qimage)
        self.pixmap_item.setPixmap(self.pixmap)

    def update_image(self):
        window_center = self.window_center_slider.value()
        window_width = self.window_width_slider.value()

        img = np.copy(self.image)
        img = img.astype(np.float16)
        img = (img - window_center + 0.5 * window_width) / window_width
        img[img < 0] = 0
        img[img > 1] = 1
        img = (img * 255).astype(np.uint8)

        # height, width = img.shape
        # bytes_per_line = width
        # qimage = QImage(img.data.tobytes(), width, height, bytes_per_line, QImage.Format.Format_Grayscale8)
        qimage = array2qimage(img)
        self.pixmap = QPixmap.fromImage(qimage)

        self.pixmap_item.setPixmap(self.pixmap)
        # self.image_view.setScene(self.pixmap_item)
        # self.image_view.fitInView(self.pixmap_item.boundingRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def create_checkboxes(self):
        filename = self.file_list[self.current_index]
        for cbox in self.findings:
            self.checkboxes[cbox] = QCheckBox(cbox, self)
            self.checkboxes[cbox].setObjectName(cbox)
            self.checkboxes[cbox].setChecked(bool(self.checkbox_values.get(filename, False).get(cbox, False)))
            self.checkboxes[cbox].stateChanged.connect(self.on_checkbox_changed)

    def set_checkbox_toolbar(self, checkboxes):
        spacer_item = QSpacerItem(0, 5, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        spacer_widget = QWidget()
        spacer_widget.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        # spacer_widget.setMaximumHeight(25)
        # spacer_widget.setMinimumHeight(25)
        spacer_widget.setLayout(QHBoxLayout())
        spacer_widget.layout().addItem(spacer_item)
        self.checkbox_toolbar.addWidget(spacer_widget)

        self.viewed_label = QLabel(self)
        self.viewed_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.viewed_label.setObjectName("viewed_label")
        self.viewed_label.setText(("" if self.is_image_viewed() else "NOT ") + "PREVIOUSLY VIEWED")
        self.checkbox_toolbar.addWidget(self.viewed_label)

        self.viewed_icon = QLabel(self)
        self.viewed_icon.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.viewed_icon.setPixmap(
            QPixmap(self.icons['viewed'].pixmap(self.file_tool_bar.iconSize() * 2) if self.is_image_viewed()
                    else self.icons['not_viewed'].pixmap(self.file_tool_bar.iconSize() * 2))
        )
        self.checkbox_toolbar.addWidget(self.viewed_icon)

        # self.checkbox_toolbar.addWidget(spacer_widget)
        spacer_widget = QWidget()
        spacer_widget.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        # spacer_widget.setMaximumHeight(25)
        # spacer_widget.setMinimumHeight(25)
        spacer_widget.setLayout(QHBoxLayout())
        spacer_widget.layout().addItem(spacer_item)
        self.checkbox_toolbar.addWidget(spacer_widget)

        checkbox_heading = QLabel(self)
        checkbox_heading.setAlignment(Qt.AlignmentFlag.AlignLeft)
        checkbox_heading.setText("FINDINGS:")
        self.checkbox_toolbar.addWidget(checkbox_heading)

        checkbox_layout = QVBoxLayout()
        for finding, checkbox in self.checkboxes.items():
            checkbox_layout.addWidget(checkbox)

        checkbox_layout.addItem(spacer_item)
        checkbox_layout.addItem(spacer_item)
        checkbox_widget = QWidget(self)
        checkbox_widget.setLayout(checkbox_layout)
        # checkbox_widget.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        # Create a toolbar to hold the checkbox widget
        self.checkbox_toolbar.addWidget(checkbox_widget)
        self.checkbox_toolbar.setStyleSheet("QToolBar QLabel { font-weight: bold; }")
        self.addToolBar(Qt.ToolBarArea.RightToolBarArea, self.checkbox_toolbar)

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

    def reset_window_sliders(self):
        self.window_center_slider.setValue(127)
        self.window_center_slider.setValue(255)

    def previous_image(self):
        self.viewed_values[self.file_list[self.current_index]] = True

        # Save current file and index
        self.save_settings()

        # Load previous file
        self.current_index -= 1
        if self.current_index < 0:
            self.current_index = len(self.file_list) - 1
        self.load_file()
        self.load_image()
        self.update_image()

        self.window_center_slider.setValue(127)
        self.window_width_slider.setValue(255)

        # Update the image
        self.setWindowTitle(f"Speedy QC - File: {self.file_list[self.current_index]}")
        self.image_view.zoom = 1
        self.image_view.fitInView(self.image_view.scene().items()[0].boundingRect(), Qt.AspectRatioMode.KeepAspectRatio)

        # Set the checkbox value for the current file
        self.set_checkbox_value()

        # viewed_icon = self.findChild(QAction, "viewed_icon")
        self.viewed_label.setText(("" if self.is_image_viewed() else "NOT ") + "PREVIOUSLY VIEWED")
        self.viewed_icon.setPixmap(
            QPixmap(self.icons['viewed'].pixmap(self.file_tool_bar.iconSize() * 2) if self.is_image_viewed()
                    else self.icons['not_viewed'].pixmap(self.file_tool_bar.iconSize() * 2))
        )

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

        self.window_center_slider.setValue(127)
        self.window_width_slider.setValue(255)

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

        self.load_image()
        self.update_image()

        # Update the image display
        self.setWindowTitle(f"Dicom Viewer - {self.file_list[self.current_index]}")
        self.image_view.fitInView(self.image_view.scene().items()[0].boundingRect(), Qt.AspectRatioMode.KeepAspectRatio)
        self.image_view.zoom = 1

        # Set the checkbox value for the current file
        self.set_checkbox_value()

        self.viewed_label.setText(("" if self.is_image_viewed() else "NOT ") + "PREVIOUSLY VIEWED")
        self.viewed_icon.setPixmap(
            QPixmap(self.icons['viewed'].pixmap(self.file_tool_bar.iconSize() * 2) if self.is_image_viewed()
                    else self.icons['not_viewed'].pixmap(self.file_tool_bar.iconSize() * 2))
        )

    def is_image_viewed(self):
        filename = self.file_list[self.current_index]
        return self.viewed_values.get(filename, False)

    def set_checkbox_value(self):
        # Get the checkbox widget for the current file
        filename = self.file_list[self.current_index]
        for cbox in self.findings:
            # Set the checkbox value based on the stored value
            checkbox_value = self.checkbox_values.get(filename, False)[cbox]
            self.checkboxes[cbox].setChecked(checkbox_value)

    def keyPressEvent(self, event):
        # Set up shortcuts
        # if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
        if event.key() == Qt.Key.Key_B:
            self.previous_image()
        elif event.key() == Qt.Key.Key_N:
            self.next_image()
        elif event.key() == Qt.Key.Key_Minus or event.key() == Qt.Key.Key_Underscore:
            self.image_view.zoom_out()
        elif event.key() == Qt.Key.Key_Plus or event.key() == Qt.Key.Key_Equal:
            self.image_view.zoom_in()
        elif event.key() == Qt.Key.Key_I:
            self.invert_grayscale()
        elif event.key() == Qt.Key.Key_R:
            self.rotate_image_right()
        elif event.key() == Qt.Key.Key_L:
            self.rotate_image_left()
        elif event.key() == Qt.Key.Key_S:
            self.save_to_csv()
        elif event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            if event.key() == Qt.Key.Key_Q:
                self.close()
        else:
            super().keyPressEvent(event)

    def save_settings(self):
        # Save current file and index
        settings = QSettings('MyApp', 'DicomViewer')
        settings.setValue('last_file', self.file_list[self.current_index])
        settings.setValue('last_index', self.current_index)

    def save_to_csv(self):
        if not self.loaded:
            saved = self.save_as()
            if not saved:
                return False
        else:
            self.save_csv(self.loaded_file)

    def save_as(self):
        file_dialog = QFileDialog()
        # file_dialog.setOption(QFileDialog.Option.DontUseNativeDialog)
        file_dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
        file_dialog.setFileMode(QFileDialog.FileMode.AnyFile)
        file_dialog.setNameFilters(['CSV Files (*.csv)'])
        file_dialog.setDefaultSuffix("csv")
        file_dialog.selectFile('untitled.csv')
        file_dialog.setWindowTitle("Save to CSV")
        if file_dialog.exec() == QDialog.DialogCode.Accepted:
            save_path = file_dialog.selectedFiles()[0]
            self.save_csv(save_path)
            self.default_directory = file_dialog.directory().path()
        if file_dialog.exec() == QDialog.DialogCode.Rejected:
            return False

    def save_csv(self, selected_file):
        with open(selected_file, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['filename', 'viewed', 'notes'] + list(self.checkboxes.keys()))

            for filename in self.file_list:
                cbox_out = {}
                viewed = self.viewed_values.get(filename, False)
                for cbox in list(self.checkboxes.keys()):
                    # Get the checkbox values for the file
                    if viewed != "FAILED":
                        cbox_out[cbox] = self.checkbox_values.get(filename, False)
                    else:
                        cbox_out[cbox] = "FAIL"

                notes = self.notes.get(filename, "")
                # Write the checkbox values to the CSV file
                writer.writerow([filename, viewed, notes] + list(cbox_out.values()))

    def load_from_csv(self):
        msg_box = QMessageBox()
        msg_box.setText("Do you want to load previous progress or create a new output file?")
        load_button = QPushButton("Load")
        msg_box.addButton(load_button, QMessageBox.ButtonRole.AcceptRole)
        new_button = QPushButton("New")
        # cancel_button = QPushButton("Cancel")
        msg_box.addButton(new_button, QMessageBox.ButtonRole.RejectRole)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Cancel)
        # msg_box.addButton(cancel_button, QMessageBox.ButtonRole.RejectRole)
        msg_box.setDefaultButton(load_button)
        msg_box.exec()

        if msg_box.clickedButton() == load_button:
            file_dialog = QFileDialog(self, 'Open previously saved CSV File', self.default_directory,
                                      'CSV Files (*.csv)')
            # file_dialog.setOption(QFileDialog.Option.DontUseNativeDialog)
            file_dialog.setNameFilters(['CSV Files (*.csv)'])
            file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
            # Set the color of the directory items
            # file_dialog.setStyleSheet(
            #     f"""color: white;
            #     background-color: {get_theme('dark_blue.xml')['primaryColor']};
            #     """
            # )

            if file_dialog.exec() == QDialog.DialogCode.Accepted:
                selected_file = file_dialog.selectedFiles()[0]
                self.default_directory = file_dialog.directory().path()
                with open(selected_file, 'r') as file:
                    reader = csv.reader(file)
                    next(reader)  # Skip the header row
                    for row in reader:
                        filename = row[0]
                        self.viewed_values[filename] = row[1]
                        self.notes[filename] = row[2]
                        self.viewed_values[filename] = True if self.viewed_values[filename] == 'True' else False
                        for i, cbox in enumerate(self.checkboxes.keys()):
                            self.checkbox_values[filename][cbox] = row[3 + i]
                            self.checkbox_values[filename][cbox] = True \
                                if self.checkbox_values[filename][cbox] == 'True' else False
                return selected_file, True
            else:
                return None, False
        elif msg_box.clickedButton() == new_button:
            return None, False
        elif msg_box.StandardButton.Cancel:
            sys.exit()

    def on_checkbox_changed(self, state):
        filename = self.file_list[self.current_index]
        cbox = self.sender().text()
        print(cbox, state)
        self.checkbox_values[filename][cbox] = bool(state)
        settings = QSettings('MyApp', 'DicomViewer')
        settings.setValue(filename, state)

    def closeEvent(self, event):
        # Ask the user if they want to save before closing

        close_msg_box = QMessageBox()
        close_msg_box.setIcon(QMessageBox.Icon.Question)
        close_msg_box.setText("Save Changes?")
        close_msg_box.setInformativeText("Do you want to save changes before closing?")
        close_msg_box.setStandardButtons(QMessageBox.StandardButton.Yes |
                                         QMessageBox.StandardButton.No |
                                         QMessageBox.StandardButton.Cancel)
        close_msg_box.setDefaultButton(QMessageBox.StandardButton.Yes)

        clicked_button = close_msg_box.exec()
        if clicked_button == close_msg_box.StandardButton.Yes:
            saved = self.save_to_csv()
            if not saved:
                event.ignore()
                return
        elif clicked_button == QMessageBox.StandardButton.Cancel:
            event.ignore()
            return

        event.accept()

    def init_menus(self):
        # create the file menu
        file_menu = QMenu("&File", self)
        save_action = QAction("&Save", self)
        save_as_action = QAction("&Save As...", self)
        menu_exit_action = QAction("&Exit", self)
        file_menu.addAction(save_action)
        file_menu.addAction(save_as_action)
        file_menu.addSeparator()
        file_menu.addAction(menu_exit_action)

        # create the help menu
        help_menu = QMenu("Help", self)
        help_action = QAction("Help", self)
        about_action = QAction("About", self)
        help_menu.addAction(help_action)
        help_menu.addAction(about_action)

        # add the menus to the menu bar
        menu_bar = QMenuBar(self)
        menu_bar.addMenu(file_menu)
        menu_bar.addMenu(help_menu)
        self.setMenuBar(menu_bar)

        save_action.triggered.connect(self.save_to_csv)
        save_as_action.triggered.connect(self.save_as)
        menu_exit_action.triggered.connect(self.close)

        # about_action.triggered.connect(self.show_help)
        about_action.triggered.connect(self.show_about)

    # def show_help(self):
    def show_about(self):
        about_box = QMessageBox()
        about_box.setWindowTitle("About...")
        about_box.setIcon(QMessageBox.Icon.Information)
        about_box.setText("Speedy QC for Desktop")
        about_box.setInformativeText("MIT License\nCopyright (c) 2023, Ian Selby")

        about_box.setDetailedText("Permission is hereby granted, free of charge, to any person obtaining a copy of "
                                  "this software and associated documentation files (the 'Software'), to deal in "
                                  "the Software without restriction, including without limitation the rights to "
                                  "use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of "
                                  "the Software, and to permit persons to whom the Software is furnished to do so, "
                                  "subject to the following conditions:\n\nThe above copyright notice and this "
                                  "permission notice shall be included in all copies or substantial portions of the "
                                  "Software.\n\nTHE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, "
                                  "EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF "
                                  "MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO "
                                  "EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, "
                                  "DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, "
                                  "ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER "
                                  "DEALINGS IN THE SOFTWARE.")

        about_box.setTextInteractionFlags(Qt.TextInteractionFlag.LinksAccessibleByMouse)
        about_box_label = QLabel()
        about_box_label.setTextFormat(Qt.TextFormat.RichText)
        about_box_label.setText("<a href='https://www.example.com'>www.example.com</a>")
        about_box_label.setOpenExternalLinks(True)

        about_box.layout().addWidget(about_box_label)

        about_box.exec()

def main():
    app = QApplication(sys.argv)

    apply_stylesheet(app, theme='dark_blue.xml')

    load_msg_box = QMessageBox()
    load_msg_box.setText("Welcome to Speedy QC for Desktop")
    load_msg_box.setInformativeText("Copyright (c) 2023, Ian Selby, MIT License\n\n"
                                    "Please select the directory containing the DICOM files...")
    ok_button = load_msg_box.addButton("Ok", QMessageBox.ButtonRole.AcceptRole)
    cancel_button = load_msg_box.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
    load_msg_box.setDefaultButton(ok_button)
    load_msg_box.exec()

    if load_msg_box.clickedButton() == ok_button:
        # Use QFileDialog to select a directory
        dir_dialog = QFileDialog()
        # dir_dialog.setOption(QFileDialog.Option.DontUseNativeDialog)
        dir_dialog.setFileMode(QFileDialog.FileMode.Directory)
        dir_dialog.setWindowTitle("Select DICOM directory")
        # dir_dialog.setStyleSheet(
        #     f"background-color: {get_theme('dark_blue.xml')['primaryLightColor']}; "
        # )
        if dir_dialog.exec() == QDialog.DialogCode.Accepted:
            dir_path = dir_dialog.selectedFiles()[0]
            if dir_path:
                window = MainWindow(dir_path)
                window.show()
        sys.exit(app.exec())
    elif load_msg_box.clickedButton() == cancel_button:
        sys.exit()


if __name__ == '__main__':
    main()
