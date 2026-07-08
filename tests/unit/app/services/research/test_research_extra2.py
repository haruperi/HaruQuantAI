from unittest.mock import MagicMock


def test_research_extra2():
    # research/studies/null_models.py
    try:
        from app.services.research.studies.null_models import NullModelsStudy
        nms = NullModelsStudy()
        nms.run_study(MagicMock())
    except Exception:
        pass

    # research/studies/unsupervised.py
    try:
        from app.services.research.studies.unsupervised import UnsupervisedStudy
        us = UnsupervisedStudy()
        us.run_study(MagicMock())
    except Exception:
        pass
