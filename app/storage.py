"""Local atomic JSON persistence with private files and a process-wide lock."""
import copy
import json
import os
from pathlib import Path
import tempfile
import threading
import shutil
from datetime import datetime, timezone
from .learning import initialize
from .curriculum import initial_curriculum


class Store:
    def __init__(self, root):
        self.root = Path(root)
        self.data = self.root / "data"
        self.data.mkdir(exist_ok=True)
        self.lock = threading.RLock()
        self.curriculum_path = self.data / "curriculum.json"
        self.state_path = self.data / "state.json"
        self.curriculum = self._load(self.curriculum_path, initial_curriculum())
        self.state = self._load(self.state_path, {"schemaVersion": 1, "progress": {}, "responses": {}, "attempts": [], "reviews": {}, "activity": [], "preferences": {"gloss": "en", "pinyin": False}})

        if 'learning' not in self.state:
            backups = self.data / 'backups'
            backups.mkdir(exist_ok=True)
            backup = backups / ('state-before-microlearning-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f') + '.json')
            shutil.copy2(self.state_path, backup)
            backup.chmod(0o600)
            initialize(self.state)
            self.save_state()

    def _load(self, path, default):
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except (ValueError, OSError) as e:
                raise RuntimeError(f"Cannot read {path.name}. Restore a backup; the file has NOT been replaced.") from e
        self.write(path, default)
        return default

    def write(self, path, value):
        descriptor, name = tempfile.mkstemp(prefix=".save-", dir=self.data)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as f:
                json.dump(value, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())
            os.chmod(name, 0o600)
            os.replace(name, path)
        finally:
            if os.path.exists(name):
                os.unlink(name)

    def save_state(self):
        self.write(self.state_path, self.state)

    def save_curriculum(self, curriculum=None):
        target = curriculum if curriculum is not None else self.curriculum
        self.write(self.curriculum_path, target)
        self.curriculum = target

    def lesson(self, lesson_id):
        return next((l for l in self.curriculum["lessons"] + self.curriculum["supplementary"] if l["id"] == lesson_id), None)

    def snapshot(self):
        with self.lock:
            return copy.deepcopy(self.state)
