"""Private immutable bases for canonical DATA contracts.

The bases preserve the validation behavior of the implemented DATA contract groups:
all are frozen and reject unknown fields, traced contracts validate request identity,
and the open variant permits arbitrary runtime types where existing schemas require
them.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, ValidationError, model_validator

from app.services.data.contracts.errors import DataError
from app.services.data.contracts.validation import validate_request_id
from app.utils import logger


class DataContractModel(BaseModel):
    """Map structural Pydantic failures to the stable DATA error taxonomy."""

    def __init__(self, **data: object) -> None:
        """Validate contract input.

        Args:
            **data: Field values supplied by the caller.

        Raises:
            DataError: If Pydantic rejects the supplied structure.
        """
        logger.debug("Validating DATA contract %s", type(self).__name__)
        try:
            super().__init__(**data)
        except ValidationError as error:
            raise DataError(
                "INVALID_INPUT",
                safe_details={"contract": type(self).__name__},
            ) from error


class FrozenContract(DataContractModel):
    """Immutable contract that forbids unknown fields and carries no trace policy."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class TracedContract(DataContractModel):
    """Immutable contract that validates any request identifier it carries."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    @model_validator(mode="after")
    def _validate_trace_identity(self) -> TracedContract:
        """Validate the carried request identifier.

        Returns:
            The validated contract instance.

        Raises:
            ValueError: If the request identifier violates trace policy.
        """
        logger.debug("Running DATA function: _validate_trace_identity")
        validate_request_id(getattr(self, "request_id", None))
        return self


class TracedOpenContract(TracedContract):
    """Traced immutable contract that additionally permits arbitrary field types."""

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid", frozen=True)


__all__: list[str] = []
