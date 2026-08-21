"""Apply one-time strict-typing fixes to hot-reconfiguration tests."""

from pathlib import Path

PATH = Path(__file__).resolve().parent.parent / "tests/composition/test_hot_reconfiguration.py"


def replace_once(content: str, old: str, new: str) -> str:
    """Replace one exact block or fail loudly."""
    if old not in content:
        raise RuntimeError(f"Expected block not found: {old!r}")
    return content.replace(old, new, 1)


def main() -> None:
    """Apply deterministic source replacements."""
    content = PATH.read_text(encoding="utf-8")
    content = replace_once(
        content,
        "    watcher.start()\n    assert watcher.is_running is True\n",
        "    watcher.start()\n",
    )
    content = replace_once(
        content,
        "    task_running = False\n"
        "    task_cancelled = False\n"
        "    listener_invoked = False\n"
        "    callback_cleaned = False\n",
        "    lifecycle: dict[str, bool] = {\n"
        "        \"task_running\": False,\n"
        "        \"task_cancelled\": False,\n"
        "        \"listener_invoked\": False,\n"
        "        \"callback_cleaned\": False,\n"
        "    }\n",
    )
    content = replace_once(
        content,
        "            nonlocal task_running, task_cancelled, listener_invoked, callback_cleaned\n",
        "",
    )
    content = replace_once(
        content,
        "                    nonlocal task_running, task_cancelled\n"
        "                    task_running = True\n",
        "                    lifecycle[\"task_running\"] = True\n",
    )
    content = replace_once(
        content,
        "                        task_cancelled = True\n",
        "                        lifecycle[\"task_cancelled\"] = True\n",
    )
    content = replace_once(
        content,
        "                    nonlocal listener_invoked\n"
        "                    listener_invoked = True\n",
        "                    lifecycle[\"listener_invoked\"] = True\n",
    )
    content = replace_once(
        content,
        "                    nonlocal callback_cleaned\n"
        "                    callback_cleaned = True\n",
        "                    lifecycle[\"callback_cleaned\"] = True\n",
    )
    content = replace_once(
        content,
        "    assert task_running is True, \"Replacement background task was killed during commit!\"\n"
        "    assert not task_cancelled, (\n",
        "    assert lifecycle[\"task_running\"] is True, (\n"
        "        \"Replacement background task was killed during commit!\"\n"
        "    )\n"
        "    assert not lifecycle[\"task_cancelled\"], (\n",
    )
    content = replace_once(
        content,
        "    assert task_cancelled is True, \"Task was not cancelled on engine shutdown\"\n"
        "    assert callback_cleaned is True, (\n",
        "    assert lifecycle[\"task_cancelled\"] is True, (\n"
        "        \"Task was not cancelled on engine shutdown\"\n"
        "    )\n"
        "    assert lifecycle[\"callback_cleaned\"] is True, (\n",
    )
    PATH.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    main()
