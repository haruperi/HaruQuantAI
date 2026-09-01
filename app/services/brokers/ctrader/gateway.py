"""cTrader gateway for the focused Broker runtime contracts."""

from __future__ import annotations

from dataclasses import asdict
from decimal import Decimal
from typing import TYPE_CHECKING, cast

from app.contracts.broker.errors import BrokerFailure
from app.contracts.broker.models import (
    BrokerAccountSnapshot,
    BrokerHistoryPage,
    BrokerOperationOutcome,
    BrokerOperationReceipt,
    BrokerSessionReadiness,
    BrokerSessionState,
    BrokerTradingState,
    ManageSessionsRequest,
    ManageSessionsSuccess,
    ProviderCorrelation,
    ProviderRecord,
    ReadProviderStateRequest,
    ReadProviderStateSuccess,
    TransportOrdersRequest,
    TransportOrdersSuccess,
)
from app.contracts.common.models import JsonObject, Money, ProblemDetails
from app.kernel.identity import generate_uuid7
from app.kernel.serialization import to_json_safe
from app.kernel.time import format_utc_timestamp, utc_now
from app.services.brokers.canonical_contracts import (
    BrokerEnvironment,
    BrokerOrderModificationRequest,
    BrokerOrderRequest,
)
from app.services.brokers.ctrader.adapter import CTraderBrokerAdapter
from app.services.brokers.ctrader.config import CTraderConfig

if TYPE_CHECKING:
    from app.contracts.broker.models import BrokerSessionRef, BrokerProviderKind
    from app.contracts.common.models import Uuid7


def _failure(request_id: Uuid7, code: str, detail: str) -> BrokerFailure:
    return BrokerFailure(
        request_id=request_id,
        code=code,  # type: ignore[arg-type]
        problem=ProblemDetails(status=503 if code == "CAPABILITY_UNAVAILABLE" else 422, code=code, detail=detail, request_id=request_id),
    )


def _provider_record(value: object) -> ProviderRecord:
    raw = cast(JsonObject, to_json_safe(asdict(value)))
    provider_id = "unknown"
    for name in ("position_id", "order_id", "deal_id", "transaction_id"):
        candidate = getattr(value, name, None)
        if candidate is not None:
            provider_id = str(candidate)
            break
    return ProviderRecord(provider_id=provider_id, record=raw)


class CTraderGateway:
    """Provider-local cTrader gateway consumed only by the dispatcher."""

    provider_kind: BrokerProviderKind = "CTRADER"
    supports_order_transport = True

    def __init__(self, config: CTraderConfig) -> None:
        self._config = config
        self._adapter = CTraderBrokerAdapter(config.to_legacy_connection())
        self._journal: dict[Uuid7, TransportOrdersSuccess] = {}

    @property
    def profile_id(self) -> Uuid7:
        return cast("Uuid7", self._config.profile_id)

    async def close(self) -> None:
        """Release the exact owned cTrader session."""
        await self._adapter.disconnect()

    def accepts(self, session: BrokerSessionRef) -> bool:
        return session.profile_id == self._config.profile_id and session.profile_version == self._config.profile_version

    def _validate_session(self, session: BrokerSessionRef, request_id: Uuid7) -> BrokerFailure | None:
        if not self.accepts(session):
            return _failure(request_id, "BROKER_PROFILE_UNSUPPORTED", "Session profile is not owned by this cTrader feature")
        if session.environment != self._config.environment:
            return _failure(request_id, "BROKER_ENVIRONMENT_MISMATCH", "Configured and requested cTrader environments differ")
        if session.account_ref != self._config.account_ref:
            return _failure(request_id, "BROKER_VALIDATION_FAILED", "Session account does not match the configured cTrader account")
        return None

    async def manage_sessions(self, request: ManageSessionsRequest) -> ManageSessionsSuccess | BrokerFailure:
        assert request.session is not None
        session = request.session
        if failure := self._validate_session(session, request.request_id):
            return failure
        now = format_utc_timestamp(utc_now())
        if request.operation == "TRANSITION":
            assert request.state is not None
            return ManageSessionsSuccess(request_id=request.request_id, session=session, state=request.state)
        if request.operation == "OPEN":
            result = await self._adapter.connect()
            state_name = "READY" if result.status == "success" else "FAILED"
        elif request.operation == "RECONNECT":
            result = await self._adapter.reconnect()
            state_name = "READY" if result.status == "success" else "FAILED"
        elif request.operation == "CLOSE":
            result = await self._adapter.disconnect()
            state_name = "DISCONNECTED" if result.status == "success" else "FAILED"
        else:
            connected = await self._adapter.is_connected()
            ready = connected.status == "success" and bool(connected.data)
            permissions_result = await self._adapter.get_permissions()
            permissions = permissions_result.data if permissions_result.status == "success" else None
            readiness = BrokerSessionReadiness(
                session_id=session.session_id,
                generation=session.generation,
                transport="READY" if ready else "NOT_READY",
                authentication="READY" if ready else "NOT_READY",
                account_authorization="READY" if ready else "NOT_READY",
                trading_permission="READY" if ready and permissions is not None and permissions.trade_write is True else "NOT_READY",
                subscriptions="READY" if ready else "NOT_READY",
                environment_verified=session.environment == self._config.environment,
                resynchronized=ready,
                assessed_at=now,
            )
            return ManageSessionsSuccess(request_id=request.request_id, session=session, readiness=readiness)
        if state_name == "FAILED":
            return _failure(request.request_id, "BROKER_SESSION_NOT_READY", f"cTrader {request.operation.lower()} failed")
        return ManageSessionsSuccess(
            request_id=request.request_id,
            session=session,
            state=BrokerSessionState(session_id=session.session_id, generation=session.generation, connection_state=state_name, transitioned_at=now, reason=request.operation.lower()),  # type: ignore[arg-type]
        )

    async def read_provider_state(self, request: ReadProviderStateRequest) -> ReadProviderStateSuccess | BrokerFailure:
        assert request.session is not None
        session = request.session
        if failure := self._validate_session(session, request.request_id):
            return failure
        if request.operation == "READ_ACCOUNT":
            result = await self._adapter.get_account_info()
            if result.status != "success" or result.data is None:
                return _failure(request.request_id, "BROKER_SESSION_NOT_READY", "cTrader account state is unavailable")
            info = result.data
            if info.currency is None or info.equity is None:
                return _failure(request.request_id, "BROKER_VALIDATION_FAILED", "cTrader account response lacks currency or equity")
            balances_result = await self._adapter.get_balances()
            balances = {
                item.asset: str(item.total)
                for item in (balances_result.data or ())
                if item.total is not None
            } if balances_result.status == "success" else {}
            return ReadProviderStateSuccess(
                request_id=request.request_id,
                account=BrokerAccountSnapshot(
                    session_id=session.session_id,
                    generation=session.generation,
                    account_ref=session.account_ref,
                    currency=info.currency,
                    equity=Money(amount=str(info.equity), currency=info.currency),
                    retrieved_at=format_utc_timestamp(info.retrieved_at),
                    balances=balances,
                    margin=Money(amount=str(info.margin), currency=info.currency) if info.margin is not None else None,
                    free_margin=Money(amount=str(info.free_margin), currency=info.currency) if info.free_margin is not None else None,
                    permissions=(),
                    provider_time=format_utc_timestamp(info.provider_timestamp) if info.provider_timestamp is not None else None,
                ),
            )
        if request.operation == "READ_TRADING_STATE":
            positions = await self._adapter.get_positions(limit=1_000)
            orders = await self._adapter.get_orders(limit=1_000)
            deals = await self._adapter.list_deal_history(limit=1_000)
            if any(result.status != "success" for result in (positions, orders, deals)):
                return _failure(request.request_id, "BROKER_SESSION_NOT_READY", "cTrader trading state is incomplete")
            return ReadProviderStateSuccess(
                request_id=request.request_id,
                trading_state=BrokerTradingState(
                    session_id=session.session_id,
                    generation=session.generation,
                    retrieved_at=format_utc_timestamp(utc_now()),
                    positions=tuple(_provider_record(item) for item in positions.data.items) if positions.data is not None else (),
                    orders=tuple(_provider_record(item) for item in orders.data.items) if orders.data is not None else (),
                    deals=tuple(_provider_record(item) for item in deals.data.items) if deals.data is not None else (),
                ),
            )
        if request.operation == "PAGE_HISTORY":
            limit = request.page_size or 1_000
            page = await self._adapter.list_order_history(cursor=request.page_cursor, limit=limit)
            if page.status != "success" or page.data is None:
                return _failure(request.request_id, "BROKER_SESSION_NOT_READY", "cTrader provider history is unavailable")
            return ReadProviderStateSuccess(
                request_id=request.request_id,
                page=BrokerHistoryPage(
                    page_id=generate_uuid7(),
                    requested_count=limit,
                    returned_count=len(page.data.items),
                    is_truncated=page.data.truncated,
                    retrieved_at=format_utc_timestamp(utc_now()),
                    provider_cursor=page.data.next_cursor,
                    records=tuple(_provider_record(item) for item in page.data.items),
                ),
            )
        if request.operation == "READ_MARKET":
            return _failure(request.request_id, "BROKER_VALIDATION_FAILED", "READ_MARKET v1 does not carry the exact provider_symbol required by the Broker boundary")
        return _failure(request.request_id, "CAPABILITY_UNAVAILABLE", "Provider event normalization is published through the Kernel event bus")

    def _legacy_order_request(self, request: TransportOrdersRequest) -> BrokerOrderRequest | BrokerFailure:
        assert request.operation_request is not None
        operation = request.operation_request
        policy = operation.policy
        side = policy.get("side")
        order_type = policy.get("order_type")
        quantity_unit = policy.get("quantity_unit")
        if not all(isinstance(value, str) and value for value in (side, order_type, quantity_unit)):
            return _failure(request.request_id, "BROKER_VALIDATION_FAILED", "Order policy requires side, order_type, and quantity_unit")
        price = Decimal(operation.normalized_price) if operation.normalized_price is not None else None
        try:
            return BrokerOrderRequest(
                symbol=operation.provider_symbol,
                side=cast("str", side),  # type: ignore[arg-type]
                order_type=cast("str", order_type),  # type: ignore[arg-type]
                quantity=Decimal(operation.normalized_quantity),
                quantity_unit=cast("str", quantity_unit),
                environment=BrokerEnvironment[self._config.environment],
                account_reference=self._config.account_ref,
                limit_price=price if order_type in {"LIMIT", "STOP_LIMIT"} else None,
                stop_price=price if order_type in {"STOP", "STOP_LIMIT"} else None,
                client_order_id=operation.idempotency_key,
            )
        except ValueError as error:
            return _failure(request.request_id, "BROKER_VALIDATION_FAILED", str(error))

    async def transport_orders(self, request: TransportOrdersRequest) -> TransportOrdersSuccess | BrokerFailure:
        if request.operation == "JOURNAL":
            assert request.operation_id is not None
            prior = self._journal.get(request.operation_id)
            if prior is None:
                return _failure(request.request_id, "CAPABILITY_UNAVAILABLE", "No in-memory cTrader transport receipt exists for this operation")
            return prior.model_copy(update={"request_id": request.request_id})
        assert request.operation_request is not None
        operation = request.operation_request
        if failure := self._validate_session(operation.session, request.request_id):
            return failure
        legacy = self._legacy_order_request(request)
        if isinstance(legacy, BrokerFailure):
            return legacy
        if request.operation == "VALIDATE_REQUEST":
            result = await self._adapter.check_order(legacy)
            provider_result = result.data
            outcome_name = "ACCEPTED" if result.status == "success" and provider_result is not None and provider_result.accepted_for_submission else "REJECTED"
        elif request.operation == "SUBMIT":
            result = await self._adapter.place_order(legacy)
            provider_result = result.data
            outcome_name = "UNKNOWN" if result.error is not None and result.error.code == "BROKER_UNKNOWN_OUTCOME" else ("ACCEPTED" if result.status == "success" and provider_result is not None and provider_result.outcome != "REJECTED" else "REJECTED")
        elif request.operation == "CANCEL":
            order_id = operation.policy.get("provider_order_id")
            if not isinstance(order_id, str) or not order_id:
                return _failure(request.request_id, "BROKER_VALIDATION_FAILED", "CANCEL requires policy.provider_order_id")
            result = await self._adapter.cancel_order(order_id)
            provider_result = result.data
            outcome_name = "UNKNOWN" if result.error is not None and result.error.code == "BROKER_UNKNOWN_OUTCOME" else ("ACCEPTED" if result.status == "success" else "REJECTED")
        else:
            order_id = operation.policy.get("provider_order_id")
            if not isinstance(order_id, str) or not order_id:
                return _failure(request.request_id, "BROKER_VALIDATION_FAILED", "MODIFY requires policy.provider_order_id")
            result = await self._adapter.modify_order(BrokerOrderModificationRequest(order_id=order_id, quantity=Decimal(operation.normalized_quantity), limit_price=Decimal(operation.normalized_price) if operation.normalized_price is not None else None))
            provider_result = result.data
            outcome_name = "UNKNOWN" if result.error is not None and result.error.code == "BROKER_UNKNOWN_OUTCOME" else ("ACCEPTED" if result.status == "success" else "REJECTED")
        receipt = BrokerOperationReceipt(
            receipt_id=generate_uuid7(),
            operation_id=operation.operation_id,
            attempt_no=operation.attempt_no,
            profile_version_id=cast("Uuid7", self._config.profile_version_id),
            environment=operation.session.environment,
            session_generation=operation.session.generation,
            request_hash=operation.request_hash,
            outcome=outcome_name,  # type: ignore[arg-type]
            provider_order_id=(str(getattr(provider_result, "order_id", "")) or None) if provider_result is not None else None,
            provider_deal_id=str(provider_result.deal_ids[0]) if provider_result is not None and getattr(provider_result, "deal_ids", ()) else None,
            provider_evidence={"legacy_outcome": str(getattr(provider_result, "outcome", outcome_name))},
            reconciliation_keys={"idempotency_key": operation.idempotency_key},
            completed_at=format_utc_timestamp(utc_now()),
        )
        outcome = BrokerOperationOutcome(operation_id=operation.operation_id, outcome=outcome_name, receipt=receipt, is_reconciled=False)  # type: ignore[arg-type]
        correlation = ProviderCorrelation(correlation_id=generate_uuid7(), operation_id=operation.operation_id, idempotency_key=operation.idempotency_key, provider_order_id=receipt.provider_order_id, provider_deal_id=receipt.provider_deal_id)
        success = TransportOrdersSuccess(request_id=request.request_id, outcome=outcome, receipt=receipt, correlation=correlation)
        self._journal[operation.operation_id] = success
        return success
