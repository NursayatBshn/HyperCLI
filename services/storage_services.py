import json
import os
from datetime import datetime

DATA_ROOT = "data"

class StorageService:
    def __init__(self, filepath):
        self.filepath = os.path.join(DATA_ROOT, filepath)
        self.max_entries = 100

    def _ensure_file_exists(self):
        # Create file if needed
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        if not os.path.exists(self.filepath):
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump([], f)

    def read_all(self):
        with open(self.filepath, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []

    def trim_entries(self):
        data = self.read_all()
        if len(data) <= self.max_entries:
            return

        with open(self.filepath, 'w', encoding='utf-8') as f:
            json.dump(data[-self.max_entries:], f, indent=4)

    def add_entry(self, entry):
        data = self.read_all()
        entry['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data.append(entry)
        data = data[-self.max_entries:]

        with open(self.filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)

class HistoryService(StorageService):
    def log_command(self, command, status, result):
        self.add_entry({"command": command, "status": status, "result": result})

class LoggerService(StorageService):
    def log_event(self, level, message):
        self.add_entry({"level": level, "message": message})
