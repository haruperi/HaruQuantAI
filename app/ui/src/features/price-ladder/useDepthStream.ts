"use client";

import { useEffect, useRef, useState } from "react";

import { apiClients, type StreamEvent } from "../../clients";

export type DepthStatus = "connecting" | "connected" | "disconnected" | "unavailable";

/** One real bid or ask price level, exactly as the order-book feed reports it. */
export interface DepthLevel {
  readonly price: number;
  readonly volume: number;
}

/** One symbol's real Depth-of-Market read, or an explicit read error. */
export interface DepthBookView {
  readonly symbol: string;
  readonly bids: readonly DepthLevel[];
  readonly asks: readonly DepthLevel[];
  readonly error: { readonly code: number } | null;
}

interface DepthState {
  readonly book: DepthBookView | null;
  readonly sequence: number | null;
  readonly stale: boolean;
  readonly status: DepthStatus;
  readonly error: string | null;
}

const INITIAL_RETRY_MS = 1_000;
const MAX_RETRY_MS = 10_000;

function toLevel(value: unknown): DepthLevel | null {
  if (typeof value !== "object" || value === null) return null;
  const record = value as Record<string, unknown>;
  const price = Number(record.price);
  const volume = Number(record.volume);
  if (!Number.isFinite(price) || !Number.isFinite(volume)) return null;
  return { price, volume };
}

function toLevels(value: unknown): DepthLevel[] {
  if (!Array.isArray(value)) return [];
  return value.map(toLevel).filter((level): level is DepthLevel => level !== null);
}

/** Extract one requested symbol's real book (or read error) from a depth event. */
function mapDepthEvent(event: StreamEvent, symbol: string): DepthBookView | null {
  const payload = event.payload;
  if (!payload) return null;
  const books = Array.isArray(payload.books) ? payload.books : [];
  const found = books.find(
    (entry): entry is Record<string, unknown> =>
      typeof entry === "object" && entry !== null &&
      (entry as Record<string, unknown>).symbol === symbol
  );
  if (found) {
    return {
      symbol,
      bids: toLevels(found.bids),
      asks: toLevels(found.asks),
      error: null,
    };
  }
  const errors = Array.isArray(payload.errors) ? payload.errors : [];
  const bookError = errors.find(
    (entry): entry is Record<string, unknown> =>
      typeof entry === "object" && entry !== null &&
      (entry as Record<string, unknown>).symbol === symbol
  );
  if (bookError) {
    const code = Number(bookError.code);
    return {
      symbol,
      bids: [],
      asks: [],
      error: { code: Number.isFinite(code) ? code : 0 },
    };
  }
  return null;
}

/** Consume one real symbol's Depth-of-Market feed through the authenticated SSE client. */
export function useDepthStream(symbol: string): DepthState {
  const [book, setBook] = useState<DepthBookView | null>(null);
  const [sequence, setSequence] = useState<number | null>(null);
  const [stale, setStale] = useState(false);
  const [status, setStatus] = useState<DepthStatus>("connecting");
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
    if (!symbol) {
      setStatus("unavailable");
      setError("No symbol selected.");
      return undefined;
    }
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
        for await (const event of apiClients.data.depthStream([symbol], {
          signal: controller.signal,
        })) {
          if (stopped) return;
          const mapped = mapDepthEvent(event, symbol);
          if (!mapped) continue;
          retryRef.current = 0;
          setBook(mapped);
          setSequence(event.sequence);
          setStale(event.payload?.stale === true);
          setStatus("connected");
          setError(null);
        }
        if (!stopped) setStatus("disconnected");
      } catch {
        if (stopped || controller.signal.aborted) return;
        setStatus("disconnected");
        setError("The Depth-of-Market stream is unavailable.");
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
  }, [symbol, isDocumentVisible]);

  return { book, sequence, stale, status, error };
}
