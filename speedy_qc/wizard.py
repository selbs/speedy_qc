"""
wizard.py

This module provides a configuration wizard for the Speedy QC application, allowing users
to customize various settings such as checkbox labels, maximum number of backup files,
and directories for backup and log files. The wizard can be run from the initial dialog
box of the application, from the command line, or from Python.

Classes:
    - RadioButtonPage: A QWizardPage class implementation for selecting a radio button.
    - RadioButtonGroupDialog: A QDialog class implementation for selecting a radio button.
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
from math import ceil

from speedy_qc.utils import open_yml_file, setup_logging, ConnectionManager

if hasattr(sys, '_MEIPASS'):
    # This is a py2app executable
    resource_dir = sys._MEIPASS
elif 'main.py' in os.listdir(os.path.dirname(os.path.abspath("__main__"))):
    # This is a regular Python script
    resource_dir = os.path.dirname(os.path.abspath("__main__"))
else:
    resource_dir = os.path.join(os.path.dirname(os.path.abspath("__main__")), 'speedy_qc')


class RadioButtonPage(QWizardPage):
    """
    A QWizardPage class implementation for adding radio button groups to the configuration.

    :param parent: The parent widget.
    :type parent: QWidget
    """
    def __init__(self, parent=None):
        """
        Initializes the page.

        :param parent: The parent widget.
        :type parent: QWidget
        """
        super().__init__(parent)

        self.connection_manager = ConnectionManager()

        self.setTitle("Radio Button Page")
        self.setSubTitle("\nPlease specify the radio button groups you want to add...\n")

        self.layout = QVBoxLayout(self)

        # Create a scroll area
        self.scrollArea = QScrollArea(self)

        # Create a widget that will contain the radio button groups
        self.scrollWidget = QWidget()
        self.scrollLayout = QVBoxLayout()
        self.scrollWidget.setLayout(self.scrollLayout)

        # Set the widget as the widget of the scroll area
        self.scrollArea.setWidget(self.scrollWidget)
        self.scrollArea.setWidgetResizable(True)

        self.addButton = QPushButton("Add Radio Button Group")
        self.connection_manager.connect(self.addButton.clicked, self.add_group)

        # Add the scroll area and button to the main layout
        self.layout.addWidget(self.addButton)
        self.layout.addWidget(self.scrollArea)

        self.radio_groups = []  # Track the radio button groups

    def add_group(self):
        """
        Adds a radio button group to the page.
        """
        dialog = RadioButtonGroupDialog(self)
        if dialog.exec() == QDialog.Accepted:
            group = QGroupBox(dialog.title)
            layout = QGridLayout()  # Use QGridLayout for multiple columns

            max_label_length = max([len(str(label)) for label in dialog.labels])
            num_columns = ceil(10 / max_label_length)  # Adjust the number of columns based on the label length

            for i, text in enumerate(dialog.labels):
                radio_button = QRadioButton(str(text))
                row = i // num_columns
                col = i % num_columns
                layout.addWidget(radio_button, row, col)

            # Adding a remove button
            removeButton = QPushButton("Remove Group")
            self.connection_manager.connect(removeButton.clicked, lambda: self.remove_group(group))
            layout.addWidget(removeButton, ceil(len(dialog.labels) / num_columns), 0, 1, num_columns)  # Span the remove button across all columns

            group.setLayout(layout)
            self.scrollLayout.addWidget(group)

            # Add the group to the radio_groups list
            self.radio_groups.append({
                'group': group,
                'title': dialog.title,
                'labels': dialog.labels
            })

    def remove_group(self, group):
        """
        Removes a radio button group from the page.
        """
        # Find the group entry in radio_groups and remove it
        for radio_group in self.radio_groups:
            if radio_group['group'] is group:
                self.scrollLayout.removeWidget(group)
                group.setParent(None)
                group.deleteLater()
                self.radio_groups.remove(radio_group)
                break

    def get_group_data(self) -> list:
        """
        Returns the data for the radio button groups.

        :return: The data for the radio button groups.
        :rtype: list
        """
        group_data = []
        for radio_group in self.radio_groups:
            group_data.append({
                'title': radio_group['title'],
                'labels': radio_group['labels']
            })
        return group_data

    def add_group_without_dialog(self, title, labels):
        """
        Adds a radio button group to the page without opening a dialog.

        :param title: The title of the group.
        :type title: str
        :param labels: The labels of the radio buttons.
        :type labels: list
        """
        group = QGroupBox(title)
        layout = QGridLayout()

        max_label_length = max(len(str(label)) for label in labels)
        num_columns = ceil(10 / max_label_length)

        for i, text in enumerate(labels):
            radio_button = QRadioButton(str(text))
            row = i // num_columns
            col = i % num_columns
            layout.addWidget(radio_button, row, col)

        remove_button = QPushButton("Remove Group")
        self.connection_manager.connect(remove_button.clicked, lambda: self.remove_group(group))
        layout.addWidget(remove_button, ceil(len(labels) / num_columns), 0, 1, num_columns)

        group.setLayout(layout)
        self.scrollLayout.addWidget(group)

        self.radio_groups.append({
            'group': group,
            'title': title,
            'labels': labels
        })

    def load_group_data(self, group_data):
        """
        Loads the radio button group data.

        :param group_data: The radio button group data.
        :type group_data: list
        """
        for group in group_data:
            self.add_group_without_dialog(group['title'], group['labels'])


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

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
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
        """
        Initializes the wizard.

        :param config_path: The path to the configuration file.
        :type config_path: str
        """
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
        self.radio_buttons = self.config_data.get('radiobuttons', [])
        self.max_backups = self.config_data.get('max_backups', 10)
        self.backup_interval = self.config_data.get('backup_interval', 5)
        self.backup_dir = self.config_data.get('backup_dir', os.path.expanduser('~/speedy_qc/backups'))
        self.log_dir = self.config_data.get('log_dir', os.path.expanduser('~/speedy_qc/logs'))
        self.tristate_checkboxes = bool(self.config_data.get('tristate_checkboxes', False))

        self.input_option_checkboxes = {}
        # Create pages for the wizard
        self.options_page = self.create_options_page()
        self.label_page = self.create_label_page()
        self.radio_page = self.create_radio_page()
        self.backup_page = self.create_backup_page()
        self.save_page = self.create_save_page()

        self.radio_page.load_group_data(self.radio_buttons)

        # Set up the wizard
        self.addPage(self.options_page)
        self.addPage(self.label_page)
        self.addPage(self.radio_page)
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

    def create_options_page(self):
        """
        Creates the first page of the wizard, allowing users to select which types of input
        they want to use (checkboxes, radio buttons, or both).

        :return: The first page of the wizard.
        :rtype: QWizardPage
        """
        page = QWizardPage()
        page.setTitle("Checkbox Page")
        page.setSubTitle("\nPlease select which types of input you want to use...\n")

        layout = QVBoxLayout(page)
        for input_type in ["Checkbox", "Radio Buttons"]:
            cbox = QCheckBox(input_type)
            layout.addWidget(cbox)
            self.input_option_checkboxes[input_type] = cbox
            layout.addWidget(cbox)

        self.input_option_checkboxes["Checkbox"].setChecked(bool(self.checkboxes))
        self.input_option_checkboxes["Radio Buttons"].setChecked(bool(self.radio_buttons))

        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        return page

    def nextId(self) -> int:
        """
        This method is used to control the order of the pages.

        :return: The ID of the next page to go to.
        :rtype: int
        """
        cboxes = bool(self.input_option_checkboxes["Checkbox"].isChecked())
        radio = bool(self.input_option_checkboxes["Radio Buttons"].isChecked())

        current_id = self.currentId()
        if current_id == 0:  # If we are on the options page...
            if cboxes and not radio:
                return 1  # Go to the checkboxes page
            elif not cboxes and radio:
                return 2  # Go to the radio buttons page
            elif cboxes and radio:
                return 1  # Go to the checkboxes page first
            else:  # If both checkboxes are not checked...
                return 0  # Go back to the options page

        elif current_id == 1:  # If we are on the checkboxes page...
            if radio:
                return 2  # Go to the radio buttons page
            else:
                return 3  # Skip to the backup page

        # If we are not on the first or second page, let QWizard handle the page order normally.
        else:
            return super().nextId()

    def create_label_page(self):
        """
        Creates the page of the wizard that allows users to name the checkboxes.

        :return: The page of the wizard that allows users to name the checkboxes.
        :rtype: QWizardPage
        """
        page = QWizardPage()
        page.setTitle("Checkbox Labels")
        page.setSubTitle("\nPlease name the checkboxes to label the images...\n")

        layout = QVBoxLayout(page)

        cbox_layout = QHBoxLayout()
        self.tristate_checkbox = QCheckBox("Use tri-state checkboxes, i.e. have third uncertain option")
        self.tristate_checkbox.setChecked(bool(self.config_data.get('tristate_checkboxes', False)))
        self.connection_manager.connect(self.tristate_checkbox.stateChanged, self.update_tristate_checkboxes_state)
        cbox_layout.addWidget(self.tristate_checkbox)
        cbox_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        cbox_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addLayout(cbox_layout)

        self.labels_widget = QWidget(page)
        self.labels_layout = QVBoxLayout(self.labels_widget)
        self.labels_layout.setAlignment(Qt.AlignmentFlag.AlignTop)  # Align to the top

        for label in self.checkboxes:
            self.add_label(label)

        self.add_label_button = QPushButton("Add Label")
        self.connection_manager.connect(self.add_label_button.clicked, lambda: self.add_label())

        # Create a QScrollArea
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)  # The contents will resize to fill the scroll area
        self.scroll_area.setWidget(self.labels_widget)

        layout.addWidget(self.scroll_area)
        layout.addWidget(self.add_label_button)

        return page

    def add_label(self, label_text=""):
        """
        Adds a label to the list of labels.
        """
        line_edit = QLineEdit(label_text)
        remove_button = QPushButton("Remove")
        remove_button.setFixedSize(100, 40)

        self.connection_manager.connect(remove_button.clicked, lambda: self.remove_label(line_edit, remove_button))

        # Create a horizontal layout for the line edit and the remove button
        hbox = QHBoxLayout()
        hbox.addWidget(line_edit)
        hbox.addWidget(remove_button)
        self.labels_layout.addLayout(hbox)

    def remove_label(self, line_edit, button):
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

    @staticmethod
    def create_radio_page() -> QWizardPage:
        """
        Creates the page of the wizard that allows users to name the radio buttons.

        :return: The page of the wizard that allows users to name the radio buttons.
        :rtype: QWizardPage
        """
        page = RadioButtonPage()
        return page

    def update_tristate_checkboxes_state(self, state):
        """
        Updates the state of the tristate_checkboxes option in the config file.

        :param state: The state of the tristate_checkboxes option.
        :type state: int
        """
        self.tristate_checkboxes = bool(state)

    def create_backup_page(self) -> QWizardPage:
        """
        Creates the page for the wizard to customise the backup and log directories, and
        the maximum number of backup files.

        :return: The page for the wizard to customise the backup and log directories, and
        the maximum number of backup files.
        :rtype: QWizardPage
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

    def create_save_page(self):
        """
        Creates the page for the wizard to save the configuration file. Allows the user to
        select/overwrite an existing configuration file or enter a new filename.

        :return: The page for the wizard to save the configuration file.
        :rtype: QWizardPage
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
        self.connection_manager.connect(self.config_files_combobox.currentTextChanged,
                                        self.update_config_combobox_state)
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

        if bool(self.input_option_checkboxes["Checkbox"].isChecked()):
            # Save the updated config data
            # Save the updated config data
            new_checkbox_labels = []
            for i in range(self.labels_layout.count()):
                hbox = self.labels_layout.itemAt(i).layout()  # Get the QHBoxLayout
                if hbox is not None:
                    line_edit = hbox.itemAt(0).widget()  # Get the QLineEdit from the QHBoxLayout
                    if line_edit.text():
                        new_checkbox_labels.append(line_edit.text())
            self.config_data['checkboxes'] = new_checkbox_labels
        else:
            self.config_data['checkboxes'] = []

        if bool(self.input_option_checkboxes["Radio Buttons"].isChecked()):
            self.config_data['radiobuttons'] = self.radio_page.get_group_data()
        else:
            self.config_data['radiobuttons'] = []

        self.config_data['tristate_checkboxes'] = self.tristate_checkboxes
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
