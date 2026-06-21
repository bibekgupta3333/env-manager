"""CLI entry point."""

import typer

from env_manager.cli.commands import config, info, lifecycle, list_cmd, plugin, scan

app = typer.Typer(
    name="envs",
    help="Cross-language virtual environment manager",
    no_args_is_help=True,
)

app.add_typer(scan.app, name="scan")
app.add_typer(list_cmd.app, name="list")
app.add_typer(info.app, name="info")
app.add_typer(plugin.app, name="plugins")
app.add_typer(config.app, name="config")
app.add_typer(lifecycle.app, name="lifecycle", help="Create, install, update, delete, restore environments")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
