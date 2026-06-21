"""Tests for the discovery scanner."""

from env_manager.adapters.base import BaseAdapter
from env_manager.discovery.scanner import Scanner
from env_manager.models.env import EnvMetadata, FreezeResult, HealthResult


class FakePythonAdapter(BaseAdapter):
    name = "python.fake"
    display_name = "Fake Python"
    version = "0.1"
    env_type = "local"

    def find_patterns(self):
        return ["**/.fake-python"]

    def detect(self, path):
        if (path / ".fake-python").exists():
            return EnvMetadata(
                language="python",
                tool="fake",
                version="3.0",
                path=str(path),
                size_bytes=100,
                interpreter_path="/bin/fake",
            )
        return None

    def inspect(self, path):
        return EnvMetadata(
            language="python",
            tool="fake",
            version="3.0",
            path=str(path),
            size_bytes=100,
            interpreter_path="/bin/fake",
            packages_count=0,
        )

    def get_packages(self, path):
        return []

    def freeze(self, path):
        return FreezeResult(
            raw_content="", format="requirements.txt", packages=[]
        )

    def check_health(self, path):
        return HealthResult(status="healthy")


class FakeNodeAdapter(BaseAdapter):
    name = "node.fake"
    display_name = "Fake Node"
    version = "0.1"
    env_type = "global"

    def find_patterns(self):
        return ["**/.fake-node"]

    def detect(self, path):
        if (path / ".fake-node").exists():
            return EnvMetadata(
                language="node",
                tool="fake",
                version="20.0",
                path=str(path),
                size_bytes=200,
                interpreter_path="/bin/fake-node",
                env_type="global",
            )
        return None

    def inspect(self, path):
        return EnvMetadata(
            language="node",
            tool="fake",
            version="20.0",
            path=str(path),
            size_bytes=200,
            interpreter_path="/bin/fake-node",
            packages_count=0,
            env_type="global",
        )

    def get_packages(self, path):
        return []

    def freeze(self, path):
        return FreezeResult(
            raw_content="", format="package-lock.json", packages=[]
        )

    def check_health(self, path):
        return HealthResult(status="healthy")


def test_scanner_finds_matching_paths(tmp_path, db_connection):
    py_proj = tmp_path / "pyproj"
    py_proj.mkdir()
    (py_proj / ".fake-python").touch()

    node_proj = tmp_path / "nodeproj"
    node_proj.mkdir()
    (node_proj / ".fake-node").touch()

    scanner = Scanner(
        db_connection, adapters=[FakePythonAdapter(), FakeNodeAdapter()]
    )
    results = scanner.scan(str(tmp_path), depth=3)

    assert len(results) == 2
    languages = {r.language for r in results}
    assert languages == {"python", "node"}


def test_scanner_respects_disabled_adapters(tmp_path, db_connection):
    py_proj = tmp_path / "pyproj"
    py_proj.mkdir()
    (py_proj / ".fake-python").touch()

    node_proj = tmp_path / "nodeproj"
    node_proj.mkdir()
    (node_proj / ".fake-node").touch()

    scanner = Scanner(db_connection, adapters=[FakePythonAdapter()])
    results = scanner.scan(str(tmp_path), depth=3)

    assert len(results) == 1
    assert results[0].language == "python"


def test_scanner_excludes_node_modules(tmp_path, db_connection):
    nm = tmp_path / "node_modules" / "somepkg"
    nm.mkdir(parents=True)
    (nm / ".fake-python").touch()

    top = tmp_path / "myapp"
    top.mkdir()
    (top / ".fake-python").touch()

    scanner = Scanner(db_connection, adapters=[FakePythonAdapter()])
    results = scanner.scan(str(tmp_path), depth=3)

    assert len(results) == 1
    assert str(top) in results[0].path


def test_scanner_handles_empty_directory(tmp_path, db_connection):
    scanner = Scanner(db_connection, adapters=[FakePythonAdapter()])
    results = scanner.scan(str(tmp_path), depth=3)
    assert len(results) == 0


def test_scanner_respects_depth(tmp_path, db_connection):
    deep = tmp_path
    for i in range(6):
        deep = deep / f"level{i}"
        deep.mkdir()
    (deep / ".fake-python").touch()

    scanner = Scanner(db_connection, adapters=[FakePythonAdapter()])
    results = scanner.scan(str(tmp_path), depth=3)
    assert len(results) == 0  # too deep

    results_deep = scanner.scan(str(tmp_path), depth=10)
    assert len(results_deep) == 1
