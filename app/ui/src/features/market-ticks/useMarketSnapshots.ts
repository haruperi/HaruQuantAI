"use client";

import { useEffect, useRef, useState } from "react";

import { apiClients, unwrapData, type StreamEvent } from "../../clients";

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

/** Consume configured MT5 snapshots through HaruQuantAI's authenticated SSE client. */
export function useMarketSnapshots(): MarketSnapshotState {
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
    if (!isDocumentVisible) {
      setStatus("disconnected");
      return undefined;
    }
    let stopped = false;
    let controller: AbortController | null = null;
    let retryTimer: ReturnType<typeof setTimeout> | null = null;

    const connect = async (): Promise<void> => {
      if (stopped) return;
      setStatus("connecting");
      controller = new AbortController();
      try {
        const settings = unwrapData(await apiClients.settings.readSystem());
        const symbols = (settings.settings.MT5_SNAPSHOT_SYMBOLS ?? "")
          .split(",")
          .map((symbol) => symbol.trim())
          .filter(Boolean);
        if (symbols.length === 0) {
          setStatus("unavailable");
          setError("MT5 snapshot symbols are not configured.");
          return;
        }

        for await (const event of apiClients.data.snapshotStream(symbols, {
          signal: controller.signal,
        })) {
          if (stopped) return;
          const mapped = mapSnapshotEvent(event);
          if (!mapped) continue;
          retryRef.current = 0;
          setSnapshot(mapped);
          setStatus("connected");
          setError(null);
        }
        if (!stopped) setStatus("disconnected");
      } catch {
        if (stopped || controller.signal.aborted) return;
        setStatus("disconnected");
        setError("The MT5 snapshot stream is unavailable.");
      }

      if (stopped) return;
      const delay = Math.min(
        MAX_RETRY_MS,
        INITIAL_RETRY_MS * 2 ** Math.min(retryRef.current, 4),
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
  }, [isDocumentVisible]);

  return { snapshot, status, error };
}
