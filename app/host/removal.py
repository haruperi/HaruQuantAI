"""Stopped-installation package removal with exact ownership and reversible moves."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from uuid import uuid4

from app.host.contracts import Document
from app.host.logging import get_logger
from app.host.packages import PackageInventory, confined_file, scan_packages

logger = get_logger(__name__)


class RemovalPlan(Document):
    """Bounded immutable target closure tied to one validated inventory fingerprint."""

    fingerprint: str
    target_ids: tuple[str, ...]
    files: tuple[str, ...]
    hashes: tuple[str, ...]


class InstallationLease:
    """Exclusive lifecycle/removal fence; stale files require explicit recovery."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.held = False
        self.token = uuid4().hex

    def acquire(self) -> None:
        """Refuse linked installations, active owners or an unreconciled stale fence."""
        if self.held:
            raise ValueError("Lease already held")
        if any(
            p.is_symlink() or p.is_junction() for p in (self.root, *self.root.parents)
        ):
            raise ValueError("Linked installation")
        self.root.mkdir(parents=True, exist_ok=True)
        with (self.root / ".package-operation.lock").open(
            "x", encoding="utf-8"
        ) as stream:
            stream.write(self.token)
        self.held = True

    def release(self) -> None:
        """Release only this lease's fence; never clear another owner's marker."""
        if self.held:
            path = self.root / ".package-operation.lock"
            if path.read_text(encoding="utf-8") != self.token:
                raise ValueError("Installation lease changed")
            path.unlink()
            self.held = False


def plan_removal(root: Path, inventory: PackageInventory, target: str) -> RemovalPlan:
    """Compute one complete pair or workspace-child closure, excluding all data.

    Raises:
        ValueError: Inventory is invalid or the requested package does not exist.
    """
    if inventory.issues:
        raise ValueError("Cannot remove from an invalid inventory")
    packages = {p.id: p for p in inventory.packages}
    if target not in packages:
        raise ValueError("Unknown removal target")
    targets = {target}
    if packages[target].kind == "workspace":
        targets.update(
            p.id for p in packages.values() if p.owner_workspace_id == target
        )
    files = sorted({f for key in targets for f in packages[key].owned_paths.files()})
    hashes = tuple(
        hashlib.sha256(confined_file(root, f).read_bytes()).hexdigest() for f in files
    )
    return RemovalPlan(
        fingerprint=inventory.fingerprint,
        target_ids=tuple(sorted(targets)),
        files=tuple(files),
        hashes=hashes,
    )


def _write_journal(
    path: Path, plan: RemovalPlan, moved: tuple[str, ...], state: str
) -> None:
    """Replace a journal atomically before/after each reversible operation."""
    temp = path.with_suffix(".pending")
    temp.write_text(
        json.dumps({"plan": plan.model_dump(), "moved": moved, "state": state}),
        encoding="utf-8",
    )
    temp.replace(path)


def apply_removal(root: Path, plan: RemovalPlan) -> Path:
    """Apply only an exact current plan under an exclusive stopped-installation fence.

    Files move to a generated quarantine under root. Interrupted apply retains a
    journal; recovery reconciles actual file locations rather than guessing targets.
    No resources, databases or capabilities' other owners are removal targets.

    Returns:
        Journal path for an explicit restore operation.

    Raises:
        ValueError: Plan was forged/stale or a target fails confinement checks.
        OSError: Active/stale fence or filesystem mutation failed.
    """
    lease = InstallationLease(root)
    lease.acquire()
    logger.info(
        "Executing removal for %d package(s): %s (%d files)",
        len(plan.target_ids),
        plan.target_ids,
        len(plan.files),
    )
    try:
        current = scan_packages(root)
        if current.fingerprint != plan.fingerprint or current.issues:
            raise ValueError("Stale removal plan")
        candidates = [plan_removal(root, current, key) for key in plan.target_ids]
        if plan not in candidates:
            raise ValueError("Removal closure mismatch")
        quarantine = root / ".package-quarantine" / uuid4().hex
        if (root / ".package-quarantine").is_symlink() or (
            root / ".package-quarantine"
        ).is_junction():
            raise ValueError("Linked quarantine")
        quarantine.mkdir(parents=True)
        journal = quarantine / "journal.json"
        moved: tuple[str, ...] = ()
        _write_journal(journal, plan, moved, "applying")
        for name in plan.files:
            source = confined_file(root, name)
            target = quarantine / name
            target.parent.mkdir(parents=True, exist_ok=True)
            source.rename(target)
            moved += (name,)
            _write_journal(journal, plan, moved, "applying")
        _write_journal(journal, plan, moved, "removed")
        logger.info(
            "Removal completed for targets: %s (quarantine journal=%s)",
            plan.target_ids,
            journal,
        )
        return journal
    finally:
        lease.release()


def restore_removal(root: Path, journal: Path) -> None:
    """Restore verified quarantined bytes without overwriting an installed file.

    Recovery validates the journal, all destinations and content hashes first.
    Repeated recovery is safe when a file was already restored with the same bytes.
    """
    logger.info("Restoring package removal from journal: %s", journal)
    lease = InstallationLease(root)
    lease.acquire()
    try:
        _restore_locked(root.resolve(), journal.absolute())
    finally:
        lease.release()


def _restore_locked(root: Path, journal: Path) -> None:
    """Reconcile interrupted moves using only journaled exact paths and hashes."""
    base = root / ".package-quarantine"
    if (
        journal != journal.resolve()
        or not journal.is_relative_to(base)
        or journal.name != "journal.json"
    ):
        raise ValueError("Invalid recovery journal")
    if any(p.is_symlink() or p.is_junction() for p in (journal, *journal.parents)):
        raise ValueError("Linked recovery path")
    raw = json.loads(journal.read_text(encoding="utf-8"))
    plan = RemovalPlan.model_validate(raw["plan"])
    if len(plan.files) != len(plan.hashes):
        raise ValueError("Invalid recovery hashes")
    pairs: list[tuple[Path, Path]] = []
    for name, digest in zip(plan.files, plan.hashes, strict=True):
        destination = confined_file(root, name, exists=False)
        source = journal.parent / name
        if any(p.is_symlink() or p.is_junction() for p in (source, *source.parents)):
            raise ValueError("Linked recovery content")
        present = source if source.is_file() else destination
        if (
            present.is_symlink()
            or hashlib.sha256(present.read_bytes()).hexdigest() != digest
        ):
            raise ValueError("Recovery content changed")
        if source.exists() and destination.exists():
            raise ValueError("Recovery would overwrite installed file")
        if source.exists():
            pairs.append((source, destination))
    for source, destination in pairs:
        destination.parent.mkdir(parents=True, exist_ok=True)
        source.rename(destination)
    _write_journal(journal, plan, (), "restored")
    logger.info(
        "Package restoration completed for plan targets: %s (%d files)",
        plan.target_ids,
        len(pairs),
    )
