"""Marketplace workspace data contracts and serialization models.

Description:
    Defines Pydantic data schemas representing StrategyQuant/HaruQuant
    Marketplace plugin descriptors, installed product entries, shareable
    file tree structures, package manifests, and install/uninstall results.

Purpose:
    FEAT-MARKETPLACE-MODELS: Authoritative schemas for marketplace domain.

Key Capabilities:
    - FR-MARKETPLACE-DESCRIPTOR: Plugin descriptor schema with navigation metadata.
    - FR-MARKETPLACE-PRODUCT: Installed product metadata, files, and summaries.
    - FR-MARKETPLACE-MANIFEST: Marketplace package manifest model (sqx-marketplace/1).
    - FR-MARKETPLACE-TREE: Shareable file tree node schema with nested items.
    - FR-MARKETPLACE-RESULTS: Result envelopes for install, uninstall, and zip builds.

Python API Usage:
    ```python
    from app.workspace.marketplace.app_marketplace_models import (
        InstalledProductModel,
        MarketplacePluginDescriptor,
    )

    descriptor = MarketplacePluginDescriptor()
    entry = InstalledProductModel(slug="indicator-pack", title="Indicators")
    ```

CLI Usage:
    ```bash
    uv run python -m pytest tests/workspace/marketplace/test_app_marketplace.py -q
    ```
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class MarketplacePluginDescriptor(BaseModel):
    """Metadata describing the AppMarketplace plugin for system registration."""

    model_config = ConfigDict(frozen=True)

    name: str = "MARKETPLACE"
    product: str = "SQUANT"
    preferred_position: int = 1000
    context_path: str = "/marketplace"
    app_code: str = "MARKETPLACE"
    tooltip: str = "MARKETPLACE"
    url: str = "../MARKETPLACE/index.html"
    icon_class: str = "fa-shopping-bag"
    section: int = 1
    iframe_id: str = "marketplace-frame"
    link_id: str = "marketplace-link"


class InstalledProductModel(BaseModel):
    """Record of an installed marketplace extension or package."""

    model_config = ConfigDict(frozen=True)

    slug: str
    title: str = ""
    version: str = ""
    file_name: str = ""
    sha256: str = ""
    installed_at: int = 0
    files: list[str] = Field(default_factory=list)


class InstalledProductSummaryModel(BaseModel):
    """Lightweight summary of an installed package for listing."""

    model_config = ConfigDict(frozen=True)

    slug: str
    version: str | None = None


class ShareManifestCategory(BaseModel):
    """Optional primary category for an extension package manifest."""

    model_config = ConfigDict(frozen=True)

    id: str = ""
    label: str = ""


class ShareManifestModel(BaseModel):
    """Metadata manifest embedded inside exported marketplace .zip packages."""

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    schema_version: str = Field(default="sqx-marketplace/1", alias="schema")
    title: str = ""
    description: str = ""
    version: str = ""
    author: str = ""
    category: ShareManifestCategory | None = None
    files: list[str] = Field(default_factory=list)
    generated_by: str = "HaruQuantAI"
    generated_at: str = ""


class ShareTreeNode(BaseModel):
    """Tree node representing a shareable file or directory."""

    model_config = ConfigDict(frozen=True)

    id: int
    text: str
    userdata: list[dict[str, str]] = Field(default_factory=list)
    item: list[ShareTreeNode] = Field(default_factory=list)


class SkippedFileModel(BaseModel):
    """Details for a file skipped during installation."""

    model_config = ConfigDict(frozen=True)

    name: str
    reason: str


class InstallResultModel(BaseModel):
    """Result payload after completing or simulating package installation."""

    model_config = ConfigDict(frozen=True)

    slug: str
    installed_files: list[str] = Field(default_factory=list)
    skipped_files: list[SkippedFileModel] = Field(default_factory=list)
    restart_required: bool = False
    install_dir: str = ""


class UninstallResultModel(BaseModel):
    """Result payload after completing package uninstallation."""

    model_config = ConfigDict(frozen=True)

    slug: str
    removed_files: list[str] = Field(default_factory=list)
    failed_files: list[str] = Field(default_factory=list)
    restart_required: bool = False


class BuildZipResultModel(BaseModel):
    """Result payload after building a shareable marketplace .zip package."""

    model_config = ConfigDict(frozen=True)

    zip_id: str
    file_name: str
    size: int
    build: str
