import sys
from io import StringIO
from unittest.mock import patch

from app.main import main


def test_main() -> None:
    with patch("sys.stdout", new=StringIO()) as mock_stdout:
        main()
        assert "Hello from haruquantai!" in mock_stdout.getvalue()
