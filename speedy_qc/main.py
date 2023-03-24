"""
main.py

Main module for Speedy QC, a DICOM viewer for desktop which allows image labeling and the drawing of bounding boxes.

This module initializes the application, sets the theme and icon styles, and displays the main window or
configuration wizard based on user input.

Functions:
    main(theme: str, material_theme: str, icon_theme: str) -> None: Initializes and runs the application.
    load_dicom_dialog() -> str: Prompts the user to select a directory containing DICOM files.

Usage:
    Run this module as a script to start the Speedy QC application:
        - From the command line (if installed by pip):
            `speedy_qc`
        - From python:
            `python -m main`
"""


import sys
import os
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from qt_material import apply_stylesheet

from speedy_qc.main_window import MainWindow
from speedy_qc.config_wizard import ConfigurationWizard
from speedy_qc.custom_windows import LoadMessageBox, SetupWindow

if hasattr(sys, '_MEIPASS'):
    # This is a py2app executable
    resource_dir = sys._MEIPASS
elif 'main.py' in os.listdir(os.path.dirname(os.path.abspath("__main__"))):
    # This is a regular Python script
    resource_dir = os.path.dirname(os.path.abspath("__main__"))
else:
    resource_dir = os.path.join(os.path.dirname(os.path.abspath("__main__")), 'speedy_qc')




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

    settings = QSettings('SpeedyQC', 'DicomViewer')

    # User selects to `Ok` -> load the load dialog box
    if result == load_msg_box.DialogCode.Accepted:
        # If the user selects to `Ok`, load the dialog to select the dicom directory
        setup_window = SetupWindow(settings)
        result = setup_window.exec()

        if result == setup_window.DialogCode.Accepted:
            # Create the main window and pass the dicom directory
            window = MainWindow(settings)
            window.show()
        else:
            sys.exit()

    # User selects to `Cancel` -> exit the application
    elif result == load_msg_box.DialogCode.Rejected:
        sys.exit()

    # User selects to `Conf. Wizard` -> show the ConfigurationWizard
    else:
        config_file = load_msg_box.config_combo.currentText()
        load_msg_box.save_last_config(config_file)
        if hasattr(sys, '_MEIPASS'):
            # This is a py2app executable
            resource_dir = sys._MEIPASS
        elif 'main.py' in os.listdir(os.path.dirname(os.path.abspath("__main__"))):
            # This is a regular Python script
            resource_dir = os.path.dirname(os.path.abspath("__main__"))
        else:
            resource_dir = os.path.join(os.path.dirname(os.path.abspath("__main__")), 'speedy_qc')
        wizard = ConfigurationWizard(os.path.join(resource_dir, 'config.yml'))
        wizard.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
