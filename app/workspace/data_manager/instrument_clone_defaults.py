"""Instrument clone defaults builder for DataManagerInstruments."""

from collections.abc import Sequence
from dataclasses import dataclass

from app.core.lib.errors import DomainError


@dataclass(frozen=True)
class InstrumentBrokerRef:
    """Reference to an instrument and its associated broker ID."""

    instrument: str
    broker_id: int


@dataclass(frozen=True)
class CloneBroker:
    """Broker descriptor used for clone dialog options."""

    id: int
    name: str
    postfix: str
    mt_use: bool


@dataclass(frozen=True)
class CloneDefaults:
    """Initial defaults for the clone instrument dialog."""

    source_name: str
    clone_name: str
    broker_id: int
    choices: tuple[CloneBroker, ...]


class CloneInstrumentDefaults:
    """Builds clone dialog defaults from current selection and catalogues."""

    @staticmethod
    def build(
        selected_names: Sequence[str],
        instruments: Sequence[InstrumentBrokerRef],
        brokers: Sequence[CloneBroker],
    ) -> CloneDefaults:
        """Produce the initial values for the instrument clone dialog.

        Args:
            selected_names: Non-empty sequence of currently selected instrument names.
            instruments: Sequence of instrument-to-broker reference records.
            brokers: Sequence of known broker records.

        Returns:
            CloneDefaults containing source name, clone name, default broker ID (-1),
            and available broker choices.

        Raises:
            DomainError: If selected_names is empty.
        """
        if not selected_names:
            raise DomainError(
                code="INSTRUMENT_SELECTION_REQUIRED",
                message="You have to select some instrument.",
                details={},
            )

        source_name = selected_names[0]
        base_name = source_name

        matching_instruments = [
            inst for inst in instruments if inst.instrument == source_name
        ]
        if len(matching_instruments) == 1:
            matched_broker_id = matching_instruments[0].broker_id
            matching_brokers = [b for b in brokers if b.id == matched_broker_id]
            if len(matching_brokers) == 1:
                postfix = matching_brokers[0].postfix
                if postfix != "" and base_name.endswith(postfix):
                    base_name = base_name[: -len(postfix)]

        clone_name = f"{base_name}Clone"
        default_broker = CloneBroker(id=-1, name="SQ default", postfix="", mt_use=True)
        choices = (default_broker, *(b for b in brokers if b.mt_use))

        return CloneDefaults(
            source_name=source_name,
            clone_name=clone_name,
            broker_id=-1,
            choices=choices,
        )
