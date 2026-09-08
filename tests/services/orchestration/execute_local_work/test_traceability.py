from app.services.orchestration.execute_local_work.worker_entrypoint import run_worker


def test_worker_entrypoint_import_has_no_runtime_effect() -> None:
    assert callable(run_worker)
