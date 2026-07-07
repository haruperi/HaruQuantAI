import pytest
from datetime import datetime, timezone, UTC

from app.utils.errors import ValidationError
from app.services.analytics._helpers import (
    validate_request_id_strict,
    to_float_list,
    to_trade_list,
    parse_utc_time,
)


class MockPandasSeries:
    def __init__(self, data):
        self.data = data
    def tolist(self):
        return self.data


class MockPandasDataFrame:
    def __init__(self, data):
        self.data = data
    def to_dict(self, orient):
        return self.data


class MockPydanticModel:
    def __init__(self, data):
        self.data = data
    def model_dump(self):
        return self.data


class MockDictObject:
    def __init__(self, data):
        self.__dict__ = data


def test_validate_request_id_strict():
    validate_request_id_strict(None)
    validate_request_id_strict("valid-id")
    
    with pytest.raises(ValidationError):
        validate_request_id_strict("")
    
    with pytest.raises(ValidationError):
        validate_request_id_strict("   ")
        
    with pytest.raises(ValidationError):
        validate_request_id_strict(123)


def test_to_float_list():
    assert to_float_list(None) == []
    assert to_float_list([1, 2, 3]) == [1.0, 2.0, 3.0]
    assert to_float_list(MockPandasSeries([1.5, 2.5])) == [1.5, 2.5]
    assert to_float_list("invalid") == []


def test_to_trade_list():
    assert to_trade_list(None) == []
    assert to_trade_list(MockPandasDataFrame([{"id": 1}])) == [{"id": 1}]
    
    dict_trade = {"id": 2}
    pydantic_trade = MockPydanticModel({"id": 3})
    dict_obj_trade = MockDictObject({"id": 4})
    tuple_trade = [("id", 5)]
    
    trades = [dict_trade, pydantic_trade, dict_obj_trade, tuple_trade]
    result = to_trade_list(trades)
    
    assert result == [{"id": 2}, {"id": 3}, {"id": 4}, {"id": 5}]
    assert to_trade_list("invalid") == []


def test_parse_utc_time():
    assert parse_utc_time(None) is None
    
    # datetime
    dt_naive = datetime(2026, 1, 1)
    assert parse_utc_time(dt_naive) == datetime(2026, 1, 1, tzinfo=UTC)
    
    dt_aware = datetime(2026, 1, 1, tzinfo=timezone.utc)
    assert parse_utc_time(dt_aware) == dt_aware
    
    # string
    assert parse_utc_time("2026-01-01T00:00:00Z") == datetime(2026, 1, 1, tzinfo=UTC)
    assert parse_utc_time("2026-01-01T00:00:00") == datetime(2026, 1, 1, tzinfo=UTC)
    assert parse_utc_time("invalid") is None
    
    # int / float
    assert parse_utc_time(0) == datetime(1970, 1, 1, tzinfo=UTC)
    assert parse_utc_time(0.0) == datetime(1970, 1, 1, tzinfo=UTC)
    assert parse_utc_time(10**20) is None
