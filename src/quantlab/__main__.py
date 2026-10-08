"""Technical command-line entry point for QuantLab."""

from __future__ import annotations

from quantlab.interfaces.cli.composition import bootstrap


def main() -> int:
    """Initialize the technical infrastructure and return a process status."""
    container = bootstrap()
    container.logger.info(
        "QuantLab infrastructure initialized",
        extra={
            "environment": container.settings.environment.value,
            "plugin_directory": str(container.settings.plugins.directory),
        },
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
