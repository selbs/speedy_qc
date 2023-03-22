import sys
import os
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QFileDialog, QDialog, QMessageBox, QDialogButtonBox
from qt_material import apply_stylesheet

from .main_window import MainWindow
from .config_wizard import ConfigurationWizard
from .custom_windows import LoadMessageBox


def main():
    app = QApplication(sys.argv)

    apply_stylesheet(app, theme='dark_blue.xml')
    QIcon.setThemeName('qtawesome')

    load_msg_box = LoadMessageBox()
    result = load_msg_box.exec()

    dicom_dir = None
    if result == load_msg_box.DialogCode.Accepted:
        while dicom_dir is None:
            # Use QFileDialog to select a directory
            dir_dialog = QFileDialog()
            dir_dialog.setFileMode(QFileDialog.FileMode.Directory)
            dir_dialog.setWindowTitle("Select DICOM directory")
            if dir_dialog.exec() == QDialog.DialogCode.Accepted:
                dir_path = dir_dialog.selectedFiles()[0]
                if dir_path:
                    dcm_files = [f for f in os.listdir(dir_path) if f.endswith('.dcm')]
                    if len(dcm_files) == 0:
                        error_msg_box = QMessageBox()
                        error_msg_box.setIcon(QMessageBox.Icon.Warning)
                        error_msg_box.setWindowTitle("Error")
                        error_msg_box.setText("The directory does not appear to contain any dicom files!")
                        error_msg_box.setInformativeText("Please try again.")
                        error_msg_box.exec()
                    else:
                        dicom_dir = dir_path
            else:
                sys.exit()
        window = MainWindow(dicom_dir)
        window.show()
    elif result == load_msg_box.DialogCode.Rejected:
        # Use the selected config file from the QComboBox
        config_file = load_msg_box.config_combo.currentText()
        # Save the selected config file to QSettings
        load_msg_box.save_last_config(config_file)

        wizard = ConfigurationWizard(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.yml'))
        wizard.show()
    else:
        sys.exit()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
