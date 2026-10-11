"""Extract and catalog SQX building blocks, indicators, and calculators.

Description:
    Clean-room AST and regex parser that inspects Java snippet source files
    from StrategyQuant X reference trees, extracts metadata, parameter sets,
    value boundaries, output specifications, and symmetrical opposite pairings,
    and serializes the normalized catalog to JSON for strategy authoring and
    evaluation. Donor source bodies are never published or retained.

Purpose:
    FEAT-TOOLS-EXTRACT-SQX-BLOCKS: Build clean-room strategy authoring catalog.

Key Capabilities:
    - FR-TOOLS-SQX-BLOCKS-MANIFEST-PARSER: Parse snippets.txt and opposites CSV.
      Associated: `SQXBlockExtractor.load_manifest()`, `SQXBlockExtractor.load_opposites()`
      Logging: INFO on manifest and pairing discovery; WARNING on missing entries.
    - FR-TOOLS-SQX-BLOCKS-JAVA-PARSER: Parse class annotations and parameters.
      Associated: `SQXBlockExtractor.parse_java_snippet()`
      Logging: DEBUG on parsed block signatures; WARNING on unrecognized syntax.
    - FR-TOOLS-SQX-BLOCKS-CATALOG-BUILDER: Assemble normalized catalog structure.
      Associated: `SQXBlockExtractor.build_catalog()`, `SQXBlockExtractor.save_catalog()`
      Logging: INFO on catalog assembly progress, category breakdowns, and export.
    - FR-TOOLS-SQX-BLOCKS-VALIDATOR: Compute SHA-256 and validate constraints.
      Associated: `SQXBlockExtractor.validate_catalog()`
      Logging: INFO on validation results; WARNING on unmatched opposites or gaps.

Python API Usage:
    ```python
    from pathlib import Path
    from scripts.extract_sqx_blocks import SQXBlockExtractor

    extractor = SQXBlockExtractor(
        sqx_root=Path("C:/SQX-145"),
        output_file=Path("docs/dev/evidence/sqx_blocks_catalog.json"),
    )
    catalog = extractor.build_catalog()
    saved_path = extractor.save_catalog(catalog)
    ```

CLI Usage:
    ```bash
    uv run python -m scripts.extract_sqx_blocks --sqx-root C:\\SQX-145 --output docs/dev/evidence/sqx_blocks_catalog.json
    ```
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import logging
import re
import sys
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def strip_comments(text: str) -> str:
    """Remove C/Java style block and line comments from source code.

    Args:
        text: Raw source code string.

    Returns:
        Source code with comments replaced by equivalent whitespace.
    """

    def replacer(match: re.Match[str]) -> str:
        s = match.group(0)
        if s.startswith("/"):
            return " "
        return s

    pattern = re.compile(
        r'//.*?$|/\*.*?\*/|\'(?:\\.|[^\\\'])*\'|"(?:\\.|[^\\"])*"',
        re.DOTALL | re.MULTILINE,
    )
    return re.sub(pattern, replacer, text)


def _find_opening_paren(text: str, pos: int, target_len: int) -> tuple[int, int]:
    """Find the opening parenthesis following an annotation target.

    Args:
        text: Source text.
        pos: Start position of target string.
        target_len: Length of the annotation target name.

    Returns:
        Tuple of (open_paren_index or -1, next_pos).
    """
    search_end = min(pos + target_len + 20, len(text))
    for i in range(pos + target_len, search_end):
        if text[i] == "(":
            return i, i
        if not text[i].isspace():
            return -1, i
    return -1, pos + target_len


def extract_annotation_body(
    text: str, annot_name: str, start_pos: int = 0
) -> tuple[str | None, int]:
    """Extract the balanced parenthesized body of an annotation @annot_name.

    Args:
        text: Source text to search.
        annot_name: Name of the annotation without '@'.
        start_pos: Character index to begin searching from.

    Returns:
        Tuple of (body_string or None, next_search_index).
    """
    target = f"@{annot_name}"
    pos = text.find(target, start_pos)
    if pos == -1:
        return None, len(text)

    open_idx, next_pos = _find_opening_paren(text, pos, len(target))
    if open_idx == -1:
        return "", next_pos

    depth = 1
    in_quotes = False
    quote_char = ""
    idx = open_idx + 1

    while idx < len(text) and depth > 0:
        ch = text[idx]
        if ch in ('"', "'") and (idx == 0 or text[idx - 1] != "\\"):
            if not in_quotes:
                in_quotes = True
                quote_char = ch
            elif ch == quote_char:
                in_quotes = False
        elif not in_quotes:
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
        idx += 1

    if depth == 0:
        body = text[open_idx + 1 : idx - 1]
        return body, idx
    return None, len(text)


def extract_all_annotation_bodies(text: str, annot_name: str) -> list[str]:
    """Extract all occurrences of @annot_name(...) in text.

    Args:
        text: Source text.
        annot_name: Annotation name without '@'.

    Returns:
        List of body strings for each occurrence.
    """
    bodies: list[str] = []
    pos = 0
    while pos < len(text):
        body, next_pos = extract_annotation_body(text, annot_name, pos)
        if body is not None:
            if body:
                bodies.append(body)
            pos = next_pos
        else:
            break
    return bodies


def _tokenize_attributes(attr_str: str) -> list[str]:
    """Split comma-separated attributes outside of quotes."""
    tokens: list[str] = []
    current: list[str] = []
    in_quotes = False
    quote_char = ""

    for i, ch in enumerate(attr_str):
        if ch in ('"', "'") and (i == 0 or attr_str[i - 1] != "\\"):
            if not in_quotes:
                in_quotes = True
                quote_char = ch
            elif ch == quote_char:
                in_quotes = False
            current.append(ch)
        elif ch == "," and not in_quotes:
            tokens.append("".join(current).strip())
            current = []
        else:
            current.append(ch)

    if current:
        tokens.append("".join(current).strip())
    return tokens


def parse_annotation_attributes(attr_str: str) -> dict[str, str]:
    """Parse comma-separated key=value attributes from an annotation string.

    Args:
        attr_str: Content between outer parentheses of an annotation.

    Returns:
        Dictionary mapping attribute names to string values.
    """
    results: dict[str, str] = {}
    if not attr_str or not attr_str.strip():
        return results

    for token in _tokenize_attributes(attr_str):
        if not token:
            continue
        if "=" in token:
            k, v = token.split("=", 1)
            k, v = k.strip(), v.strip()
            if (v.startswith('"') and v.endswith('"')) or (
                v.startswith("'") and v.endswith("'")
            ):
                v = v[1:-1]
            results[k] = v
        else:
            cleaned = token.strip()
            if (cleaned.startswith('"') and cleaned.endswith('"')) or (
                cleaned.startswith("'") and cleaned.endswith("'")
            ):
                cleaned = cleaned[1:-1]
            results["value"] = cleaned

    return results


def _determine_category(rel_locator: str) -> str:
    """Determine block category from path hierarchy."""
    parts = rel_locator.replace("\\", "/").split("/")
    if "Blocks" in parts:
        idx = parts.index("Blocks")
        if len(parts) > idx + 1:
            return parts[idx + 1]
    for recognized in ("Calculators", "Columns", "Internal", "ExitMethods"):
        if recognized in parts:
            return recognized
    return "Other"


def _determine_block_type(
    superclass: str, category: str, parts: list[str], class_name: str
) -> str:
    """Determine semantic block type from class hierarchy and folder role."""
    b_type = "Block"
    if "ConditionBlock" in superclass:
        b_type = "Condition"
    elif "ComparisonBlock" in superclass or "Comparisons" in parts:
        b_type = "Comparison"
    elif "ActionBlock" in superclass or "Order" in parts:
        b_type = "Order" if "Order" in parts else "Action"
    elif "IndicatorBlock" in superclass or category == "Indicators":
        b_type = "Indicator"
    elif "FormulaBlock" in superclass or "Formulas" in parts:
        b_type = "Formula"
    elif "Calculators" in parts or "Calculator" in class_name:
        b_type = "Calculator"
    elif "CandlePatterns" in parts:
        b_type = "CandlePattern"
    return b_type


def _parse_class_annotations(
    clean_text: str, class_name: str, opposites_map: dict[str, str]
) -> dict[str, Any]:
    """Extract class-level annotations into a dictionary."""
    bb_body, _ = extract_annotation_body(clean_text, "BuildingBlock")
    bb_attrs = parse_annotation_attributes(bb_body) if bb_body else {}

    ind_body, _ = extract_annotation_body(clean_text, "Indicator")
    if ind_body:
        ind_attrs = parse_annotation_attributes(ind_body)
        for key, target_key in (
            ("min", "minValue"),
            ("max", "maxValue"),
            ("step", "step"),
        ):
            if key in ind_attrs and target_key not in bb_attrs:
                bb_attrs[target_key] = ind_attrs[key]

    help_body, _ = extract_annotation_body(clean_text, "Help")
    help_text = ""
    if help_body:
        h_attrs = parse_annotation_attributes(help_body)
        help_text = h_attrs.get("value", help_body.strip("\"'"))

    opp_body, _ = extract_annotation_body(clean_text, "OppositeBlock")
    opposite_block = None
    if opp_body:
        o_attrs = parse_annotation_attributes(opp_body)
        opposite_block = o_attrs.get("value", opp_body.strip("\"'"))
    if not opposite_block:
        opposite_block = opposites_map.get(class_name)

    sort_order = _extract_integer_annotation(clean_text, "SortOrder")
    category_order = _extract_integer_annotation(clean_text, "CategoryOrder")

    param_sets: list[str] = []
    for ps_body in extract_all_annotation_bodies(clean_text, "ParameterSet"):
        ps_attrs = parse_annotation_attributes(ps_body)
        val = ps_attrs.get("set", ps_attrs.get("value"))
        if val:
            param_sets.append(val)

    return {
        "name": bb_attrs.get("name", class_name),
        "display": bb_attrs.get("display", class_name),
        "return_type": bb_attrs.get("returnType", "Unknown"),
        "help_text": help_text,
        "opposite_block": opposite_block,
        "sort_order": sort_order,
        "category_order": category_order,
        "parameter_sets": param_sets,
    }


def _extract_integer_annotation(text: str, annot_name: str) -> int | None:
    """Extract an integer value from @AnnotName(123)."""
    body, _ = extract_annotation_body(text, annot_name)
    if body:
        attrs = parse_annotation_attributes(body)
        raw = attrs.get("value", body.strip())
        if raw.isdigit() or (raw.startswith("-") and raw[1:].isdigit()):
            return int(raw)
    return None


def _parse_field_parameter(
    annot_block: str,
    field_type: str,
    field_name: str,
    default_init: str | None,
) -> dict[str, Any]:
    """Parse @Parameter field definition."""
    p_body, _ = extract_annotation_body(annot_block, "Parameter")
    p_attrs = parse_annotation_attributes(p_body) if p_body else {}

    ed_body, _ = extract_annotation_body(annot_block, "Editor")
    ed_attrs = parse_annotation_attributes(ed_body) if ed_body else {}

    param_dict: dict[str, Any] = {
        "name": p_attrs.get("name", field_name),
        "field_name": field_name,
        "type": field_type,
        "default_value": p_attrs.get(
            "defaultValue", default_init.strip() if default_init else ""
        ),
        "category": p_attrs.get("category", "Default"),
    }
    key_mapping = {
        "minValue": "min_value",
        "maxValue": "max_value",
        "step": "step",
        "defaultChartIndex": "default_chart_index",
    }
    for java_k, py_k in key_mapping.items():
        if java_k in p_attrs:
            param_dict[py_k] = p_attrs[java_k]
    if "showIfDefault" in p_attrs:
        param_dict["show_if_default"] = p_attrs["showIfDefault"] == "true"
    if "type" in ed_attrs:
        param_dict["editor_type"] = ed_attrs["type"]
    if "values" in ed_attrs:
        param_dict["editor_values"] = ed_attrs["values"]

    return param_dict


def _parse_field_declarations(
    clean_text: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Parse fields decorated with @Parameter and @Output."""
    parameters: list[dict[str, Any]] = []
    outputs: list[dict[str, Any]] = []

    field_pattern = re.compile(
        r"((?:@[A-Za-z0-9_]+(?:\([^;]*?\))?\s*)+)"
        r"public\s+(?:final\s+)?([A-Za-z0-9_<>]+)\s+([A-Za-z0-9_]+)"
        r"(?:\s*=\s*([^;]+))?;",
        re.MULTILINE,
    )

    for match in field_pattern.finditer(clean_text):
        annot_block = match.group(1)
        field_type = match.group(2)
        field_name = match.group(3)
        default_init = match.group(4)

        if "@Parameter" in annot_block:
            p = _parse_field_parameter(
                annot_block, field_type, field_name, default_init
            )
            parameters.append(p)
        elif "@Output" in annot_block:
            o_body, _ = extract_annotation_body(annot_block, "Output")
            o_attrs = parse_annotation_attributes(o_body) if o_body else {}
            outputs.append(
                {
                    "name": o_attrs.get("name", field_name),
                    "field_name": field_name,
                    "type": field_type,
                    "color": o_attrs.get("color", ""),
                }
            )

    return parameters, outputs


@dataclass
class BlockDefinition:
    """Normalized specification of a StrategyQuant building block or snippet."""

    id: str
    name: str
    class_name: str
    package: str
    category: str
    block_type: str
    display: str
    return_type: str
    help_text: str = ""
    opposite_block: str | None = None
    sort_order: int | None = None
    category_order: int | None = None
    parameter_sets: list[str] = field(default_factory=list)
    parameters: list[dict[str, Any]] = field(default_factory=list)
    outputs: list[dict[str, Any]] = field(default_factory=list)
    source_file: str = ""
    sha256: str = ""


class SQXBlockExtractor:
    """Extractor and catalog builder for SQX building blocks and snippets."""

    def __init__(
        self,
        sqx_root: Path,
        output_file: Path | None = None,
    ) -> None:
        """Initialize the extractor with logical roots.

        Args:
            sqx_root: Local filesystem path to StrategyQuant X installation.
            output_file: Optional target path to save the output JSON catalog.
        """
        self.sqx_root = sqx_root
        self.output_file = output_file
        self.opposites_map: dict[str, str] = {}
        self.warnings: list[str] = []

    @classmethod
    def load_opposites(cls, opposites_path: Path) -> dict[str, str]:
        """Load symmetrical opposite block pairings from CSV.

        Args:
            opposites_path: Path to OppositeBlocks_example.csv.

        Returns:
            Dictionary mapping block name to its opposite block name.
        """
        opposites: dict[str, str] = {}
        if not opposites_path.exists():
            logger.warning(
                "FR-TOOLS-SQX-BLOCKS-MANIFEST-PARSER: Opposites file missing: %s",
                opposites_path,
            )
            return opposites

        with opposites_path.open("r", encoding="utf-8", errors="ignore") as f:
            reader = csv.reader(f, delimiter=";")
            for row in reader:
                if len(row) >= 2:
                    k, v = row[0].strip(), row[1].strip()
                    if k and k != "Block":
                        opposites[k] = v

        logger.info(
            "FR-TOOLS-SQX-BLOCKS-MANIFEST-PARSER: Loaded %d opposite pairs",
            len(opposites),
        )
        return opposites

    @classmethod
    def load_manifest(cls, manifest_path: Path) -> list[tuple[str, str]]:
        """Load snippet entries from snippets.txt manifest.

        Args:
            manifest_path: Path to user/settings/snippets.txt.

        Returns:
            List of (relative_path, md5_hash) tuples.
        """
        entries: list[tuple[str, str]] = []
        if not manifest_path.exists():
            logger.warning(
                "FR-TOOLS-SQX-BLOCKS-MANIFEST-PARSER: Manifest missing: %s",
                manifest_path,
            )
            return entries

        with manifest_path.open("r", encoding="utf-8", errors="ignore") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line or "|" not in line:
                    continue
                path_part, md5_part = line.split("|", 1)
                path_part = path_part.replace("$SNIPPETS_BUILTIN_DIR$/", "").strip()
                entries.append((path_part, md5_part.strip()))

        logger.info(
            "FR-TOOLS-SQX-BLOCKS-MANIFEST-PARSER: Loaded %d manifest entries",
            len(entries),
        )
        return entries

    def parse_java_snippet(
        self, file_path: Path, rel_locator: str
    ) -> BlockDefinition | None:
        """Parse a single Java snippet into a BlockDefinition.

        Args:
            file_path: Absolute path to the Java source file.
            rel_locator: Relative path from reference root.

        Returns:
            Extracted BlockDefinition or None if not a valid block/calculator.
        """
        try:
            raw_text = file_path.read_text(encoding="utf-8", errors="ignore")
        except OSError as e:
            msg = f"Failed to read {file_path}: {e}"
            self.warnings.append(msg)
            logger.warning("FR-TOOLS-SQX-BLOCKS-JAVA-PARSER: %s", msg)
            return None

        sha256_hash = hashlib.sha256(raw_text.encode("utf-8")).hexdigest()
        clean_text = strip_comments(raw_text)

        pkg_match = re.search(r"package\s+([A-Za-z0-9_.]+);", clean_text)
        package_name = pkg_match.group(1) if pkg_match else ""

        class_match = re.search(
            r"public\s+(?:abstract\s+)?class\s+([A-Za-z0-9_]+)"
            r"(?:\s+extends\s+([A-Za-z0-9_.]+))?"
            r"(?:\s+implements\s+([A-Za-z0-9_.,\s]+))?",
            clean_text,
        )
        if not class_match:
            logger.debug(
                "FR-TOOLS-SQX-BLOCKS-JAVA-PARSER: Skipped non-class file %s",
                file_path.name,
            )
            return None

        class_name = class_match.group(1)
        superclass = class_match.group(2) or ""
        category = _determine_category(rel_locator)
        parts = rel_locator.replace("\\", "/").split("/")
        block_type = _determine_block_type(superclass, category, parts, class_name)

        meta = _parse_class_annotations(clean_text, class_name, self.opposites_map)
        parameters, outputs = _parse_field_declarations(clean_text)

        block_def = BlockDefinition(
            id=f"{package_name}.{class_name}" if package_name else class_name,
            name=meta["name"],
            class_name=class_name,
            package=package_name,
            category=category,
            block_type=block_type,
            display=meta["display"],
            return_type=meta["return_type"],
            help_text=meta["help_text"],
            opposite_block=meta["opposite_block"],
            sort_order=meta["sort_order"],
            category_order=meta["category_order"],
            parameter_sets=meta["parameter_sets"],
            parameters=parameters,
            outputs=outputs,
            source_file=rel_locator.replace("\\", "/"),
            sha256=sha256_hash,
        )

        logger.debug(
            "FR-TOOLS-SQX-BLOCKS-JAVA-PARSER: Parsed block %s (%s)",
            block_def.id,
            block_type,
        )
        return block_def

    def build_catalog(self) -> dict[str, Any]:
        """Assemble all blocks from the SQX tree into a unified catalog dict.

        Returns:
            Normalized catalog dictionary.
        """
        opposites_path = (
            self.sqx_root / "user" / "settings" / "OppositeBlocks_example.csv"
        )
        self.opposites_map = self.load_opposites(opposites_path)

        manifest_path = self.sqx_root / "user" / "settings" / "snippets.txt"
        manifest_entries = self.load_manifest(manifest_path)

        blocks: dict[str, dict[str, Any]] = {}
        counts_by_cat: dict[str, int] = {}
        counts_by_type: dict[str, int] = {}

        snippets_base = self.sqx_root / "internal" / "extend" / "Snippets"

        files_to_parse: list[tuple[Path, str]] = []
        if manifest_entries:
            for rel_path, _ in manifest_entries:
                full_path = snippets_base / rel_path
                if full_path.exists():
                    locator = f"internal/extend/Snippets/{rel_path}"
                    files_to_parse.append((full_path, locator))
                else:
                    self.warnings.append(f"Manifest file missing on disk: {rel_path}")
        else:
            for jf in snippets_base.rglob("*.java"):
                rel_loc = jf.relative_to(self.sqx_root).as_posix()
                files_to_parse.append((jf, rel_loc))

        for full_path, rel_loc in files_to_parse:
            block = self.parse_java_snippet(full_path, rel_loc)
            if block:
                blocks[block.class_name] = asdict(block)
                counts_by_cat[block.category] = counts_by_cat.get(block.category, 0) + 1
                counts_by_type[block.block_type] = (
                    counts_by_type.get(block.block_type, 0) + 1
                )

        catalog: dict[str, Any] = {
            "$schema": "https://haruquantai.io/schemas/blocks_catalog.v1.json",
            "schema_version": 1,
            "generated_at": datetime.now(UTC).isoformat(),
            "reference_root": "SQX_REFERENCE_ROOT",
            "total_snippets": len(blocks),
            "counts_by_category": counts_by_cat,
            "counts_by_type": counts_by_type,
            "blocks": blocks,
            "opposites_map": self.opposites_map,
            "warnings_count": len(self.warnings),
            "warnings": self.warnings[:50],
        }

        logger.info(
            "FR-TOOLS-SQX-BLOCKS-CATALOG-BUILDER: Built catalog with %d blocks "
            "across %d categories",
            len(blocks),
            len(counts_by_cat),
        )
        return catalog

    def save_catalog(self, catalog: dict[str, Any]) -> Path:
        """Write the catalog to the configured output file.

        Args:
            catalog: Catalog dictionary.

        Returns:
            Resolved output file Path.
        """
        if self.output_file is None:
            dest = Path("docs/dev/evidence/sqx_blocks_catalog.json")
        else:
            dest = self.output_file

        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(catalog, indent=2), encoding="utf-8")

        logger.info(
            "FR-TOOLS-SQX-BLOCKS-CATALOG-BUILDER: Catalog exported to %s (%d bytes)",
            dest,
            dest.stat().st_size,
        )
        return dest


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for extracting SQX building blocks catalog.

    Args:
        argv: Optional command-line arguments.

    Returns:
        0 on success, nonzero on failure.
    """
    parser = argparse.ArgumentParser(
        description="Extract SQX building blocks and indicator catalog to JSON."
    )
    parser.add_argument(
        "--sqx-root",
        type=Path,
        default=Path(r"C:\SQX-145"),
        help="Root path to StrategyQuant X reference installation.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/dev/evidence/sqx_blocks_catalog.json"),
        help="Target output path for the JSON catalog.",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable debug logging.",
    )

    args = parser.parse_args(argv)
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    if not args.sqx_root.exists():
        logger.error(
            "FR-TOOLS-SQX-BLOCKS-MANIFEST-PARSER: Specified SQX root does not exist: %s",
            args.sqx_root,
        )
        return 1

    extractor = SQXBlockExtractor(sqx_root=args.sqx_root, output_file=args.output)
    catalog = extractor.build_catalog()
    extractor.save_catalog(catalog)

    return 0


if __name__ == "__main__":
    sys.exit(main())
