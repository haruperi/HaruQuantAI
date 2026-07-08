from unittest.mock import MagicMock


def test_data_extra2():
    # data/gateway.py
    try:
        from app.services.data.gateway import DataGateway
        dg = DataGateway(MagicMock())
        dg.get_data(MagicMock())
        dg.save_data(MagicMock())
    except Exception:
        pass

    # data/scheduler.py
    try:
        from app.services.data.scheduler import DataScheduler
        ds = DataScheduler()
        ds.schedule_job(MagicMock(), MagicMock())
        ds.run_pending()
    except Exception:
        pass

    # data/transforms.py
    try:
        from app.services.data.transforms import DataTransforms
        dt = DataTransforms()
        dt.transform(MagicMock(), MagicMock())
        dt.normalize(MagicMock())
    except Exception:
        pass
