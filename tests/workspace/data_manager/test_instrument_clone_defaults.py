"""Tests for instrument clone defaults."""

import pytest
from app.core.lib.errors import DomainError
from app.workspace.data_manager.instrument_clone_defaults import (
    CloneBroker,
    CloneInstrumentDefaults,
    InstrumentBrokerRef,
)


def test_strips_one_matching_postfix() -> None:
    names = ["EURUSD-Demo"]
    instruments = [InstrumentBrokerRef(instrument="EURUSD-Demo", broker_id=7)]
    brokers = [CloneBroker(id=7, name="Demo", postfix="-Demo", mt_use=True)]

    result = CloneInstrumentDefaults.build(names, instruments, brokers)

    assert result.source_name == "EURUSD-Demo"
    assert result.clone_name == "EURUSDClone"
    assert result.broker_id == -1
    assert [b.id for b in result.choices] == [-1, 7]
    assert result.choices == (
        CloneBroker(id=-1, name="SQ default", postfix="", mt_use=True),
        CloneBroker(id=7, name="Demo", postfix="-Demo", mt_use=True),
    )


def test_multiple_instrument_matches_keep_suffix() -> None:
    names = ["EURUSD-Demo"]
    instruments = [
        InstrumentBrokerRef(instrument="EURUSD-Demo", broker_id=7),
        InstrumentBrokerRef(instrument="EURUSD-Demo", broker_id=7),
    ]
    brokers = [CloneBroker(id=7, name="Demo", postfix="-Demo", mt_use=True)]

    result = CloneInstrumentDefaults.build(names, instruments, brokers)

    assert result.source_name == "EURUSD-Demo"
    assert result.clone_name == "EURUSD-DemoClone"
    assert result.broker_id == -1


@pytest.mark.parametrize("postfix", ["", "-Other"])
def test_nonmatching_or_empty_postfix_keeps_name(postfix: str) -> None:
    names = ["EURUSD-Demo"]
    instruments = [InstrumentBrokerRef(instrument="EURUSD-Demo", broker_id=7)]
    brokers = [CloneBroker(id=7, name="Demo", postfix=postfix, mt_use=True)]

    result = CloneInstrumentDefaults.build(names, instruments, brokers)

    assert result.source_name == "EURUSD-Demo"
    assert result.clone_name == "EURUSD-DemoClone"
    assert result.broker_id == -1


def test_uses_first_selection() -> None:
    names = ["A", "B"]
    instruments: list[InstrumentBrokerRef] = []
    brokers: list[CloneBroker] = []

    result = CloneInstrumentDefaults.build(names, instruments, brokers)

    assert result.source_name == "A"
    assert result.clone_name == "AClone"
    assert result.broker_id == -1
    assert [b.id for b in result.choices] == [-1]
    assert result.choices == (
        CloneBroker(id=-1, name="SQ default", postfix="", mt_use=True),
    )


def test_excludes_unusable_broker_from_choices() -> None:
    names = ["EURUSD"]
    instruments: list[InstrumentBrokerRef] = []
    brokers = [
        CloneBroker(id=8, name="No", postfix="", mt_use=False),
        CloneBroker(id=7, name="Yes", postfix="", mt_use=True),
    ]

    result = CloneInstrumentDefaults.build(names, instruments, brokers)

    assert [b.id for b in result.choices] == [-1, 7]


def test_empty_selection_error() -> None:
    with pytest.raises(DomainError) as exc_info:
        CloneInstrumentDefaults.build([], [], [])

    err = exc_info.value
    assert err.code == "INSTRUMENT_SELECTION_REQUIRED"
    assert err.message == "You have to select some instrument."
    assert err.details == {}
