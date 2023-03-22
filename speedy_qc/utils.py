import logging.config
import yaml
import os


def create_default_config():
    default_config = {
        'checkboxes': ['QC1', 'QC2', 'QC3', 'QC4', 'QC5'],
        'max_backups': 10,
        'backup_dir': '~/speedy_qc/backups',
        'log_dir': '~/speedy_qc/logs'
    }

    save_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.yml')

    with open(save_path, 'w') as f:
        yaml.dump(default_config, f)

    return default_config


def open_yml_file(config_path):
    if not os.path.isfile(config_path):
        print(f"Could not find config file at {config_path}")
        if os.path.isfile(os.path.abspath('./speedy_qc/config.yml')):
            print(f"Using default config file at "
                  f"{os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.yml')}")
            config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.yml')
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
        else:
            print(f"Could not find default config file at {config_path}")
            print(f"Creating a new default config file at "
                  f"{os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.yml')}")
            config_data = create_default_config()
    else:
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)

    return config_data


def setup_logging(log_out_path):
    full_log_file_path = os.path.expanduser(os.path.join(log_out_path, "speedy_qc.log"))
    os.makedirs(os.path.dirname(full_log_file_path), exist_ok=True)
    logging.config.fileConfig(os.path.abspath('./speedy_qc/log.conf'), defaults={'log_file_path': full_log_file_path})
    logger = logging.getLogger(__name__)
    console_msg = logging.getLogger(__name__)
    return logger, console_msg

class Connection:
    def __init__(self, signal, slot):
        self.signal = signal
        self.slot = slot
        self.connection = self.signal.connect(self.slot)

    def disconnect(self):
        self.signal.disconnect(self.slot)


class ConnectionManager:
    def __init__(self):
        self.connections = {}

    def connect(self, signal, slot):
        connection = Connection(signal, slot)
        self.connections[id(connection)] = connection

    def disconnect_all(self):
        for connection in self.connections.values():
            if isinstance(connection, Connection):
                connection.disconnect()
        self.connections = {}

