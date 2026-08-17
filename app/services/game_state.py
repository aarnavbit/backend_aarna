import time
import uuid
import threading

class GlobalGameState:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(GlobalGameState, cls).__new__(cls)
                cls._instance.reset()
        return cls._instance

    def reset(self):
        self.status = 'waiting' # 'waiting' | 'playing' | 'ended'
        self.round_id = None
        self.round_number = 0
        self.start_time = None
        self.end_time = None
        self.connected_clients = 0

    def start_round(self, round_number: int = None):
        with self._lock:
            self.status = 'playing'
            self.round_id = str(uuid.uuid4())
            if round_number is not None and int(round_number) > 0:
                self.round_number = int(round_number)
            else:
                self.round_number += 1
            self.start_time = int(time.time() * 1000)
            self.end_time = None
            return self.get_state()

    def stop_round(self):
        with self._lock:
            self.status = 'ended'
            self.end_time = int(time.time() * 1000)
            return self.get_state()

    def reset_lobby(self):
        with self._lock:
            self.status = 'waiting'
            self.round_id = None
            self.start_time = None
            self.end_time = None
            return self.get_state()

    def set_connected_clients(self, count: int):
        with self._lock:
            self.connected_clients = count

    def get_state(self):
        return {
            "status": self.status,
            "round_id": self.round_id,
            "roundId": self.round_id,
            "round_number": self.round_number,
            "roundNumber": self.round_number,
            "start_time": self.start_time,
            "startTime": self.start_time,
            "end_time": self.end_time,
            "endTime": self.end_time,
            "connected_clients": self.connected_clients,
            "connectedClients": self.connected_clients
        }

game_state = GlobalGameState()
