"""Manages the active set of adapters. Supports enable/disable per language."""

from __future__ import annotations

import sqlite3
from typing import Any

from env_manager.adapters.base import BaseAdapter
from env_manager.adapters.loader import (
    discover_builtin_adapters,
    discover_pip_adapters,
)


class AdapterRegistry:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self._adapters: dict[str, BaseAdapter] = {}
        self._sync_from_db()

    def _sync_from_db(self) -> None:
        rows = self.conn.execute("SELECT * FROM adapter_registry").fetchall()
        if not rows:
            self._seed_builtins()
            rows = self.conn.execute(
                "SELECT * FROM adapter_registry"
            ).fetchall()

        adapter_classes = {}
        for cls in discover_builtin_adapters() + discover_pip_adapters():
            inst = cls()
            adapter_classes[inst.name] = cls

        for row in rows:
            if row["enabled"] and row["name"] in adapter_classes:
                self._adapters[row["name"]] = adapter_classes[row["name"]]()

    def _seed_builtins(self) -> None:
        for cls in discover_builtin_adapters():
            inst = cls()
            self.conn.execute(
                """INSERT OR IGNORE INTO adapter_registry
                   (name, display_name, version, env_type, source)
                   VALUES (?, ?, ?, ?, 'builtin')""",
                (inst.name, inst.display_name, inst.version, inst.env_type),
            )
        self.conn.commit()

    def get(self, name: str) -> BaseAdapter | None:
        return self._adapters.get(name)

    def get_for_language(self, language: str) -> list[BaseAdapter]:
        return [
            a for a in self._adapters.values() if a.name.startswith(language)
        ]

    def get_all_enabled(self) -> list[BaseAdapter]:
        return list(self._adapters.values())

    def enable(self, name: str) -> bool:
        for cls in discover_builtin_adapters() + discover_pip_adapters():
            inst = cls()
            if inst.name == name:
                self.conn.execute(
                    "UPDATE adapter_registry SET enabled = 1 WHERE name = ?",
                    (name,),
                )
                self.conn.commit()
                self._adapters[name] = cls()
                return True
        return False

    def disable(self, name: str) -> bool:
        if name not in self._adapters:
            return False
        self.conn.execute(
            "UPDATE adapter_registry SET enabled = 0 WHERE name = ?", (name,)
        )
        self.conn.commit()
        del self._adapters[name]
        return True

    def list_all(self) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM adapter_registry ORDER BY name"
        ).fetchall()
        return [dict(r) for r in rows]
