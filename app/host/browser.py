"""Optional default-browser launch for the host entrypoint.

Call launch only after the server is listening. This module delegates to the
standard-library browser integration; it does not create a client session or
confirm that a page loaded. Importing it does not launch a browser.
"""

import webbrowser

from app.host.logging import get_logger

logger = get_logger(__name__)


def launch(url: str) -> bool:
    """Ask the system browser to open the supplied host URL.

    Logs the launch outcome without logging the URL. A False result does not stop
    the backend; unrelated exceptions propagate to the caller.

    Args:
        url: Host address assembled by the caller after successful binding.

    Returns:
        The browser API acceptance flag, or False on webbrowser.Error.
    """
    try:
        opened = webbrowser.open(url)
    except webbrowser.Error:
        logger.warning("Browser launch failed")
        return False
    logger.info("Browser launch outcome: %s", opened)
    return opened
