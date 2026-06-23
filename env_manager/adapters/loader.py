"""Discovers and loads adapters from built-in packages."""

import importlib
import pkgutil

import env_manager.adapters as pkg
from env_manager.adapters.base import BaseAdapter


def discover_builtin_adapters() -> list[type[BaseAdapter]]:
    adapters: list[type[BaseAdapter]] = []

    for _, name, is_pkg in pkgutil.iter_modules(pkg.__path__):
        if not is_pkg or name in ("base", "loader", "registry"):
            continue
        try:
            mod = importlib.import_module(f"env_manager.adapters.{name}")
            for attr_name in dir(mod):
                attr = getattr(mod, attr_name)
                if (
                    isinstance(attr, type)
                    and issubclass(attr, BaseAdapter)
                    and attr is not BaseAdapter
                ):
                    adapters.append(attr)
        except ImportError:
            continue
    return adapters


def discover_pip_adapters() -> list[type[BaseAdapter]]:
    """Discover adapters installed via pip (envs-plugin-* packages)."""
    return []
