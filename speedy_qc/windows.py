"""
windows.py

This module contains custom QDialog classes used for displaying specific dialogs in the application.
These dialogs include the initial dialog box for loading a configuration file and the 'About' dialog box
that provides information about the application and its license.

Classes:
    - LoadMessageBox: A custom QDialog for selecting a configuration file when launching the application.
    - AboutMessageBox: A custom QDialog for displaying information about the application and its license.
    - SetupWindow: A custom QDialog for displaying the setup window when the application is first launched to allow
                            the user to select the image directory and decide whether to continue previous progress by
                             loading an existing json file.

Functions:
    - load_json_filenames_findings: Load the filenames and findings from a json file.
"""

import os
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from typing import Optional, List
import sys
import json
from qt_material import get_theme

from speedy_qc.utils import ConnectionManager

if hasattr(sys, '_MEIPASS'):
    # This is a py2app executable
    resource_dir = sys._MEIPASS
elif 'main.py' in os.listdir(os.path.dirname(os.path.realpath(__file__))):
    resource_dir = os.path.dirname(os.path.realpath(__file__))
elif 'main.py' in os.listdir(os.path.dirname(os.path.abspath("__main__"))):
    # This is a regular Python script
    resource_dir = os.path.dirname(os.path.abspath("__main__"))
elif 'main.py' in os.path.join(os.path.dirname(os.path.abspath("__main__")), 'speedy_qc'):
    resource_dir = os.path.join(os.path.dirname(os.path.abspath("__main__")), 'speedy_qc')
elif 'main.py' in os.path.join(os.path.dirname(os.path.abspath("__main__")), 'speedy_qc', 'speedy_qc'):
    resource_dir = os.path.join(os.path.dirname(os.path.abspath("__main__")), 'speedy_qc', 'speedy_qc')
else:
    raise (FileNotFoundError(f"Resource directory not found from {os.path.dirname(os.path.abspath('__main__'))}"))


class AboutMessageBox(QDialog):
    """
    A custom QDialog for displaying information about the application from the About option in the menu.

    :param parent: QWidget or None, the parent widget of this QDialog (default: None).
    :type parent: QWidget or None
    """
    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the AboutMessageBox.

        :param parent: QWidget or None, the parent widget of this QDialog (default: None).
        :type parent: QWidget or None
        """
        super().__init__(parent)
        # self.connections = {}
        self.connection_manager = ConnectionManager()

        # Set the window title
        self.setWindowTitle("About...")

        # Create a top-level layout
        top_layout = QHBoxLayout()

        left_layout = QVBoxLayout()

        # Add the icon to the left side of the message box using a QLabel
        path = os.path.normpath(os.path.join(resource_dir, 'assets/3x/white_panel@3x.png'))
        grey_logo = QPixmap(path).scaled(320, 320, Qt.AspectRatioMode.KeepAspectRatio)
        icon_label = QLabel()
        icon_label.setPixmap(grey_logo)
        left_layout.addStretch(1)
        left_layout.addWidget(icon_label)

        right_layout = QVBoxLayout()
        right_layout.addStretch(1)

        text_layout = QVBoxLayout()

        # Add the app title
        main_text = QLabel("Speedy QC for Desktop!")
        main_text.setStyleSheet("font-weight: bold; font-size: 16px;")
        main_text.setAlignment(Qt.AlignmentFlag.AlignBottom)
        text_layout.addWidget(main_text)

        # Add the copyright information
        sub_text = QLabel("MIT License\nCopyright (c) 2024, Ian Selby")
        sub_text.setWordWrap(True)
        sub_text.setStyleSheet("font-size: 14px;")
        sub_text.setAlignment(Qt.AlignmentFlag.AlignBottom)
        sub_text.setFixedWidth(200)
        text_layout.addWidget(sub_text)

        right_layout.addLayout(text_layout)
        right_layout.addStretch(1)

        # Create a horizontal layout for buttons
        hbox = QHBoxLayout()

        # Create a QPlainTextEdit for the licence information
        self.detailed_info = QTextEdit()
        self.detailed_info.setReadOnly(True)
        self.detailed_info.setText(
            "Permission is hereby granted, free of charge, to any person obtaining a copy of "
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
            "DEALINGS IN THE SOFTWARE."
        )
        self.detailed_info.setFixedHeight(300)
        self.detailed_info.setFixedWidth(300)
        self.detailed_info.hide()  # Hide the detailed information by default
        right_layout.addWidget(self.detailed_info)

        # Create a QPushButton for "Details..."
        self.details_button = QPushButton("Details...")
        self.connection_manager.connect(self.details_button.clicked, self.toggle_details)
        # self.connections['details'] = self.details_button.clicked.connect(self.toggle_details)
        hbox.addWidget(self.details_button)

        # Add a QPushButton for "OK"
        self.cancel_button = QPushButton("Cancel")
        self.connection_manager.connect(self.cancel_button.clicked, self.reject)
        # self.connections['reject'] = cancel_button.clicked.connect(self.reject)
        hbox.addWidget(self.cancel_button)

        # Add the horizontal layout to the vertical layout
        right_layout.addLayout(hbox)

        # Add the vertical layout to the top-level layout
        top_layout.addLayout(right_layout)
        top_layout.addLayout(left_layout)

        # Set the layout for the QDialog
        self.setLayout(top_layout)

    def toggle_details(self):
        """
        Toggle the visibility of the license information.
        """
        if self.detailed_info.isVisible():
            self.detailed_info.hide()
            self.details_button.setText("Details...")
        else:
            self.detailed_info.show()
            self.details_button.setText("Hide Details")


class LoadMessageBox(QDialog):
    """
    The initial dialog box that appears when the application is launched. This dialog box allows
    the user to select the config file to load into the application and allows them to launch the
    configuration wizard to customise Speedy QC.

    :param parent: QWidget or None, the parent widget of this QDialog (default: None).
    :type parent: QWidget or None
    """
    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the LoadMessageBox.

        :param parent: QWidget or None, the parent widget of this QDialog (default: None).
        :type parent: QWidget or None
        """
        super().__init__(parent)
        # self.connections = {}
        self.connection_manager = ConnectionManager()

        # Set the window title
        self.setWindowTitle("Speedy QC")

        # Create a top-level layout
        top_layout = QHBoxLayout()

        left_layout = QVBoxLayout()

        # path = pkg_resources.resource_filename('speedy_qc', 'assets/3x/white@3x.png')
        path = os.path.normpath(os.path.join(resource_dir, 'assets/3x/white_panel@3x.png'))
        logo = QPixmap(path).scaled(320, 320, Qt.AspectRatioMode.KeepAspectRatio)

        # Create a QLabel to display the logo
        icon_label = QLabel()
        icon_label.setPixmap(logo)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        left_layout.addWidget(icon_label)

        # Create a QLabel to display the website link
        web_text = QLabel("<a href='https://github.com/selbs/speedy_qc'>https://github.com/selbs/speedy_qc</a>")
        web_text.setTextFormat(Qt.TextFormat.RichText)
        web_text.setAlignment(Qt.AlignmentFlag.AlignRight)
        web_text.setOpenExternalLinks(True)
        left_layout.addWidget(web_text)

        # Create a QLabel to display the copyright information
        cr_text = QLabel("MIT License, Copyright (c) 2023, Ian Selby.")
        cr_text.setStyleSheet("font-size: 8px;")
        cr_text.setAlignment(Qt.AlignmentFlag.AlignRight)
        left_layout.addWidget(cr_text)

        right_layout = QVBoxLayout()

        spacer = QSpacerItem(0, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        # Create a QLabel to display the title of the application
        main_text = QLabel("Welcome to Speedy QC!")
        main_text.setStyleSheet("font-weight: bold; font-size: 16px;")
        main_text.setAlignment(Qt.AlignmentFlag.AlignBottom)
        right_layout.addWidget(main_text)

        main_sub_text = QLabel("A straightforward, open-source application for labelling medical images.")
        main_sub_text.setStyleSheet("font-weight: normal; font-size: 13px;")
        main_sub_text.setAlignment(Qt.AlignmentFlag.AlignBottom)
        main_sub_text.setWordWrap(True)
        right_layout.addWidget(main_sub_text)

        right_layout.addStretch()

        # Set up QSettings to remember the last config file used
        self.settings = QSettings('SpeedyQC', 'DicomViewer')

        # Create a horizontal layout for buttons
        hbox = QHBoxLayout()

        # Add a QPushButton for "Configuration Wizard"
        config_wizard_button = QPushButton("New")
        self.connection_manager.connect(config_wizard_button.clicked, self.on_wizard_button_clicked)
        hbox.addWidget(config_wizard_button)

        # Add a QPushButton for "OK"
        ok_button = QPushButton("Load")
        self.connection_manager.connect(ok_button.clicked, self.accept)
        hbox.addWidget(ok_button)

        # Add a spacer to create some space between the buttons and the Configuration Wizard button
        spacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        hbox.addItem(spacer)

        # Add a QPushButton for "Cancel"
        cancel_button = QPushButton("Cancel")
        self.connection_manager.connect(cancel_button.clicked, self.reject)
        hbox.addWidget(cancel_button)

        # Add the horizontal layout to the vertical layout
        right_layout.addLayout(hbox)

        # Add the vertical layout to the top-level layout
        top_layout.addLayout(right_layout)
        top_layout.addLayout(left_layout)

        # Set the layout for the QDialog
        self.setLayout(top_layout)

        ok_button.setDefault(True)

    def on_wizard_button_clicked(self):
        """
        Open the configuration wizard when the Configuration Wizard button is clicked.
        """
        self.custom_return_code = 42
        self.accept()

    def exec(self) -> int:
        """
        Overwrite the exec method to return a custom return code for the configuration wizard.

        :return: 1 if the user clicks "OK", 0 if the user clicks "Cancel", 42 if the user
            clicks "Configuration Wizard"
        :rtype: int
        """
        result = super().exec()
        try:
            return self.custom_return_code
        except AttributeError:
            if result == self.DialogCode.Accepted:
                return 1
            else:
                return 0

    def save_last_config(self, conf_name: str):
        """
        Save the selected config file to QSettings

        :param conf_name: The name of the selected config file
        :type conf_name: str
        """
        self.settings.setValue("last_config_file", os.path.normpath(os.path.join(resource_dir, conf_name)))

    def closeEvent(self, event: QCloseEvent):
        """
        Handles a close event and disconnects connections between signals and slots.

        :param event: The close event
        :type event: QCloseEvent
        """
        self.connection_manager.disconnect_all()
        event.accept()

    def show_help_box(self, message):
        QMessageBox.information(self, "Help", message)


class SetupWindow(QDialog):
    """
    A QDialog window for setting up Speedy QC for Desktop, including chosing a directory of images to load and
    selecting a json file to continue previous labelling.

    :param settings: A QSettings object for storing settings
    :type settings: QSettings
    """
    def __init__(self, settings: QSettings):
        """
        Initialise the SetupWindow.

        :param settings: A QSettings object for storing settings
        :type settings: QSettings
        """
        super().__init__()

        # Set up UI elements
        self.settings = settings
        self.connection_manager = ConnectionManager()
        self.folder_label = QLabel()
        self.json_label = QLabel()
        self.folder_label.setText(self.settings.value("image_path", ""))
        self.json_label.setText(self.settings.value("json_path", ""))
        self.json_button = QPushButton("...")
        self.json_button.setFixedSize(25, 25)
        self.new_json = False
        self.config = None

        # Set window title
        self.setWindowTitle("Speedy QC Setup")

        spacer = QSpacerItem(50, 50, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        expanding_spacer = QSpacerItem(10, 10, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Set up layout
        layout = QVBoxLayout()

        logo_layout = QHBoxLayout()

        info_layout = QVBoxLayout()

        general_info_label = QLabel("Load Progress...")

        general_info_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        general_info_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        general_info_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        info_layout.addWidget(general_info_label)
        general_add_info_label = QLabel("To load progress, please select an existing save (.json) file:")
        general_add_info_label.setStyleSheet("font-size: 12px; font-style: italic;")
        general_add_info_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        general_add_info_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        info_layout.addWidget(general_add_info_label)
        logo_layout.addLayout(info_layout)

        logo_layout.addItem(spacer)

        path = os.path.normpath(os.path.join(resource_dir, 'assets/2x/white_panel@2x.png'))
        logo = QPixmap(path).scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio)
        icon_label = QLabel()
        icon_label.setPixmap(logo)
        logo_layout.addWidget(icon_label)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addLayout(logo_layout)

        try:
            help_colour = get_theme(self.settings.value('theme', 'dark_blue.xml'))['secondaryTextColor']
        except KeyError:
            help_colour = get_theme(self.settings.value('theme', 'dark_blue.xml'))['secondaryLightColor']

        layout.addSpacerItem(expanding_spacer)

        json_frame = QFrame()
        json_layout = QVBoxLayout()

        json_selection_layout = QHBoxLayout()
        json_selection_layout.addWidget(self.json_label)
        json_selection_layout.addWidget(self.json_button)

        json_explanation_text = ("<p style='white-space: pre-wrap; width: 100px;'>"
                                 "Progress is stored in a .json file. Please choose the file you wish to load.\n\n"
                                 "N.B. The 'check to start from scratch' tickbox above must be deselected.</p>")
        self.json_explanation_btn = QPushButton('?')
        self.json_explanation_btn.setFixedSize(25, 25)
        self.json_explanation_btn.setToolTip(json_explanation_text)
        self.json_explanation_btn.setToolTipDuration(0)
        # self.json_explanation_btn.setDisabled(True)
        self.connection_manager.connect(self.json_explanation_btn.clicked,
                                        lambda: self.show_help_box(json_explanation_text))

        self.json_button.setWhatsThis(json_explanation_text)
        self.json_explanation_btn.setStyleSheet(f"color: {help_colour}; border: 1px solid {help_colour};")
        json_selection_layout.addWidget(self.json_explanation_btn)

        json_layout.addLayout(json_selection_layout)

        json_frame.setLayout(json_layout)
        layout.addWidget(json_frame)

        # layout.addItem(spacer)

        layout.addSpacerItem(expanding_spacer)

        # Add dialog buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        cancel_button = self.button_box.button(QDialogButtonBox.StandardButton.Cancel)
        cancel_button.setText("Back")

        self.connection_manager.connect(self.button_box.accepted, self.on_accepted)
        self.connection_manager.connect(self.button_box.rejected, self.reject)
        layout.addWidget(self.button_box)

        self.setLayout(layout)

        # Connect buttons to functions
        self.connection_manager.connect(self.json_button.clicked, self.select_json)

        # Load previously selected files
        self.load_saved_files(settings)

    def show_help_box(self, message):
        QMessageBox.information(self, "Help", message)

    def on_accepted(self):
        """
        Overwrite the default accept method to prevent the dialog from closing if the json file is not compatible.
        """
        if not self.check_json_compatibility(self.json_label.text()):
            # Prevent the dialog from closing
            self.button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)
            return
        else:
            super().accept()

    def accept(self):
        """
        Overwrite the default accept method to prevent the dialog from closing with an incompatible json.
        """
        pass

    def load_saved_files(self, settings: QSettings):
        """
        Load previously selected files from QSettings.

        :param settings: QSettings object
        :type settings: QSettings
        """
        # Get saved file paths from QSettings
        json_path = settings.value("json_path", "")

        # Update labels with saved file paths
        if json_path:
            self.json_label.setText(json_path)

    @staticmethod
    def save_file_paths(settings: QSettings, json_path: str):
        """
        Update QSettings

        :param settings: QSettings object to update
        :type settings: QSettings
        :param json_path: Path to JSON file
        :type json_path: str
        """
        # Save file paths to QSettings
        settings.setValue("json_path", json_path)

    def select_json(self):
        """
        Open file dialog to select JSON file.
        """
        # Open file dialog to select JSON file
        json_path, _ = QFileDialog.getOpenFileName(self, "Select JSON File", "", "JSON Files (*.json)")

        # Update label and save file path
        if json_path:
            self.json_label.setText(json_path)
            self.save_file_paths(self.settings, json_path)
            self.button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(True)

    def generate_json_image_incompatibility_msg(self):
        """
        Generate a message box to inform the user that the selected json file is incompatible with the image folder
        as it contains image filenames which are not present in the folder.
        """
        QMessageBox.critical(self,
                             "Error",
                             f"JSON - IMAGE FOLDER CONFLICT!\n\n"
                             f"The selected json file has image files which are not present in the selected image "
                             f"directory.\n\n"
                             f"Please select a new json file or image directory. Alternatively, start again and select "
                             f"a new config file. ",
                             QMessageBox.StandardButton.Ok,
                             defaultButton=QMessageBox.StandardButton.Ok)

    def generate_no_image_msg(self):
        """
        Generate a message box to inform the user that no dcm folder is selected.
        """
        QMessageBox.critical(self,
                             "Error",
                             f"NO IMAGE DIRECTORY SELECTED!\n\n"
                             f"Please select an image directory or start again and select a new config file. ",
                             QMessageBox.StandardButton.Ok,
                             defaultButton=QMessageBox.StandardButton.Ok)

    def check_json_image_compatibility(self, filenames: List[str]) -> bool:
        """
        Check if the selected json file is compatible with the image folder.

        :param filenames: list of image filenames in the json file
        :type filenames: list
        :return: True if compatible, False otherwise
        :rtype: bool
        """
        if os.path.isdir(self.folder_label.text()):
            imgs = sorted([f for f in os.listdir(self.folder_label.text()) if f.endswith((
                    '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.tif', '.dcm', '.dicom',
                ))])

            # Get list of dcms in json
            for file in filenames:
                if file not in imgs:
                    self.generate_json_image_incompatibility_msg()
                    return False

            return True
        # elif self.new_json_tickbox.isChecked():
        #     self.generate_no_image_msg()
        #     return False
        else:
            return True

    def check_json_compatibility(self, json_path: str) -> bool:
        """
        Check if the selected json file is compatible with the image files in the image directory and the selected
        config yml file. This prevents the program from crashing if incompatible files are selected.

        :param json_path: path to the json file
        :type json_path: str
        :return: True if compatible, False otherwise
        :rtype: bool
        """
        if os.path.isfile(json_path):
            self.config, filenames, cboxes, cbox_values, rbs = self.load_json_filenames_findings(json_path)
            dcm_compatible = self.check_json_image_compatibility(filenames)
            if dcm_compatible:
                self.settings.setValue("json_path", json_path)
                return True
            return False
        else:
            self.button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)
            return False

    def closeEvent(self, event: QCloseEvent):
        """
        Handles a close event and disconnects connections between signals and slots.

        :param event: close event
        :type event: QCloseEvent
        """
        self.connection_manager.disconnect_all()
        event.accept()

    def load_json_filenames_findings(self, json_path: str):
        """
        Load the filenames and findings from a json file.

        :param json_path: path to the json file
        :type json_path: str
        """

        with open(json_path, 'r') as file:
            data = json.load(file)

        config = data['config']
        filenames = [entry['filename'] for entry in data['files']]
        self.folder_label.setText(self.settings.value(data['image_directory'], self.folder_label.text()))
        cboxes = [cbox for entry in data['files'] if 'checkboxes' in entry for cbox in entry['checkboxes'].keys()]
        cbox_values = [value for entry in data['files'] if 'checkboxes' in entry for value in entry['checkboxes'].values()]
        radiobs = [rb for entry in data['files'] if 'radiobuttons' in entry for rb in entry['radiobuttons'].keys()]

        unique_cboxes = sorted(list(set(cboxes)))
        unique_cbox_values = sorted(list(set(cbox_values)))
        unique_radiobs = sorted(list(set(radiobs)))

        return config, filenames, unique_cboxes, unique_cbox_values, unique_radiobs


class FileSelectionDialog(QDialog):
    """
    Dialog for selecting a file from a list of files.

    :param file_list: list of files
    :type file_list: List[str]
    :param parent: parent widget
    :type parent: Optional[QWidget]
    """
    def __init__(self, file_list: List[str], parent: Optional[QWidget] = None):
        """
        Initialize the dialog.

        :param file_list: list of files
        :type file_list: List[str]
        :param parent: parent widget
        :type parent: Optional[QWidget]
        """
        super().__init__(parent)
        self.setWindowTitle("Select Image")

        self.file_list = file_list
        self.filtered_list = file_list

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.search_bar = QLineEdit()
        self.connection_manager = ConnectionManager()
        self.connection_manager.connect(self.search_bar.textChanged, self.filter_list)
        self.layout.addWidget(self.search_bar)

        self.list_widget = QListWidget()
        self.list_widget.addItems(self.file_list)
        self.connection_manager.connect(self.list_widget.itemClicked, self.select_file)
        self.connection_manager.connect(self.list_widget.itemDoubleClicked, self.select_and_accept_file)
        self.layout.addWidget(self.list_widget)

        self.buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)
        self.connection_manager.connect(self.buttonBox.accepted, self.accept_file)
        self.connection_manager.connect(self.buttonBox.rejected, self.reject)
        self.layout.addWidget(self.buttonBox)

        self.selected_file = None
        self.adjust_size()

    def adjust_size(self):
        """
        Adjust the size of the dialog to fit the list of files.
        """
        max_width = 0
        fm = QFontMetrics(self.font())
        for file in self.file_list:
            width = fm.horizontalAdvance(file)
            if width > max_width:
                max_width = width
        # Consider some padding
        max_width += 50
        height = 500
        self.resize(max_width, height)

    def filter_list(self, query):
        """
        Filter the list of files based on a query.

        :param query: query to filter the list of files
        :type query: str
        """
        self.filtered_list = [file for file in self.file_list if query.lower() in file.lower()]
        self.list_widget.clear()
        self.list_widget.addItems(self.filtered_list)

    def select_file(self, item):
        """
        Select a file from the list of files.

        :param item: item to select
        :type item: QListWidgetItem
        """
        self.selected_file = item.text()
        self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setEnabled(True)

    def select_and_accept_file(self, item):
        """
        Select a file from the list of files and accept the dialog.

        :param item: item to select
        :type item: QListWidgetItem
        """
        self.selected_file = item.text()
        self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setEnabled(True)
        self.accept_file()

    def accept_file(self):
        """
        Accept the dialog if a file is selected, otherwise reject it.
        """
        if self.selected_file is not None:
            self.accept()
        else:
            self.reject()
