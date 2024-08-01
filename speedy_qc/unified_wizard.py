"""
unified_wizard.py

This is an updated version of the ConfigurationWizard class from speedy_iqa/config_wizard.py. It allows users to
customize the configuration of the Speedy IQA application without the need to restart the application.
"""
import logging

from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
import yaml
import os
from qt_material import apply_stylesheet, get_theme
import sys
from math import ceil

from speedy_qc.utils import open_yml_file, setup_logging, ConnectionManager, find_relative_image_path
import json

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
else:
    raise (FileNotFoundError(f"Resource directory not found from {os.path.dirname(os.path.abspath('__main__'))}"))

resource_dir = os.path.normpath(os.path.abspath(resource_dir))


class AdvancedSettingsDialog(QDialog):
    def __init__(self, unified_page_instance, parent=None):
        super().__init__(parent)
        self.unified_page_instance = unified_page_instance
        self.wiz = unified_page_instance.wiz
        self.settings = unified_page_instance.settings
        self.connection_manager = unified_page_instance.connection_manager
        self.log_dir = os.path.normpath(self.wiz.log_dir)
        self.backup_dir = os.path.normpath(self.wiz.backup_dir)
        self.backup_interval = self.wiz.backup_interval
        self.max_backups = self.wiz.max_backups
        self.setWindowTitle("Advanced Settings")

        try:
            self.entry_colour = get_theme(self.settings.value('theme', 'dark_blue.xml'))['secondaryTextColor']
        except KeyError:
            self.entry_colour = get_theme(self.settings.value('theme', 'dark_blue.xml'))['secondaryLightColor']
        try:
            self.disabled_colour = get_theme(self.settings.value('theme', 'dark_blue.xml'))['secondaryLightColor']
        except KeyError:
            self.disabled_colour = get_theme(self.settings.value('theme', 'dark_blue.xml'))['primaryLightColor']
        try:
            self.border_color = get_theme(self.settings.value("theme", 'dark_blue.xml'))['secondaryLightColor']
        except KeyError:
            self.border_color = get_theme(self.settings.value("theme", 'dark_blue.xml'))['secondaryColor']

        self.setStyleSheet(f"""
            QLineEdit {{
                color: {self.entry_colour};
            }}
            QSpinBox {{
                color: {self.entry_colour};
            }}
            QComboBox {{
                color: {self.entry_colour};
            }}
        """)

        self.layout = QVBoxLayout()

        config_frame = QFrame()
        config_frame.setObjectName("ConfigFrame")
        config_frame.setStyleSheet(f"#ConfigFrame {{ border: 2px solid {self.border_color}; border-radius: 5px; }}")
        self.config_layout = QVBoxLayout()
        self.config_file_title = QLabel("Configuration File Settings:")
        self.config_file_title.setStyleSheet("font-weight: bold;")
        self.config_layout.addWidget(self.config_file_title)

        # Create QComboBox for the list of available .yml files
        self.config_files_combobox = QComboBox()
        for file in os.listdir(resource_dir):
            if file.endswith('.yml'):
                self.config_files_combobox.addItem(file)

        existing_combo_layout = QHBoxLayout()
        existing_combo_title = QLabel("Existing Configuration Files:")
        existing_combo_title.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        existing_combo_layout.addWidget(existing_combo_title)
        existing_combo_layout.addWidget(self.config_files_combobox)
        self.config_layout.addLayout(existing_combo_layout)

        # Create QLineEdit for the filename
        new_filename_layout = QHBoxLayout()
        self.filename_edit = QLineEdit()
        self.filename_edit.setPlaceholderText("config.yml")
        self.connection_manager.connect(self.filename_edit.textChanged,
                                        self.update_config_combobox_state)
        new_filename_layout.addWidget(QLabel("New Filename (Optional):"))
        new_filename_layout.addWidget(self.filename_edit)
        self.config_layout.addLayout(new_filename_layout)

        # Display the save path
        save_path_layout = QHBoxLayout()
        save_path_label = QLabel("Save directory:")
        save_path_layout.addWidget(save_path_label)
        save_dir_label = QLabel(resource_dir)
        save_path_label.setStyleSheet("font-style: italic;")
        save_dir_label.setStyleSheet("font-style: italic;")
        save_path_layout.addWidget(save_dir_label)
        save_path_layout.addStretch()
        self.config_layout.addLayout(save_path_layout)

        config_frame.setLayout(self.config_layout)
        self.layout.addStretch()
        self.layout.addWidget(config_frame)
        self.layout.addStretch()

        log_frame = QFrame()
        log_frame.setObjectName("LogFrame")
        log_frame.setStyleSheet(f"#LogFrame {{ border: 2px solid {self.border_color}; border-radius: 5px; }}")
        self.log_layout = QVBoxLayout()

        # Create a widget for the log directory
        self.log_dir_title = QLabel("Log Settings:")
        self.log_dir_title.setStyleSheet("font-weight: bold;")
        self.log_layout.addWidget(self.log_dir_title)

        self.log_dir_layout = QHBoxLayout()
        log_dir_label = QLabel("Log directory:")
        self.log_dir_edit = QLineEdit()
        self.log_dir_edit.setText(self.settings.value("log_dir", os.path.normpath(os.path.expanduser(self.log_dir))))
        self.log_dir_layout.addWidget(log_dir_label)
        self.log_dir_layout.addWidget(self.log_dir_edit)
        self.log_layout.addLayout(self.log_dir_layout)

        log_frame.setLayout(self.log_layout)
        self.layout.addWidget(log_frame)
        self.layout.addStretch()

        backup_frame = QFrame()
        backup_frame.setObjectName("BackupFrame")
        backup_frame.setStyleSheet(f"#BackupFrame {{ border: 2px solid {self.border_color}; border-radius: 5px; }}")
        self.backup_layout = QVBoxLayout()

        # Create a widget for the log directory
        self.backup_title = QLabel("Backup Settings:")
        self.backup_title.setStyleSheet("font-weight: bold;")
        self.backup_layout.addWidget(self.backup_title)

        backup_dir_layout = QHBoxLayout()
        backup_dir_label = QLabel("Backup directory:")
        self.backup_dir_edit = QLineEdit()
        self.backup_dir_edit.setText(self.settings.value("backup_dir", os.path.normpath(
            os.path.expanduser(self.backup_dir)
        )))
        backup_dir_layout.addWidget(backup_dir_label)
        backup_dir_layout.addWidget(self.backup_dir_edit)
        self.backup_layout.addLayout(backup_dir_layout)

        # Create a widget for the maximum number of backups
        no_backups_layout = QHBoxLayout()
        self.backup_spinbox = QSpinBox()
        self.backup_spinbox.setRange(1, 100)
        self.backup_spinbox.setValue(self.max_backups)

        no_backups_layout.addWidget(QLabel("Maximum number of backups:"))
        no_backups_layout.addWidget(self.backup_spinbox)
        no_backups_layout.addStretch()
        self.backup_layout.addLayout(no_backups_layout)

        backup_int_layout = QHBoxLayout()
        self.backup_int_spinbox = QSpinBox()
        self.backup_int_spinbox.setRange(1, 30)
        self.backup_int_spinbox.setValue(self.backup_interval)

        backup_int_layout.addWidget(QLabel("Backup interval (mins):"))
        backup_int_layout.addWidget(self.backup_int_spinbox)
        backup_int_layout.addStretch()
        self.backup_layout.addLayout(backup_int_layout)

        backup_frame.setLayout(self.backup_layout)
        self.layout.addWidget(backup_frame)
        self.layout.addStretch()

        # Add a "Back" button
        back_button = QPushButton("Back")
        self.connection_manager.connect(back_button.clicked, self.close)
        self.layout.addWidget(back_button)

        self.setLayout(self.layout)
        self.setMinimumSize(400, 520)

        QTimer.singleShot(0, self.update_config_combobox_state)

    def update_config_combobox_state(self):
        """
        Updates the QComboBox on the save page with the list of existing .yml files.
        """
        if self.filename_edit.text():
            self.config_files_combobox.setEnabled(False)
        else:
            self.config_files_combobox.setEnabled(True)
        self.update_combobox_stylesheet()

    def update_combobox_stylesheet(self):
        """
        Updates the stylesheet of the QComboBox on the save page to indicate whether it is
        enabled or disabled.
        """
        if self.config_files_combobox.isEnabled():
            self.config_files_combobox.setStyleSheet(f"QComboBox {{ color: {self.entry_colour}; }}")
        else:
            self.config_files_combobox.setStyleSheet(f"QComboBox {{ color: {self.disabled_colour}; }}")

    def close(self):
        # self.settings.setValue("log_dir", self.log_dir_edit.text())
        # self.settings.setValue("backup_dir", self.backup_dir_edit.text())
        # self.settings.setValue("max_backups", self.backup_spinbox.value())
        # self.settings.setValue("backup_interval", self.backup_int_spinbox.value())

        if self.filename_edit.text():
            self.wiz.config_filename = self.filename_edit.text()
        else:
            self.wiz.config_filename = self.config_files_combobox.currentText()
        self.wiz.log_dir = os.path.normpath(self.log_dir_edit.text())
        self.wiz.backup_dir = os.path.normpath(self.backup_dir_edit.text())
        self.wiz.backup_interval = self.backup_int_spinbox.value()
        self.wiz.max_backups = self.backup_spinbox.value()
        super().close()

class RadioButtonGroupDialog(QDialog):
    """
    A QDialog class implementation for adding radio button groups to the configuration.

    :param parent: The parent widget.
    :type parent: QWidget
    """
    def __init__(self, parent=None):
        """
        Initializes the dialog.

        :param parent: The parent widget.
        :type parent: QWidget
        """
        super().__init__(parent)

        self.connection_manager = ConnectionManager()

        self.setWindowTitle("New Radio Button Group")

        self.titleInput = QLineEdit(self)
        self.labelsInput = QTextEdit(self)
        self.labelsInput.setPlaceholderText("Enter one label per line")

        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self)
        self.connection_manager.connect(self.buttons.accepted, self.accept)
        self.connection_manager.connect(self.buttons.rejected, self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Group Title:"))
        layout.addWidget(self.titleInput)
        layout.addWidget(QLabel("Button Labels:"))
        layout.addWidget(self.labelsInput)
        layout.addWidget(self.buttons)

    @property
    def title(self) -> str:
        """
        The title of the radio button group.
        """
        return self.titleInput.text()

    @property
    def labels(self) -> list:
        """
        The labels of the radio buttons.
        """
        return self.labelsInput.toPlainText().split("\n")


class SelectImagesPage(QWizardPage):
    def __init__(self, wiz, parent=None):
        """
        Initializes the page.

        :param parent: The parent widget.
        :type parent: QWidget
        """
        super().__init__(parent)

        self.connection_manager = ConnectionManager()

        self.wiz = wiz
        self.settings = wiz.settings

        self.setTitle("Select Images")
        self.setSubTitle("\nPlease select the directory containing the images for annotation")

        self.layout = QVBoxLayout(self)

        self.folder_button = QPushButton("...")
        self.folder_button.setFixedSize(25, 25)
        self.folder_label = QLabel()
        self.folder_label.setText(self.settings.value("image_path", ""))

        # Connect buttons to functions
        self.connection_manager.connect(self.folder_button.clicked, self.select_folder)

        expanding_spacer = QSpacerItem(10, 10, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        try:
            help_colour = get_theme(self.settings.value('theme', 'dark_blue.xml'))['secondaryTextColor']
        except KeyError:
            help_colour = get_theme(self.settings.value('theme', 'dark_blue.xml'))['secondaryLightColor']

        im_selection_layout = QHBoxLayout()
        im_selection_label = QLabel("Current directory:")
        im_selection_label.setStyleSheet("font-weight: bold;")
        im_selection_layout.addWidget(im_selection_label)
        im_selection_layout.addSpacerItem(expanding_spacer)
        im_selection_layout.addWidget(self.folder_label)
        im_selection_layout.addWidget(self.folder_button)
        im_folder_explanation_text = ("<p style='white-space: pre-wrap; width: 100px;'>"
                                      "This folder should contain the images to be labelled.\n\n"
                                      "N.B. The images can be in subfolders.</p>")
        self.im_folder_explanation_btn = QPushButton('?')
        self.im_folder_explanation_btn.setFixedSize(25, 25)
        self.im_folder_explanation_btn.setToolTip(im_folder_explanation_text)
        self.im_folder_explanation_btn.setToolTipDuration(0)
        # self.im_folder_explanation_btn.setDisabled(True)
        self.connection_manager.connect(self.im_folder_explanation_btn.clicked,
                                        lambda: self.show_help_box(im_folder_explanation_text))
        self.im_folder_explanation_btn.setStyleSheet(f"color: {help_colour}; border: 1px solid {help_colour};")
        self.folder_button.setWhatsThis(im_folder_explanation_text)
        im_selection_layout.addWidget(self.im_folder_explanation_btn)

        self.layout.addLayout(im_selection_layout)

        self.conflict_resolution_checkbox = QCheckBox("Resolve conflicts between two annotators?")
        self.conflict_resolution_checkbox.setChecked(wiz.conflict_resolution)
        self.layout.addWidget(self.conflict_resolution_checkbox)

        self.connection_manager.connect(
            self.conflict_resolution_checkbox.stateChanged, self.wiz.update_conflict_resolution
        )

    def initializePage(self):

        self.wizard().setButtonLayout([
            QWizard.WizardButton.CustomButton1,
            QWizard.WizardButton.CustomButton2,
            QWizard.WizardButton.Stretch,
            QWizard.WizardButton.BackButton,
            QWizard.WizardButton.NextButton,
            QWizard.WizardButton.CancelButton
        ])

        self.wizard().button(QWizard.WizardButton.BackButton).hide()

        advanced_button = QPushButton("Advanced")
        self.connection_manager.connect(advanced_button.clicked, self.open_advanced_settings)
        self.wizard().setButton(QWizard.WizardButton.CustomButton1, advanced_button)

        load_config_button = QPushButton("Load Config.")
        self.connection_manager.connect(load_config_button.clicked, self.wiz.config_load_dialog)
        self.wizard().setButton(QWizard.WizardButton.CustomButton2, load_config_button)

        self.wizard().button(QWizard.WizardButton.NextButton).setEnabled(False)

    def select_folder(self):
        """
        Open file dialog to select directory.
        """
        image_dir = None
        while image_dir is None:
            # Open file dialog to select image folder
            folder_path = QFileDialog.getExistingDirectory(self, "Select Image Directory", self.folder_label.text())

            # Update label and save file path
            if folder_path:
                self.folder_label.setText(folder_path)
                img_files = find_relative_image_path(folder_path)
                if len(img_files) == 0:
                    error_msg_box = QMessageBox()
                    error_msg_box.setIcon(QMessageBox.Icon.Warning)
                    error_msg_box.setWindowTitle("Error")
                    error_msg_box.setText("The directory does not appear to contain any image files!")
                    error_msg_box.setInformativeText("Please try again.")
                    error_msg_box.exec()
                    self.wizard().button(QWizard.WizardButton.NextButton).setEnabled(False)
                else:
                    self.folder_label.setText(folder_path)
                    self.settings.setValue("image_path", folder_path)
                    image_dir = folder_path
                    self.wizard().button(QWizard.WizardButton.NextButton).setEnabled(True)
            else:
                break

    def show_help_box(self, message):
        QMessageBox.information(self, "Help", message)

    def open_advanced_settings(self):
        advanced_settings_dialog = AdvancedSettingsDialog(self)
        advanced_settings_dialog.exec()


class UnifiedCheckboxPage(QWizardPage):
    def __init__(self, wiz, parent=None):
        """
        Initializes the page.

        :param parent: The parent widget.
        :type parent: QWidget
        """
        super().__init__(parent)

        self.connection_manager = wiz.connection_manager

        self.wiz = wiz
        self.cboxes = wiz.cboxes
        self.settings = wiz.settings

        self.setTitle(f"Checkboxes")
        self.setSubTitle(f"\nAllow a bounding box to be drawn around the finding in the image.")

        self.layout = QVBoxLayout(self)

        self.tristate_checkboxes = wiz.tristate_checkboxes
        self.tristate_checkbox = QCheckBox("Use tri-state checkboxes, i.e. have third uncertain option")
        self.tristate_checkbox.setChecked(wiz.tristate_checkboxes)
        self.connection_manager.connect(self.tristate_checkbox.stateChanged, self.update_tristate_checkboxes_state)

        self.scrollArea = QScrollArea(self)
        self.scrollWidget = QWidget()
        self.scrollLayout = QVBoxLayout()
        self.scrollWidget.setLayout(self.scrollLayout)
        self.scrollArea.setWidget(self.scrollWidget)
        self.scrollArea.setWidgetResizable(True)
        self.layout.addWidget(self.scrollArea)

        self.cbox_widget = QWidget(self)
        self.cbox_top_layout = QVBoxLayout(self.cbox_widget)
        self.cbox_top_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scrollArea.setWidget(self.cbox_widget)

        self.cbox_lower_layout = QVBoxLayout()

        frame = QFrame()
        frame.setObjectName("CBoxFrame")
        try:
            border_color = get_theme(self.settings.value("theme", 'dark_blue.xml'))['secondaryLightColor']
        except KeyError:
            border_color = get_theme(self.settings.value("theme", 'dark_blue.xml'))['secondaryColor']
        frame.setStyleSheet(f"#CBoxPageFrame {{ border: 2px solid {border_color}; border-radius: 5px; }}")

        self.add_cbox_button = QPushButton("+")
        self.add_cbox_button.setProperty('class', 'success')

        row_header_layout = QHBoxLayout()
        row_header_layout.addWidget(self.tristate_checkbox)
        row_header_layout.addStretch()
        row_header_layout.addWidget(self.add_cbox_button, alignment=Qt.AlignmentFlag.AlignTop)
        self.cbox_lower_layout.addLayout(row_header_layout)

        self.cbox_box_layouts = QVBoxLayout()
        for cbox in self.cboxes:
            self.add_cbox(cbox)

        self.cbox_lower_layout.addLayout(self.cbox_box_layouts)
        frame.setLayout(self.cbox_lower_layout)

        self.cbox_top_layout.addWidget(frame)

        self.connection_manager.connect(self.add_cbox_button.clicked, lambda: self.add_cbox())

    def initializePage(self):

        self.wizard().setButtonLayout([
            QWizard.WizardButton.CustomButton1,
            QWizard.WizardButton.CustomButton2,
            QWizard.WizardButton.Stretch,
            QWizard.WizardButton.BackButton,
            QWizard.WizardButton.NextButton,
            QWizard.WizardButton.CancelButton
        ])

        advanced_button = QPushButton("Advanced")
        self.connection_manager.connect(advanced_button.clicked, self.open_advanced_settings)
        self.wizard().setButton(QWizard.WizardButton.CustomButton1, advanced_button)

        load_config_button = QPushButton("Load Config.")
        self.connection_manager.connect(load_config_button.clicked, self.wiz.config_load_dialog)
        self.wizard().setButton(QWizard.WizardButton.CustomButton2, load_config_button)

    def open_advanced_settings(self):
        advanced_settings_dialog = AdvancedSettingsDialog(self)
        advanced_settings_dialog.exec()

    def add_cbox(self, label_text=""):
        """
        Adds a label to the list of labels.
        """
        line_edit = QLineEdit(label_text)
        remove_button = QPushButton("-")
        remove_button.setProperty('class', 'danger')
        # remove_button.setFixedSize(100, 40)

        self.connection_manager.connect(
            remove_button.clicked, lambda: self.remove_cbox(line_edit, remove_button)
        )

        # Create a horizontal layout for the line edit and the remove button
        hbox = QHBoxLayout()
        hbox.addWidget(line_edit)
        hbox.addWidget(remove_button)
        self.cbox_box_layouts.addLayout(hbox)

    @staticmethod
    def remove_cbox(line_edit, button):
        """
        Removes a label from the list of labels.
        """
        # Get the layout that contains the line edit and the button
        hbox = line_edit.parent().layout()

        # Remove the line edit and the button from the layout
        hbox.removeWidget(line_edit)
        hbox.removeWidget(button)

        # Delete the line edit and the button
        line_edit.deleteLater()
        button.deleteLater()

    def update_tristate_checkboxes_state(self, state):
        """
        Updates the state of the tristate_checkboxes option in the config file.

        :param state: The state of the tristate_checkboxes option.
        :type state: int
        """
        self.tristate_checkboxes = bool(state)


class ResolveConflictsPage(QWizardPage):
    def __init__(self, wiz, parent=None):
        """
        Initializes the page.

        :param parent: The parent widget.
        :type parent: QWidget
        """
        super().__init__(parent)
        self.connection_manager = wiz.connection_manager

        self.wiz = wiz
        self.settings = wiz.settings

        self.setTitle("Resolve Conflicts")
        self.setSubTitle("\nSelect the JSON save files for the two annotators...")

        self.layout = QVBoxLayout(self)

        self.conflict_resolution = wiz.conflict_resolution

        # Add input fields for JSON file directories
        self.json1_label = QLabel("JSON file for Annotator 1:")
        self.json1_edit = QLineEdit(self)
        self.json1_button = QPushButton("Browse")
        # set value to the current value
        self.json1_edit.setText(wiz.conflict_resolution_json_files.get("1", ""))
        self.connection_manager.connect(self.json1_button.clicked, self.browse_json1)

        self.json2_label = QLabel("JSON file for Annotator 2:")
        self.json2_edit = QLineEdit(self)
        self.json2_button = QPushButton("Browse")
        # set value to the current value
        self.json2_edit.setText(wiz.conflict_resolution_json_files.get("2", ""))
        self.connection_manager.connect(self.json2_button.clicked, self.browse_json2)

        # Add the JSON file input fields and buttons to the layout
        self.json1_layout = QHBoxLayout()
        self.json1_layout.addWidget(self.json1_edit)
        self.json1_layout.addWidget(self.json1_button)

        self.json2_layout = QHBoxLayout()
        self.json2_layout.addWidget(self.json2_edit)
        self.json2_layout.addWidget(self.json2_button)

        self.layout.addWidget(self.json1_label)
        self.layout.addLayout(self.json1_layout)
        self.layout.addWidget(self.json2_label)
        self.layout.addLayout(self.json2_layout)

        self.json1_label.show()
        self.json1_edit.show()
        self.json1_button.show()
        self.json2_label.show()
        self.json2_edit.show()
        self.json2_button.show()

    def browse_json1(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select First JSON File", "", "JSON Files (*.json)")
        if file_path:
            self.json1_edit.setText(file_path)
            self.check_json_compatibility()

    def browse_json2(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Second JSON File", "", "JSON Files (*.json)")
        if file_path:
            self.json2_edit.setText(file_path)
            self.check_json_compatibility()

    def check_json_compatibility(self):
        def _read_jsons(json_paths):
            json_data = []
            for i, json_path in enumerate(json_paths):
                with open(json_path, "r") as f:
                    json_data.append(json.load(f))
            return json_data

        def _compare_json_config(json_data):
            config_dicts = []
            keys_to_check = ['checkboxes', 'radiobuttons', 'tristate_checkboxes']
            for j in json_data:
                if 'config' not in j:
                    return False
                config_dicts.append({k: j['config'][k] for k in keys_to_check if k in j['config']})
            reference = config_dicts[0]
            for other in config_dicts[1:]:
                if other != reference:
                    return False
            return True

        def _show_incompatible_json_warning():
            # Display warning message
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.setText(f"Error!\n\nThe JSONs for the annotators have incompatible configurations.\n\n"
                            f"Please check that the same checkboxes and radiobuttons were used.")
            ok_button = msg_box.addButton('Ok', QMessageBox.ButtonRole.AcceptRole)
            msg_box.exec()

        if self.json1_edit and self.json2_edit:
            jsons = _read_jsons([self.json1_edit.text(), self.json2_edit.text()])
            compatible = _compare_json_config(jsons)
            if compatible:
                self.wizard().button(QWizard.WizardButton.FinishButton).setEnabled(True)
            else:
                self.wizard().button(QWizard.WizardButton.FinishButton).setEnabled(False)
                _show_incompatible_json_warning()
        else:
            self.wizard().button(QWizard.WizardButton.FinishButton).setEnabled(False)


    def initializePage(self):
        self.wizard().setButtonLayout([
            QWizard.WizardButton.CustomButton1,
            QWizard.WizardButton.CustomButton2,
            QWizard.WizardButton.Stretch,
            QWizard.WizardButton.BackButton,
            QWizard.WizardButton.NextButton,
            QWizard.WizardButton.FinishButton,
            QWizard.WizardButton.CancelButton
        ])

        self.wizard().button(QWizard.WizardButton.NextButton).hide()

        advanced_button = QPushButton("Advanced")
        self.connection_manager.connect(advanced_button.clicked, self.open_advanced_settings)
        self.wizard().setButton(QWizard.WizardButton.CustomButton1, advanced_button)

        load_config_button = QPushButton("Load Config.")
        self.connection_manager.connect(load_config_button.clicked, self.wiz.config_load_dialog)
        self.wizard().setButton(QWizard.WizardButton.CustomButton2, load_config_button)

    def open_advanced_settings(self):
        advanced_settings_dialog = AdvancedSettingsDialog(self)
        advanced_settings_dialog.exec()

    def get_json_file_paths(self):
        """
        Returns the paths of the JSON files if the checkbox is checked.

        :return: Tuple of paths to the JSON files.
        :rtype: tuple
        """
        if self.conflict_resolution:
            return {"1": self.json1_edit.text(), "2": self.json2_edit.text()}
        return {"1": "", "2": ""}

class UnifiedRadiobuttonPage(QWizardPage):
    def __init__(self, wiz, parent=None):
        """
        Initializes the page.

        :param parent: The parent widget.
        :type parent: QWidget
        """
        super().__init__(parent)

        self.connection_manager = wiz.connection_manager

        self.wiz = wiz
        self.radiobuttons = []
        self.settings = wiz.settings

        self.setTitle(f"Radiobuttons")
        self.setSubTitle(f"\nAllow exclusive selection of one of a list of options.")

        self.layout = QVBoxLayout(self)

        row_header_layout = QHBoxLayout()
        row_header_layout.addStretch()

        self.scrollArea = QScrollArea(self)
        self.scrollWidget = QWidget()
        self.scrollLayout = QVBoxLayout()
        self.scrollWidget.setLayout(self.scrollLayout)
        self.scrollArea.setWidget(self.scrollWidget)
        self.scrollArea.setWidgetResizable(True)
        self.layout.addWidget(self.scrollArea)

        # self.rbox_widget = QWidget(self)
        # self.rbox_top_layout = QVBoxLayout(self.rbox_widget)
        # self.rbox_top_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        # self.scrollArea.setWidget(self.rbox_widget)

        self.rbox_layout = QVBoxLayout()

        self.add_rbox_button = QPushButton("+")
        self.add_rbox_button.setProperty('class', 'success')

        row_header_layout.addWidget(self.add_rbox_button, alignment=Qt.AlignmentFlag.AlignTop)
        self.scrollLayout.addLayout(row_header_layout)
        self.scrollLayout.addLayout(self.rbox_layout)
        self.scrollLayout.addStretch()

        self.connection_manager.connect(self.add_rbox_button.clicked, lambda: self.add_group())

    def initializePage(self):

        self.wizard().setButtonLayout([
            QWizard.WizardButton.CustomButton1,
            QWizard.WizardButton.CustomButton2,
            QWizard.WizardButton.Stretch,
            QWizard.WizardButton.BackButton,
            QWizard.WizardButton.NextButton,
            QWizard.WizardButton.FinishButton,
            QWizard.WizardButton.CancelButton
        ])

        # self.wizard().button(QWizard.WizardButton.BackButton).hide()
        self.wizard().button(QWizard.WizardButton.NextButton).hide()

        advanced_button = QPushButton("Advanced")
        self.connection_manager.connect(advanced_button.clicked, self.open_advanced_settings)
        self.wizard().setButton(QWizard.WizardButton.CustomButton1, advanced_button)

        load_config_button = QPushButton("Load Config.")
        self.connection_manager.connect(load_config_button.clicked, self.wiz.config_load_dialog)
        self.wizard().setButton(QWizard.WizardButton.CustomButton2, load_config_button)

    def open_advanced_settings(self):
        advanced_settings_dialog = AdvancedSettingsDialog(self)
        advanced_settings_dialog.exec()

    def add_group(self):
        """
        Adds a radio button group to the page.
        """
        dialog = RadioButtonGroupDialog()
        if dialog.exec() == QDialog.DialogCode.Accepted:
            group = QGroupBox()
            group.setStyleSheet("QGroupBox { margin-top: 0px; padding: 10px; }")
            group_layout = QVBoxLayout()
            grid_layout = QGridLayout()

            remove_button = QPushButton("-")
            remove_button.setProperty('class', 'danger')

            title_layout = QHBoxLayout()
            title_label = QLabel(dialog.title)
            title_layout.addWidget(title_label)
            title_layout.addStretch()
            title_layout.addWidget(remove_button)
            title_label.setAlignment(Qt.AlignmentFlag.AlignTop)
            title_label.setStyleSheet("font-weight: bold; text-transform: uppercase;")
            group_layout.addLayout(title_layout)

            max_label_length = max([len(str(label)) for label in dialog.labels])
            num_columns = ceil(10 / max_label_length)  # Adjust the number of columns based on the label length

            for i, text in enumerate(dialog.labels):
                radio_button = QRadioButton(str(text))
                radio_button.setEnabled(False)
                row = i // num_columns
                col = i % num_columns
                grid_layout.addWidget(radio_button, row, col)

            group_layout.addLayout(grid_layout)
            group.setLayout(group_layout)
            self.rbox_layout.addWidget(group)

            # Add the group to the radio_groups list
            self.radiobuttons.append({
                'group': group,
                'title': dialog.title,
                'labels': dialog.labels
            })

            self.connection_manager.connect(remove_button.clicked, lambda: self.remove_group(group))

    def add_group_without_dialog(self, title, labels):
        """
        Adds a radio button group to the page without opening a dialog.

        :param title: The title of the group.
        :type title: str
        :param labels: The labels of the radio buttons.
        :type labels: list
        """
        group = QGroupBox()
        group.setStyleSheet("QGroupBox { margin-top: 0px; padding: 10px; }")
        group_layout = QVBoxLayout()
        grid_layout = QGridLayout()

        remove_button = QPushButton("-")
        remove_button.setProperty('class', 'danger')

        title_layout = QHBoxLayout()
        title_label = QLabel(title)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addWidget(remove_button)
        title_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        title_label.setStyleSheet("font-weight: bold; text-transform: uppercase;")
        group_layout.addLayout(title_layout)

        max_label_length = max(len(str(label)) for label in labels)
        num_columns = ceil(10 / max_label_length)

        for i, text in enumerate(labels):
            radio_button = QRadioButton(str(text))
            radio_button.setEnabled(False)
            row = i // num_columns
            col = i % num_columns
            grid_layout.addWidget(radio_button, row, col)

        group_layout.addLayout(grid_layout)
        group.setLayout(group_layout)
        self.rbox_layout.addWidget(group)

        self.radiobuttons.append({
            'group': group,
            'title': title,
            'labels': labels
        })

        self.connection_manager.connect(remove_button.clicked, lambda: self.remove_group(group))

    def remove_group(self, group):
        """
        Removes a radio button group from the page.
        """
        # Find the group entry in radio_groups and remove it
        for radio_group in self.radiobuttons:
            if radio_group['group'] is group:
                self.scrollLayout.removeWidget(group)
                group.setParent(None)
                group.deleteLater()
                self.radiobuttons.remove(radio_group)
                break

    def get_group_data(self) -> list:
        """
        Returns the data for the radio button groups.

        :return: The data for the radio button groups.
        :rtype: list
        """
        group_data = []
        for radio_group in self.radiobuttons:
            group_data.append({
                'title': radio_group['title'],
                'labels': radio_group['labels']
            })
        return group_data

    def load_group_data(self, group_data):
        """
        Loads the radio button group data.

        :param group_data: The radio button group data.
        :type group_data: list
        """
        for group in group_data:
            self.add_group_without_dialog(group['title'], group['labels'])


class ConfigurationWizard(QWizard):
    """
    A QWizard implementation for customizing the configuration of the Speedy IQA application.
    Allows users to customize checkbox labels, maximum number of backup files, and directories
    for backup and log files. Can be run from the initial dialog box, from the command line,
    or from Python.

    Methods:
        - create_label_page: Creates the first page of the wizard, allowing users to customize
                                the labels of the checkboxes.
        - create_backup_page: Creates the second page of the wizard, allowing users to customize
                                the maximum number of backup files and the directories for backup
                                and log files.
        - add_label: Adds a new label to the label page for a new checkbox/finding.
        - create_save_page: Creates the third page of the wizard, allowing users to save the
                                configuration to a .yml file.
        - update_combobox_stylesheet: Updates the stylesheet of the QComboBoxes in the label page
                                        to make the options more visible.
        - update_combobox_state: Updates the QComboBox on the save page with the list of existing .yml files.
        - accept: Saves the configuration to a .yml file and closes the wizard.
    """

    def __init__(self, config_file: str):
        """
        Initializes the wizard.

        :param config_file: The configuration file name.
        :type config_file: str
        """
        super().__init__()
        self.settings = QSettings('SpeedyQC', 'DicomViewer')
        self.connection_manager = ConnectionManager()
        self.skip = False
        self.pages = []

        self.setStyleSheet(f"""
            QLineEdit {{
                color: {get_theme(self.settings.value('theme', 'dark_blue.xml'))['secondaryTextColor']};
            }}
            QSpinBox {{
                color: {get_theme(self.settings.value('theme', 'dark_blue.xml'))['secondaryTextColor']};
            }}
            QComboBox {{
                color: {get_theme(self.settings.value('theme', 'dark_blue.xml'))['secondaryTextColor']};
            }}
        """)

        # Set the wizard style to have the title and icon at the top
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)

        self.config_filepath = config_file
        self.config_filename = os.path.basename(config_file)
        self.config_data = None

        # Enable IndependentPages option
        self.setOption(QWizard.WizardOption.IndependentPages, True)

        # Set the logo pixmap
        icon_path = os.path.normpath(os.path.join(resource_dir, 'assets/3x/white_panel@3x.png'))
        pixmap = QPixmap(icon_path)
        self.setPixmap(QWizard.WizardPixmap.LogoPixmap, pixmap.scaled(250, 250, Qt.AspectRatioMode.KeepAspectRatio))

        # Load the config file
        self.config_data = open_yml_file(os.path.normpath(os.path.join(resource_dir, self.config_filename)))

        self.max_backups = self.config_data.get('max_backups', 10)
        self.backup_interval = self.config_data.get('backup_interval', 5)
        self.backup_dir = os.path.normpath(
            self.config_data.get('backup_dir', os.path.normpath(os.path.expanduser('~/speedy_qc/backups')))
        )
        self.log_dir = os.path.normpath(
            self.config_data.get('log_dir', os.path.normpath(os.path.expanduser('~/speedy_qc/logs')))
        )

        self.conflict_resolution = bool(self.config_data.get('conflict_resolution', False))
        self.image_dir_selection_page = SelectImagesPage(self)
        self.addPage(self.image_dir_selection_page)

        self.tristate_checkboxes = bool(self.config_data.get('tristate_checkboxes', False))
        self.cboxes = self.config_data.get('checkboxes', [])
        self.cbox_page = UnifiedCheckboxPage(self)

        self.conflict_resolution_json_files = self.config_data.get('conflict_resolution_json_files', {})
        self.conflict_resolution_page = ResolveConflictsPage(self)

        self.radiobuttons = self.config_data.get('radiobuttons', [])
        self.radio_page = UnifiedRadiobuttonPage(self)
        self.radio_page.load_group_data(self.radiobuttons)

        self.setup_pages()

        # Set the window title and modality
        self.setWindowTitle("Speedy QC Settings")
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        # Set the size of the wizard
        self.resize(640, 800)
        self.setMinimumSize(600, 540)

        self.connection_manager.connect(self.finished, self.save_config)

        self.connection_manager.connect(self.currentIdChanged, self.on_current_id_changed)

    def setup_pages(self):
        # Clear all dynamic pages
        current_page_ids = self.pageIds()
        dynamic_pages = [self.cbox_page, self.radio_page, self.conflict_resolution_page]

        # Remove pages by checking their references
        for page in dynamic_pages:
            # Obtain the page ID by checking if it's in the wizard's current page list
            page.setCommitPage(False)
            for page_id in current_page_ids:
                if self.page(page_id) is page:
                    self.removePage(page_id)

        # Manually manage pages list to ensure accuracy
        self.pages.clear()

        # Always add the image selection page since it's a static first page
        if self.image_dir_selection_page not in self.pages:
            self.pages.append(self.image_dir_selection_page)

        # Based on the conflict resolution, conditionally add other pages
        if not self.conflict_resolution:
            self.addPage(self.cbox_page)
            self.pages.append(self.cbox_page)
            self.addPage(self.radio_page)
            self.pages.append(self.radio_page)
            self.image_dir_selection_page.setCommitPage(False)
            self.radio_page.setCommitPage(True)
        else:
            self.addPage(self.conflict_resolution_page)
            self.pages.append(self.conflict_resolution_page)
            self.image_dir_selection_page.setCommitPage(False)
            self.conflict_resolution_page.setCommitPage(True)

    def on_current_id_changed(self, id: int):
        if self.page(id) is self.conflict_resolution_page:
            self.conflict_resolution_page.check_json_compatibility()

    def update_conflict_resolution(self, state: int):
        self.conflict_resolution = bool(state)
        self.setup_pages()

    def get_annotator_config(self, logger):
        fpath = self.config_data["conflict_resolution_json_files"]['1']
        with open(fpath, 'r') as f:
            data = json.load(f)
        try:
            config = data['config']
            return config['tristate_checkboxes'], config['checkboxes'], config['radiobuttons']
        except KeyError as e:
            logger.error("Couldn't find checkbox and radiobutton config in json for annotator 1.")
            raise e
        except Exception as e:
            raise e

    def save_config(self):
        """
        Saves the configuration file and closes the wizard.
        """
        logger, console_msg = setup_logging(os.path.normpath(self.config_data['log_dir']))

        if not self.skip:

            self.config_data['log_dir'] = os.path.normpath(os.path.abspath(self.log_dir))
            self.config_data['backup_dir'] = os.path.normpath(os.path.abspath(self.backup_dir))
            self.config_data['max_backups'] = self.max_backups
            self.config_data['backup_interval'] = self.backup_interval
            self.config_data['conflict_resolution'] = self.conflict_resolution
            self.config_data["conflict_resolution_json_files"] = self.conflict_resolution_page.get_json_file_paths()

            if not self.conflict_resolution:
                self.config_data['tristate_checkboxes'] = self.cbox_page.tristate_checkboxes
                cboxes = []
                for i in range(self.cbox_page.cbox_box_layouts.count()):
                    hbox = self.cbox_page.cbox_box_layouts.itemAt(i).layout()  # Get the QHBoxLayout
                    if hbox is not None:
                        if hbox.count() > 0:
                            line_edit = hbox.itemAt(0).widget()  # Get the QLineEdit from the QHBoxLayout
                            if line_edit.text():
                                cboxes.append(line_edit.text())
                self.config_data['checkboxes'] = cboxes
                self.config_data['radiobuttons'] = self.radio_page.get_group_data()
            else:
                tristate_checkboxes, checkboxes, radiobuttons = self.get_annotator_config(logger)
                self.config_data['tristate_checkboxes'] = tristate_checkboxes
                self.config_data['checkboxes'] = checkboxes
                self.config_data['radiobuttons'] = radiobuttons

            if not self.config_filename.endswith('.yml'):
                self.config_filename += '.yml'

            self.settings.setValue("last_config_file", os.path.normpath(
                os.path.join(os.path.normpath(os.path.abspath(resource_dir)), self.config_filename))
                                   )
            self.settings.setValue("log_dir", os.path.normpath(os.path.abspath(self.log_dir)))
            self.settings.setValue("backup_dir", os.path.normpath(os.path.abspath(self.backup_dir)))
            self.settings.setValue("max_backups", self.max_backups)
            self.settings.setValue("backup_interval", self.backup_interval)
            self.settings.setValue('tristate_checkboxes', self.tristate_checkboxes)
            self.settings.setValue('conflict_resolution', self.conflict_resolution)
            self.settings.setValue('conflict_resolution_json_files', self.conflict_resolution_page.get_json_file_paths())

            # Save the config file
            with open(os.path.normpath(os.path.join(os.path.abspath(resource_dir), self.config_filename)), 'w') as f:
                yaml.dump(self.config_data, f)

            # Makes a log of the new configuration
            logger.info(f"Configuration saved to {os.path.normpath(os.path.join(resource_dir, self.config_filename))}")
            # super().close()

        else:

            logger.info(f"Configuration loaded from {self.config_filepath}.")

    def config_load_dialog(self):
        load_config_dialog = QFileDialog(self)
        load_config_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        load_config_dialog.setNameFilter("YAML files (*.yml)")
        load_config_dialog.setWindowTitle("Load Configuration File")
        load_config_dialog.setDirectory(resource_dir)
        load_config_dialog.exec()
        if load_config_dialog.result() == QDialog.DialogCode.Accepted:
            self.config_filepath = os.path.normpath(os.path.abspath(load_config_dialog.selectedFiles()[0]))
            self.settings.setValue("last_config_file", self.config_filepath)
            self.skip = True
            super().accept()
        else:
            return


if __name__ == '__main__':
    # Create the application and apply the qt material stylesheet
    app = QApplication([])
    apply_stylesheet(app, theme='dark_blue.xml')

    # Set the directory of the main.py file as the default directory for the config files
    default_dir = resource_dir

    # Load the last config file used
    settings = QSettings('SpeedyQC', 'DicomViewer')
    config_file = settings.value('last_config_file', os.path.normpath(os.path.join(resource_dir, 'config.yml')))

    # Create the configuration wizard
    wizard = ConfigurationWizard(config_file)

    # Run the wizard
    wizard.show()

    app.exec()
