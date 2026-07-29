"""Content-addressed staging writer with strict path containment.

`FR-AGENTIC-048` says the coder may write only to staging. That is enforced
here, and it is the one guarantee in this feature that does not depend on an
injected runtime: every path is validated as a relative POSIX path, resolved
against the staging root, and re-checked after resolution so a symlink cannot
carry a write outside the tree.

The guards are deliberately conservative. A generated path that is merely
unusual is rejected rather than normalized, because normalizing an attacker's
path is how containment fails.

Nothing here imports, executes, or registers what it writes.
"""

from __future__ import annotations

from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING

from app.utils import get_logger

if TYPE_CHECKING:
    from app.agentic.agents.engineering.coder.schemas import (
        CodeArtifact,
        GeneratedFile,
    )

logger = get_logger(__name__)

_MAX_PATH_DEPTH = 8
_MAX_COMPONENT_LENGTH = 96

# Windows resolves these names as devices regardless of directory or
# extension, so `CON.py` is not a file. They are rejected on every platform:
# a staged artefact must be portable, and a path that means something
# different on the reviewer's machine is not portable.
_RESERVED_STEMS = frozenset(
    {"con", "prn", "aux", "nul"}
    | {f"com{index}" for index in range(1, 10)}
    | {f"lpt{index}" for index in range(1, 10)},
)

# Characters that either separate paths, open an NTFS alternate data stream,
# or are invalid in a Windows filename.
_FORBIDDEN_CHARACTERS = frozenset('\\:*?"<>|\0\n\r\t')

_PERMITTED_SUFFIXES = frozenset({".py", ".md", ".toml", ".txt", ".json"})


def validate_relative_path(candidate: str) -> str | None:
    """Report why a declared staging path cannot be written.

    Args:
        candidate: Declared staging-relative POSIX path.

    Returns:
        The failing condition, or None when the path is acceptable.
    """
    failure = _validate_raw(candidate)
    if failure is not None:
        return failure
    # Components are checked on the raw split rather than on parsed parts.
    # `PurePosixPath` silently drops a `.` component, so parsing first would
    # accept `a/./b.py` — and normalizing an attacker's path is how
    # containment fails.
    segments = candidate.split("/")
    if len(segments) > _MAX_PATH_DEPTH:
        return f"path must not exceed {_MAX_PATH_DEPTH} components"
    for segment in segments:
        failure = _validate_component(segment)
        if failure is not None:
            return failure
    pure = PurePosixPath(candidate)
    if pure.suffix.lower() not in _PERMITTED_SUFFIXES:
        return f"path suffix {pure.suffix!r} is not permitted in staging"
    return None


def _validate_raw(candidate: str) -> str | None:
    """Report why the raw declared text cannot be a staging path.

    These checks run on the text as written, before any parsing, because
    parsing is itself a normalization step that can hide an escape.

    Args:
        candidate: Declared staging-relative POSIX path.

    Returns:
        The failing condition, or None when the text is acceptable.
    """
    if not candidate or candidate != candidate.strip():
        return "path must be non-empty trimmed text"
    if len(candidate) > _MAX_COMPONENT_LENGTH * _MAX_PATH_DEPTH:
        return "path is too long"
    for character in candidate:
        if character in _FORBIDDEN_CHARACTERS:
            return f"path contains the forbidden character {character!r}"
    if candidate.startswith(("/", "~")):
        return "path must be relative to the staging root"
    # A drive-relative path such as `C:file.py` loses its colon to the
    # forbidden-character check above; this catches the bare-letter form.
    if len(candidate) > 1 and candidate[1] == ":":
        return "path must not name a drive"
    return None


def validate_artifact_identity(candidate: str) -> str | None:
    """Report why an artefact identity cannot be a staging directory name.

    An identity becomes a directory, so it is held to a strict charset rather
    than to the general path rules: anything that is not a plain name is
    rejected outright.

    Args:
        candidate: Candidate artefact identity.

    Returns:
        The failing condition, or None when the identity is acceptable.
    """
    if not candidate or len(candidate) > _MAX_COMPONENT_LENGTH:
        return "identity must be non-empty and bounded"
    if not all(character.isalnum() or character in "-_" for character in candidate):
        return "identity must contain only letters, digits, dashes, and underscores"
    if candidate.lower() in _RESERVED_STEMS:
        return f"identity {candidate!r} names a reserved device"
    return None


def _validate_component(part: str) -> str | None:
    """Report why one path component cannot be written.

    Args:
        part: Single path component.

    Returns:
        The failing condition, or None when the component is acceptable.
    """
    if not part:
        return "path must not contain an empty component"
    if part in {".", ".."}:
        return "path must not contain a relative traversal component"
    if len(part) > _MAX_COMPONENT_LENGTH:
        return f"path component must not exceed {_MAX_COMPONENT_LENGTH} characters"
    # Windows silently strips trailing dots and spaces, so `evil.py.` and
    # `evil.py ` resolve to a different file than the one declared.
    if part != part.rstrip(". "):
        return "path component must not end with a dot or a space"
    stem = part.split(".", maxsplit=1)[0].lower()
    if stem in _RESERVED_STEMS:
        return f"path component {part!r} names a reserved device"
    return None


def _resolved_target(staging_root: Path, relative_path: str) -> Path | None:
    """Resolve one declared path and confirm it stays inside the root.

    Resolution is what catches a symlink: the declared path may look ordinary
    while its resolved target sits outside the tree.

    Args:
        staging_root: Root the artefact may write to.
        relative_path: Validated staging-relative POSIX path.

    Returns:
        The resolved absolute target, or None when it escapes the root.
    """
    root = staging_root.resolve()
    target = (root / relative_path).resolve()
    if not target.is_relative_to(root):
        logger.warning("Refusing a staging path that resolves outside its root")
        return None
    # A resolved parent that is a symlink escapes just as effectively as a
    # symlinked leaf, so the whole chain is checked.
    for parent in [target, *target.parents]:
        if parent == root:
            break
        if parent.is_symlink():
            logger.warning("Refusing a staging path that traverses a symlink")
            return None
    return target


def stage_files(
    staging_root: Path,
    artifact_id: str,
    files: tuple[GeneratedFile, ...],
) -> tuple[Path, ...]:
    """Write one artefact's files under its own staging directory.

    Args:
        staging_root: Root every artefact is written beneath.
        artifact_id: Artefact identity, used as the containing directory.
        files: Validated generated files.

    Returns:
        Ordered absolute paths written.

    Raises:
        ValueError: If the artefact identity or any declared path is
            unacceptable, or if a path escapes the staging root.
    """
    identity_failure = validate_artifact_identity(artifact_id)
    if identity_failure is not None:
        message = f"artefact identity is not a safe directory name: {identity_failure}"
        raise ValueError(message)

    root = staging_root.resolve()
    artifact_root = root / artifact_id
    written: list[Path] = []
    for generated in files:
        failure = validate_relative_path(generated.relative_path)
        if failure is not None:
            message = f"refusing staging path {generated.relative_path!r}: {failure}"
            raise ValueError(message)
        target = _resolved_target(artifact_root, generated.relative_path)
        if target is None:
            message = (
                f"refusing staging path {generated.relative_path!r}: "
                "it resolves outside the staging root"
            )
            raise ValueError(message)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(generated.content, encoding="utf-8", newline="\n")
        written.append(target)

    logger.info(
        "Staged %d files for artefact %s",
        len(written),
        artifact_id,
    )
    return tuple(written)


def read_staged_file(
    staging_root: Path,
    artifact_id: str,
    relative_path: str,
) -> str | None:
    """Read one staged file as text.

    Args:
        staging_root: Root every artefact is written beneath.
        artifact_id: Artefact identity.
        relative_path: Staging-relative POSIX path.

    Returns:
        The file content, or None when the path is unacceptable or absent.
    """
    if validate_relative_path(relative_path) is not None:
        return None
    target = _resolved_target(staging_root.resolve() / artifact_id, relative_path)
    if target is None or not target.is_file():
        return None
    return target.read_text(encoding="utf-8")


def verify_staged_artifact(
    staging_root: Path,
    artifact: CodeArtifact,
) -> tuple[str, ...]:
    """Report which of an artefact's files no longer match their digests.

    Args:
        staging_root: Root every artefact is written beneath.
        artifact: Staged artefact to verify.

    Returns:
        Ordered relative paths whose staged content has drifted or vanished.
    """
    from app.agentic.agents.engineering.coder.schemas import derive_content_hash

    drifted: list[str] = []
    for generated in artifact.files:
        content = read_staged_file(
            staging_root,
            artifact.artifact_id,
            generated.relative_path,
        )
        if content is None or derive_content_hash(content) != generated.content_hash:
            drifted.append(generated.relative_path)
    return tuple(drifted)
