"""
main.py

Main module for Speedy QC, a DICOM viewer for desktop which allows image labeling and the drawing of bounding boxes.

This module initializes the application, sets the theme and icon styles, and displays the main window or
configuration wizard based on user input.

Functions:
    load_dicom_dialog() -> str: Prompts the user to select a directory containing DICOM files.
    main(theme: str, material_theme: str, icon_theme: str) -> None: Initializes and runs the application.

Usage:
    Run this module as a script to start the Speedy QC application:
        - From the command line (if installed by pip):
            `speedy_qc`
        - From python:
            `python -m main`
"""


import sys
import os
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QFileDialog, QDialog, QMessageBox, QStyleFactory
from qt_material import apply_stylesheet

from .main_window import MainWindow
from .config_wizard import ConfigurationWizard
from .custom_windows import LoadMessageBox


def load_dicom_dialog():
    """
    Prompts the user to select a directory of DICOM files. The function continues to prompt the user until
    a valid directory containing DICOM files is selected or the user cancels the operation.

    :return: str, the selected directory containing DICOM files. If the user cancels the operation, the program exits.
    """

    # Continue to prompt the user to select a directory until a valid directory is selected
    dicom_dir = None
    while dicom_dir is None:
        # Use QFileDialog to select a directory
        dir_dialog = QFileDialog()
        dir_dialog.setFileMode(QFileDialog.FileMode.Directory)
        dir_dialog.setWindowTitle("Select DICOM directory")
        if dir_dialog.exec() == QDialog.DialogCode.Accepted:
            dir_path = dir_dialog.selectedFiles()[0]
            if dir_path:
                # List dicom files in the selected directory
                dcm_files = [f for f in os.listdir(dir_path) if f.endswith('.dcm')]
                # Show an error message box if the selected directory does not contain any dicom files
                if len(dcm_files) == 0:
                    error_msg_box = QMessageBox()
                    error_msg_box.setIcon(QMessageBox.Icon.Warning)
                    error_msg_box.setWindowTitle("Error")
                    error_msg_box.setText("The directory does not appear to contain any dicom files!")
                    error_msg_box.setInformativeText("Please try again.")
                    error_msg_box.exec()
                else:
                    return dir_path
        else:
            sys.exit()


def main(theme='qt_material', material_theme='dark_blue.xml', icon_theme='qtawesome'):
    """
    Main function. Creates the main window and runs the application.

    If the user selects to `Conf. Wizard` in the initial dialog box (load_msg_box), the ConfigurationWizard is shown
    instead, allowing the user to configure the application settings. The last selected config .yml file is saved and
    shown as the default in the QComboBox of the initial dialog box.

    The user must select a folder of DICOM files to run the application. If the selected folder does not contain any
    DICOM files, an error message box is shown, and the user is prompted to select a new folder.

    :param theme: str, the application theme. Default is 'qt_material', which uses the qt_material library. Other options
        include 'Fusion', 'Windows', 'WindowsVista', 'WindowsXP', 'Macintosh', 'Plastique', 'Cleanlooks', 'CDE', 'GTK+'
        and 'Motif' from the QStyleFactory class.
    :param material_theme: str, the qt_material theme if theme set to qt_material. Default is 'dark_blue.xml'.
    :param icon_theme: str, the icon theme. Default is 'qtawesome', which uses the qtawesome library. Other options
        include 'breeze', 'breeze-dark', 'hicolor', 'oxygen', 'oxygen-dark', 'tango', 'tango-dark', and 'faenza' from the
        QIcon class.
    """

    # Create the application
    app = QApplication(sys.argv)

    # Set the application theme
    if theme == 'qt_material':
        apply_stylesheet(app, theme=material_theme)
    else:
        app.setStyle(QStyleFactory.create(theme))

    # Set the application icon theme
    QIcon.setThemeName(icon_theme)

    # Create the initial dialog box
    load_msg_box = LoadMessageBox()
    result = load_msg_box.exec()

    if result == load_msg_box.DialogCode.Accepted:
        # If the user selects to `Ok`, load the dialog to select the dicom directory
        dicom_dir = load_dicom_dialog()
        # Create the main window and pass the dicom directory
        window = MainWindow(dicom_dir)
        window.show()
    elif result == load_msg_box.DialogCode.Rejected:
        # If the user selects to `Cancel`, exit the application
        sys.exit()
    else:
        # If the user selects to `Conf. Wizard`, show the ConfigurationWizard
        config_file = load_msg_box.config_combo.currentText()
        load_msg_box.save_last_config(config_file)
        wizard = ConfigurationWizard(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.yml'))
        wizard.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
