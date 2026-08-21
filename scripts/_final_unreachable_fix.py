"""Apply the final one-time strict mypy narrowing fix."""

from pathlib import Path

PATH = (
    Path(__file__).resolve().parent.parent
    / "tests/composition/test_hot_reconfiguration.py"
)


def main() -> None:
    """Replace direct dictionary-item assertions with an observation callable."""
    content = PATH.read_text(encoding="utf-8")
    old = (
        "    # CRITICAL: Replacement task must STILL be running, not killed by shadow scope close!\n"
        '    assert lifecycle["task_running"] is True, (\n'
    )
    new = (
        "    # CRITICAL: Replacement task must STILL be running, not killed by shadow scope close!\n"
        "    read_flag = lifecycle.__getitem__\n"
        '    assert read_flag("task_running") is True, (\n'
    )
    if old not in content:
        raise RuntimeError("Expected first lifecycle assertion was not found")
    content = content.replace(old, new, 1)
    replacements = {
        'assert not lifecycle["task_cancelled"], (': 'assert not read_flag("task_cancelled"), (',
        'assert lifecycle["task_cancelled"] is True, (': 'assert read_flag("task_cancelled") is True, (',
        'assert lifecycle["callback_cleaned"] is True, (': 'assert read_flag("callback_cleaned") is True, (',
    }
    for previous, replacement in replacements.items():
        if previous not in content:
            raise RuntimeError(f"Expected assertion was not found: {previous}")
        content = content.replace(previous, replacement, 1)
    PATH.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    main()
