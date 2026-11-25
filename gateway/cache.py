import hashlib
import json
import sqlite3
import time
from typing import Optional


class DiagnosticCache:
    def __init__(self, db_path: str = "edge_cache.db", ttl_seconds: int = 3600):
        self.db_path = db_path
        self.ttl = ttl_seconds
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    state_hash TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    created_at REAL NOT NULL
                )
            """)

    def _compute_key(self, alarm_code: int, temp_band: int, pressure_band: int) -> str:
        # Discretiza variáveis contínuas em faixas para funcionar como cache semântico de estado
        raw = f"alarm:{alarm_code}|temp_band:{temp_band}|p_desc_band:{pressure_band}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def get(self, alarm_code: int, temp_c: float, p_desc_psi: float) -> Optional[dict]:
        key = self._compute_key(alarm_code, int(temp_c // 2), int(p_desc_psi // 15))
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT payload, created_at FROM cache WHERE state_hash = ?", (key,)
            ).fetchone()

        if not row:
            return None

        payload, created_at = row
        if time.time() - created_at > self.ttl:
            return None

        return json.loads(payload)

    def set(self, alarm_code: int, temp_c: float, p_desc_psi: float, diagnosis: dict):
        key = self._compute_key(alarm_code, int(temp_c // 2), int(p_desc_psi // 15))
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO cache (state_hash, payload, created_at) VALUES (?, ?, ?)",
                (key, json.dumps(diagnosis, ensure_ascii=False), time.time()),
            )
