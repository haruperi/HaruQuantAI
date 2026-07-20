"""Simulator-backed replay orchestration for risk frames."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import pandas as pd

from app.services.risk.core import (
    PortfolioStateEngine,
    RecommendationEngine,
    RiskScorecardEngine,
    RiskSnapshotEngine,
    TimelineReconstructor,
)
from app.services.risk.domain import PortfolioState

from .cockpit_state import build_cockpit_state
from .models import ReplayFrame, ReplayRun


class ReplayEngine:
    """Replay simulator timelines into deterministic risk frames."""

    def __init__(
        self,
        portfolio_state_engine: PortfolioStateEngine | None = None,
        snapshot_engine: RiskSnapshotEngine | None = None,
        scorecard_engine: RiskScorecardEngine | None = None,
        recommendation_engine: RecommendationEngine | None = None,
        timeline_reconstructor: TimelineReconstructor | None = None,
    ):
        self.portfolio_state_engine = portfolio_state_engine or PortfolioStateEngine()
        self.snapshot_engine = snapshot_engine or RiskSnapshotEngine()
        self.scorecard_engine = scorecard_engine or RiskScorecardEngine()
        self.recommendation_engine = recommendation_engine or RecommendationEngine(
            snapshot_engine=self.snapshot_engine,
            scorecard_engine=self.scorecard_engine,
        )
        self.timeline_reconstructor = timeline_reconstructor or TimelineReconstructor()

    def replay(
        self,
        engine: Any,
        data: pd.DataFrame,
        symbols: list[str],
        timeframe: str,
        market_data: dict[str, pd.DataFrame],
        limits=None,
        symbol_to_cluster: dict[str, str] | None = None,
        metadata: dict[str, Any] | None = None,
        frame_mode: str = "bar",
        include_recommendations: bool = True,
        candidate_symbols: Iterable[str] | None = None,
        hedge_symbols: Iterable[str] | None = None,
        max_recommendations: int = 5,
        max_frames: int | None = None,
        run_kwargs: dict[str, Any] | None = None,
    ) -> ReplayRun:
        """Run the simulator and capture deterministic replay frames."""
        timeline = self.timeline_reconstructor.build_timeline(
            data, frame_mode=frame_mode
        )
        if max_frames is not None:
            timeline = timeline[: int(max_frames)]

        frames: list[ReplayFrame] = []
        capture_plan = {
            pd.Timestamp(point.capture_timestamp): point for point in timeline
        }
        previous_schedule = dict(getattr(engine, "run_schedule", {}))
        if hasattr(engine, "configure_run_schedule"):
            engine.configure_run_schedule(
                positions_every=1,
                pending_orders_every=1,
                account_every=1,
                portfolio_every=None,
                risk_every=None,
            )

        def _observer(engine, timestamp, tick_number, batch_end):
            _ = tick_number
            _ = batch_end
            if timestamp is None:
                return
            capture_timestamp = pd.Timestamp(timestamp)
            point = capture_plan.get(capture_timestamp)
            if point is None:
                return
            if hasattr(engine, "monitor_positions"):
                engine.monitor_positions(verbose=False)
            if hasattr(engine, "monitor_pending_orders"):
                engine.monitor_pending_orders(verbose=False)
            if hasattr(engine, "monitor_account"):
                engine.monitor_account(verbose=False)
            frame = self._build_frame(
                engine=engine,
                point=point,
                symbols=symbols,
                timeframe=timeframe,
                market_data=market_data,
                limits=limits,
                symbol_to_cluster=symbol_to_cluster or {},
                metadata=metadata or {},
                include_recommendations=include_recommendations,
                candidate_symbols=candidate_symbols,
                hedge_symbols=hedge_symbols,
                max_recommendations=max_recommendations,
            )
            frames.append(frame)

        try:
            engine.run(
                data,
                engine_type="event_driven",
                frame_observer=_observer,
                **dict(run_kwargs or {}),
            )
        finally:
            if hasattr(engine, "configure_run_schedule"):
                engine.configure_run_schedule(
                    positions_every=previous_schedule.get("positions"),
                    pending_orders_every=previous_schedule.get("pending_orders"),
                    account_every=previous_schedule.get("account"),
                    portfolio_every=previous_schedule.get("portfolio"),
                    risk_every=previous_schedule.get("risk"),
                )

        summary = {
            "frame_mode": frame_mode,
            "timeline_signature": self.timeline_reconstructor.timeline_signature(
                timeline, frame_mode=frame_mode
            ),
            "frame_count": len(frames),
            "captured_symbols": list(symbols),
        }
        return ReplayRun(timeline=timeline, frames=frames, summary=summary)

    def _build_frame(
        self,
        engine: Any,
        point,
        symbols: list[str],
        timeframe: str,
        market_data: dict[str, pd.DataFrame],
        limits,
        symbol_to_cluster: dict[str, str],
        metadata: dict[str, Any],
        include_recommendations: bool,
        candidate_symbols,
        hedge_symbols,
        max_recommendations: int,
    ) -> ReplayFrame:
        frame_state = self._build_portfolio_state(
            engine=engine,
            frame_timestamp=pd.Timestamp(point.frame_timestamp),
            symbols=symbols,
            timeframe=timeframe,
            market_data=market_data,
            limits=limits,
            symbol_to_cluster=symbol_to_cluster,
            metadata=metadata,
        )
        snapshot = self.snapshot_engine.build_snapshot(frame_state)
        scorecard = self.scorecard_engine.build_scorecard(snapshot)
        recommendations = None
        if include_recommendations:
            recommendations = self.recommendation_engine.build_recommendations(
                frame_state,
                snapshot=snapshot,
                scorecard=scorecard,
                candidate_symbols=candidate_symbols,
                hedge_symbols=hedge_symbols,
                max_recommendations=max_recommendations,
            )
        frame = ReplayFrame(
            frame_index=int(point.frame_index),
            timestamp=pd.Timestamp(point.frame_timestamp),
            capture_timestamp=pd.Timestamp(point.capture_timestamp),
            state=frame_state,
            snapshot=snapshot,
            scorecard=scorecard,
            recommendations=recommendations,
            context={"timeframe": timeframe},
        )
        cockpit = build_cockpit_state(frame)
        return ReplayFrame(
            frame_index=frame.frame_index,
            timestamp=frame.timestamp,
            capture_timestamp=frame.capture_timestamp,
            state=frame.state,
            snapshot=frame.snapshot,
            scorecard=frame.scorecard,
            recommendations=frame.recommendations,
            cockpit_state=cockpit,
            context=frame.context,
        )

    def _build_portfolio_state(
        self,
        engine: Any,
        frame_timestamp: pd.Timestamp,
        symbols: list[str],
        timeframe: str,
        market_data: dict[str, pd.DataFrame],
        limits,
        symbol_to_cluster: dict[str, str],
        metadata: dict[str, Any],
    ) -> PortfolioState:
        sliced_market_data = self._slice_market_data(market_data, frame_timestamp)
        symbol_specs = {
            symbol: engine.symbol_info(symbol)
            for symbol in symbols
            if hasattr(engine, "symbol_info") and engine.symbol_info(symbol) is not None
        }
        merged_metadata = {
            **dict(metadata or {}),
            "source": "replay_frame",
            "timeframe": timeframe,
            "frame_timestamp": frame_timestamp.isoformat(),
            "equity_curve": self._build_equity_curve_series(engine, frame_timestamp),
            "peak_equity": self._build_peak_equity(engine, frame_timestamp),
        }
        return self.portfolio_state_engine.build_state(
            account=engine.account_info(),
            positions=engine.positions_get(),
            symbol_specs=symbol_specs,
            market_data=sliced_market_data,
            limits=limits,
            symbol_to_cluster=symbol_to_cluster,
            timeframe=timeframe,
            as_of=frame_timestamp.isoformat(),
            metadata=merged_metadata,
        )

    def _slice_market_data(
        self,
        market_data: dict[str, pd.DataFrame],
        frame_timestamp: pd.Timestamp,
    ) -> dict[str, pd.DataFrame]:
        out: dict[str, pd.DataFrame] = {}
        for symbol, bars in market_data.items():
            prepared = bars.copy()
            if isinstance(prepared.index, pd.DatetimeIndex):
                prepared = prepared[prepared.index <= frame_timestamp]
            out[symbol] = prepared.copy()
        return out

    def _build_equity_curve_series(self, engine: Any, frame_timestamp: pd.Timestamp):
        if not hasattr(engine, "get_equity_curve"):
            return None
        points = []
        values = []
        for point in engine.get_equity_curve():
            timestamp = getattr(point, "timestamp", None)
            equity = getattr(point, "equity", None)
            if timestamp is None or equity is None:
                continue
            ts = pd.Timestamp(timestamp)
            if ts <= frame_timestamp:
                points.append(ts)
                values.append(float(equity))
        if not points:
            account = engine.account_info()
            return pd.Series(
                [float(account.get("equity", account.get("balance", 0.0)) or 0.0)],
                index=[frame_timestamp],
                dtype=float,
            )
        return pd.Series(values, index=pd.DatetimeIndex(points), dtype=float)

    def _build_peak_equity(
        self, engine: Any, frame_timestamp: pd.Timestamp
    ) -> float | None:
        series = self._build_equity_curve_series(engine, frame_timestamp)
        if series is None or series.empty:
            return None
        return float(series.max())
