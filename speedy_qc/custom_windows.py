"""
custom_windows.py

This module contains custom QDialog classes used for displaying specific dialogs in the application.
These dialogs include the initial dialog box for loading a configuration file and the 'About' dialog box
that provides information about the application and its license.

Classes:
    - LoadMessageBox: A custom QDialog for selecting a configuration file when launching the application.
    - AboutMessageBox: A custom QDialog for displaying information about the application and its license.
"""

import os
import logging
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from typing import Optional
import sys
import pkg_resources

from speedy_qc.utils import ConnectionManager

logger = logging.getLogger(__name__)
console_msg = logging.getLogger('consoleLog')


if hasattr(sys, '_MEIPASS'):
    # This is a py2app executable
    resource_dir = sys._MEIPASS
    print("************************************************")
    print(f"Running from py2app executable at {resource_dir}")
    print("************************************************")
else:
    # This is a regular Python script
    resource_dir = os.path.dirname(os.path.abspath("__main__"))

class AboutMessageBox(QDialog):
    """
    A custom QDialog for displaying information about the application from the About option in the menu.
    """
    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the AboutMessageBox.

        :param parent: QWidget or None, the parent widget of this QDialog (default: None).
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
        path = os.path.join(resource_dir, 'assets/3x/white_panel@3x.png')
        grey_logo = QPixmap(path)
        icon_label = QLabel()
        icon_label.setPixmap(grey_logo)
        left_layout.addWidget(icon_label)

        right_layout = QVBoxLayout()

        text_layout = QVBoxLayout()

        # Add the app title
        main_text = QLabel("Speedy QC for Desktop!")
        main_text.setStyleSheet("font-weight: bold; font-size: 16px;")
        main_text.setAlignment(Qt.AlignmentFlag.AlignBottom)
        text_layout.addWidget(main_text)

        # Add the copyright information
        sub_text = QLabel("MIT License\nCopyright (c) 2023, Ian Selby")
        sub_text.setStyleSheet("font-size: 14px;")
        sub_text.setAlignment(Qt.AlignmentFlag.AlignTop)
        text_layout.addWidget(sub_text)

        right_layout.addLayout(text_layout)

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
    """
    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the LoadMessageBox.

        :param parent: QWidget or None, the parent widget of this QDialog (default: None).
        """
        super().__init__(parent)
        # self.connections = {}
        self.connection_manager = ConnectionManager()

        # Set the window title
        self.setWindowTitle("Speedy QC for Desktop")

        # Create a top-level layout
        top_layout = QHBoxLayout()

        left_layout = QVBoxLayout()

        # path = pkg_resources.resource_filename('speedy_qc', 'assets/3x/white@3x.png')
        path = os.path.join(resource_dir, 'assets/3x/white_panel@3x.png')
        logo = QPixmap(path)

        # Logs a warning if the logo cannot be loaded
        if logo.isNull():
            logger.warning(f"Failed to load logo at path: {path}")

        # Create a QLabel to display the logo
        icon_label = QLabel()
        icon_label.setPixmap(logo)
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
        main_text = QLabel("Welcome to Speedy QC for Desktop!")
        main_text.setStyleSheet("font-weight: bold; font-size: 16px;")
        main_text.setAlignment(Qt.AlignmentFlag.AlignBottom)
        right_layout.addWidget(main_text)

        right_layout.addItem(spacer)

        # Set up QSettings to remember the last config file used
        self.settings = QSettings('SpeedyQC', 'DicomViewer')

        # Create a QComboBox for selecting the config file
        self.config_combo = QComboBox()
        for file in os.listdir(resource_dir):
            if file.endswith('.yml'):
                self.config_combo.addItem(file)

        # Set the default value of the QComboBox to the last config file used
        last_config_file = self.settings.value("last_config_file", os.path.join(resource_dir, "config.yml"))
        self.config_combo.setCurrentText(last_config_file)

        # Add the QComboBox to the dialog box
        config_layout = QVBoxLayout()
        config_label = QLabel("Please select a config file to use:")
        config_label.setStyleSheet("font-size: 14px;")
        config_layout.addWidget(config_label)
        config_layout.addWidget(self.config_combo)
        right_layout.addLayout(config_layout)
        config_label2 = QLabel("N.B. the config file can be edited in the Config. Wizard.")
        config_label2.setStyleSheet("font-size: 14px; font-style: italic;")
        config_layout.addWidget(config_label2)

        # Connect the currentTextChanged signal of the QComboBox to a slot
        # that saves the selected config file to QSettings
        self.config_combo.currentTextChanged.connect(self.save_last_config)

        right_layout.addItem(spacer)

        # Create a QLabel to display a prompt to the user for the following dialog
        sub_text2 = QLabel("In the next window, please select a directory to\nload the DICOM files...")
        sub_text2.setStyleSheet("font-size: 14px;")
        sub_text2.setAlignment(Qt.AlignmentFlag.AlignTop)
        right_layout.addWidget(sub_text2)

        # Create a horizontal layout for buttons
        hbox = QHBoxLayout()

        # Add a QPushButton for "Configuration Wizard"
        config_wizard_button = QPushButton("Config. Wizard")
        self.connection_manager.connect(config_wizard_button.clicked, self.on_wizard_button_clicked)
        hbox.addWidget(config_wizard_button)

        # Add a spacer to create some space between the buttons and the Configuration Wizard button
        spacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        hbox.addItem(spacer)

        # Add a QPushButton for "OK"
        ok_button = QPushButton("OK")
        self.connection_manager.connect(ok_button.clicked, self.accept)
        hbox.addWidget(ok_button)

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

        :return: int, 1 if the user clicks "OK", 0 if the user clicks "Cancel", 42 if the user
                                clicks "Configuration Wizard"
        """
        result = super().exec()
        try:
            return self.custom_return_code
        except AttributeError:
            if result == self.DialogCode.Accepted:
                return 1
            else:
                return 0
    def save_last_config(self, config_file: str):
        """
        Save the selected config file to QSettings
        """
        # Save the selected config file to QSettings
        self.settings.setValue("last_config_file", config_file)
