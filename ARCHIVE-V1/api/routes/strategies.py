"""Strategy routes for managing trading strategies."""

import json
import os
import tempfile
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any

from data.database import GovernanceRepository
from data.database.sqlite.database_operations import DatabaseManager
from data.strategies import storage
from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.services.utils import logger

router = APIRouter()
db_manager = DatabaseManager()

IMPORT_FILE = File(...)


def _canonical_json_hash(payload: Any) -> str:
    encoded = json.dumps(
        payload or {}, sort_keys=True, separators=(",", ":"), default=str
    )
    return sha256(encoded.encode("utf-8")).hexdigest()


def _code_hash(code: str) -> str:
    return sha256((code or "").encode("utf-8")).hexdigest()


def _governance_strategy_id(user_id: int, strategy_id: int) -> str:
    return f"strategy:{user_id}:{strategy_id}"


@dataclass(frozen=True)
class StrategyCatalogCreateRequest:
    name: str
    code: str
    description: str | None = None
    category: str | None = None
    parameters: dict[str, Any] | None = None
    parameter_types: dict[str, str] | None = None
    symbol: str | None = None
    timeframe: str | None = None
    strategy_type: str | None = None
    money_management: dict[str, Any] | None = None
    variables: dict[str, Any] | None = None
    variable_types: dict[str, str] | None = None


@dataclass(frozen=True)
class StrategyCatalogUpdateRequest:
    name: str | None = None
    description: str | None = None
    status: str | None = None
    category: str | None = None
    code: str | None = None
    parameters: dict[str, Any] | None = None
    parameter_types: dict[str, str] | None = None
    symbol: str | None = None
    timeframe: str | None = None
    strategy_type: str | None = None
    money_management: dict[str, Any] | None = None
    variables: dict[str, Any] | None = None
    variable_types: dict[str, str] | None = None
    changelog: str | None = None


class StrategyCatalogService:
    """Route-local service for strategy DB rows and versioned source artifacts."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        governance_repository: GovernanceRepository | None = None,
    ) -> None:
        self.db = db_manager
        self.storage = storage
        self.governance = governance_repository or GovernanceRepository(self.db.db_path)

    def create_strategy(
        self, request: StrategyCatalogCreateRequest, *, user_id: int
    ) -> dict[str, Any]:
        if not request.name.strip():
            raise ValueError("Strategy name is required.")
        if not request.code:
            raise ValueError("Strategy code is required.")

        strategy_id = self.db.create_strategy(
            user_id=user_id,
            name=request.name,
            description=request.description,
            category=request.category,
            status="inactive",
            is_public=False,
        )
        username = self._username_for(user_id)
        family = self._strategy_family(request.category)
        gov_id = _governance_strategy_id(user_id, strategy_id)
        version = "1.0.0"
        file_path = self.storage.save_strategy(
            user_id=user_id,
            strategy_id=strategy_id,
            version=version,
            code=request.code,
            parameters=request.parameters or {},
            username=username,
            strategy_name=request.name,
            metadata=self._metadata_from_create(request),
        )
        self.db.create_strategy_version(
            strategy_id=strategy_id,
            version=version,
            file_path=file_path,
            parameters=request.parameters or {},
            changelog="Initial version",
            created_by=user_id,
        )
        artifact_root = self.storage.get_strategy_artifact_root(
            user_id=user_id,
            strategy_id=strategy_id,
            username=username,
            strategy_name=request.name,
        )
        self._update_catalog_fields(
            strategy_id,
            governance_strategy_id=gov_id,
            artifact_root=artifact_root,
            strategy_family=family,
        )
        governance = self._upsert_governance(
            strategy_id=strategy_id,
            user_id=user_id,
            strategy_name=request.name,
            strategy_family=family,
            code=request.code,
            parameters=request.parameters or {},
        )
        strategy = self.get_strategy(strategy_id, user_id=user_id)
        strategy.update(self._governance_projection(governance))
        return strategy

    def list_strategies(
        self,
        *,
        user_id: int,
        status: str | None = None,
        category: str | None = None,
        include_shared: bool = False,
    ) -> list[dict[str, Any]]:
        rows = self.db.get_user_strategies(
            user_id=user_id,
            status=status,
            category=category,
            include_shared=include_shared,
        )
        return [self._enrich_with_governance(row) for row in rows]

    def get_strategy(
        self, strategy_id: int, *, user_id: int | None = None
    ) -> dict[str, Any]:
        strategy = self.db.get_strategy(strategy_id)
        if not strategy:
            raise LookupError(f"Strategy {strategy_id} not found")
        self._assert_owner(strategy, user_id)
        return self._enrich_with_governance(strategy)

    def update_strategy(
        self,
        strategy_id: int,
        request: StrategyCatalogUpdateRequest,
        *,
        user_id: int,
    ) -> dict[str, Any]:
        current = self.get_strategy(strategy_id, user_id=user_id)
        update_fields: dict[str, Any] = {}
        if request.name:
            update_fields["name"] = request.name
        if request.description is not None:
            update_fields["description"] = request.description
        if request.status:
            update_fields["status"] = request.status
        if request.category:
            update_fields["category"] = request.category
            update_fields["strategy_family"] = self._strategy_family(request.category)
        if update_fields:
            self.db.update_strategy(strategy_id, **update_fields)

        if request.code:
            strategy_name = request.name or str(current["name"])
            parameters = request.parameters if request.parameters is not None else {}
            self.create_strategy_version(
                strategy_id=strategy_id,
                code=request.code,
                parameters=parameters,
                user_id=user_id,
                strategy_name=strategy_name,
                metadata=self._metadata_from_update(request, strategy_name),
                changelog=request.changelog or "Updated via editor",
            )
            updated = self.get_strategy(strategy_id, user_id=user_id)
            self._upsert_governance(
                strategy_id=strategy_id,
                user_id=user_id,
                strategy_name=str(updated["name"]),
                strategy_family=self._strategy_family(
                    updated.get("strategy_family") or updated.get("category")
                ),
                code=request.code,
                parameters=parameters,
            )
        return self.get_strategy(strategy_id, user_id=user_id)

    def create_strategy_version(
        self,
        *,
        strategy_id: int,
        code: str,
        parameters: dict[str, Any] | None,
        user_id: int,
        strategy_name: str,
        metadata: dict[str, Any],
        changelog: str | None,
        major_bump: bool = False,
    ) -> str:
        username = self._username_for(user_id)
        new_version = self._next_version(
            self.db.get_strategy_versions(strategy_id),
            major_bump=major_bump,
        )
        file_path = self.storage.save_strategy(
            user_id=user_id,
            strategy_id=strategy_id,
            version=new_version,
            code=code,
            parameters=parameters or {},
            username=username,
            strategy_name=strategy_name,
            metadata=metadata,
        )
        self.db.create_strategy_version(
            strategy_id=strategy_id,
            version=new_version,
            file_path=file_path,
            parameters=parameters or {},
            changelog=changelog,
            created_by=user_id,
        )
        artifact_root = self.storage.get_strategy_artifact_root(
            user_id=user_id,
            strategy_id=strategy_id,
            username=username,
            strategy_name=strategy_name,
        )
        self._update_catalog_fields(strategy_id, artifact_root=artifact_root)
        return new_version

    def delete_strategy(self, strategy_id: int, *, user_id: int) -> None:
        strategy = self.get_strategy(strategy_id, user_id=user_id)
        username = self._username_for(user_id)
        if not self.db.delete_strategy(strategy_id):
            raise LookupError(f"Strategy {strategy_id} not found")
        self.storage.delete_strategy(
            user_id=user_id,
            strategy_id=strategy_id,
            username=username,
            strategy_name=str(strategy["name"]),
        )

    def list_versions(self, strategy_id: int) -> list[dict[str, Any]]:
        return self.db.get_strategy_versions(strategy_id)

    def get_version_code(
        self, *, strategy_id: int, version_id: int, user_id: int
    ) -> dict[str, Any]:
        version = self.db.get_strategy_version(version_id)
        if version is None:
            raise LookupError(f"Strategy version {version_id} not found")
        strategy = self.get_strategy(strategy_id, user_id=user_id)
        file_path = version.get("file_path")
        metadata: dict[str, Any] = {}
        code: str | None = None
        if file_path and Path(str(file_path)).exists():
            strategy_file = Path(str(file_path))
            code = strategy_file.read_text(encoding="utf-8")
            metadata = self._load_metadata_from_file_path(strategy_file)
        else:
            username = self._username_for(user_id)
            code = self.storage.load_strategy_code(
                user_id=user_id,
                strategy_id=strategy_id,
                version=str(version["version"]),
                username=username,
                strategy_name=str(strategy["name"]),
            )
            metadata = self.storage.load_strategy_metadata(
                user_id=user_id,
                strategy_id=strategy_id,
                version=str(version["version"]),
                username=username,
                strategy_name=str(strategy["name"]),
            )
        return {
            "version_id": version_id,
            "version": version["version"],
            "code": code,
            "parameters": version.get("parameters") or {},
            "symbol": metadata.get("symbol"),
            "timeframe": metadata.get("timeframe"),
            "type": metadata.get("type"),
            "parameterTypes": metadata.get("parameterTypes"),
            "moneyManagement": metadata.get("moneyManagement"),
            "variables": metadata.get("variables"),
            "variableTypes": metadata.get("variableTypes"),
        }

    def rollback_version(
        self, *, strategy_id: int, version_id: int, user_id: int
    ) -> None:
        self.get_strategy(strategy_id, user_id=user_id)
        version = self.db.get_strategy_version(version_id)
        if version is None or int(version["strategy_id"]) != strategy_id:
            raise LookupError(
                f"Strategy version {version_id} not found for strategy {strategy_id}"
            )
        self.db.update_strategy(strategy_id, active_version_id=version_id)

    def export_strategy(self, *, strategy_id: int, user_id: int) -> str:
        strategy = self.get_strategy(strategy_id, user_id=user_id)
        active_version = strategy.get("active_version")
        if not active_version:
            raise LookupError(f"Strategy {strategy_id} has no active version")
        username = self._username_for(user_id)
        export_path = str(
            Path(tempfile.gettempdir())
            / f"strategy_{strategy_id}_v{active_version}.zip"
        )
        return self.storage.export_strategy(
            user_id=user_id,
            strategy_id=strategy_id,
            version=str(active_version),
            export_path=export_path,
            username=username,
            strategy_name=str(strategy["name"]),
        )

    def import_strategy(
        self,
        *,
        strategy_id: int,
        import_path: str,
        original_filename: str,
        user_id: int,
    ) -> str:
        strategy = self.get_strategy(strategy_id, user_id=user_id)
        username = self._username_for(user_id)
        new_version = self._next_version(
            self.db.get_strategy_versions(strategy_id), major_bump=True
        )
        strategy_name = str(strategy["name"])
        file_path = self.storage.import_strategy(
            user_id=user_id,
            strategy_id=strategy_id,
            version=new_version,
            import_path=import_path,
            username=username,
            strategy_name=strategy_name,
        )
        metadata = self.storage.load_strategy_metadata(
            user_id=user_id,
            strategy_id=strategy_id,
            version=new_version,
            username=username,
            strategy_name=strategy_name,
        )
        parameters = metadata.get("parameters", {})
        self.db.create_strategy_version(
            strategy_id=strategy_id,
            version=new_version,
            file_path=file_path,
            parameters=parameters,
            changelog=f"Imported from {original_filename}",
            created_by=user_id,
        )
        imported_code = Path(file_path).read_text(encoding="utf-8")
        self._upsert_governance(
            strategy_id=strategy_id,
            user_id=user_id,
            strategy_name=strategy_name,
            strategy_family=self._strategy_family(
                strategy.get("strategy_family") or strategy.get("category")
            ),
            code=imported_code,
            parameters=parameters,
        )
        return new_version

    def _upsert_governance(
        self,
        *,
        strategy_id: int,
        user_id: int,
        strategy_name: str,
        strategy_family: str,
        code: str,
        parameters: dict[str, Any] | None,
    ):
        return self.governance.upsert_strategy(
            strategy_id=_governance_strategy_id(user_id, strategy_id),
            strategy_name=strategy_name,
            strategy_family=strategy_family,
            current_lifecycle_state="RESEARCH",
            code_hash=_code_hash(code),
            parameter_hash=_canonical_json_hash(parameters or {}),
            owner_id=str(user_id),
        )

    def _enrich_with_governance(self, strategy: dict[str, Any]) -> dict[str, Any]:
        enriched = dict(strategy)
        gov_id = enriched.get("governance_strategy_id") or _governance_strategy_id(
            int(enriched["user_id"]),
            int(enriched["id"]),
        )
        enriched["governance_strategy_id"] = gov_id
        governance = self.governance.get_strategy(str(gov_id))
        if governance:
            enriched.update(self._governance_projection(governance))
        return enriched

    @staticmethod
    def _governance_projection(governance) -> dict[str, Any]:
        return {
            "governance_strategy_id": governance.strategy_id,
            "lifecycle_state": governance.current_lifecycle_state,
            "code_hash": governance.code_hash,
            "parameter_hash": governance.parameter_hash,
            "strategy_family": governance.strategy_family,
        }

    def _username_for(self, user_id: int) -> str:
        user = self.db.get_user(user_id=user_id)
        return str((user.get("username") if user else None) or f"user_{user_id}")

    @staticmethod
    def _assert_owner(strategy: dict[str, Any], user_id: int | None) -> None:
        if user_id is not None and int(strategy["user_id"]) != int(user_id):
            raise PermissionError(
                f"User {user_id} does not own strategy {strategy['id']}"
            )

    @staticmethod
    def _strategy_family(value: Any | None) -> str:
        text = str(value or "").strip()
        return text or "custom"

    def _update_catalog_fields(self, strategy_id: int, **fields: Any) -> None:
        clean = {key: value for key, value in fields.items() if value is not None}
        if clean:
            self.db.update_strategy(strategy_id, **clean)

    @staticmethod
    def _metadata_from_create(request: StrategyCatalogCreateRequest) -> dict[str, Any]:
        return {
            "name": request.name,
            "description": request.description,
            "symbol": request.symbol,
            "timeframe": request.timeframe,
            "type": request.strategy_type,
            "parameterTypes": request.parameter_types,
            "moneyManagement": request.money_management,
            "variables": request.variables,
            "variableTypes": request.variable_types,
        }

    @staticmethod
    def _metadata_from_update(
        request: StrategyCatalogUpdateRequest, strategy_name: str
    ) -> dict[str, Any]:
        return {
            "name": request.name or strategy_name,
            "description": request.description,
            "symbol": request.symbol,
            "timeframe": request.timeframe,
            "type": request.strategy_type,
            "parameterTypes": request.parameter_types,
            "moneyManagement": request.money_management,
            "variables": request.variables,
            "variableTypes": request.variable_types,
            "changelog": request.changelog,
        }

    @staticmethod
    def _load_metadata_from_file_path(strategy_file: Path) -> dict[str, Any]:
        metadata_file = strategy_file.parent / "metadata.json"
        if not metadata_file.exists():
            return {}
        return json.loads(metadata_file.read_text(encoding="utf-8"))

    @staticmethod
    def _next_version(
        versions: list[dict[str, Any]], *, major_bump: bool = False
    ) -> str:
        if not versions:
            return "1.0.0"
        major, minor, patch = (
            int(part) for part in str(versions[0]["version"]).split(".")
        )
        if major_bump:
            return f"{major + 1}.0.0"
        return f"{major}.{minor}.{patch + 1}"


catalog = StrategyCatalogService(db_manager=db_manager)


# Pydantic models for request/response
class StrategyCreateRequest(BaseModel):
    """Request payload for creating a strategy."""

    name: str
    description: str | None = None
    category: str | None = None
    code: str
    parameters: dict[str, Any] | None = None
    parameterTypes: dict[str, str] | None = None
    symbol: str | None = None
    timeframe: str | None = None
    type: str | None = None
    moneyManagement: dict[str, Any] | None = None
    variables: dict[str, Any] | None = None
    variableTypes: dict[str, str] | None = None


class StrategyUpdateRequest(BaseModel):
    """Request payload for updating a strategy."""

    name: str | None = None
    description: str | None = None
    status: str | None = None
    category: str | None = None
    code: str | None = None
    parameters: dict[str, Any] | None = None
    parameterTypes: dict[str, str] | None = None
    symbol: str | None = None
    timeframe: str | None = None
    type: str | None = None
    moneyManagement: dict[str, Any] | None = None
    variables: dict[str, Any] | None = None
    variableTypes: dict[str, str] | None = None
    changelog: str | None = None


class StrategyResponse(BaseModel):
    """Response model for strategy metadata."""

    id: int
    user_id: int
    name: str
    description: str | None
    status: str
    category: str | None
    is_public: bool
    active_version: str | None
    active_version_id: int | None
    governance_strategy_id: str | None = None
    lifecycle_state: str | None = None
    code_hash: str | None = None
    parameter_hash: str | None = None
    artifact_root: str | None = None
    strategy_family: str | None = None
    created_at: str
    updated_at: str


class VersionResponse(BaseModel):
    """Response model for strategy versions."""

    id: int
    strategy_id: int
    version: str
    parameters: dict[str, Any]
    changelog: str | None
    created_at: str


class PerformanceSummaryRequest(BaseModel):
    """Request payload for summarizing performance."""

    trades: list[dict[str, Any]]
    initial_balance: float = 10000.0


def _build_strategy_update_fields(request: StrategyUpdateRequest) -> dict[str, Any]:
    update_fields: dict[str, Any] = {}
    if request.name:
        update_fields["name"] = request.name
    if request.description is not None:
        update_fields["description"] = request.description
    if request.status:
        update_fields["status"] = request.status
    if request.category:
        update_fields["category"] = request.category
    return update_fields


def _next_strategy_version(db_versions: list[dict[str, Any]]) -> str:
    if not db_versions:
        return "1.0.0"

    last_version = db_versions[0]["version"]
    major, minor, patch = map(int, last_version.split("."))
    return f"{major}.{minor}.{patch + 1}"


def _create_strategy_version(
    strategy_id: int,
    request: StrategyUpdateRequest,
    user_id: int,
    username: str,
    strategy_name: str,
):
    db_versions = db_manager.get_strategy_versions(strategy_id)
    new_version = _next_strategy_version(db_versions)

    file_path = storage.save_strategy(
        user_id=user_id,
        strategy_id=strategy_id,
        version=new_version,
        code=request.code or "",
        parameters=request.parameters or {},
        username=username,
        strategy_name=strategy_name,
        metadata={
            "name": request.name or strategy_name,
            "description": request.description,
            "symbol": request.symbol,
            "timeframe": request.timeframe,
            "type": request.type,
            "parameterTypes": request.parameterTypes,
            "moneyManagement": request.moneyManagement,
            "variables": request.variables,
            "variableTypes": request.variableTypes,
            "changelog": request.changelog or f"Updated to v{new_version}",
        },
    )

    db_manager.create_strategy_version(
        strategy_id=strategy_id,
        version=new_version,
        file_path=file_path,
        parameters=request.parameters,
        changelog=request.changelog,
        created_by=user_id,
    )

    return new_version


def _load_strategy_class(
    user_id: int, strategy_id: int, version_id: int
) -> tuple[dict[str, Any], Any]:
    version = db_manager.get_strategy_version(version_id)
    strategy = db_manager.get_strategy(strategy_id)
    if version is None:
        raise ValueError(f"Strategy version {version_id} not found")
    if strategy is None:
        raise ValueError(f"Strategy {strategy_id} not found")

    user = db_manager.get_user(user_id=user_id)
    username = (user.get("username") if user else "") or ""
    strategy_name = (strategy.get("name") if strategy else "") or ""

    strategy_class = storage.load_strategy_class(
        user_id=user_id,
        strategy_id=strategy_id,
        version=version["version"],
        username=username,
        strategy_name=strategy_name,
    )

    return version, strategy_class


# Template endpoints
@router.get("/templates/{template_name}")
async def get_strategy_template(template_name: str) -> dict[str, str]:
    """
    Get a strategy template by name.

    Available templates:
    - empty: Empty strategy template with TODO comments
    - trend_following: EMA crossover trend following strategy
    """
    try:
        # Map template names to files
        template_map = {
            "empty": "template_strategy.py",
            "trend_following": "template_strategy.py",
        }

        if template_name not in template_map:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template '{template_name}' not found. Available: {list(template_map.keys())}",
            )

        # Get template file path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, "../../.."))
        template_file = os.path.join(
            project_root,
            "services",
            "strategy",
            "templates",
            template_map[template_name],
        )

        # Read template content
        if not os.path.exists(template_file):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template file not found: {template_file}",
            )

        with open(template_file, encoding="utf-8") as f:
            code = f.read()

        logger.info(f"Serving template: {template_name}")

        return {
            "template_name": template_name,
            "code": code,
            "description": f"{template_name.replace('_', ' ').title()} Strategy Template",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading template '{template_name}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load template: {e!s}",
        )


# Strategy CRUD endpoints
@router.post("/", response_model=StrategyResponse, status_code=status.HTTP_201_CREATED)
async def create_strategy(
    request: StrategyCreateRequest, user_id: int = 1
) -> StrategyResponse:
    """
    Create a new strategy.

    Note: In production, user_id would come from authentication token.
    For now, defaulting to user_id=1 for testing.
    """
    try:
        logger.info(f"Creating strategy: {request.name} for user {user_id}")
        strategy = catalog.create_strategy(
            StrategyCatalogCreateRequest(
                name=request.name,
                description=request.description,
                category=request.category,
                code=request.code,
                parameters=request.parameters,
                parameter_types=request.parameterTypes,
                symbol=request.symbol,
                timeframe=request.timeframe,
                strategy_type=request.type,
                money_management=request.moneyManagement,
                variables=request.variables,
                variable_types=request.variableTypes,
            ),
            user_id=user_id,
        )
        logger.info(f"Strategy created successfully: ID={strategy['id']}")
        return StrategyResponse(**strategy)

    except Exception as e:
        logger.error(f"Error creating strategy: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create strategy: {e!s}",
        )


@router.get("/", response_model=list[StrategyResponse])
async def list_strategies(
    user_id: int = 1,
    strategy_status: str | None = None,
    category: str | None = None,
    include_shared: bool = False,
) -> list[StrategyResponse]:
    """List all strategies for a user."""
    try:
        strategies = catalog.list_strategies(
            user_id=user_id,
            status=strategy_status,
            category=category,
        )

        return [StrategyResponse(**s) for s in strategies]

    except Exception as e:
        logger.error(f"Error listing strategies: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list strategies: {e!s}",
        )


@router.get("/{strategy_id}", response_model=StrategyResponse)
async def get_strategy(strategy_id: int) -> StrategyResponse:
    """Get a specific strategy."""
    try:
        strategy = catalog.get_strategy(strategy_id)

        return StrategyResponse(**strategy)

    except LookupError as e:
        logger.warning(str(e))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting strategy: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get strategy: {e!s}",
        )


@router.put("/{strategy_id}", response_model=StrategyResponse)
async def update_strategy(
    strategy_id: int, request: StrategyUpdateRequest, user_id: int = 1
) -> StrategyResponse:
    """
    Update a strategy.

    If code is provided, creates a new version.
    """
    try:
        updated_strategy = catalog.update_strategy(
            strategy_id,
            StrategyCatalogUpdateRequest(
                name=request.name,
                description=request.description,
                status=request.status,
                category=request.category,
                code=request.code,
                parameters=request.parameters,
                parameter_types=request.parameterTypes,
                symbol=request.symbol,
                timeframe=request.timeframe,
                strategy_type=request.type,
                money_management=request.moneyManagement,
                variables=request.variables,
                variable_types=request.variableTypes,
                changelog=request.changelog,
            ),
            user_id=user_id,
        )

        return StrategyResponse(**updated_strategy)

    except LookupError as e:
        logger.warning(str(e))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except PermissionError as e:
        logger.warning(str(e))
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        ) from e
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating strategy: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update strategy: {e!s}",
        )


@router.delete("/{strategy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_strategy(strategy_id: int, user_id: int = 1) -> None:
    """Delete a strategy and all its versions."""
    try:
        catalog.delete_strategy(strategy_id, user_id=user_id)

        logger.info(f"Strategy {strategy_id} deleted successfully")

    except LookupError as e:
        logger.warning(str(e))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except PermissionError as e:
        logger.warning(str(e))
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        ) from e
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting strategy: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete strategy: {e!s}",
        )


# Version endpoints
@router.get("/{strategy_id}/versions", response_model=list[VersionResponse])
async def list_versions(strategy_id: int) -> list[VersionResponse]:
    """List all versions of a strategy."""
    try:
        versions = catalog.list_versions(strategy_id)
        return [VersionResponse(**v) for v in versions]

    except Exception as e:
        logger.error(f"Error listing versions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list versions: {e!s}",
        )


@router.get("/{strategy_id}/versions/{version_id}/code")
async def get_version_code(
    strategy_id: int, version_id: int, user_id: int = 1
) -> dict[str, Any]:
    """Get the code for a specific version."""
    try:
        return catalog.get_version_code(
            strategy_id=strategy_id,
            version_id=version_id,
            user_id=user_id,
        )

    except LookupError as e:
        logger.warning(str(e))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except FileNotFoundError as e:
        logger.warning(str(e))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except PermissionError as e:
        logger.warning(str(e))
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        ) from e
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting version code: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get version code: {e!s}",
        )


@router.post("/{strategy_id}/versions/{version_id}/rollback")
async def rollback_version(
    strategy_id: int, version_id: int, user_id: int = 1
) -> dict[str, str]:
    """Rollback to a specific version (make it the active version)."""
    try:
        catalog.rollback_version(
            strategy_id=strategy_id,
            version_id=version_id,
            user_id=user_id,
        )

        logger.info(f"Strategy {strategy_id} rolled back to version {version_id}")

        return {"message": "Version rolled back successfully"}

    except LookupError as e:
        logger.warning(str(e))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except PermissionError as e:
        logger.warning(str(e))
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"Error rolling back version: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to rollback version: {e!s}",
        )


# Export/Import endpoints
@router.post("/{strategy_id}/export")
async def export_strategy(strategy_id: int, user_id: int = 1) -> FileResponse:
    """Export strategy as a zip file."""
    try:
        zip_path = catalog.export_strategy(strategy_id=strategy_id, user_id=user_id)
        return FileResponse(
            zip_path, media_type="application/zip", filename=os.path.basename(zip_path)
        )

    except LookupError as e:
        logger.warning(str(e))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except PermissionError as e:
        logger.warning(str(e))
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        ) from e
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting strategy: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export strategy: {e!s}",
        )


@router.post("/{strategy_id}/import")
async def import_strategy(
    strategy_id: int, file: UploadFile = IMPORT_FILE, user_id: int = 1
) -> dict[str, str]:
    """Import strategy from a zip file."""
    try:
        # Save uploaded file to temp location
        temp_dir = tempfile.gettempdir()
        import_path = os.path.join(temp_dir, file.filename or "unknown.zip")

        with open(import_path, "wb") as f:
            content = await file.read()
            f.write(content)

        new_version = catalog.import_strategy(
            strategy_id=strategy_id,
            import_path=import_path,
            original_filename=file.filename or "unknown.zip",
            user_id=user_id,
        )
        logger.info(f"Strategy version created from import: {file.filename}")

        # Clean up temp file
        os.remove(import_path)

        logger.info(f"Strategy imported: version {new_version}")

        return {"message": "Strategy imported successfully", "version": new_version}

    except LookupError as e:
        logger.warning(str(e))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except PermissionError as e:
        logger.warning(str(e))
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        ) from e
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing strategy: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import strategy: {e!s}",
        )
