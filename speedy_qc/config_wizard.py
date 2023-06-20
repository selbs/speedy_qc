"""
config_wizard.py

This module provides a configuration wizard for the Speedy QC application, allowing users
to customize various settings such as checkbox labels, maximum number of backup files,
and directories for backup and log files. The wizard can be run from the initial dialog
box of the application, from the command line, or from Python.

Classes:
    - ConfigurationWizard: A QWizard class implementation to guide users through the process of
                           customizing the application configuration.
"""

from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
import yaml
import os
from qt_material import apply_stylesheet, get_theme
import sys
import pkg_resources

from speedy_qc.utils import open_yml_file, setup_logging, ConnectionManager

if hasattr(sys, '_MEIPASS'):
    # This is a py2app executable
    resource_dir = sys._MEIPASS
elif 'main.py' in os.listdir(os.path.dirname(os.path.abspath("__main__"))):
    # This is a regular Python script
    resource_dir = os.path.dirname(os.path.abspath("__main__"))
else:
    resource_dir = os.path.join(os.path.dirname(os.path.abspath("__main__")), 'speedy_qc')

class ConfigurationWizard(QWizard):
    """
    A QWizard implementation for customizing the configuration of the Speedy QC application.
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
    def __init__(self, config_path: str):
        super().__init__()
        self.settings = QSettings('SpeedyQC', 'DicomViewer')
        self.connection_manager = ConnectionManager()

        self.setStyleSheet(f"""
            QLineEdit {{
                color: {get_theme('dark_blue.xml')['primaryLightColor']};
            }}
            QSpinBox {{
                color: {get_theme('dark_blue.xml')['primaryLightColor']};
            }}
            QComboBox {{
                color: {get_theme('dark_blue.xml')['primaryLightColor']};
            }}
        """)

        # Set the wizard style to have the title and icon at the top
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)

        self.config_path = config_path
        self.config_data = None

        # Enable IndependentPages option
        self.setOption(QWizard.WizardOption.IndependentPages, True)

        # Set the logo pixmap

        icon_path = os.path.join(resource_dir, 'assets/3x/white_panel@3x.png')
        pixmap = QPixmap(icon_path)
        self.setPixmap(QWizard.WizardPixmap.LogoPixmap, pixmap.scaled(320, 320, Qt.AspectRatioMode.KeepAspectRatio))

        # Load the config file
        self.config_data = open_yml_file(self.config_path)
        self.checkboxes = self.config_data.get('checkboxes', [])
        self.max_backups = self.config_data.get('max_backups', 10)
        self.backup_interval = self.config_data.get('backup_interval', 5)
        self.backup_dir = self.config_data.get('backup_dir', os.path.expanduser('~/speedy_qc/backups'))
        self.log_dir = self.config_data.get('log_dir', os.path.expanduser('~/speedy_qc/logs'))
        self.tristate_cboxes = self.config_data.get('tristate_checkboxes', False)

        # Create pages for the wizard
        self.label_page = self.create_label_page()
        self.backup_page = self.create_backup_page()
        self.save_page = self.create_save_page()

        # Set up the wizard
        self.addPage(self.label_page)
        self.addPage(self.backup_page)
        self.addPage(self.save_page)

        # Set the window title and modality
        self.setWindowTitle("Speedy QC Configuration Wizard")
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        # Set the size of the wizard to allow for list of checkboxes to fit nicely
        self.resize(700, 800)

        # Set the default button to be the next / finish button
        next_button = self.button(QWizard.NextButton)
        next_button.setDefault(True)

    def create_label_page(self):
        """
        Creates the page for the wizard to customize the labels for the checkboxes.

        Returns:
            QWizardPage: The QWizardPage containing the UI elements for customizing checkbox labels.
        """
        page = QWizardPage()
        page.setTitle("Checkbox Labels")
        page.setSubTitle("\nPlease name the checkboxes to label the images...\n")

        # Create a vertical layout for the page
        layout = QVBoxLayout(page)

        cbox_layout = QHBoxLayout()
        self.tristate_checkbox = QCheckBox("Use tri-state checkboxes, i.e. have third uncertain option")
        self.tristate_checkbox.setChecked(bool(self.config_data.get('tristate_checkboxes', False)))
        self.connection_manager.connect(self.tristate_checkbox.stateChanged, self.update_tristate_checkboxes_state)
        cbox_layout.addWidget(self.tristate_checkbox)
        cbox_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        cbox_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addLayout(cbox_layout)

        # Create a widget for the checkbox labels
        self.labels_widget = QWidget(page)
        self.labels_layout = QVBoxLayout(self.labels_widget)

        for label in self.checkboxes:
            line_edit = QLineEdit(label)
            self.labels_layout.addWidget(line_edit)

        self.add_label_button = QPushButton("Add Label")
        self.add_label_button.clicked.connect(self.add_label)

        layout.addWidget(self.labels_widget)
        layout.addWidget(self.add_label_button)

        return page

    def update_tristate_checkboxes_state(self, state):
        """
        Updates the state of the tristate_checkboxes option in the config file.
        """
        self.config_data['tristate_checkboxes'] = state

    def create_backup_page(self):
        """
        Creates the page for the wizard to customise the backup and log directories, and
        the maximum number of backup files.
        """

        page = QWizardPage()
        page.setTitle("Logging and Backup Files")
        page.setSubTitle("\nPlease choose where logs and backups should be stored, and\n"
                         "specify maximum number of backup files...\n")

        # Create a vertical layout for the page
        layout = QVBoxLayout(page)


        self.backup_widget = QWidget(page)
        self.backup_layout = QVBoxLayout(self.backup_widget)

        # Create a widget for the log directory
        log_dir_label = QLabel("Log Directory:")
        self.log_dir_edit = QLineEdit()
        self.log_dir_edit.setText(self.settings.value("log_dir", os.path.expanduser(self.log_dir)))
        self.backup_layout.addWidget(log_dir_label)
        self.backup_layout.addWidget(self.log_dir_edit)

        spacer = QSpacerItem(0, 40, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.backup_layout.addItem(spacer)

        backup_dir_label = QLabel("Backup Directory:")
        self.backup_dir_edit = QLineEdit()
        self.backup_dir_edit.setText(self.settings.value("backup_dir", os.path.expanduser(self.backup_dir)))
        self.backup_layout.addWidget(backup_dir_label)
        self.backup_layout.addWidget(self.backup_dir_edit)

        # Create a widget for the maximum number of backups
        self.backup_spinbox = QSpinBox()
        self.backup_spinbox.setRange(1, 100)
        self.backup_spinbox.setValue(self.max_backups)

        self.backup_layout.addWidget(QLabel("Maximum Number of Backups:"))
        self.backup_layout.addWidget(self.backup_spinbox)

        self.backup_int_spinbox = QSpinBox()
        self.backup_int_spinbox.setRange(1, 30)
        self.backup_int_spinbox.setValue(self.backup_interval)

        self.backup_layout.addWidget(QLabel("Backup Interval (mins):"))
        self.backup_layout.addWidget(self.backup_int_spinbox)

        layout.addWidget(self.backup_widget)

        return page

    def add_label(self):
        """
        Adds a new label to the list of labels to add additional checkboxes.
        """
        line_edit = QLineEdit()
        self.labels_layout.addWidget(line_edit)

    def create_save_page(self):
        """
        Creates the page for the wizard to save the configuration file. Allows the user to
        select/overwrite an existing configuration file or enter a new filename.

        Returns:
            QWizardPage: The QWizardPage containing the UI elements for saving the configuration file.
        """
        page = QWizardPage()
        page.setTitle("Save Configuration")
        page.setSubTitle("\nPlease select an existing configuration file or enter a new filename...\n")

        # Create a vertical layout for the page
        layout = QVBoxLayout(page)

        # Create QComboBox for the list of available .yml files
        self.config_files_combobox = QComboBox()
        for file in os.listdir(resource_dir):
            if file.endswith('.yml'):
                self.config_files_combobox.addItem(file)

        layout.addWidget(QLabel("Existing Configuration Files:"))
        layout.addWidget(self.config_files_combobox)

        # Create QLineEdit for the filename
        self.filename_edit = QLineEdit()
        self.filename_edit.setPlaceholderText("config.yml")
        self.filename_edit.textChanged.connect(self.update_config_combobox_state)  # Connect the textChanged signal
        layout.addWidget(QLabel("New Filename (Optional):"))
        layout.addWidget(self.filename_edit)

        # Display the save path
        layout.addWidget(QLabel("Save directory:"))
        save_dir_label = QLabel(resource_dir)
        layout.addWidget(save_dir_label)

        return page

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
            self.config_files_combobox.setStyleSheet(f"""QComboBox {{
                color: {get_theme('dark_blue.xml')['primaryLightColor']};
            }}""")
        else:
            self.config_files_combobox.setStyleSheet("QComboBox { color: gray; }")

    def accept(self):
        """
        Saves the configuration file and closes the wizard.
        """
        # Get the filename from the QLineEdit or QComboBox
        filename = self.filename_edit.text()
        if not filename:
            filename = self.config_files_combobox.currentText()

        # Add .yml extension if not provided by the user
        if not filename.endswith('.yml'):
            filename += '.yml'

        # Save the updated config data
        new_checkbox_labels = []
        for i in range(self.labels_layout.count()):
            line_edit = self.labels_layout.itemAt(i).widget()
            if line_edit.text():
                new_checkbox_labels.append(line_edit.text())

        self.config_data['checkboxes'] = new_checkbox_labels
        self.config_data['tristate_cboxes'] = bool(self.tristate_checkbox.checkState())
        self.config_data['max_backups'] = self.backup_spinbox.value()
        self.config_data['backup_interval'] = self.backup_int_spinbox.value()
        self.config_data['backup_dir'] = self.backup_dir_edit.text()
        self.config_data['log_dir'] = self.log_dir_edit.text()

        save_path = os.path.join(resource_dir, filename)

        # Save the config file
        with open(save_path, 'w') as f:
            yaml.dump(self.config_data, f)

        # Makes a log of the new configuration
        logger, console_msg = setup_logging(self.config_data['log_dir'])
        logger.info(f"Configuration saved to {save_path}")

        # Inform the user that the configuration has been saved
        QMessageBox.information(self, "Configuration Saved", "The configuration has been saved.")

        super().accept()


if __name__ == '__main__':

    # Create the application and apply the qt material stylesheet
    app = QApplication([])
    apply_stylesheet(app, theme='dark_blue.xml')

    # Set the directory of the main.py file as the default directory for the config files
    default_dir = resource_dir

    # Load the last config file used
    settings = QSettings('SpeedyQC', 'DicomViewer')
    config_file = settings.value('config_file', os.path.join(default_dir, 'config.yml'))

    # Create the configuration wizard
    wizard = ConfigurationWizard(config_file)

    # Run the wizard
    wizard.show()

    app.exec()
