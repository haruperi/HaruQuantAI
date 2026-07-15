"""Private base that prevents Pydantic exceptions crossing DATA boundaries."""

from pydantic import BaseModel, ValidationError

from app.services.data.contracts.errors import DataError
from app.utils import logger


class DataContractModel(BaseModel):
    """Base model mapping structural failures to the stable DATA taxonomy."""

    def __init__(self, **data: object) -> None:
        """Validate model input and normalize third-party validation failures."""
        logger.debug("Validating DATA contract %s", type(self).__name__)
        try:
            super().__init__(**data)
        except ValidationError as error:
            raise DataError(
                "INVALID_INPUT",
                safe_details={"contract": type(self).__name__},
            ) from error


__all__: list[str] = []
