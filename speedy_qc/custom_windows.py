import sys
import os
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

from .connection_manager import ConnectionManager

class AboutMessageBox(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        # self.connections = {}
        self.connection_manager = ConnectionManager()

        # Set the window title
        self.setWindowTitle("About...")

        # Create a top-level layout
        top_layout = QHBoxLayout()

        left_layout = QVBoxLayout()

        # Add the icon to the left side of the message box using a QLabel
        # path = pkg_resources.resource_filename('speedy_qc', 'assets/3x/white@3x.png')
        path = os.path.join(os.path.dirname(__file__), 'assets/3x/white_panel@3x.png')
        grey_logo = QPixmap(path)
        icon_label = QLabel()
        icon_label.setPixmap(grey_logo)
        left_layout.addWidget(icon_label)

        web_text = QLabel("<a href='https://www.example.com'>www.example.com</a>")
        web_text.setTextFormat(Qt.TextFormat.RichText)
        web_text.setAlignment(Qt.AlignmentFlag.AlignRight)
        web_text.setText("<a href='https://www.example.com'>www.example.com</a>")
        web_text.setOpenExternalLinks(True)

        right_layout = QVBoxLayout()

        text_layout = QVBoxLayout()

        main_text = QLabel("Speedy QC for Desktop!")
        main_text.setStyleSheet("font-weight: bold; font-size: 16px;")
        main_text.setAlignment(Qt.AlignmentFlag.AlignBottom)
        text_layout.addWidget(main_text)

        sub_text = QLabel("MIT License\nCopyright (c) 2023, Ian Selby")
        sub_text.setStyleSheet("font-size: 14px;")
        sub_text.setAlignment(Qt.AlignmentFlag.AlignTop)
        text_layout.addWidget(sub_text)

        right_layout.addLayout(text_layout)

        # Create a horizontal layout for buttons
        hbox = QHBoxLayout()

        # Create a QPlainTextEdit for detailed information
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
        if self.detailed_info.isVisible():
            self.detailed_info.hide()
            self.details_button.setText("Details...")
        else:
            self.detailed_info.show()
            self.details_button.setText("Hide Details")


class LoadMessageBox(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        # self.connections = {}
        self.connection_manager = ConnectionManager()

        # Set the window title
        self.setWindowTitle("Speedy QC for Desktop")

        # Create a top-level layout
        top_layout = QHBoxLayout()

        left_layout = QVBoxLayout()

        # Add the icon to the left side of the message box using a QLabel
        path = os.path.dirname(__file__)
        print(path)

        # path = pkg_resources.resource_filename('speedy_qc', 'assets/3x/white@3x.png')
        path = os.path.join(os.path.dirname(__file__), 'assets/3x/white_panel@3x.png')
        grey_logo = QPixmap(path)
        print(path)
        if grey_logo.isNull():
            print("***WARNING***")
            print("FAILED TO LOAD LOGO!")
            print("******"*10)
        else:
            print("******"*10)
            print(grey_logo)
        icon_label = QLabel()
        icon_label.setPixmap(grey_logo)
        left_layout.addWidget(icon_label)

        web_text = QLabel("<a href='https://www.example.com'>www.example.com</a>")
        web_text.setTextFormat(Qt.TextFormat.RichText)
        web_text.setAlignment(Qt.AlignmentFlag.AlignRight)
        web_text.setText("<a href='https://www.example.com'>www.example.com</a>")
        web_text.setOpenExternalLinks(True)
        left_layout.addWidget(web_text)
        cr_text = QLabel("MIT License, Copyright (c) 2023, Ian Selby.")
        cr_text.setStyleSheet("font-size: 8px;")
        cr_text.setAlignment(Qt.AlignmentFlag.AlignRight)
        left_layout.addWidget(cr_text)

        right_layout = QVBoxLayout()

        spacer = QSpacerItem(0, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        main_text = QLabel("Welcome to Speedy QC for Desktop!")
        main_text.setStyleSheet("font-weight: bold; font-size: 16px;")
        main_text.setAlignment(Qt.AlignmentFlag.AlignBottom)
        right_layout.addWidget(main_text)

        right_layout.addItem(spacer)


        # Set up QSettings to remember the last config file used
        self.settings = QSettings()

        # Create a QComboBox for selecting the config file
        self.config_combo = QComboBox()
        self.config_combo.addItem("config.yml")
        self.config_combo.addItem("other_config.yml")

        # Set the default value of the QComboBox to the last config file used
        last_config_file = self.settings.value("last_config_file", "config.yml")
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

        # Connect the currentTextChanged signal of the QComboBox to a slot that saves the selected config file to QSettings
        self.config_combo.currentTextChanged.connect(self.save_last_config)

        right_layout.addItem(spacer)

        sub_text2 = QLabel("In the next window, please select a directory to\nload the DICOM files...")
        sub_text2.setStyleSheet("font-size: 14px;")
        sub_text2.setAlignment(Qt.AlignmentFlag.AlignTop)
        right_layout.addWidget(sub_text2)


        # Create a horizontal layout for buttons
        hbox = QHBoxLayout()

        # Add a QPushButton for "Configuration Wizard"
        config_wizard_button = QPushButton("Config. Wizard")
        self.connection_manager.connect(config_wizard_button.clicked, self.reject)
        hbox.addWidget(config_wizard_button)

        # Add a spacer to create some space between the buttons and the Configuration Wizard button
        spacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        hbox.addItem(spacer)

        # Add a QPushButton for "OK"
        ok_button = QPushButton("OK")
        ok_button.setDefault(True)
        self.connection_manager.connect(ok_button.clicked, self.accept)
        hbox.addWidget(ok_button)

        # Add a QPushButton for "Cancel"
        cancel_button = QPushButton("Cancel")
        self.connection_manager.connect(cancel_button.clicked, self.cancel)
        hbox.addWidget(cancel_button)

        # Add the horizontal layout to the vertical layout
        right_layout.addLayout(hbox)

        # Add the vertical layout to the top-level layout
        top_layout.addLayout(right_layout)
        top_layout.addLayout(left_layout)

        # Set the layout for the QDialog
        self.setLayout(top_layout)

    def cancel(self):
        sys.exit()

    def save_last_config(self, config_file):
        # Save the selected config file to QSettings
        self.settings.setValue("last_config_file", config_file)