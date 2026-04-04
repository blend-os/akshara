import sys


def info(msg: str) -> None:
    """Print an informative message to stdout.

    Args:
        msg: String containing the message.
    """
    print(f"I: {msg}")


def warn(msg: str) -> None:
    """Print a warning message to stderr.

    Args:
        msg: String containing the message."""
    print(f"W: {msg}", file=sys.stderr)


def error(msg: str) -> None:
    """Print an error message to stderr.

    Args:
        msg: String containing the message.
    """
    print(f"E: {msg}", file=sys.stderr)
