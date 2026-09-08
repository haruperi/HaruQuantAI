import multiprocessing


def test_spawn_context_is_available() -> None:
    assert multiprocessing.get_context("spawn").get_start_method() == "spawn"
