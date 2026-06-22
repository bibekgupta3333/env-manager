"""Versions command — show available runtime versions from version managers."""

import shutil
from pathlib import Path

import typer

app = typer.Typer(help="Show available language runtime versions")


@app.callback(invoke_without_command=True)
def versions() -> None:
    """Show what language runtimes are installed on your system."""
    typer.echo("Available runtime versions on this system:")
    typer.echo("")

    _show_python()
    _show_node()
    _show_ruby()
    _show_go()
    _show_rust()
    _show_java()


def _show_python() -> None:
    home = Path.home()
    managers = []

    pyenv = home / ".pyenv" / "versions"
    if pyenv.exists():
        vers = [p.name for p in pyenv.iterdir() if p.is_dir() and not p.name.startswith(".")]
        managers.append(("pyenv", vers))

    asdf_py = home / ".asdf" / "installs" / "python"
    if asdf_py.exists():
        vers = [p.name for p in asdf_py.iterdir() if p.is_dir()]
        managers.append(("asdf", vers))

    if managers:
        typer.echo("[bold]Python:[/bold]")
        for mgr, vers in managers:
            typer.echo(f"  {mgr}: {', '.join(sorted(vers))}")
        typer.echo("")

    # System python
    for cmd in ["python3", "python"]:
        found = shutil.which(cmd)
        if found:
            typer.echo(f"  system: {found}")
            break


def _show_node() -> None:
    home = Path.home()
    managers = []

    for mgr_name, subpath in [
        ("nvm", ".nvm/versions/node"),
        ("fnm", ".fnm/node-versions"),
        ("volta", ".volta/tools/image/node"),
    ]:
        p = home / subpath
        if p.exists():
            vers = [d.name.lstrip("v") for d in p.iterdir() if d.is_dir()]
            managers.append((mgr_name, vers))

    asdf_node = home / ".asdf" / "installs" / "nodejs"
    if asdf_node.exists():
        vers = [p.name for p in asdf_node.iterdir() if p.is_dir()]
        managers.append(("asdf", vers))

    if managers:
        typer.echo("[bold]Node.js:[/bold]")
        for mgr, vers in managers:
            typer.echo(f"  {mgr}: {', '.join(sorted(vers))}")
        typer.echo("")

    found = shutil.which("node")
    if found:
        typer.echo(f"  system: {found}")


def _show_ruby() -> None:
    home = Path.home()
    managers = []

    for mgr_name, subpath in [
        ("rbenv", ".rbenv/versions"),
        ("rvm", ".rvm/rubies"),
    ]:
        p = home / subpath
        if p.exists():
            vers = [d.name for d in p.iterdir() if d.is_dir()]
            managers.append((mgr_name, vers))

    asdf_ruby = home / ".asdf" / "installs" / "ruby"
    if asdf_ruby.exists():
        vers = [p.name for p in asdf_ruby.iterdir() if p.is_dir()]
        managers.append(("asdf", vers))

    if managers:
        typer.echo("[bold]Ruby:[/bold]")
        for mgr, vers in managers:
            typer.echo(f"  {mgr}: {', '.join(sorted(vers))}")
        typer.echo("")


def _show_go() -> None:
    home = Path.home()
    managers = []

    goenv = home / ".goenv" / "versions"
    if goenv.exists():
        vers = [p.name for p in goenv.iterdir() if p.is_dir()]
        managers.append(("goenv", vers))

    asdf_go = home / ".asdf" / "installs" / "golang"
    if asdf_go.exists():
        vers = [p.name for p in asdf_go.iterdir() if p.is_dir()]
        managers.append(("asdf", vers))

    if managers:
        typer.echo("[bold]Go:[/bold]")
        for mgr, vers in managers:
            typer.echo(f"  {mgr}: {', '.join(sorted(vers))}")
        typer.echo("")


def _show_rust() -> None:
    home = Path.home()
    rustup = home / ".rustup" / "toolchains"
    if rustup.exists():
        vers = [p.name for p in rustup.iterdir() if p.is_dir()]
        typer.echo("[bold]Rust:[/bold]")
        typer.echo(f"  rustup: {', '.join(sorted(vers))}")
        typer.echo("")


def _show_java() -> None:
    home = Path.home()
    managers = []

    jabba = home / ".jabba" / "jdk"
    if jabba.exists():
        vers = [p.name for p in jabba.iterdir() if p.is_dir()]
        managers.append(("jabba", vers))

    sdkman = home / ".sdkman" / "candidates" / "java"
    if sdkman.exists():
        vers = [p.name for p in sdkman.iterdir() if p.is_dir()]
        managers.append(("sdkman", vers))

    if managers:
        typer.echo("[bold]Java:[/bold]")
        for mgr, vers in managers:
            typer.echo(f"  {mgr}: {', '.join(sorted(vers))}")
        typer.echo("")
