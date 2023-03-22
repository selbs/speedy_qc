"""
main_window.py

This module contains the main window of the application.
"""

import os
import pydicom
import numpy as np
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from pydicom.pixel_data_handlers.util import apply_modality_lut, apply_voi_lut
from qimage2ndarray import array2qimage
from qt_material import get_theme
import qtawesome as qta
from PyQt6.QtCore import QTimer
import datetime
import json
import math

from .custom_windows import AboutMessageBox
from .utils import ConnectionManager, open_yml_file, setup_logging

settings = QSettings('SpeedyQC', 'DicomViewer')
config_file = settings.value("last_config_file", os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.yml"))
config_data = open_yml_file(os.path.join(os.path.dirname(os.path.abspath(__file__)), config_file))
logger, console_msg = setup_logging(config_data['log_dir'])

# Set the default colors for the icons
qta.set_defaults(
    color=get_theme("dark_blue.xml")['primaryLightColor'],
    color_disabled=get_theme("dark_blue.xml")['secondaryDarkColor'],
    color_active=get_theme("dark_blue.xml")['primaryColor'],
)

# Set the icons dictionary used in the main window
icons = {
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
    'not_viewed': qta.icon("mdi.close-circle", color="red", scale=2),
    'question': qta.icon("mdi.help-circle", color="white", scale=2)
}



class CustomGraphicsView(QGraphicsView):
    """
    Custom graphics view to handle zooming, panning, resizing and drawing bounding boxes. This class is used to display
    the DICOM images and is the central widget of the main window.
    """
    def __init__(self, parent=None):
        """
        Initialize the custom graphics view.
        """
        super().__init__()
        # self.connections = {}
        self.connection_manager = ConnectionManager()
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setOptimizationFlag(QGraphicsView.OptimizationFlag.DontAdjustForAntialiasing, True)
        self.setOptimizationFlag(QGraphicsView.OptimizationFlag.DontSavePainterState, True)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.zoom = 1.0
        self.start_rect = None
        self.current_finding = None
        self.current_color = None
        # self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        self.touch_points = []
        self.rect_items = {}

        if isinstance(parent, MainWindow):
            self.connection_manager.connect(parent.resized, self.on_main_window_resized)

    def zoom_in(self, factor=1.2):
        """
        Zoom in by a default factor of 1.2 (20%).

        :param factor: float, the zoom factor.
        """
        self.zoom *= factor
        self.scale(factor, factor)

    def zoom_out(self, factor=0.8):
        """
        Zoom out by a default factor of 0.8 (20%).

        :param factor: float, the zoom factor.
        """
        self.zoom /= factor
        self.scale(factor, factor)

    def on_main_window_resized(self):
        """
        Resize the image and maintain the same zoom when the main window is resized.
        """
        if self.scene() and self.scene().items():
            self.fitInView(self.scene().items()[-1].boundingRect(), Qt.AspectRatioMode.KeepAspectRatio)
            self.scale(self.zoom, self.zoom)

    def mousePressEvent(self, event):
        """
        Start drawing a bounding box when the left mouse button is pressed.

        :param event: QMouseEvent, the mouse press event containing information about the button and position
        """
        if event.button() == Qt.MouseButton.LeftButton:
            if self.scene() and self.current_finding:
                pos = self.mapToScene(event.position().toPoint())
                color = self.current_color
                self.start_rect = BoundingBoxItem(QRectF(pos, QSizeF(0, 0)), color)
                self.scene().addItem(self.start_rect)
                if self.current_finding in self.rect_items:
                    self.rect_items[self.current_finding].append(self.start_rect)
                else:
                    self.rect_items[self.current_finding] = [self.start_rect]
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """
        Update the size of the bounding box as the mouse is moved.

        :param event: QMouseEvent, the mouse move event containing information about the buttons and position
        """
        if event.buttons() & Qt.MouseButton.LeftButton:
            if self.start_rect:
                pos = self.mapToScene(event.position().toPoint())
                width = pos.x() - self.start_rect.rect().x()
                height = pos.y() - self.start_rect.rect().y()
                self.start_rect.setRect(QRectF(self.start_rect.rect().x(), self.start_rect.rect().y(), width, height))
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """
        Stop drawing the bounding box when the left mouse button is released.

        :param event: QMouseEvent, the mouse release event containing information about the button and position
        """
        if event.button() == Qt.MouseButton.LeftButton:
            if self.start_rect:
                self.start_rect = None
        super().mouseReleaseEvent(event)

    def set_current_finding(self, finding, color):
        """
        Set the current finding and color to be used when drawing bounding boxes.

        :param finding: str, the name of the finding/checkbox
        :param color: QColor, the color to be used when drawing the bounding box
        """
        self.current_finding = finding
        self.current_color = color

    def remove_all_bounding_boxes(self):
        """
        Remove all bounding boxes from the scene.
        """
        for finding, bboxes in self.rect_items.items():
            for bbox in bboxes:
                self.scene().removeItem(bbox)
        self.rect_items.clear()

    def add_bboxes(self, rect_items):
        """
        Add previously drawn bounding boxes to the scene.

        :param rect_items: dict, a dictionary of finding/checkbox names and their corresponding bounding boxes
        """
        # Add previously drawn bounding boxes to the scene
        for finding, bboxes in rect_items.items():
            for bbox in bboxes:
                self.scene().addItem(bbox)
                if finding in self.rect_items:
                    self.rect_items[finding].append(bbox)
                else:
                    self.rect_items[finding] = [bbox]

class BoundingBoxItem(QGraphicsRectItem):
    """
    Custom graphics item to handle drawing bounding boxes on DICOM images.
    This class inherits from QGraphicsRectItem and provides selectable, movable, and removable bounding boxes.
    """
    def __init__(self, rect, color, parent=None):
        """
        Initializes a new BoundingBoxItem with the given rectangle, color, and optional parent item.

        :param rect: QRectF, the rectangle defining the bounding box's geometry
        :param color: QColor, the color of the bounding box's border
        :param parent: QGraphicsItem, optional parent item (default: None)
        """
        super().__init__(rect, parent)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)
        self.setPen(QPen(color, 5))

    def contextMenuEvent(self, event):
        """
        Show a context menu when the bounding box is right-clicked, allowing them to be removed.

        :param event: QGraphicsSceneContextMenuEvent, the event that triggered the context menu.
        """
        menu = QMenu()
        remove_action = menu.addAction("Remove")
        selected_action = menu.exec(event.screenPos())

        if selected_action == remove_action:
            self.scene().removeItem(self)

class MainWindow(QMainWindow):
    """
    Main window for the application.
    """
    resized = pyqtSignal()

    def __init__(self, dir_path):
        """
        Initialize the main window.
        :param dir_path: str, the path to the directory containing the DICOM files.
        """
        super().__init__()
        # Initialize UI
        self.setWindowTitle(f"Speedy QC - File: {self.file_list[self.current_index]}")
        self.connection_manager = ConnectionManager()
        self.about_box = AboutMessageBox()
        self.setMouseTracking(True)
        self.setAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents, True)

        # Initialize variables
        self.current_index = 0
        self.checkboxes = {}
        self.colors = {}
        self.icons = icons
        self.default_directory = settings.value("default_directory", os.path.dirname(os.path.abspath(__file__)))
        self.dir_path = dir_path

        # Set the initial window size
        self.resize(1200, 900)

        # Set the window icon
        icon_path = os.path.join(os.path.dirname(__file__), 'assets/3x/white_panel.icns')
        self.setWindowIcon(QIcon(icon_path))

        # Set the central widget to the image viewer
        self.image_view = CustomGraphicsView(self)
        self.image_view.resize(self.size())

        # Load the DICOM file list
        self.file_list = sorted([f for f in os.listdir(self.dir_path) if f.endswith('.dcm')])

        # Load the configuration file
        config = self.open_findings_yml()
        self.findings = config['checkboxes']
        self.max_backups = config['max_backups']
        self.backup_dir = config['backup_dir']

        # Initialize dictionaries for outputs
        self.viewed_values = {f: False for f in self.file_list}
        self.rotation = {f: 0 for f in self.file_list}
        self.notes = {f: "" for f in self.file_list}
        self.checkbox_values = {f: {finding: False for finding in self.findings} for f in self.file_list}
        self.bboxes = {f: {} for f in self.file_list}

        # Assign colors to findings
        self.assign_colors_to_findings()

        # Load the checkbox values from json file
        self.loaded_file, self.loaded = self.load_from_json()
        if self.loaded:
            self.restore_from_saved_state()

        # Now set up the main window layout and toolbars
        main_layout = QVBoxLayout()

        # Create the image scene and set as the central widget
        self.image_scene = QGraphicsScene(self)
        self.pixmap_item = QGraphicsPixmapItem()
        self.load_file()
        self.image_scene.addItem(self.pixmap_item)
        self.image_view.setScene(self.image_scene)
        main_layout.addWidget(self.image_view)
        self.apply_stored_rotation()    # Apply any rotation previously applied to the image
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

        # Create the checkbox toolbar
        self.checkbox_toolbar = QToolBar(self)
        self.create_checkboxes()
        self.set_checkbox_toolbar()
        # Add the textbox for notes
        self.textbox = QTextEdit()
        self.textbox.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        text_action = QWidgetAction(self)
        text_action.setDefaultWidget(self.textbox)
        self.textbox_label = QLabel(self)
        self.textbox_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.textbox_label.setObjectName("Notes")
        self.textbox_label.setText("NOTES:")
        self.checkbox_toolbar.addWidget(self.textbox_label)
        self.checkbox_toolbar.addAction(text_action)

        # Create the image toolbar for image manipulation
        self.image_toolbar = QToolBar(self)
        self.invert_action = QAction(self.icons['inv'], "Invert Grayscale", self)
        self.image_toolbar.addAction(self.invert_action)
        self.rotate_left_action = QAction(self.icons['rot_left'], "Rotate 90° Left", self)
        self.image_toolbar.addAction(self.rotate_left_action)
        self.rotate_right_action = QAction(self.icons['rot_right'], "Rotate 90° Right", self)
        self.image_toolbar.addAction(self.rotate_right_action)

        # Create zoom buttons
        self.zoom_in_action = QAction(self.icons['zoom_in'], "Zoom In", self)
        self.zoom_out_action = QAction(self.icons['zoom_out'], "Zoom Out", self)
        self.image_toolbar.addAction(self.zoom_in_action)
        self.image_toolbar.addAction(self.zoom_out_action)

        # Create sliders for windowing
        self.window_center_label = QAction(self.icons['wc'], "Window Center", self)
        self.window_width_label = QAction(self.icons['ww'], "Window Width", self)
        self.window_center_slider = QSlider(Qt.Orientation.Horizontal)
        self.window_width_slider = QSlider(Qt.Orientation.Horizontal)
        self.window_center_slider.setRange(1, 255)
        self.window_center_slider.setValue(127)
        self.window_width_slider.setRange(1, 450)
        self.window_width_slider.setValue(255)

        # Create a space between the windowing sliders and the next button
        spacer = QSpacerItem(16, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        spacer_layout = QHBoxLayout()
        spacer_widget = QWidget()
        spacer_widget.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        spacer_widget.setLayout(spacer_layout)
        spacer_widget.layout().addItem(spacer)

        # Create a reset window button and label the window sliders
        self.image_toolbar.addSeparator()
        self.reset_window_action = QAction(self.icons['reset_win'], "Reset Windowing", self)
        self.image_toolbar.addAction(self.reset_window_action)
        self.image_toolbar.addAction(self.window_center_label)
        self.image_toolbar.addWidget(self.window_center_slider)
        self.image_toolbar.addAction(self.window_width_label)
        self.image_toolbar.addWidget(self.window_width_slider)
        self.image_toolbar.addWidget(spacer_widget)

        # Add the image toolbar to the top of the main window
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.image_toolbar)

        # Add buttons to the navigator toolbar to navigate to previous and next image
        self.nav_toolbar = QToolBar(self)
        self.prevAction = QAction(self.icons['prev'], "&Back", self)
        self.nextAction = QAction(self.icons['next'], "&Next", self)
        self.nav_toolbar.addAction(self.prevAction)
        self.nav_toolbar.addAction(self.nextAction)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.nav_toolbar)

        # Initiate connections between buttons / sliders and their functions
        self.init_connections()

        # Initiate window menus
        self.init_menus()

        # Backup progress... just in case...
        self.backup_files = None
        self.timer = QTimer()
        self.timer.setInterval(10 * 60 * 1000)  # 10 minutes in milliseconds
        self.connection_manager.connect(self.timer.timeout, self.backup_file)
        self.timer.start()

        # Add and rotate the bounding boxes as necessary to match the rotation of the first image
        self.prep_first_image()

    def prep_first_image(self):
        """
        Add and rotate the bounding boxes as necessary to match the rotation of the first image
        """
        self.rotate_bounding_boxes(
            self.file_list[self.current_index], self.rotation[self.file_list[self.current_index]]
        )
        self.image_view.add_bboxes(self.bboxes.get(self.file_list[self.current_index], {}))

    def init_connections(self):
        """
        Initiate connections between buttons / sliders and their functions
        """
        self.connection_manager.connect(self.textbox.textChanged, self.on_text_changed)
        self.connection_manager.connect(self.invert_action.triggered, self.invert_grayscale)
        self.connection_manager.connect(self.rotate_left_action.triggered, self.rotate_image_left)
        self.connection_manager.connect(self.rotate_right_action.triggered, self.rotate_image_right)
        self.connection_manager.connect(self.zoom_in_action.triggered, self.image_view.zoom_in)
        self.connection_manager.connect(self.zoom_out_action.triggered, self.image_view.zoom_out)
        self.connection_manager.connect(self.reset_window_action.triggered, self.reset_window_sliders)
        self.connection_manager.connect(self.window_center_slider.valueChanged, self.update_image)
        self.connection_manager.connect(self.window_width_slider.valueChanged, self.update_image)
        self.connection_manager.connect(self.nextAction.triggered, self.reset_window_sliders)
        self.connection_manager.connect(self.prevAction.triggered, self.reset_window_sliders)
        self.connection_manager.connect(self.prevAction.triggered, self.previous_image)
        self.connection_manager.connect(self.nextAction.triggered, self.next_image)
        self.connection_manager.connect(self.saveAction.triggered, self.save_to_json)
        self.connection_manager.connect(self.exitAction.triggered, self.quit_app)

    def backup_file(self):
        """
        Backs up the current file to a backup folder when triggered by the timer.
        """

        backup_folder_path = self.backup_dir
        # Create the backup folder if it doesn't exist
        os.makedirs(backup_folder_path, exist_ok=True)

        if self.backup_files is None:
            self.backup_files = backup_folder_path

        # Get the current time as a string
        current_time_str = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

        # Construct the backup file name
        backup_file_name = f"auto_backup_{current_time_str}.bak"

        # Get a list of existing backup files
        backup_files = sorted(
            [f for f in os.listdir(backup_folder_path)])

        # If the number of backup files exceeds the maximum, delete the oldest one
        if len(backup_files) >= self.max_backups:
            os.remove(os.path.join(backup_folder_path, backup_files[0]))
            backup_files.pop(0)

        # Copy the original file to the backup folder with the new name
        self.save_json(os.path.join(backup_folder_path + backup_file_name))

        # Add the new backup file name to the list
        self.backup_files.append(backup_file_name)

        return backup_files

    def wheelEvent(self, event: QWheelEvent):
        """
        Override the wheelEvent function to allow for scrolling with the mouse wheel to change the windowing parameters.
        - Ctrl/Cmd + Scroll: Change window width
        - Shift + Scroll: Change window center

        :param event: QWheelEvent
        """
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
        """
        Opens the config .yml file and returns the data, including the list of findings/checkboxes,
        the maximum number of backups, the backup directory and the log directory.
        """
        last_config_file = settings.value("last_config_file", "config.yml")
        cbox_file = os.path.join(os.path.dirname(__file__), last_config_file)
        return open_yml_file(cbox_file)

    def on_text_changed(self):
        """
        Updates the notes dictionary when the text in the notes textbox is changed.
        """
        textbox = self.sender()
        text_entered = textbox.toPlainText().replace("\n", " ").replace(",", ";")
        self.notes[self.file_list[self.current_index]] = text_entered

    def invert_grayscale(self):
        """
        Inverts the grayscale image.
        """
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
        """
        Rotates the image 90 degrees to the right.
        """
        self.bboxes[self.file_list[self.current_index]] = self.image_view.rect_items.copy()
        # Rotate the image by 90 degrees and update the display
        rotated_image = np.rot90(self.image, k=-1)
        self.rotation[self.file_list[self.current_index]] = (self.rotation[self.file_list[self.current_index]]-90) % 360
        self.image = rotated_image
        self.load_image()
        self.update_image()
        self.rotate_bounding_boxes(self.file_list[self.current_index], -90)

    def rotate_image_left(self):
        """
        Rotates the image 90 degrees to the left.
        """
        self.bboxes[self.file_list[self.current_index]] = self.image_view.rect_items.copy()
        # Rotate the image by 90 degrees and update the display
        rotated_image = np.rot90(self.image, k=1)
        self.rotation[self.file_list[self.current_index]] = (self.rotation[self.file_list[self.current_index]]+90) % 360
        self.image = rotated_image
        self.load_image()
        self.update_image()
        self.rotate_bounding_boxes(self.file_list[self.current_index], 90)

    def apply_stored_rotation(self):
        """
        Applies the stored rotation to the image from previous settings.
        """
        rotation_angle = self.rotation.get(self.file_list[self.current_index], 0)
        self.image = np.rot90(self.image, k=rotation_angle // 90)

    def rotate_bounding_boxes(self, filename, rotation_angle, reverse=False):
        """
        Rotates the bounding boxes around the center of the image to match the image rotation.

        :param filename: str, the name of the image file.
        :param rotation_angle: int, the angle to rotate the bounding boxes by.
        :param reverse: bool, if True, the rotation is reversed, default is False.
        """
        if not reverse:
            rotation_angle = -rotation_angle

        if rotation_angle != 0:
            center = self.pixmap_item.boundingRect().center()
            for finding, bboxes in self.bboxes[filename].items():
                for bbox in bboxes:
                    rect = bbox.rect()

                    rect_center = rect.center()

                    # Translate rect center to the origin
                    rect_center -= QPointF(center.x(), center.y())

                    # Rotate rect center around the origin
                    angle_rad = math.radians(rotation_angle)
                    new_x = rect_center.x() * math.cos(angle_rad) - rect_center.y() * math.sin(angle_rad)
                    new_y = rect_center.x() * math.sin(angle_rad) + rect_center.y() * math.cos(angle_rad)

                    # Translate rect center back to its original position
                    new_center = QPointF(new_x, new_y) + QPointF(center.x(), center.y())

                    # Swap the width and height of the bounding box if the rotation angle is 90 or 270 degrees
                    if rotation_angle % 180 != 0:
                        new_width = rect.height()
                        new_height = rect.width()
                        rect.setWidth(new_width)
                        rect.setHeight(new_height)

                    # Set the new rect center
                    rect.moveCenter(new_center)

                    # Update the bounding box rect
                    bbox.setRect(rect)

    def resizeEvent(self, event):
        """
        Emits a signal to update the image size and zoom when the window is resized.

        :param event: QResizeEvent, the resize event containing the old and new sizes of the widget
        """
        super().resizeEvent(event)
        self.resized.emit()

    def load_file(self):
        """
        Loads the DICOM file and applies the look-up tables.
        """
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
            logger.exception(f"Failed to load file: {file_path} - Message: {str(e)}")

    def load_image(self):
        """
        Loads the image into the image view.
        """
        # Load the image
        qimage = array2qimage(self.image)
        self.pixmap = QPixmap.fromImage(qimage)
        self.pixmap_item.setPixmap(self.pixmap)

    def update_image(self):
        """
        Updates the image in the image view with new windowing settings.
        """
        window_center = self.window_center_slider.value()
        window_width = self.window_width_slider.value()

        img = np.copy(self.image)
        img = img.astype(np.float16)
        img = (img - window_center + 0.5 * window_width) / window_width
        img[img < 0] = 0
        img[img > 1] = 1
        img = (img * 255).astype(np.uint8)

        qimage = array2qimage(img)
        self.pixmap = QPixmap.fromImage(qimage)
        self.pixmap_item.setPixmap(self.pixmap)

    def create_checkboxes(self):
        """
        Creates the checkboxes for the findings.
        """
        filename = self.file_list[self.current_index]
        for cbox in self.findings:
            self.checkboxes[cbox] = QCheckBox(cbox, self)
            self.checkboxes[cbox].setObjectName(cbox)
            self.checkboxes[cbox].setStyleSheet(f"QCheckBox::indicator:checked {{ "
                                                f"background-color: {self.colors[cbox].name()}; "
                                                f"image: url(nocheck);"
                                                f"border: 1px solid #999;"
                                                f"width: 18px;"
                                                f"height: 18px;"
                                                f"}}")
            self.checkboxes[cbox].setChecked(bool(self.checkbox_values.get(filename, False).get(cbox, False)))
            self.connection_manager.connect(self.checkboxes[cbox].stateChanged, self.on_checkbox_changed)

    def set_checkbox_toolbar(self):
        """
        Sets the checkbox toolbar.
        """
        spacer_item = QSpacerItem(0, 5, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        spacer_widget = QWidget()
        spacer_widget.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
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

        # Create a toolbar to hold the checkbox widget
        self.checkbox_toolbar.addWidget(checkbox_widget)
        self.checkbox_toolbar.setStyleSheet("QToolBar QLabel { font-weight: bold; }")
        self.addToolBar(Qt.ToolBarArea.RightToolBarArea, self.checkbox_toolbar)

    def restore_from_saved_state(self):
        """
        Restores the state of the application from the saved state.
        """
        # Check for saved settings and restore last viewed file
        if settings.contains('last_file') and settings.contains('last_index'):
            last_file = settings.value('last_file')
            last_index = settings.value('last_index')
            self.current_index = self.file_list.index(last_file) if last_file in self.file_list else last_index

        # Create a new file list that puts unviewed files after the current file.
        unviewed_files = [f for f in self.file_list[self.current_index + 1:] if not self.viewed_values[f]]
        viewed_files = [f for f in self.file_list[:self.current_index + 1] if self.viewed_values[f]]
        if len(unviewed_files) == 0:
            QMessageBox.information(self, "All Images Viewed", "You have viewed all the images.")
        else:
            self.file_list = unviewed_files + viewed_files

    def reset_window_sliders(self):
        """
        Resets the window sliders to the default values.
        """
        self.window_center_slider.setValue(127)
        self.window_width_slider.setValue(255)

    def change_image(self, direction, prev_failed=False):
        """
        Changes the current image in the file list based on the given direction.

        :param direction: str, either "previous" or "next"
        :param prev_failed: bool, only applicable if direction is "next"
        """
        if direction not in ("previous", "next"):
            raise ValueError("Invalid direction value. Expected 'previous' or 'next'.")

        if direction == "previous":
            self.viewed_values[self.file_list[self.current_index]] = True
        elif not prev_failed:
            self.viewed_values[self.file_list[self.current_index]] = True
        else:
            self.viewed_values[self.file_list[self.current_index]] = "FAILED"

        self.bboxes[self.file_list[self.current_index]] = self.image_view.rect_items.copy()
        self.rotate_bounding_boxes(
            self.file_list[self.current_index], self.rotation[self.file_list[self.current_index]],
            reverse=True
        )
        self.image_view.remove_all_bounding_boxes()

        # Save current file and index
        self.save_settings()

        if direction == "previous":
            self.current_index -= 1
            if self.current_index < 0:
                self.current_index = len(self.file_list) - 1
        else:
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
            else:
                self.current_index = next_unviewed_index

        self.load_file()
        self.apply_stored_rotation()
        self.load_image()
        self.update_image()

        self.window_center_slider.setValue(127)
        self.window_width_slider.setValue(255)

        self.setWindowTitle(f"Speedy QC - File: {self.file_list[self.current_index]}")
        self.image_view.zoom = 1
        self.image_view.fitInView(self.image_view.scene().items()[-1].boundingRect(),
                                  Qt.AspectRatioMode.KeepAspectRatio)

        self.rotate_bounding_boxes(
            self.file_list[self.current_index], self.rotation[self.file_list[self.current_index]]
        )
        self.image_view.add_bboxes(self.bboxes.get(self.file_list[self.current_index], {}))

        self.set_checkbox_value()

        self.viewed_label.setText(("" if self.is_image_viewed() else "NOT ") + "PREVIOUSLY VIEWED")
        self.viewed_icon.setPixmap(
            QPixmap(self.icons['viewed'].pixmap(self.file_tool_bar.iconSize() * 2) if self.is_image_viewed()
                    else self.icons['not_viewed'].pixmap(self.file_tool_bar.iconSize() * 2))
        )

    def previous_image(self):
        """
        Loads the previous image in the file list.
        """
        self.change_image("previous")

    def next_image(self, prev_failed=False):
        """
        Loads the next image in the file list.

        :param prev_failed: bool, whether the image previously failed to load
        """
        self.change_image("next", prev_failed)

    def is_image_viewed(self):
        """
        Checks if the current image has been viewed previously.
        """
        filename = self.file_list[self.current_index]
        return self.viewed_values.get(filename, False)

    def set_checkbox_value(self):
        """
        Sets the checkbox value for the current file.
        """
        # Get the checkbox widget for the current file
        filename = self.file_list[self.current_index]
        for cbox in self.findings:
            # Set the checkbox value based on the stored value
            checkbox_value = self.checkbox_values.get(filename, False)[cbox]
            self.checkboxes[cbox].setChecked(checkbox_value)

    def keyPressEvent(self, event):
        """
        Handles key presses as shortcuts.

        :param event: QKeyEvent, the key press event
        """
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
            self.save_to_json()
        elif event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            if event.key() == Qt.Key.Key_Q:
                QApplication.quit()
        else:
            super().keyPressEvent(event)

    def save_settings(self):
        """
        Saves the current settings to the QSettings.
        """
        # Save current file and index
        settings.setValue('last_file', self.file_list[self.current_index])
        settings.setValue('last_index', self.current_index)
        settings.setValue("max_backups", self.max_backups)
        settings.setValue("backup_dir", self.backup_dir)
        settings.setValue("default_directory", self.default_directory)

    def save_to_json(self):
        """
        Saves the current outputs to a JSON file, by directing to the save or save as method as appropriate.
        """
        if not self.loaded:
            saved = self.save_as()
            if not saved:
                return False
        else:
            self.save_json(self.loaded_file)

    def save_as(self):
        """
        Save as dialog.
        """
        # file_dialog.setOption(QFileDialog.Option.DontUseNativeDialog)
        file_dialog = QFileDialog(self, 'Save to JSON', self.default_directory,
                                  'JSON Files (*.json)')
        file_dialog.setFileMode(QFileDialog.FileMode.AnyFile)
        file_dialog.setDefaultSuffix("json")
        file_dialog.selectFile('untitled.json')
        file_dialog.exec()
        if file_dialog.DialogCode.Accepted:
            save_path = file_dialog.selectedFiles()[0]
            self.save_json(save_path)
            self.default_directory = file_dialog.directory().path()
            self.save_settings()
        else:
            return False

    def save_json(self, selected_file):
        """
        Saves the current outputs to a JSON file.

        :param selected_file: str, the path to the file to save to
        """
        # Update bboxes for current file
        self.bboxes[self.file_list[self.current_index]] = self.image_view.rect_items

        data = []
        for filename in self.file_list:
            cbox_out = {}
            viewed = self.viewed_values.get(filename, False)
            rotation = self.rotation.get(filename, 0)
            for cbox in list(self.checkboxes.keys()):
                # Get the checkbox values for the file
                if viewed != "FAILED":
                    cbox_out[cbox] = self.checkbox_values[filename].get(cbox, False)
                else:
                    cbox_out[cbox] = "FAIL"

            bbox_out = {}
            self.rotate_bounding_boxes(filename, self.rotation.get(filename, 0), reverse=True)
            for finding, bboxes in self.bboxes[filename].items():
                for bbox in bboxes:
                    if finding in bbox_out:
                        bbox_out[finding].append(bbox.rect().getRect())
                    else:
                        bbox_out[finding] = [bbox.rect().getRect()]

            notes = self.notes.get(filename, "")

            data.append({
                'filename': filename,
                'viewed': viewed,
                'rotation': rotation,
                'notes': notes,
                'checkboxes': cbox_out,
                'bboxes': bbox_out
            })

        with open(selected_file, 'w') as file:
            json.dump(data, file, indent=2)


    def load_from_json(self):
        """
        Loads the previous outputs from a JSON file.
        """
        msg_box = QMessageBox()
        msg_box.setText("Do you want to load previous progress or create a new output file?")
        icon_label = QLabel()
        icon_label.setPixmap(self.icons['question'].pixmap(64, 64))
        msg_box.setIconPixmap(icon_label.pixmap())

        load_button = QPushButton("Load")
        msg_box.addButton(load_button, QMessageBox.ButtonRole.AcceptRole)
        new_button = QPushButton("New")
        msg_box.addButton(new_button, QMessageBox.ButtonRole.RejectRole)
        cancel_button = msg_box.addButton(QMessageBox.StandardButton.Cancel)
        msg_box.exec()
        clicked_button = msg_box.clickedButton()

        if clicked_button == load_button:
            file_dialog = QFileDialog(self, 'Open previously saved JSON File', self.default_directory,
                                      'JSON Files (*.json)')
            file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
            file_dialog.exec()

            if file_dialog.DialogCode.Accepted:
                selected_file = file_dialog.selectedFiles()[0]
                self.default_directory = file_dialog.directory().path()

                with open(selected_file, 'r') as file:
                    data = json.load(file)

                for entry in data:
                    filename = entry['filename']
                    self.viewed_values[filename] = entry['viewed']
                    self.rotation[filename] = entry['rotation']
                    self.notes[filename] = entry['notes']

                    if 'checkboxes' in entry:
                        for cbox, value in entry['checkboxes'].items():
                            if filename in self.checkbox_values:
                                self.checkbox_values[filename][cbox] = value
                            else:
                                self.checkbox_values[filename] = {cbox: value}

                    if 'bboxes' in entry:
                        for finding, coord_sets in entry['bboxes'].items():
                            for coord_set in coord_sets:
                                self.load_bounding_box(filename, finding, coord_set)

                return selected_file, True

            else:
                return None, False

        elif clicked_button == new_button:
            return None, False

        elif clicked_button == cancel_button:
            QApplication.quit()

    def load_bounding_box(self, file, finding, raw_rect):
        """
        Loads a bounding box object from the x, y, height, width stored in the JSON file and adds it to the appropriate
        bboxes dictionary entry.

        :param file: str, the file path of the image associated with the bounding box
        :param finding: str, the finding type associated with the bounding box
        :param raw_rect: tuple of (float, float, float, float), the (x, y, width, height) values of the bounding box
        """
        bbx, bby, bbw, bbh = raw_rect
        color = self.colors[finding]
        bbox_item = BoundingBoxItem(QRectF(bbx, bby, bbw, bbh), color)
        if finding in self.bboxes:
            self.bboxes[file][finding].append(bbox_item)
        else:
            self.bboxes[file][finding] = [bbox_item]

    def on_checkbox_changed(self, state):
        """
        Updates the checkbox values when a checkbox is changed, updates the cursor mode, and sets the current finding
        in the image view based on the checkbox state.

        :param state: int, the state of the checkbox (Qt.CheckState.Unchecked or Qt.CheckState.Checked)
        """
        filename = self.file_list[self.current_index]
        cbox = self.sender().text()
        self.checkbox_values[filename][cbox] = bool(state)
        settings.setValue(filename, state)

        if state:
            self.image_view.setDragMode(QGraphicsView.DragMode.NoDrag)
            self.image_view.viewport().setCursor(QCursor(Qt.CursorShape.CrossCursor))
            sender = self.sender()
            if isinstance(sender, QCheckBox):
                self.image_view.set_current_finding(cbox, self.colors[cbox])
        else:
            self.image_view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            self.image_view.viewport().setCursor(QCursor(Qt.CursorShape.ArrowCursor))
            self.image_view.set_current_finding(None, None)

    def assign_colors_to_findings(self):
        """
        Assigns a color to each finding/checkbox.
        """
        colors = [
            QColor(255, 0, 0), QColor(0, 255, 0), QColor(0, 0, 255),
            QColor(255, 255, 0), QColor(0, 255, 255), QColor(255, 0, 255),
        ]

        for idx, finding in enumerate(self.findings):
            color = colors[idx % len(colors)]
            self.colors[finding] = color

    def closeEvent(self, event):
        """
        Handles the close event.

        :param event: QCloseEvent, the close event
        """
        # Ask the user if they want to save before closing

        close_msg_box = QMessageBox()

        icon_label = QLabel()
        icon_label.setPixmap(self.icons['question'].pixmap(64, 64))
        close_msg_box.setIconPixmap(icon_label.pixmap())

        close_msg_box.setText("Save Changes?")
        close_msg_box.setInformativeText("Do you want to save changes before closing?")
        close_msg_box.setStandardButtons(QMessageBox.StandardButton.Yes |
                                         QMessageBox.StandardButton.No |
                                         QMessageBox.StandardButton.Cancel)
        close_msg_box.setDefaultButton(QMessageBox.StandardButton.Yes)

        clicked_button = close_msg_box.exec()
        if clicked_button == close_msg_box.StandardButton.Yes:
            saved = self.save_to_json()
            if not saved:
                event.ignore()
                return
        elif clicked_button == QMessageBox.StandardButton.Cancel:
            event.ignore()
            return

        event.accept()

    def init_menus(self):
        """
        Initializes the menus.
        """
        # create the file menu
        file_menu = QMenu("&File", self)
        menu_save_action = QAction("&Save", self)
        menu_save_as_action = QAction("&Save As...", self)
        menu_exit_action = QAction("&Exit", self)
        file_menu.addAction(menu_save_action)
        file_menu.addAction(menu_save_as_action)
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

        self.connection_manager.connect(menu_save_action.triggered, self.save_to_json)
        self.connection_manager.connect(menu_save_as_action.triggered, self.save_as)
        self.connection_manager.connect(menu_exit_action.triggered, self.quit_app)
        self.connection_manager.connect(about_action.triggered, self.show_about)

    def show_about(self):
        """
        Shows the about box.
        """
        self.about_box.exec()

    def quit_app(self):
        """
        Quits the application, disconnecting all signals.
        """
        self.timer.stop()
        self.connection_manager.disconnect_all()
        self.about_box.connection_manager.disconnect_all()
        self.image_view.connection_manager.disconnect_all()
        QApplication.quit()
