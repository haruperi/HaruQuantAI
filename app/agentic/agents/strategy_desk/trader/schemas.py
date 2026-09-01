"""Non-executable trade proposals and the receipts they come back with.

`TradeProposal` carries the nine things `FR-AGENTIC-058` names — thesis,
instrument, direction, horizon, invalidation, evidence, uncertainty, evaluation
request, and expiry — and nothing a broker could act on. The prohibition is by
absence: no price, quantity, lot size, notional, stop, target, order type,
venue, or account field exists on the model, so there is no value in a proposal
that an execution path could consume even if the object were mishandled.

`TradeProposalReceipt` records what the receiver said and refuses to say more
(`FR-AGENTIC-060`). Its status comes from Strategy's own enumeration, the most
favourable of which is `accepted_for_evaluation` — a receipt cannot express a
fill, an order, or a position because there is no field for one. When the
receiver produced a canonical intent, the receipt records that it exists and
its identity, never its contents: an intent is Strategy's object, and copying
its fields here is how a proposal starts looking like an order.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timedelta
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.agentic.deliberation.models import reject_authorization_language
from app.composition.logging import get_logger
from app.kernel.serialization import canonical_digest

logger = get_logger(__name__)

_MAX_TEXT = 2_000
_MAX_SHORT_TEXT = 200
_MAX_ITEMS = 32

# A statement shorter than this is not a statement. Low enough to catch "n/a"
# and "none", not brevity.
_MIN_STATEMENT_TEXT = 24

# The receiver bounds a proposal's horizon at thirty-one days. Declaring the
# same bound here means a proposal this domain builds cannot fail Strategy on a
# constraint we could have checked before submitting.
MAX_HORIZON_SECONDS = 31 * 24 * 60 * 60

type ProposalDirection = Literal["BUY", "SELL"]

# Passed through to the receiver verbatim. Agentic never widens the scope a
# caller asked for.
type EvaluationScope = Literal["SIGNAL_ONLY", "TRADE_INTENT_IF_SUPPORTED"]

# Strategy's own enumeration, carried verbatim. `accepted_for_evaluation` is
# the most a receipt can say; there is no value here that means "filled".
type ReceiptStatus = Literal[
    "accepted_for_evaluation",
    "rejected",
    "expired",
    "no_signal",
]

# Field names that would make a proposal executable, or a receipt into order
# truth. No model here defines one; the tuple states the intent so a later
# change has to argue with it, and tests assert both the field sets and the
# module source stay clear of them.
FORBIDDEN_BROKER_FIELDS: tuple[str, ...] = (
    "account",
    "account_id",
    "entry_price",
    "fill",
    "fill_price",
    "filled",
    "limit_price",
    "lot_size",
    "lots",
    "notional",
    "order_id",
    "order_type",
    "position",
    "position_size",
    "price",
    "quantity",
    "sl",
    "stop_loss",
    "take_profit",
    "tp",
    "units",
    "venue",
    "volume",
)


def _text(value: str, field: str, *, limit: int = _MAX_TEXT) -> str:
    """Validate bounded non-empty trimmed text.

    Args:
        value: Candidate text.
        field: Safe field label for validation.
        limit: Maximum permitted character count.

    Returns:
        Validated text.

    Raises:
        ValueError: If the text is empty, untrimmed, or oversized.
    """
    if not value or value != value.strip():
        message = f"{field} must be non-empty trimmed text"
        raise ValueError(message)
    if len(value) > limit:
        message = f"{field} must not exceed {limit} characters"
        raise ValueError(message)
    return value


def _proposal_text(value: str, field: str) -> str:
    """Validate text that must describe a view rather than instruct a trade.

    `FEAT-AGT-07` owns what reads as an authorization and is reused rather than
    restated. This adds only the broker vocabulary a trader must never emit.

    Args:
        value: Candidate text.
        field: Safe field label for validation.

    Returns:
        The validated text.

    Raises:
        ValueError: If the text names an executable level, size, or venue.
    """
    checked = reject_authorization_language(_text(value, field), field)
    lowered = checked.lower()
    for phrase in _EXECUTABLE_PHRASES:
        if phrase in lowered:
            message = (
                f"{field} must not name an executable level, size, or venue; a "
                "proposal describes a view, not an order"
            )
            raise ValueError(message)
    return checked


# Vocabulary that turns a described view into an instruction. Naming an entry
# price authorizes nothing in the deliberation sense, but it produces a value
# an execution path could consume, which a proposal must never contain.
_EXECUTABLE_PHRASES: tuple[str, ...] = (
    "buy at",
    "entry at",
    "entry price",
    "limit order",
    "lot size",
    "market order",
    "sell at",
    "stop loss",
    "stop-loss",
    "take profit",
    "take-profit",
    "units of",
)


def _entries(
    value: tuple[str, ...],
    field: str,
    *,
    required: bool = False,
    unique: bool = False,
) -> tuple[str, ...]:
    """Validate one bounded tuple of proposal statements.

    Args:
        value: Candidate entries.
        field: Safe field label for validation.
        required: Whether the tuple must carry at least one entry.
        unique: Whether duplicate entries are rejected.

    Returns:
        Validated entries.

    Raises:
        ValueError: If the tuple is empty when required, oversized, or carries
            a duplicate when uniqueness is required.
    """
    if required and not value:
        message = f"{field} is required"
        raise ValueError(message)
    if len(value) > _MAX_ITEMS:
        message = f"{field} must not exceed {_MAX_ITEMS} entries"
        raise ValueError(message)
    validated = tuple(_proposal_text(item, field) for item in value)
    # The receiver rejects duplicated evidence references outright, so a
    # duplicate is caught here rather than at the boundary.
    if unique and len(set(validated)) != len(validated):
        message = f"{field} entries must be unique"
        raise ValueError(message)
    return validated


class TradeProposal(BaseModel):
    """One non-executable view submitted for deterministic evaluation.

    Attributes:
        proposal_id: Stable proposal identity.
        task_id: Owning task identity.
        thesis_id: Strategy thesis this proposal rests on.
        strategy_id: Registered strategy the receiver should evaluate against.
        strategy_version: Exact registered version.
        instrument: Instrument the view concerns.
        direction: Direction of the view.
        horizon_seconds: How long the view is claimed to hold.
        rationale: Why the thesis supports the view.
        invalidation: What would show the view to be wrong.
        evidence_refs: Evidence references the view rests on.
        uncertainty: What the evidence cannot establish.
        evaluation_scope: What the proposal asks the receiver to do.
        issued_at: Issue instant, as an ISO-8601 UTC string.
        expires_at: Expiry instant, as an ISO-8601 UTC string.
        content_hash: Derived digest over the whole proposal.
    """

    model_config = ConfigDict(
        allow_inf_nan=False,
        extra="forbid",
        frozen=True,
        strict=True,
    )

    proposal_id: str
    task_id: str
    thesis_id: str
    strategy_id: str
    strategy_version: str
    instrument: str
    direction: ProposalDirection
    horizon_seconds: int
    rationale: str
    invalidation: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    uncertainty: str
    evaluation_scope: EvaluationScope
    issued_at: str
    expires_at: str
    content_hash: str

    @field_validator(
        "proposal_id",
        "task_id",
        "thesis_id",
        "strategy_id",
        "strategy_version",
        "instrument",
        "issued_at",
        "expires_at",
        "content_hash",
    )
    @classmethod
    def _validate_reference(cls, value: str) -> str:
        """Validate one required proposal reference.

        Args:
            value: Candidate reference.

        Returns:
            Validated reference.
        """
        return _text(value, "proposal reference", limit=_MAX_SHORT_TEXT)

    @field_validator("horizon_seconds")
    @classmethod
    def _validate_horizon(cls, value: int) -> int:
        """Validate the declared horizon against the receiver's own bound.

        Args:
            value: Candidate horizon.

        Returns:
            Validated horizon.

        Raises:
            ValueError: If the horizon is not positive or exceeds the bound.
        """
        if value <= 0:
            message = "a proposal horizon must be positive"
            raise ValueError(message)
        if value > MAX_HORIZON_SECONDS:
            message = (
                f"a proposal horizon must not exceed {MAX_HORIZON_SECONDS} "
                "seconds, the receiver's own bound"
            )
            raise ValueError(message)
        return value

    @field_validator("rationale", "uncertainty")
    @classmethod
    def _validate_statement(cls, value: str) -> str:
        """Validate one required proposal statement.

        Args:
            value: Candidate statement.

        Returns:
            Validated statement.

        Raises:
            ValueError: If the statement is too short to be one.
        """
        checked = _proposal_text(value, "proposal statement")
        if len(checked) < _MIN_STATEMENT_TEXT:
            message = (
                "a proposal statement must say what was considered; state it or refuse"
            )
            raise ValueError(message)
        return checked

    @field_validator("invalidation", "evidence_refs")
    @classmethod
    def _validate_required_entries(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate one required unique proposal tuple.

        Args:
            value: Candidate entries.

        Returns:
            Validated entries.
        """
        return _entries(value, "proposal entry", required=True, unique=True)

    @model_validator(mode="after")
    def _validate_window(self) -> Self:
        """Validate the proposal lifetime against its declared horizon.

        The receiver requires expiry to follow the request time and to fall
        within the declared horizon. Checking it here means a proposal this
        domain builds cannot fail Strategy on a rule we could have applied.

        Returns:
            The validated proposal.

        Raises:
            ValueError: If either instant is unreadable, or the window is
                empty or exceeds the horizon.
        """
        issued = _instant(self.issued_at, "issued_at")
        expires = _instant(self.expires_at, "expires_at")
        if expires <= issued:
            message = (
                "a trade proposal must expire strictly after it was issued; "
                f"{self.expires_at} does not follow {self.issued_at}"
            )
            raise ValueError(message)
        if expires > issued + timedelta(seconds=self.horizon_seconds):
            message = (
                "a trade proposal must not outlive its declared horizon of "
                f"{self.horizon_seconds} seconds"
            )
            raise ValueError(message)
        return self

    def is_expired(self, at_time: datetime) -> bool:
        """Report whether the proposal has passed its own expiry.

        Args:
            at_time: Instant to judge the proposal at.

        Returns:
            True when the proposal is no longer current.
        """
        return at_time >= _instant(self.expires_at, "expires_at")


class TradeProposalReceipt(BaseModel):
    """What the receiver said about one proposal, and nothing more.

    Attributes:
        receipt_id: Stable receipt identity.
        task_id: Owning task identity.
        proposal_id: Proposal this receipt answers.
        proposal_content_hash: Digest of the proposal as submitted.
        evaluation_request_id: Receiver-derived request identity.
        status: The receiver's own enumerated outcome, carried verbatim.
        reason_codes: The receiver's own reason codes, carried verbatim.
        intent_produced: Whether the receiver constructed a canonical intent.
        intent_ref: Identity of that intent, never its contents.
        signals_evaluated: How many signals the receiver evaluated.
        audit_event_ref: The receiver's audit reference, when it recorded one.
        received_at: Receipt time, as an ISO-8601 UTC string.
    """

    model_config = ConfigDict(
        allow_inf_nan=False,
        extra="forbid",
        frozen=True,
        strict=True,
    )

    receipt_id: str
    task_id: str
    proposal_id: str
    proposal_content_hash: str
    evaluation_request_id: str
    status: ReceiptStatus
    reason_codes: tuple[str, ...]
    intent_produced: bool
    signals_evaluated: int
    received_at: str
    intent_ref: str | None = None
    audit_event_ref: str | None = None

    @field_validator(
        "receipt_id",
        "task_id",
        "proposal_id",
        "proposal_content_hash",
        "evaluation_request_id",
        "received_at",
    )
    @classmethod
    def _validate_reference(cls, value: str) -> str:
        """Validate one required receipt reference.

        Args:
            value: Candidate reference.

        Returns:
            Validated reference.
        """
        return _text(value, "receipt reference", limit=_MAX_SHORT_TEXT)

    @field_validator("intent_ref", "audit_event_ref")
    @classmethod
    def _validate_optional_reference(cls, value: str | None) -> str | None:
        """Validate one optional receiver-returned reference.

        Args:
            value: Candidate reference.

        Returns:
            Validated reference, or None.
        """
        if value is None:
            return None
        return _text(value, "receipt reference", limit=_MAX_SHORT_TEXT)

    @field_validator("reason_codes")
    @classmethod
    def _validate_reasons(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate the receiver-returned reason codes.

        Args:
            value: Candidate codes.

        Returns:
            Validated codes.

        Raises:
            ValueError: If the tuple is oversized.
        """
        if len(value) > _MAX_ITEMS:
            message = f"receipt reason codes must not exceed {_MAX_ITEMS} entries"
            raise ValueError(message)
        return tuple(
            _text(item, "reason code", limit=_MAX_SHORT_TEXT) for item in value
        )

    @field_validator("signals_evaluated")
    @classmethod
    def _validate_signal_count(cls, value: int) -> int:
        """Validate the reported signal count.

        Args:
            value: Candidate count.

        Returns:
            Validated count.

        Raises:
            ValueError: If the count is negative.
        """
        if value < 0:
            message = "a receipt cannot report a negative signal count"
            raise ValueError(message)
        return value

    @model_validator(mode="after")
    def _validate_outcome(self) -> Self:
        """Validate that the receipt claims no more than the receiver said.

        Returns:
            The validated receipt.

        Raises:
            ValueError: If an intent is claimed without an identity, or an
                intent is reported against a status that cannot produce one.
        """
        if self.intent_produced and self.intent_ref is None:
            message = "a receipt claiming an intent must carry that intent's identity"
            raise ValueError(message)
        if not self.intent_produced and self.intent_ref is not None:
            message = "a receipt carrying an intent identity must report the intent"
            raise ValueError(message)
        # Only an accepted proposal can have produced anything. A rejected,
        # expired, or signal-free proposal reporting an intent would be
        # describing an outcome the receiver did not reach.
        if self.intent_produced and self.status != "accepted_for_evaluation":
            message = (
                f"a {self.status!r} proposal produced no intent; a receipt cannot "
                "report one"
            )
            raise ValueError(message)
        if self.signals_evaluated and self.status in {"rejected", "expired"}:
            message = (
                f"a {self.status!r} proposal was not evaluated; a receipt cannot "
                "report evaluated signals"
            )
            raise ValueError(message)
        return self


def _instant(value: str, field: str) -> datetime:
    """Parse one aware UTC instant from its ISO-8601 form.

    Args:
        value: Candidate instant.
        field: Safe field label for validation.

    Returns:
        The parsed aware instant.

    Raises:
        ValueError: If the instant is unreadable or carries no offset.
    """
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as error:
        message = f"{field} must be an ISO-8601 instant: {error}"
        raise ValueError(message) from error
    if parsed.tzinfo is None:
        message = f"{field} must carry a UTC offset"
        raise ValueError(message)
    return parsed


def derive_proposal_hash(fields: Mapping[str, object]) -> str:
    """Derive the content digest of one trade proposal.

    The digest is what the receiver records as `source_content_hash`, so a
    proposal altered after submission no longer matches the one evaluated.

    Args:
        fields: Proposal fields excluding the derived digest.

    Returns:
        The canonical content digest.
    """
    payload = {key: value for key, value in fields.items() if key != "content_hash"}
    return canonical_digest(payload)


def build_trade_proposal(fields: Mapping[str, object]) -> TradeProposal:
    """Build one non-executable trade proposal.

    Args:
        fields: Complete proposal fields excluding the derived digest.

    Returns:
        A validated immutable proposal carrying its content digest.
    """
    logger.debug("Building a trade proposal")
    return TradeProposal.model_validate(
        {**fields, "content_hash": derive_proposal_hash(fields)},
    )


def build_trade_proposal_receipt(fields: Mapping[str, object]) -> TradeProposalReceipt:
    """Build one proposal receipt.

    Args:
        fields: Complete receipt fields.

    Returns:
        A validated immutable receipt.
    """
    logger.debug("Building a trade proposal receipt")
    return TradeProposalReceipt.model_validate(fields)


def forbidden_fields(model: type[BaseModel]) -> tuple[str, ...]:
    """Return the broker-native fields one model defines.

    Args:
        model: Candidate contract class.

    Returns:
        Ordered forbidden field names the model carries, empty when clean.
    """
    return tuple(sorted(set(model.model_fields) & set(FORBIDDEN_BROKER_FIELDS)))
