"use client";

import { useEffect, useRef, useState } from "react";

import { ApiClientError, apiClients, unwrapData, type StreamEvent } from "../../clients";

export type SnapshotStatus =
  | "connecting"
  | "connected"
  | "disconnected"
  | "unavailable";

export interface MarketSnapshotView {
  readonly sequence: number;
  readonly sourceId: string;
  readonly gap: number;
  readonly stale: boolean;
  readonly quotes: readonly Record<string, unknown>[];
}

interface MarketSnapshotState {
  readonly snapshot: MarketSnapshotView | null;
  readonly status: SnapshotStatus;
  readonly error: string | null;
}

/** Lifecycle options owned by the FEAT-UI-25 feature adapter. */
export interface MarketSnapshotsOptions {
  /** Explicit symbol set; empty/undefined derives from system settings. */
  readonly symbols?: readonly string[];
  /** First reconnect delay in milliseconds (exponential backoff base). */
  readonly initialRetryMs?: number;
  /** Reconnect backoff ceiling in milliseconds. */
  readonly maxRetryMs?: number;
  /** When false the widget performs no transport activity at all. */
  readonly enabled?: boolean;
}

const INITIAL_RETRY_MS = 1_000;
const MAX_RETRY_MS = 10_000;

function mapSnapshotEvent(event: StreamEvent): MarketSnapshotView | null {
  const payload = event.payload;
  if (!payload || !Array.isArray(payload.quotes)) return null;
  return {
    sequence: event.sequence,
    sourceId: typeof payload.source_id === "string" ? payload.source_id : "unknown",
    gap: typeof payload.gap === "number" ? payload.gap : 0,
    stale: payload.stale === true,
    quotes: payload.quotes.filter(
      (quote): quote is Record<string, unknown> =>
        typeof quote === "object" && quote !== null,
    ),
  };
}

/**
 * Consume configured MT5 snapshots through HaruQuantAI's authenticated
 * SSE client. The FEAT-UI-25 feature adapter owns the lifecycle options;
 * this hook owns presentation-safe reconnect and gap state only.
 */
export function useMarketSnapshots(
  options: MarketSnapshotsOptions = {},
): MarketSnapshotState {
  const { symbols, enabled = true } = options;
  const initialRetryMs = options.initialRetryMs ?? INITIAL_RETRY_MS;
  const maxRetryMs = options.maxRetryMs ?? MAX_RETRY_MS;
  const [snapshot, setSnapshot] = useState<MarketSnapshotView | null>(null);
  const [status, setStatus] = useState<SnapshotStatus>("connecting");
  const [error, setError] = useState<string | null>(null);
  const retryRef = useRef(0);
  const [isDocumentVisible, setIsDocumentVisible] = useState(
    () => document.visibilityState === "visible",
  );

  useEffect(() => {
    const handleVisibilityChange = (): void => {
      setIsDocumentVisible(document.visibilityState === "visible");
    };
    document.addEventListener("visibilitychange", handleVisibilityChange);
    return () => document.removeEventListener("visibilitychange", handleVisibilityChange);
  }, []);

  useEffect(() => {
    if (!enabled) {
      setStatus("connecting");
      return undefined;
    }
    if (!isDocumentVisible) {
      setStatus("disconnected");
      return undefined;
    }
    let stopped = false;
    let controller: AbortController | null = null;
    let retryTimer: ReturnType<typeof setTimeout> | null = null;

    const resolveSymbols = async (): Promise<string[] | null> => {
      if (symbols && symbols.length > 0) return [...symbols];
      const settings = unwrapData(await apiClients.settings.readSystem());
      const settingsSymbols = (settings.settings.MT5_SNAPSHOT_SYMBOLS ?? "")
        .split(",")
        .map((symbol) => symbol.trim())
        .filter(Boolean);
      return settingsSymbols.length > 0 ? settingsSymbols : null;
    };

    const consume = async (
      activeController: AbortController,
      streamSymbols: string[],
    ): Promise<void> => {
      for await (const event of apiClients.data.snapshotStream(
        [...streamSymbols],
        {
          signal: activeController.signal,
        },
      )) {
        if (stopped) return;
        const mapped = mapSnapshotEvent(event);
        if (!mapped) continue;
        retryRef.current = 0;
        setSnapshot(mapped);
        setStatus("connected");
        setError(null);
      }
    };

    const connect = async (): Promise<void> => {
      if (stopped) return;
      setStatus("connecting");
      const activeController = new AbortController();
      controller = activeController;
      try {
        const streamSymbols = await resolveSymbols();
        if (streamSymbols === null) {
          setStatus("unavailable");
          setError("MT5 snapshot symbols are not configured.");
          return;
        }
        await consume(activeController, streamSymbols);
        if (!stopped) setStatus("disconnected");
      } catch (cause) {
        if (stopped || activeController.signal.aborted) return;
        if (cause instanceof ApiClientError && cause.status === 503) {
          setStatus("unavailable");
          setError("The market ticks gateway is unavailable.");
        } else {
          setStatus("disconnected");
          setError("The MT5 snapshot stream is unavailable.");
        }
      }

      if (stopped) return;
      const delay = Math.min(
        maxRetryMs,
        initialRetryMs * 2 ** Math.min(retryRef.current, 4),
      );
      retryRef.current += 1;
      retryTimer = setTimeout(() => void connect(), delay);
    };

    void connect();
    return () => {
      stopped = true;
      controller?.abort();
      if (retryTimer !== null) clearTimeout(retryTimer);
    };
  }, [isDocumentVisible, symbols, initialRetryMs, maxRetryMs, enabled]);

  return { snapshot, status, error };
}
