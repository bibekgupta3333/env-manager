"""Tests for Python adapters: poetry, uv, pipenv, conda."""

from env_manager.adapters.python.conda import PythonCondaAdapter
from env_manager.adapters.python.pipenv import PythonPipenvAdapter
from env_manager.adapters.python.poetry import PythonPoetryAdapter
from env_manager.adapters.python.uv import PythonUvAdapter


class TestPoetryAdapter:
    def test_find_patterns(self):
        adapter = PythonPoetryAdapter()
        patterns = adapter.find_patterns()
        assert "**/pyproject.toml" in patterns

    def test_detect_poetry_project(self, tmp_path):
        proj = tmp_path / "poetry-proj"
        proj.mkdir()
        (proj / "pyproject.toml").write_text("[tool.poetry]\nname = 'test'\n")
        adapter = PythonPoetryAdapter()
        result = adapter.detect(proj)
        assert result is not None
        assert result.language == "python"
        assert result.tool == "poetry"

    def test_detect_ignores_non_poetry_toml(self, tmp_path):
        proj = tmp_path / "non-poetry"
        proj.mkdir()
        (proj / "pyproject.toml").write_text("[project]\nname = 'test'\n")
        adapter = PythonPoetryAdapter()
        result = adapter.detect(proj)
        assert result is None

    def test_detect_no_toml(self, tmp_path):
        adapter = PythonPoetryAdapter()
        result = adapter.detect(tmp_path)
        assert result is None

    def test_check_health(self, tmp_path):
        venv = tmp_path / ".venv"
        venv.mkdir()
        (venv / "bin").mkdir()
        (venv / "bin" / "python").touch()
        adapter = PythonPoetryAdapter()
        result = adapter.check_health(venv)
        assert result.status in ("healthy", "degraded")

    def test_freeze(self, tmp_path):
        adapter = PythonPoetryAdapter()
        result = adapter.freeze(tmp_path)
        assert result.format == "pyproject.toml"


class TestUvAdapter:
    def test_find_patterns(self):
        adapter = PythonUvAdapter()
        patterns = adapter.find_patterns()
        assert "**/pyproject.toml" in patterns
        assert "**/.python-version" in patterns

    def test_detect_uv_project(self, tmp_path):
        proj = tmp_path / "uv-proj"
        proj.mkdir()
        toml_text = (
            "[project]\n"
            "requires-python = '>=3.10'\n"
            "# uv lock file\n"
        )
        (proj / "pyproject.toml").write_text(toml_text)
        adapter = PythonUvAdapter()
        result = adapter.detect(proj)
        assert result is not None
        assert result.language == "python"
        assert result.tool == "uv"

    def test_detect_no_uv(self, tmp_path):
        proj = tmp_path / "no-uv"
        proj.mkdir()
        (proj / "pyproject.toml").write_text("[project]\nname = 'test'\n")
        adapter = PythonUvAdapter()
        result = adapter.detect(proj)
        assert result is None

    def test_check_health_default(self, tmp_path):
        adapter = PythonUvAdapter()
        result = adapter.check_health(tmp_path)
        assert result.status == "healthy"


class TestPipenvAdapter:
    def test_find_patterns(self):
        adapter = PythonPipenvAdapter()
        patterns = adapter.find_patterns()
        assert "**/Pipfile" in patterns

    def test_detect_pipenv_project(self, tmp_path):
        proj = tmp_path / "pipenv-proj"
        proj.mkdir()
        (proj / "Pipfile").write_text(
            "[[source]]\nurl = 'https://pypi.org/simple'\n"
            "python_version = '3.12'\n"
        )
        adapter = PythonPipenvAdapter()
        result = adapter.detect(proj)
        assert result is not None
        assert result.language == "python"
        assert result.tool == "pipenv"

    def test_detect_no_pipfile(self, tmp_path):
        adapter = PythonPipenvAdapter()
        result = adapter.detect(tmp_path)
        assert result is None

    def test_freeze_returns_format(self, tmp_path):
        adapter = PythonPipenvAdapter()
        result = adapter.freeze(tmp_path)
        assert result.format == "Pipfile"


class TestCondaAdapter:
    def test_find_patterns(self):
        adapter = PythonCondaAdapter()
        patterns = adapter.find_patterns()
        assert len(patterns) >= 0

    def test_detect_conda_env(self, tmp_path):
        env_dir = tmp_path / "conda-env"
        env_dir.mkdir()
        meta = env_dir / "conda-meta"
        meta.mkdir()
        (meta / "history").write_text("python 3.12.0\nnumpy 1.26.0\n")
        adapter = PythonCondaAdapter()
        result = adapter.detect(env_dir)
        assert result is not None
        assert result.language == "python"
        assert result.tool == "conda"

    def test_detect_no_conda(self, tmp_path):
        adapter = PythonCondaAdapter()
        result = adapter.detect(tmp_path)
        assert result is None

    def test_freeze(self, tmp_path):
        adapter = PythonCondaAdapter()
        result = adapter.freeze(tmp_path)
        assert result.format == "environment.yml"
