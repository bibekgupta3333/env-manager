"""Tests for Node, Ruby, Go, Rust adapters."""

from env_manager.adapters.go.goenv import GoGoenvAdapter
from env_manager.adapters.node.nvm import NodeNvmAdapter
from env_manager.adapters.node.volta import NodeVoltaAdapter
from env_manager.adapters.ruby.rbenv import RubyRbenvAdapter
from env_manager.adapters.ruby.rvm import RubyRvmAdapter
from env_manager.adapters.rust.rustup import RustRustupAdapter


class TestNvmAdapter:
    def test_find_patterns(self):
        adapter = NodeNvmAdapter()
        patterns = adapter.find_patterns()
        assert "**/.nvmrc" in patterns
        assert "**/package.json" in patterns

    def test_detect_nvmrc(self, tmp_path):
        proj = tmp_path / "node-proj"
        proj.mkdir()
        (proj / ".nvmrc").write_text("v20.10.0")
        adapter = NodeNvmAdapter()
        result = adapter.detect(proj)
        assert result is not None
        assert result.language == "node"
        assert result.tool == "nvm"

    def test_detect_package_json(self, tmp_path):
        proj = tmp_path / "pkg-proj"
        proj.mkdir()
        (proj / "package.json").write_text(
            '{"name":"test","engines":{"node":">=18"}}'
        )
        adapter = NodeNvmAdapter()
        result = adapter.detect(proj)
        assert result is not None
        assert result.language == "node"

    def test_detect_no_match(self, tmp_path):
        adapter = NodeNvmAdapter()
        result = adapter.detect(tmp_path)
        assert result is None

    def test_freeze_format(self, tmp_path):
        adapter = NodeNvmAdapter()
        result = adapter.freeze(tmp_path)
        assert result.format == "package.json"


class TestVoltaAdapter:
    def test_find_patterns(self):
        adapter = NodeVoltaAdapter()
        patterns = adapter.find_patterns()
        assert len(patterns) > 0

    def test_detect_volta_config(self, tmp_path):
        proj = tmp_path / "volta-proj"
        proj.mkdir()
        (proj / "package.json").write_text(
            '{"volta":{"node":"20.10.0","npm":"10.0.0"}}'
        )
        adapter = NodeVoltaAdapter()
        result = adapter.detect(proj)
        assert result is not None
        assert result.language == "node"
        assert result.tool == "volta"
        assert result.version == "20.10.0"

    def test_detect_no_volta(self, tmp_path):
        proj = tmp_path / "no-volta"
        proj.mkdir()
        (proj / "package.json").write_text('{"name":"test"}')
        adapter = NodeVoltaAdapter()
        result = adapter.detect(proj)
        assert result is None


class TestRbenvAdapter:
    def test_find_patterns(self):
        adapter = RubyRbenvAdapter()
        patterns = adapter.find_patterns()
        assert "**/.ruby-version" in patterns

    def test_detect_ruby_version(self, tmp_path):
        proj = tmp_path / "ruby-proj"
        proj.mkdir()
        (proj / ".ruby-version").write_text("3.3.0")
        adapter = RubyRbenvAdapter()
        result = adapter.detect(proj)
        assert result is not None
        assert result.language == "ruby"
        assert result.tool == "rbenv"

    def test_detect_no_match(self, tmp_path):
        adapter = RubyRbenvAdapter()
        result = adapter.detect(tmp_path)
        assert result is None

    def test_freeze(self, tmp_path):
        adapter = RubyRbenvAdapter()
        result = adapter.freeze(tmp_path)
        assert result.format == "Gemfile"


class TestRvmAdapter:
    def test_find_patterns(self):
        adapter = RubyRvmAdapter()
        patterns = adapter.find_patterns()
        assert len(patterns) > 0

    def test_detect_ruby_version(self, tmp_path):
        proj = tmp_path / "rvm-proj"
        proj.mkdir()
        (proj / ".ruby-version").write_text("3.2.0")
        adapter = RubyRvmAdapter()
        result = adapter.detect(proj)
        assert result is not None
        assert result.language == "ruby"
        assert result.tool == "rvm"

    def test_detect_no_match(self, tmp_path):
        adapter = RubyRvmAdapter()
        result = adapter.detect(tmp_path)
        assert result is None


class TestGoenvAdapter:
    def test_find_patterns(self):
        adapter = GoGoenvAdapter()
        patterns = adapter.find_patterns()
        assert "**/.go-version" in patterns

    def test_detect_go_version(self, tmp_path):
        proj = tmp_path / "go-proj"
        proj.mkdir()
        (proj / ".go-version").write_text("1.22.0")
        adapter = GoGoenvAdapter()
        result = adapter.detect(proj)
        assert result is not None
        assert result.language == "go"
        assert result.tool == "goenv"

    def test_detect_no_match(self, tmp_path):
        adapter = GoGoenvAdapter()
        result = adapter.detect(tmp_path)
        assert result is None

    def test_freeze(self, tmp_path):
        adapter = GoGoenvAdapter()
        result = adapter.freeze(tmp_path)
        assert result.format == "go.mod"


class TestRustupAdapter:
    def test_find_patterns(self):
        adapter = RustRustupAdapter()
        patterns = adapter.find_patterns()
        assert "**/rust-toolchain.toml" in patterns

    def test_detect_toolchain(self, tmp_path):
        proj = tmp_path / "rust-proj"
        proj.mkdir()
        (proj / "rust-toolchain.toml").write_text(
            '[toolchain]\nchannel = "stable"\n'
        )
        adapter = RustRustupAdapter()
        result = adapter.detect(proj)
        assert result is not None
        assert result.language == "rust"
        assert result.tool == "rustup"

    def test_detect_legacy_toolchain(self, tmp_path):
        proj = tmp_path / "rust-legacy"
        proj.mkdir()
        (proj / "rust-toolchain").write_text("nightly")
        adapter = RustRustupAdapter()
        result = adapter.detect(proj)
        assert result is not None
        assert result.language == "rust"
        assert result.tool == "rustup"

    def test_detect_no_match(self, tmp_path):
        adapter = RustRustupAdapter()
        result = adapter.detect(tmp_path)
        assert result is None

    def test_freeze(self, tmp_path):
        adapter = RustRustupAdapter()
        result = adapter.freeze(tmp_path)
        assert result.format == "Cargo.toml"
