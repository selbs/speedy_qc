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

