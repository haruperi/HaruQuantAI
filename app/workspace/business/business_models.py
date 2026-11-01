"""Business workspace data contracts and serialization models.

Description:
    Defines Pydantic data schemas representing StrategyQuant/HaruQuant
    SQX Business plugin descriptors, compiler path configurations,
    MQL Market project configurations, EA parameters, and build job states.

Purpose:
    FEAT-APP-BUSINESS: Authoritative schemas for SQX Business domain.

Key Capabilities:
    - FR-BUSINESS-DESCRIPTOR: Plugin descriptor schema with navigation metadata.
    - FR-BUSINESS-SETTINGS-MODEL: MetaTrader compiler path settings model.
    - FR-BUSINESS-PROJECT-MODEL: Commercial strategy project data model.
    - FR-BUSINESS-EA-PARAM-MODEL: Expert Advisor parameter model.
    - FR-BUSINESS-BUILD-JOB-MODEL: Build pipeline status and progress tracking model.

Python API Usage:
    ```python
    from app.workspace.business.business_models import (
        MQLMarketProjectModel,
        SQXBusinessPluginDescriptor,
    )

    descriptor = SQXBusinessPluginDescriptor()
    project = MQLMarketProjectModel(name="AlphaScalper")
    ```

CLI Usage:
    ```bash
    uv run python -m pytest tests/workspace/business/test_business.py -q
    ```
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class SQXBusinessPluginDescriptor(BaseModel):
    """Metadata describing the AppSQXBusiness plugin for system registration."""

    model_config = ConfigDict(frozen=True)

    name: str = "SQX Business"
    product: str = "SQUANT"
    preferred_position: int = 10
    context_path: str = "/sqxbusiness"
    app_code: str = "SQXBUSINESS"
    tooltip: str = "SQX Business"
    url: str = "../SQXBUSINESS/dist/index.html"
    icon_class: str = "fa-briefcase"
    section: int = 1
    iframe_id: str = "sqxbusiness-frame"
    link_id: str = "sqxbusiness-frame-link"
    hidden: bool = True


class SQXBusinessMainSettingsModel(BaseModel):
    """Configuration paths for external MetaTrader 5 compiler."""

    model_config = ConfigDict(frozen=True)

    mt5_path: str = ""


class MQLMarketProjectModel(BaseModel):
    """Commercial strategy packaging project record."""

    model_config = ConfigDict(frozen=True)

    name: str
    config_xml: str = ""
    sample: bool = False


class EAParameterModel(BaseModel):
    """Parameter extracted from or configured for an Expert Advisor."""

    model_config = ConfigDict(frozen=True)

    name: str
    value: str = ""
    param_type: str = "string"
    comment: str = ""


class EAOptionsModel(BaseModel):
    """Configurable options and variables for an Expert Advisor build."""

    model_config = ConfigDict(frozen=True)

    name: str
    description: str = ""
    default_value: str = ""
    options: list[str] = Field(default_factory=list)


class MQLMarketBuildJobModel(BaseModel):
    """State record for a commercial EA build and packaging job."""

    model_config = ConfigDict(frozen=True)

    project_name: str
    status: str = "idle"
    progress: int = 0
    log: list[str] = Field(default_factory=list)
