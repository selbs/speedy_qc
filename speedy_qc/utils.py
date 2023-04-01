"""
utils.py

Utility module for the speedy_qc application.

This module provides utility functions and classes to support the speedy_qc application, including:

1. Default configuration file creation and management.
2. YAML file loading.
3. Logging setup.
4. Connection management for signals and slots in a Qt application.

Functions:
    create_default_config() -> dict
    open_yml_file(config_path: str) -> dict
    setup_logging(log_out_path: str) -> Tuple[logging.Logger, logging.Logger]

Classes:
    Connection
    ConnectionManager
"""

import logging.config
import yaml
import os
from typing import Dict, Tuple, Any
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
import sys
from qt_material import get_theme


if hasattr(sys, '_MEIPASS'):
    # This is a py2app executable
    resource_dir = sys._MEIPASS
elif 'main.py' in os.listdir(os.path.dirname(os.path.abspath("__main__"))):
    # This is a regular Python script
    resource_dir = os.path.dirname(os.path.abspath("__main__"))
else:
    resource_dir = os.path.join(os.path.dirname(os.path.abspath("__main__")), 'speedy_qc')

def create_default_config() -> Dict:
    """
    Creates a default config file in the speedy_qc directory.

    :return: dict, the default configuration data.
    """
    # Default config...
    default_config = {
        'checkboxes': ['QC1', 'QC2', 'QC3', 'QC4', 'QC5'],
        'max_backups': 10,
        'backup_dir': os.path.expanduser('~/speedy_qc/backups'),
        'log_dir': os.path.expanduser('~/speedy_qc/logs'),
        'tristate_checkboxes': True,
        'backup_interval': 5,
    }

    save_path = os.path.join(resource_dir, 'config.yml')

    # Save the default config to the speedy_qc directory
    with open(save_path, 'w') as f:
        yaml.dump(default_config, f)

    return default_config

def open_yml_file(config_path: str) -> Dict:
    """
    Opens a config .yml file and returns the data. If the file does not exist, it will look
    for the default config file, otherwise, it will create a new default config file.

    :param config_path: str, the path to the config file.
    :return: dict, the loaded configuration data from the YAML file.
    """
    # print("*"*50)
    # print("Resource directory:", resource_dir)
    # print("*"*50)

    if not os.path.isfile(config_path):
        # If the config file does not exist, look for the default config file
        print(f"Could not find config file at {config_path}")
        if os.path.isfile(os.path.join(resource_dir, 'config.yml')):
            print(f"Using default config file at "
                  f"{os.path.join(resource_dir, 'config.yml')}")
            config_path = os.path.join(resource_dir, 'config.yml')
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
        else:
            # If the default config file does not exist, create a new one
            print(f"Could not find default config file at {os.path.join(resource_dir, 'config.yml')}")
            print(f"Creating a new default config file at "
                  f"{os.path.join(resource_dir, 'config.yml')}")
            config_data = create_default_config()
    else:
        # Open the config file and load the data
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)

    return config_data


def setup_logging(log_out_path: str) -> Tuple[logging.Logger, logging.Logger]:
    """
    Sets up the logging for the application. The log file will be saved in the log_out_path in the directory
    specified in the chosen config .yml file.

    :param log_out_path: str, the path to the directory where the log file will be saved.
    :return: tuple (logger, console_msg), where logger is a configured logging.Logger instance, and console_msg is a
             reference to the same logger to be used for console messaging.
    """
    full_log_file_path = os.path.expanduser(os.path.join(log_out_path, "speedy_qc.log"))
    os.makedirs(os.path.dirname(full_log_file_path), exist_ok=True)
    logging.config.fileConfig(os.path.join(resource_dir, 'log.conf'), defaults={'log_file_path': full_log_file_path})
    logger = logging.getLogger(__name__)
    console_msg = logging.getLogger(__name__)
    return logger, console_msg

class Connection:
    """
    A class to manage a single connection between a signal and a slot in a Qt application.
    """
    def __init__(self, signal: pyqtSignal, slot: callable):
        self.signal = signal
        self.slot = slot
        self.connection = self.signal.connect(self.slot)

    def disconnect(self):
        """
        Disconnects the signal from the slot.
        """
        self.signal.disconnect(self.slot)


class ConnectionManager:
    """
    A class to manage multiple connections between signals and slots in a Qt application.
    """
    def __init__(self):
        self.connections = {}

    def connect(self, signal: Any, slot: callable):
        """
        Connects a signal to a slot and stores the connection in a dictionary.

        :param signal: QtCore.pyqtSignal, the signal to connect.
        :param slot: callable, the slot (function or method) to connect to the signal.
        """
        connection = Connection(signal, slot)
        self.connections[id(connection)] = connection

    def disconnect_all(self):
        """
        Disconnects all connections and clears the dictionary.
        """
        for connection in self.connections.values():
            if isinstance(connection, Connection):
                connection.disconnect()
        self.connections = {}

