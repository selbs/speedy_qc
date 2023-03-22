from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
import yaml
import os
from qt_material import apply_stylesheet, get_theme

class ConfigurationWizard(QWizard):
    def __init__(self, config_path):
        super().__init__()
        self.settings = QSettings('SpeedyQC', 'DicomViewer')

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

        # Set the wizard style
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)

        self.config_path = config_path
        self.config_data = None

        # Enable IndependentPages option
        self.setOption(QWizard.WizardOption.IndependentPages, True)

        # Set the logo pixmap
        icon_path = os.path.join(os.path.dirname(__file__), 'assets/3x/white_panel@3x.png')
        pixmap = QPixmap(icon_path)
        self.setPixmap(QWizard.WizardPixmap.LogoPixmap, pixmap.scaled(240, 240, Qt.AspectRatioMode.KeepAspectRatio))

        # Load the config file
        with open(self.config_path, 'r') as f:
            self.config_data = yaml.safe_load(f)

        self.checkbox_labels = self.config_data.get('checkbox_labels', [])
        self.max_backups = self.config_data.get('max_backups', 10)
        self.backup_dir = self.config_data.get('backup_dir', '~/.speedy_qc_backups')

        # Create pages for the wizard
        self.label_page = self.create_label_page()
        self.backup_page = self.create_backup_page()
        self.save_page = self.create_save_page()

        # Set up the wizard
        self.addPage(self.label_page)
        self.addPage(self.backup_page)
        self.addPage(self.save_page)

        self.setWindowTitle("Speedy QC Configuration Wizard")
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        self.resize(700, 800)

    def create_label_page(self):
        page = QWizardPage()
        page.setTitle("Checkbox Labels")
        page.setSubTitle("\nPlease name the checkboxes to label the images...\n")

        # Create a vertical layout for the page
        layout = QVBoxLayout(page)

        # Create a widget for the checkbox labels
        self.labels_widget = QWidget(page)
        self.labels_layout = QVBoxLayout(self.labels_widget)

        for label in self.checkbox_labels:
            line_edit = QLineEdit(label)
            self.labels_layout.addWidget(line_edit)

        self.add_label_button = QPushButton("Add Label")
        self.add_label_button.clicked.connect(self.add_label)

        layout.addWidget(self.labels_widget)
        layout.addWidget(self.add_label_button)

        return page

    def create_backup_page(self):
        page = QWizardPage()
        page.setTitle("Backup Files")
        page.setSubTitle("\nPlease choose where backups should be stored and maximum number of backup files...\n")

        # Create a vertical layout for the page
        layout = QVBoxLayout(page)

        # Create a widget for the maximum number of backups
        self.backup_widget = QWidget(page)
        self.backup_layout = QVBoxLayout(self.backup_widget)

        self.backup_spinbox = QSpinBox()
        self.backup_spinbox.setRange(1, 100)
        self.backup_spinbox.setValue(self.max_backups)

        self.backup_layout.addWidget(QLabel("Maximum Number of Backups:"))
        self.backup_layout.addWidget(self.backup_spinbox)

        backup_dir_label = QLabel("Backup Directory:")
        self.backup_dir_edit = QLineEdit()
        self.backup_dir_edit.setText(self.settings.value("backup_dir", os.path.expanduser("~/.speedy_qc_backups")))
        self.backup_layout.addWidget(backup_dir_label)
        self.backup_layout.addWidget(self.backup_dir_edit)

        layout.addWidget(self.backup_widget)

        return page

    def add_label(self):
        line_edit = QLineEdit()
        self.labels_layout.addWidget(line_edit)

    def create_save_page(self):
        page = QWizardPage()
        page.setTitle("Save Configuration")
        page.setSubTitle("\nPlease select an existing configuration file or enter a new filename...\n")

        # Create a vertical layout for the page
        layout = QVBoxLayout(page)

        # Create QComboBox for the list of available .yml files
        self.config_files_combobox = QComboBox()
        script_dir = os.path.dirname(os.path.abspath(__file__))
        for file in os.listdir(script_dir):
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
        save_dir_label = QLabel(os.path.dirname(os.path.abspath(__file__)))
        layout.addWidget(save_dir_label)

        return page

    def update_config_combobox_state(self):
        if self.filename_edit.text():
            self.config_files_combobox.setEnabled(False)
        else:
            self.config_files_combobox.setEnabled(True)
        self.update_combobox_stylesheet()

    def update_combobox_stylesheet(self):
        if self.config_files_combobox.isEnabled():
            self.config_files_combobox.setStyleSheet(f"""QComboBox {{
                color: {get_theme('dark_blue.xml')['primaryLightColor']};
            }}""")
        else:
            self.config_files_combobox.setStyleSheet("QComboBox { color: gray; }")

    def accept(self):
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
        self.config_data['max_backups'] = self.backup_spinbox.value()

        save_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)

        with open(save_path, 'w') as f:
            yaml.dump(self.config_data, f)

        QMessageBox.information(self, "Configuration Saved", "The configuration has been saved.")

        super().accept()


if __name__ == '__main__':
    app = QApplication([])

    apply_stylesheet(app, theme='dark_blue.xml')

    # Set the directory of the main.py file as the default save directory
    default_dir = os.path.dirname(os.path.abspath(__file__))

    # Create the configuration wizard
    wizard = ConfigurationWizard(os.path.join(default_dir, 'config.yml'))

    # Run the wizard
    wizard.show()

    app.exec()
