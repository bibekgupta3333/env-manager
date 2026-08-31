"""Discovers and loads adapters from built-in packages."""

import importlib
import pkgutil

import env_manager.adapters as pkg
from env_manager.adapters.base import BaseAdapter


def _scan_module(mod: object, adapters: list[type[BaseAdapter]]) -> None:
    for attr_name in dir(mod):
        attr = getattr(mod, attr_name)
        if (
            isinstance(attr, type)
            and issubclass(attr, BaseAdapter)
            and attr is not BaseAdapter
        ):
            adapters.append(attr)


def discover_builtin_adapters() -> list[type[BaseAdapter]]:
    adapters: list[type[BaseAdapter]] = []

    for _, name, is_pkg in pkgutil.iter_modules(pkg.__path__):
        if name in ("base", "loader", "registry"):
            continue
        try:
            mod = importlib.import_module(f"env_manager.adapters.{name}")
            _scan_module(mod, adapters)
            if is_pkg:
                for _, sub_name, _ in pkgutil.iter_modules(mod.__path__):
                    try:
                        full_name = f"env_manager.adapters.{name}.{sub_name}"
                        sub_mod = importlib.import_module(full_name)
                        _scan_module(sub_mod, adapters)
                    except ImportError:
                        continue
        except ImportError:
            continue
    return adapters


def discover_pip_adapters() -> list[type[BaseAdapter]]:
    """Discover adapters installed via pip (envs-plugin-* packages)."""
    return []
