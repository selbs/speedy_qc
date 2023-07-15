"""
graphics.py: Custom graphics items for the Speedy QC Package.

This module defines custom graphics items for the Speedy QC Package to allow for drawing bounding boxes on images.

Classes:
    - BoundingBoxItem: Custom graphics item to handle drawing bounding boxes on images.
    - CustomGraphicsView: Custom graphics view to handle drawing bounding boxes on images.
"""

from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from typing import Optional, Dict, List
from speedy_qc.utils import ConnectionManager
import math


class BoundingBoxItem(QGraphicsRectItem):
    """
    Custom graphics item to handle drawing bounding boxes on images.
    This class inherits from QGraphicsRectItem and provides selectable, movable, and removable bounding boxes.

    Methods:
        - contextMenuEvent: Show a context menu when the bounding box is right-clicked, allowing them to be removed.
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

    def contextMenuEvent(self, event: QGraphicsSceneContextMenuEvent):
        """
        Show a context menu when the bounding box is right-clicked, allowing them to be removed.

        :param event: QGraphicsSceneContextMenuEvent, the event that triggered the context menu.
        """
        menu = QMenu()
        remove_action = menu.addAction("Remove")
        selected_action = menu.exec(event.screenPos())

        if selected_action == remove_action:
            self.scene().removeItem(self)

    def rotate(self, rotation_angle: float, center: QPointF):
        """
        Rotate the bounding box around the given center point by the given rotation angle.

        :param rotation_angle: float, the angle to rotate the bounding box by
        :type rotation_angle: float
        :param center: QPointF, the center point to rotate the bounding box around
        :type center: QPointF
        """
        rect = self.rect()
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
        self.setRect(rect)


class CustomGraphicsView(QGraphicsView):
    """
    Custom graphics view to handle zooming, panning, resizing and drawing bounding boxes. This class is used to display
    the images and is the central widget of the main window.

    Methods:
        - zoom_in (self): Zoom in by a factor of 1.2 (20%).
        - zoom_out (self): Zoom out by a factor of 0.8 (20%).
        - on_main_window_resized (self): Resize the image and maintain the same zoom when the main window is resized.
        - mousePressEvent (self, event: QMouseEvent): Start drawing a bounding box when the left mouse button is
                                pressed.
        - mouseMoveEvent (self, event: QMouseEvent): Update the bounding box when the mouse is moved.
        - mouseReleaseEvent (self, event: QMouseEvent): Finish drawing the bounding box when the left mouse button is
                                released.
        - set_current_finding (self, finding: str, color: QColor): Set the current finding/checkbox to give context to
                                any bounding box drawn.
        - remove_all_bounding_boxes (self): Remove all bounding boxes from the scene.
        - add_bboxes (self, rect_items: dict): Add previously drawn bounding boxes to the scene.
    """
    def __init__(self, parent: Optional[QWidget] = None, main_window = False):
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

        if main_window:
            self.connection_manager.connect(parent.resized, self.on_main_window_resized)

    def zoom_in(self):
        """
        Zoom in by a factor of 1.2 (20%).
        """
        factor = 1.2
        self.zoom *= factor
        self.scale(factor, factor)

    def zoom_out(self):
        """
        Zoom out by a factor of 0.8 (20%).
        """
        factor = 0.8
        self.zoom /= factor
        self.scale(factor, factor)

    def on_main_window_resized(self):
        """
        Resize the image and maintain the same zoom when the main window is resized.
        """
        if self.scene() and self.scene().items():
            self.fitInView(self.scene().items()[-1].boundingRect(), Qt.AspectRatioMode.KeepAspectRatio)
            self.scale(self.zoom, self.zoom)

    def mousePressEvent(self, event: QMouseEvent):
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

    def mouseMoveEvent(self, event: QMouseEvent):
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

    def mouseReleaseEvent(self, event: QMouseEvent):
        """
        Stop drawing the bounding box when the left mouse button is released.

        :param event: QMouseEvent, the mouse release event containing information about the button and position
        """
        if event.button() == Qt.MouseButton.LeftButton:
            if self.start_rect:
                self.start_rect = None
        super().mouseReleaseEvent(event)

    def set_current_finding(self, finding: Optional[str], color: Optional[QColor]):
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

    def add_bboxes(self, rect_items: Dict[str, List]):
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



