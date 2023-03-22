import logging.config
import yaml
import os

def open_yml_file(config_path):
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

