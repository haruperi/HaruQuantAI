"""Marketplace workspace business logic, package management, and file mapping.

Description:
    Provides the core service implementation for AppMarketplace, including
    plugin descriptor provision, installed package tracking, shareable file
    tree generation with exclusions, package packaging with manifest metadata,
    safe archive unpacking with path-traversal prevention, and uninstallation.

Purpose:
    FEAT-APP-MARKETPLACE: Marketplace service and packaging infrastructure.

Key Capabilities:
    - FR-MARKETPLACE-STORE: File-backed isolated persistence of installed products.
    - FR-MARKETPLACE-FILEMAP: Generation of shareable file trees with exclusions.
    - FR-MARKETPLACE-INSTALL: Secure archive extraction, SHA-256 verification,
      and plugin restart detection.
    - FR-MARKETPLACE-UNINSTALL: Extension uninstallation and parent directory pruning.
    - FR-MARKETPLACE-BUILD-ZIP: Exporting zip packages with sqx-marketplace/1 manifest.

Python API Usage:
    ```python
    from app.workspace.marketplace.app_marketplace import (
        MarketplaceService,
        MarketplaceStore,
    )

    store = MarketplaceStore()
    service = MarketplaceService(store=store)
    descriptor = service.get_descriptor()
    installed = service.list_installed()
    ```

CLI Usage:
    ```bash
    uv run python -m pytest tests/workspace/marketplace/test_app_marketplace.py -q
    ```
"""

from __future__ import annotations

import hashlib
import io
import json
import re
import threading
import time
import uuid
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.core.host.logging import get_logger
from app.workspace.marketplace.app_marketplace_models import (
    BuildZipResultModel,
    InstalledProductModel,
    InstalledProductSummaryModel,
    InstallResultModel,
    MarketplacePluginDescriptor,
    ShareManifestCategory,
    ShareManifestModel,
    SkippedFileModel,
    UninstallResultModel,
)

logger = get_logger(__name__)

EXCLUDED_TOP_DIRS: frozenset[str] = frozenset(
    {"settings", "log", "logs", "data", "customdata", "temp", "tmp", "cache"}
)
RESTART_REQUIRED_PREFIX = "extend/Plugins/"
CUSTOM_INDICATORS_PREFIX = "custom_indicators/"
MANIFEST_ENTRY = "manifest.json"
UUID_REGEX = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)


class MarketplaceStore:
    """Thread-safe isolated JSON store for tracking installed marketplace products."""

    def __init__(self, file_path: Path | None = None) -> None:
        """Initialize the store with a backing file path.

        Args:
            file_path: Optional JSON path. If omitted, uses default repository path.
        """
        if file_path is None:
            repo_root = Path(__file__).resolve().parents[3]
            self._file_path = repo_root / "data" / "marketplace" / "installed.json"
        else:
            self._file_path = file_path
        self._lock = threading.Lock()
        self._records: dict[str, InstalledProductModel] = {}
        self._load()

    def _load(self) -> None:
        """Load stored records from JSON file if it exists."""
        with self._lock:
            if not self._file_path.exists():
                self._records = {}
                return
            try:
                raw_text = self._file_path.read_text(encoding="utf-8")
                raw_data = json.loads(raw_text)
                self._records = {
                    slug: InstalledProductModel.model_validate(item)
                    for slug, item in raw_data.items()
                }
                logger.info(
                    "FR-MARKETPLACE-STORE: Loaded %d installed products from %s",
                    len(self._records),
                    self._file_path.as_posix(),
                )
            except json.JSONDecodeError, OSError:
                logger.exception(
                    "FR-MARKETPLACE-STORE: Failed reading installed store %s",
                    self._file_path.as_posix(),
                )
                self._records = {}

    def _save(self) -> None:
        """Persist stored records to JSON file atomically."""
        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        dump = {slug: rec.model_dump() for slug, rec in self._records.items()}
        temp_path = self._file_path.with_suffix(".tmp")
        temp_path.write_text(json.dumps(dump, indent=2), encoding="utf-8")
        temp_path.replace(self._file_path)

    def record_install(
        self,
        slug: str,
        title: str,
        version: str,
        file_name: str,
        *,
        sha256: str = "",
        installed_files: list[str] | None = None,
    ) -> None:
        """Record an installed product into persistence.

        Args:
            slug: Product identifier slug.
            title: Product display title.
            version: Product version.
            file_name: Originating file name.
            sha256: Package SHA-256 digest.
            installed_files: List of extracted relative file paths.
        """
        with self._lock:
            entry = InstalledProductModel(
                slug=slug,
                title=title,
                version=version,
                file_name=file_name,
                sha256=sha256,
                installed_at=int(time.time() * 1000),
                files=installed_files or [],
            )
            self._records[slug] = entry
            self._save()
            logger.info(
                "FR-MARKETPLACE-STORE: Recorded install for slug='%s', version='%s'",
                slug,
                version,
            )

    def get_installed_files(self, slug: str) -> list[str]:
        """Return the list of files installed for a given slug.

        Args:
            slug: Product identifier slug.

        Returns:
            List of file paths or empty list if record does not exist.
        """
        with self._lock:
            record = self._records.get(slug)
            return list(record.files) if record else []

    def get_installed_record(self, slug: str) -> InstalledProductModel | None:
        """Return the full record for an installed product.

        Args:
            slug: Product identifier slug.

        Returns:
            InstalledProductModel or None.
        """
        with self._lock:
            return self._records.get(slug)

    def delete_install(self, slug: str) -> None:
        """Delete an installed product record.

        Args:
            slug: Product identifier slug to remove.
        """
        with self._lock:
            if slug in self._records:
                del self._records[slug]
                self._save()
                logger.info(
                    "FR-MARKETPLACE-STORE: Deleted install for slug='%s'",
                    slug,
                )

    def list_installed(self) -> list[InstalledProductSummaryModel]:
        """Return sorted summary list of installed products.

        Returns:
            List of summary models sorted alphabetically by slug.
        """
        with self._lock:
            return [
                InstalledProductSummaryModel(
                    slug=slug,
                    version=rec.version or None,
                )
                for slug, rec in sorted(self._records.items(), key=lambda x: x[0])
            ]


class MarketplaceFileMap:
    """Shareable file tree scanner honoring system exclusion boundaries."""

    @staticmethod
    def excluded_top_dirs() -> list[str]:
        """Return sorted list of excluded top-level directory names.

        Returns:
            Alphabetically sorted list of excluded directory names.
        """
        return sorted(EXCLUDED_TOP_DIRS)

    @staticmethod
    def is_excluded_from_share(target: Path, user_root: Path) -> bool:
        """Check whether a target path is excluded from sharing.

        Args:
            target: Candidate file or directory path.
            user_root: User directory root boundary.

        Returns:
            True if path falls outside user_root or in an excluded directory.
        """
        try:
            target_canonical = target.resolve()
            root_canonical = user_root.resolve()
        except OSError:
            return True

        if target_canonical == root_canonical:
            return False

        try:
            rel = target_canonical.relative_to(root_canonical)
        except ValueError:
            return True

        top_part = rel.parts[0].lower() if rel.parts else ""
        return top_part in EXCLUDED_TOP_DIRS

    @classmethod
    def generate_tree(
        cls,
        source_dirs: dict[str, str],
        filter_str: str = "",
        start_index: int = 0,
    ) -> list[dict[str, Any]]:
        """Generate a nested UI tree for shareable files.

        Args:
            source_dirs: Mapping of directory paths to top-level labels.
            filter_str: Optional search filter string.
            start_index: Initial node integer ID.

        Returns:
            List of top-level tree item dictionaries.
        """
        norm_filter = filter_str.strip().lower()
        items: list[dict[str, Any]] = []
        cur_id = start_index

        for dir_path_str, desc in source_dirs.items():
            dir_path = Path(dir_path_str)
            if not dir_path.exists():
                continue

            top_obj: dict[str, Any] = {
                "id": cur_id,
                "text": desc,
                "userdata": [
                    {"name": "file", "content": str(dir_path.resolve())},
                    {"name": "fileType", "content": "dir"},
                ],
                "item": [],
            }
            cur_id += 1

            sub_items, cur_id = cls._parse_folder(
                dir_path, dir_path, norm_filter, cur_id
            )
            top_obj["item"] = sub_items
            items.append(top_obj)

        return items

    @classmethod
    def _parse_folder(
        cls,
        folder: Path,
        user_root: Path,
        filter_str: str,
        start_id: int,
    ) -> tuple[list[dict[str, Any]], int]:
        """Scan a folder recursively for shareable entries matching the filter."""
        items: list[dict[str, Any]] = []
        cur_id = start_id

        try:
            children = sorted(folder.iterdir(), key=lambda p: p.name.lower())
        except OSError:
            return items, cur_id

        for child in children:
            if cls.is_excluded_from_share(child, user_root):
                continue

            if child.is_dir():
                sub_items, cur_id = cls._parse_folder(
                    child, user_root, filter_str, cur_id
                )
                if filter_str and not sub_items:
                    continue

                node: dict[str, Any] = {
                    "id": cur_id,
                    "text": child.name,
                    "userdata": [
                        {"name": "file", "content": str(child.resolve())},
                        {"name": "fileType", "content": "dir"},
                    ],
                    "item": sub_items,
                }
                cur_id += 1
                items.append(node)
            else:
                stem_lower = child.stem.lower()
                if filter_str and filter_str not in stem_lower:
                    continue

                node = {
                    "id": cur_id,
                    "text": child.name,
                    "userdata": [
                        {"name": "file", "content": str(child.resolve())},
                        {"name": "fileType", "content": "file"},
                    ],
                }
                cur_id += 1
                items.append(node)

        return items, cur_id


def _collect_shareable_files(
    candidates: list[str | Path],
    user_root: Path,
) -> list[Path]:
    """Validate and collect physical files for a marketplace package."""
    valid_paths: list[Path] = []
    for item in candidates:
        p = Path(item).resolve()
        if not p.is_relative_to(user_root):
            raise ValueError(f"File '{item}' is not inside the user folder.")
        if MarketplaceFileMap.is_excluded_from_share(p, user_root):
            raise ValueError(f"File '{item}' is in a folder that cannot be shared.")
        if not p.exists():
            raise ValueError(f"File '{item}' does not exist.")

        if p.is_dir():
            valid_paths.extend(
                child.resolve()
                for child in p.rglob("*")
                if child.is_file()
                and not MarketplaceFileMap.is_excluded_from_share(child, user_root)
            )
        else:
            valid_paths.append(p)
    return valid_paths


def _build_manifest_model(
    meta: dict[str, Any] | str | None,
    rel_entry_names: list[str],
) -> ShareManifestModel:
    """Create a ShareManifestModel from user metadata and package entries."""
    meta_dict: dict[str, Any] = {}
    if isinstance(meta, str) and meta.strip():
        meta_dict = json.loads(meta)
    elif isinstance(meta, dict):
        meta_dict = meta

    manifest_cat = None
    cat_id = meta_dict.get("categoryId", "")
    cat_label = meta_dict.get("categoryLabel", "")
    if cat_id or cat_label:
        manifest_cat = ShareManifestCategory(id=cat_id, label=cat_label)

    return ShareManifestModel(
        title=meta_dict.get("title", ""),
        description=meta_dict.get("description", ""),
        version=meta_dict.get("version", ""),
        author=meta_dict.get("author", ""),
        category=manifest_cat,
        files=rel_entry_names,
        generated_at=datetime.now(UTC).isoformat(),
    )


class MarketplaceService:
    """Core domain service for StrategyQuant/HaruQuant Marketplace integration."""

    def __init__(
        self,
        store: MarketplaceStore | None = None,
        data_dir: Path | None = None,
    ) -> None:
        """Initialize the marketplace service.

        Args:
            store: Optional persistence store. If omitted, uses default.
            data_dir: Optional root data directory for user files and temp storage.
        """
        self.store = store if store is not None else MarketplaceStore()
        if data_dir is None:
            repo_root = Path(__file__).resolve().parents[3]
            self.data_dir = repo_root / "data"
        else:
            self.data_dir = data_dir

        self.user_dir = self.data_dir / "user"
        self.custom_indicators_dir = self.data_dir / "custom_indicators"
        self.builtin_dir = self.data_dir / "internal"
        self.tmp_root = self.data_dir / "internal" / "tmp" / "marketplace"

    def get_descriptor(self) -> MarketplacePluginDescriptor:
        """Return plugin descriptor for host registration.

        Returns:
            MarketplacePluginDescriptor model.
        """
        return MarketplacePluginDescriptor()

    def list_installed(self) -> list[InstalledProductSummaryModel]:
        """Return summary of all installed marketplace products.

        Returns:
            List of InstalledProductSummaryModel objects.
        """
        return self.store.list_installed()

    def record_share(
        self,
        slug: str,
        title: str = "",
        version: str = "",
        file_name: str = "",
        sha256: str = "",
    ) -> str:
        """Record an author-shared package in the local catalog.

        Args:
            slug: Product identifier slug.
            title: Product display title.
            version: Product version string.
            file_name: Target package file name.
            sha256: Package SHA-256 hash.

        Returns:
            Registered product slug.

        Raises:
            ValueError: If slug is empty.
        """
        trimmed = slug.strip()
        if not trimmed:
            raise ValueError("Missing product slug.")
        self.store.record_install(
            slug=trimmed,
            title=title or trimmed,
            version=version,
            file_name=file_name,
            sha256=sha256,
            installed_files=[],
        )
        return trimmed

    def list_shareable(
        self,
        filter_str: str = "",
        license_owner: str = "HaruQuant User",
    ) -> dict[str, Any]:
        """List user-shareable files formatted for the share popup tree view.

        Args:
            filter_str: Optional search query.
            license_owner: License holder name.

        Returns:
            Dictionary matching donor JSON response contract.
        """
        source_dirs = {str(self.user_dir.resolve()): "user"}
        tree_items = MarketplaceFileMap.generate_tree(
            source_dirs=source_dirs,
            filter_str=filter_str,
            start_index=1,
        )
        excluded = [
            name
            for name in MarketplaceFileMap.excluded_top_dirs()
            if (self.user_dir / name).is_dir()
        ]
        return {
            "id": 0,
            "item": tree_items,
            "excluded": excluded,
            "licenseOwner": license_owner,
            "success": "Sources listed.",
        }

    def build_zip(
        self,
        files: list[str | Path],
        file_name: str,
        meta: dict[str, Any] | str | None = None,
    ) -> BuildZipResultModel:
        """Build an exportable marketplace package .zip with manifest.

        Args:
            files: List of file paths to include in the archive.
            file_name: Desired name of the zip file (must end in .zip).
            meta: Metadata fields for manifest.json.

        Returns:
            BuildZipResultModel with zip_id, file_name, size, and build.

        Raises:
            ValueError: On invalid file name, traversal, or excluded file inclusion.
        """
        norm_name = Path(file_name).name
        if not norm_name.lower().endswith(".zip") or norm_name != file_name:
            raise ValueError("File name must end with .zip")

        if not files:
            raise ValueError("There are no files to share.")

        user_root = self.user_dir.resolve()
        valid_paths = _collect_shareable_files(files, user_root)
        if not valid_paths:
            raise ValueError("There are no files to share.")

        zip_id = str(uuid.uuid4())
        out_dir = self.tmp_root / zip_id
        out_dir.mkdir(parents=True, exist_ok=True)
        zip_path = out_dir / file_name

        rel_entry_names = [p.relative_to(user_root).as_posix() for p in valid_paths]
        manifest = _build_manifest_model(meta, rel_entry_names)

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            manifest_json = manifest.model_dump_json(by_alias=True, indent=2)
            zf.writestr(MANIFEST_ENTRY, manifest_json)
            for path, entry_name in zip(valid_paths, rel_entry_names, strict=True):
                zf.write(path, arcname=entry_name)

        logger.info(
            "FR-MARKETPLACE-BUILD-ZIP: Built package zip_id='%s', files=%d, bytes=%d",
            zip_id,
            len(valid_paths),
            zip_path.stat().st_size,
        )
        return BuildZipResultModel(
            zip_id=zip_id,
            file_name=file_name,
            size=zip_path.stat().st_size,
            build="HaruQuantAI",
        )

    def cleanup_zip(self, zip_id: str) -> None:
        """Clean up temporary directory associated with a built package.

        Args:
            zip_id: 36-character UUID string.

        Raises:
            ValueError: If zip_id is not a valid UUID format.
        """
        if not UUID_REGEX.match(zip_id):
            raise ValueError("Invalid package id.")

        target_dir = self.tmp_root / zip_id
        if target_dir.exists():
            for child in target_dir.rglob("*"):
                if child.is_file():
                    child.unlink()
            for child in sorted(target_dir.rglob("*"), reverse=True):
                if child.is_dir():
                    child.rmdir()
            target_dir.rmdir()
            logger.info("FR-MARKETPLACE-BUILD-ZIP: Cleaned up zip_id='%s'", zip_id)

    def install_package(
        self,
        slug: str,
        title: str,
        version: str,
        zip_bytes_or_path: bytes | Path,
        expected_sha256: str,
        *,
        file_name: str = "",
    ) -> InstallResultModel:
        """Securely unpack an extension zip package into the user directory.

        Args:
            slug: Product identifier slug.
            title: Product display title.
            version: Product version string.
            zip_bytes_or_path: Raw bytes or Path to the zip file.
            expected_sha256: Required SHA-256 checksum for verification.
            file_name: Originating file name.

        Returns:
            InstallResultModel containing installed files, skipped files, and flags.

        Raises:
            ValueError: If checksum mismatches, entry attempts directory traversal,
                        or package structure is invalid.
        """
        data = (
            zip_bytes_or_path.read_bytes()
            if isinstance(zip_bytes_or_path, Path)
            else zip_bytes_or_path
        )
        actual_sha = hashlib.sha256(data).hexdigest()
        if actual_sha.lower() != expected_sha256.strip().lower():
            raise ValueError(
                "Checksum mismatch - the downloaded file is corrupted or tampered with."
            )

        installed_files: list[str] = []
        skipped_files: list[SkippedFileModel] = []
        restart_required = False

        user_root = self.user_dir.resolve()
        ci_root = self.custom_indicators_dir.resolve()
        builtin_root = self.builtin_dir.resolve()

        with zipfile.ZipFile(io.BytesIO(data), mode="r") as zf:
            for member in zf.infolist():
                if member.is_dir():
                    continue

                raw_entry = member.filename.replace("\\", "/")
                entry_name = raw_entry.removeprefix("user/")
                if entry_name == MANIFEST_ENTRY:
                    continue

                root = (
                    ci_root
                    if entry_name.startswith(CUSTOM_INDICATORS_PREFIX)
                    else user_root
                )
                rel_target = entry_name.removeprefix(CUSTOM_INDICATORS_PREFIX)

                dest_path = (root / rel_target).resolve()
                if not dest_path.is_relative_to(root):
                    raise ValueError(
                        f"Invalid package - entry '{entry_name}' points "
                        "outside the user folder."
                    )

                if root == user_root:
                    builtin_path = (builtin_root / entry_name).resolve()
                    if builtin_path.exists():
                        skipped_files.append(
                            SkippedFileModel(
                                name=entry_name,
                                reason="already exists in Builtin",
                            )
                        )
                        continue

                dest_path.parent.mkdir(parents=True, exist_ok=True)
                dest_path.write_bytes(zf.read(member))
                installed_files.append(entry_name)

                if entry_name.startswith(RESTART_REQUIRED_PREFIX):
                    restart_required = True

        self.store.record_install(
            slug=slug,
            title=title or slug,
            version=version,
            file_name=file_name or f"{slug}.zip",
            sha256=expected_sha256,
            installed_files=installed_files,
        )

        logger.info(
            "FR-MARKETPLACE-INSTALL: Installed '%s' (%d files, %d skipped)",
            slug,
            len(installed_files),
            len(skipped_files),
        )

        return InstallResultModel(
            slug=slug,
            installed_files=installed_files,
            skipped_files=skipped_files,
            restart_required=restart_required,
            install_dir=str(user_root),
        )

    def uninstall_package(self, slug: str) -> UninstallResultModel:
        """Uninstall an extension and prune empty parent directories.

        Args:
            slug: Product identifier slug.

        Returns:
            UninstallResultModel detailing removed files and restart status.

        Raises:
            ValueError: If slug is empty.
        """
        trimmed = slug.strip()
        if not trimmed:
            raise ValueError("Missing product id.")

        installed = self.store.get_installed_files(trimmed)
        removed_files: list[str] = []
        failed_files: list[str] = []
        restart_required = False

        user_root = self.user_dir.resolve()
        ci_root = self.custom_indicators_dir.resolve()

        for entry_name in installed:
            norm_entry = entry_name.replace("\\", "/").removeprefix("user/")
            root = (
                ci_root
                if norm_entry.startswith(CUSTOM_INDICATORS_PREFIX)
                else user_root
            )
            local_path = norm_entry.removeprefix(CUSTOM_INDICATORS_PREFIX)

            target_file = (root / local_path).resolve()
            if target_file.is_relative_to(root) and target_file.is_file():
                try:
                    target_file.unlink()
                    removed_files.append(entry_name)
                    self._delete_empty_parents(target_file.parent, root)
                except OSError:
                    failed_files.append(entry_name)
            else:
                failed_files.append(entry_name)

            if norm_entry.startswith(RESTART_REQUIRED_PREFIX):
                restart_required = True

        self.store.delete_install(trimmed)
        logger.info(
            "FR-MARKETPLACE-UNINSTALL: Uninstalled '%s' (%d removed, %d failed)",
            trimmed,
            len(removed_files),
            len(failed_files),
        )

        return UninstallResultModel(
            slug=trimmed,
            removed_files=removed_files,
            failed_files=failed_files,
            restart_required=restart_required,
        )

    @staticmethod
    def _delete_empty_parents(directory: Path, root: Path) -> None:
        """Recursively delete empty parent directories up to root."""
        curr = directory.resolve()
        root_res = root.resolve()
        while curr != root_res and curr.is_relative_to(root_res):
            try:
                if any(curr.iterdir()):
                    break
                curr.rmdir()
                curr = curr.parent
            except OSError:
                break
