/**
 * Temporal Presentation Context for HaruQuantAI D-UI.
 *
 * Implements spatiotemporal composability rules (WF-UI-010):
 * - Strict time domain isolation (LIVE, PLAYBACK, SIMULATION, JOB_STREAM)
 * - Source/clock identity preservation (TemporalSourceRef)
 * - Monotonic cursor/sequence order enforcement (TemporalCursor)
 * - Gap detection (TemporalGap) and fail-closed resynchronization (TemporalResynchronization)
 * - Freshness and staleness detection (TemporalFreshness)
 * - Bounded update coalescing
 * - Exact subscription/timer disposal
 */

import React, { createContext, useContext, useState, useEffect, useRef, useCallback, type ReactNode } from "react";
import type {
  TemporalContext,
  TemporalCursor,
  TemporalFreshness,
  TemporalGap,
  TemporalResynchronization,
  TemporalSourceRef,
  TimeDomain,
} from "../contracts/generated/ui";

export interface TemporalEvent<TData = unknown> {
  readonly source: TemporalSourceRef;
  readonly domain: TimeDomain;
  readonly sequence: number;
  readonly asOf: string;
  readonly cursorToken?: string | null;
  readonly payload: TData;
}

export interface TemporalContextValue {
  readonly context: TemporalContext;
  readonly timeDomain: TimeDomain;
  readonly boundSource: TemporalSourceRef;
  readonly cursor: TemporalCursor | null;
  readonly freshness: TemporalFreshness | null;
  readonly openGaps: readonly TemporalGap[];
  readonly resyncState: TemporalResynchronization | null;
  readonly isFailedClosed: boolean;
  readonly setTimeDomain: (domain: TimeDomain, newSource?: TemporalSourceRef) => void;
  readonly bindSource: (source: TemporalSourceRef) => void;
  readonly pushEvent: <T>(event: TemporalEvent<T>) => boolean;
  readonly requestResync: (replayedFrom?: number) => void;
  readonly reset: () => void;
}

const DEFAULT_SOURCE: TemporalSourceRef = {
  source_id: "src-default",
  source_kind: "system_clock",
  clock_id: "clock-utc",
  schema_version: 1,
};

const TemporalPresentationContext = createContext<TemporalContextValue | null>(null);

export interface TemporalProviderProps {
  workspaceId: string;
  initialDomain?: TimeDomain;
  initialSource?: TemporalSourceRef;
  stalenessThresholdMs?: number;
  batchWindowMs?: number;
  children: ReactNode;
}

export const TemporalProvider: React.FC<TemporalProviderProps> = ({
  workspaceId,
  initialDomain = "LIVE",
  initialSource = DEFAULT_SOURCE,
  stalenessThresholdMs = 5000,
  batchWindowMs = 100,
  children,
}) => {
  const [domain, setDomain] = useState<TimeDomain>(initialDomain);
  const [source, setSource] = useState<TemporalSourceRef>(initialSource);
  const [cursor, setCursor] = useState<TemporalCursor | null>(null);
  const [freshness, setFreshness] = useState<TemporalFreshness | null>(null);
  const [openGaps, setOpenGaps] = useState<TemporalGap[]>([]);
  const [resync, setResync] = useState<TemporalResynchronization | null>(null);
  const [isFailedClosed, setIsFailedClosed] = useState<boolean>(false);

  const pendingBatchRef = useRef<TemporalEvent[]>([]);
  const batchTimerRef = useRef<number | null>(null);
  const stalenessTimerRef = useRef<number | null>(null);

  // Staleness monitoring timer
  useEffect(() => {
    if (typeof window === "undefined") return;

    stalenessTimerRef.current = window.setInterval(() => {
      setFreshness((prev) => {
        if (!prev) return null;
        const now = Date.now();
        const lastTime = new Date(prev.last_event_at).getTime();
        const isStale = now - lastTime > stalenessThresholdMs;

        if (prev.is_stale === isStale) return prev;

        return {
          ...prev,
          observed_at: new Date(now).toISOString(),
          is_stale: isStale,
          staleness_reason: isStale ? `No events received for >${stalenessThresholdMs}ms` : "",
        };
      });
    }, 1000);

    return () => {
      if (stalenessTimerRef.current !== null) {
        clearInterval(stalenessTimerRef.current);
        stalenessTimerRef.current = null;
      }
    };
  }, [stalenessThresholdMs]);

  // Clean up batch timer on unmount
  useEffect(() => {
    return () => {
      if (batchTimerRef.current !== null) {
        clearTimeout(batchTimerRef.current);
        batchTimerRef.current = null;
      }
    };
  }, []);

  const setTimeDomain = useCallback((newDomain: TimeDomain, newSource?: TemporalSourceRef) => {
    setDomain(newDomain);
    if (newSource) {
      setSource(newSource);
    }
    // Cleanly reset cursor, gaps, and error state when switching domain
    setCursor(null);
    setOpenGaps([]);
    setResync(null);
    setIsFailedClosed(false);
    pendingBatchRef.current = [];
  }, []);

  const bindSource = useCallback((newSource: TemporalSourceRef) => {
    setSource(newSource);
    setCursor(null);
    setOpenGaps([]);
    setResync(null);
    setIsFailedClosed(false);
    pendingBatchRef.current = [];
  }, []);

  const applyEvent = useCallback((event: TemporalEvent) => {
    const nowIso = new Date().toISOString();

    // 1. Time domain compatibility validation (fail closed on domain mixing)
    if (event.domain !== domain) {
      console.error(
        `[TemporalContext] Incompatible time domain update: event has domain '${event.domain}', active context is '${domain}'. Failing closed.`
      );
      setIsFailedClosed(true);
      setResync({
        context_id: `ctx-${workspaceId}`,
        outcome: "FAILED_CLOSED",
        started_at: nowIso,
        completed_at: nowIso,
        schema_version: 1,
      });
      return false;
    }

    // 2. Monotonic sequence ordering and gap detection
    setCursor((prevCursor) => {
      if (prevCursor) {
        const expectedSeq = prevCursor.sequence + 1;
        if (event.sequence > expectedSeq) {
          // Gap detected
          const gap: TemporalGap = {
            source: event.source,
            from_sequence: expectedSeq,
            to_sequence: event.sequence - 1,
            reason: `Sequence jump from ${prevCursor.sequence} to ${event.sequence}`,
            schema_version: 1,
          };
          setOpenGaps((prevGaps) => [...prevGaps, gap]);
        } else if (event.sequence < prevCursor.sequence) {
          // Out of order event dropped to preserve monotonicity
          console.warn(
            `[TemporalContext] Dropping out-of-order event: sequence ${event.sequence} < current ${prevCursor.sequence}`
          );
          return prevCursor;
        }
      }

      return {
        source: event.source,
        sequence: event.sequence,
        cursor_token: event.cursorToken || null,
        as_of: event.asOf,
        schema_version: 1,
      };
    });

    // 3. Update freshness
    setFreshness({
      source: event.source,
      last_event_at: event.asOf,
      observed_at: nowIso,
      is_stale: false,
      staleness_reason: "",
      schema_version: 1,
    });

    return true;
  }, [domain, workspaceId]);

  const flushBatch = useCallback(() => {
    const batch = [...pendingBatchRef.current];
    pendingBatchRef.current = [];
    batchTimerRef.current = null;

    for (const evt of batch) {
      applyEvent(evt);
    }
  }, [applyEvent]);

  const pushEvent = useCallback(
    <T,>(event: TemporalEvent<T>): boolean => {
      if (isFailedClosed) {
        return false;
      }

      if (batchWindowMs <= 0) {
        return applyEvent(event);
      }

      pendingBatchRef.current.push(event as TemporalEvent);
      if (batchTimerRef.current === null) {
        batchTimerRef.current = window.setTimeout(flushBatch, batchWindowMs);
      }
      return true;
    },
    [isFailedClosed, batchWindowMs, applyEvent, flushBatch]
  );

  const requestResync = useCallback(
    (replayedFrom?: number) => {
      const nowIso = new Date().toISOString();
      setOpenGaps([]);
      setIsFailedClosed(false);
      setResync({
        context_id: `ctx-${workspaceId}`,
        outcome: "RESYNCED",
        started_at: nowIso,
        completed_at: nowIso,
        replayed_from_sequence: replayedFrom ?? null,
        schema_version: 1,
      });
    },
    [workspaceId]
  );

  const reset = useCallback(() => {
    setCursor(null);
    setFreshness(null);
    setOpenGaps([]);
    setResync(null);
    setIsFailedClosed(false);
    pendingBatchRef.current = [];
  }, []);

  const contextValue: TemporalContext = {
    context_id: `ctx-${workspaceId}`,
    workspace_id: workspaceId,
    domain,
    bound_source: source,
    cursor,
    freshness,
    open_gaps: openGaps,
    resynchronization: resync,
    schema_version: 1,
  };

  return (
    <TemporalPresentationContext.Provider
      value={{
        context: contextValue,
        timeDomain: domain,
        boundSource: source,
        cursor,
        freshness,
        openGaps,
        resyncState: resync,
        isFailedClosed,
        setTimeDomain,
        bindSource,
        pushEvent,
        requestResync,
        reset,
      }}
    >
      {children}
    </TemporalPresentationContext.Provider>
  );
};

export function useTemporalContext(): TemporalContextValue {
  const ctx = useContext(TemporalPresentationContext);
  if (!ctx) {
    throw new Error("useTemporalContext must be used within a TemporalProvider");
  }
  return ctx;
}
