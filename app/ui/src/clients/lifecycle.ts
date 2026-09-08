/** Scoped request and stream ownership for FEAT-UI-TYPED_BACKEND. */

import type { ApiResponse, StreamEvent } from "./contracts";
import { ApiClientError, request, type RequestOptions } from "./request";
import type { RouteContract } from "./routes";
import {
  openStream,
  type StreamTransportOptions,
} from "./stream";

const MAX_KEY_LENGTH = 128;
const MAX_STREAM_RECONNECTS = 1;
const SAFE_KEY = /^[A-Za-z0-9._:-]+$/;

/** Function boundary used to inject the request transport in offline tests. */
export type RequestTransport = typeof request;
/** Function boundary used to inject the stream transport in offline tests. */
export type StreamTransport = typeof openStream;
/** Listener for one validated stream event. */
export type StreamListener = (event: StreamEvent) => void;
/** Listener for a terminal stream failure. */
export type StreamErrorListener = (error: ApiClientError) => void;

/** Handle returned for one subscriber to a shared observation. */
export interface StreamSubscription {
  /** Settles when the shared underlying observation finishes. */
  readonly done: Promise<void>;
  /** Remove this subscriber; the final removal aborts the shared stream. */
  dispose(): void;
}

interface Subscriber {
  readonly onEvent: StreamListener;
  readonly onError?: StreamErrorListener;
}

interface SharedStream {
  readonly controller: AbortController;
  readonly subscribers: Set<Subscriber>;
  done: Promise<void>;
  lastSequence?: number;
}

/** Assert that an ownership key contains no payload or credential material. */
function validateKey(key: string): void {
  if (
    key.length === 0 ||
    key.length > MAX_KEY_LENGTH ||
    !SAFE_KEY.test(key)
  ) {
    throw new ApiClientError({
      message: "client lifecycle key is invalid",
      status: 0,
      code: "VALIDATION_FAILED",
    });
  }
}

/** Link an optional caller signal to an owned controller. */
function linkSignal(
  source: AbortSignal | undefined,
  target: AbortController,
): () => void {
  if (!source) return () => undefined;
  if (source.aborted) {
    target.abort(source.reason);
    return () => undefined;
  }
  const abort = (): void => target.abort(source.reason);
  source.addEventListener("abort", abort, { once: true });
  return () => source.removeEventListener("abort", abort);
}

/** Convert an unknown terminal failure to the public typed error. */
function typedStreamError(error: unknown): ApiClientError {
  if (error instanceof ApiClientError) return error;
  return new ApiClientError({
    message: "stream observation failed",
    status: 0,
    code: "UPSTREAM_UNAVAILABLE",
    retryable: false,
    cause: error,
  });
}

/**
 * Own latest-only requests and shared stream observations for one UI scope.
 *
 * Instances are explicit lifecycle resources: there is no global registry,
 * import-time I/O, or hidden provider fallback.
 */
export class TypedBackendLifecycle {
  private readonly requests = new Map<string, AbortController>();
  private readonly streams = new Map<string, SharedStream>();
  private readonly tasks = new Set<Promise<unknown>>();
  private disposed = false;

  public constructor(
    private readonly requestTransport: RequestTransport = request,
    private readonly streamTransport: StreamTransport = openStream,
  ) {}

  /** Whether this feature scope has been disposed. */
  public get isDisposed(): boolean {
    return this.disposed;
  }

  /**
   * Run the latest request for a presentation key and abort its predecessor.
   */
  public async requestLatest<T>(
    key: string,
    contract: RouteContract,
    options: RequestOptions = {},
  ): Promise<ApiResponse<T>> {
    this.assertAvailable();
    validateKey(key);
    this.requests.get(key)?.abort("superseded");
    const controller = new AbortController();
    const unlink = linkSignal(options.signal, controller);
    this.requests.set(key, controller);
    const operation = this.requestTransport<T>(contract, {
      ...options,
      signal: controller.signal,
    });
    this.tasks.add(operation);
    try {
      return await operation;
    } finally {
      unlink();
      this.tasks.delete(operation);
      if (this.requests.get(key) === controller) {
        this.requests.delete(key);
      }
    }
  }

  /**
   * Share one cursor-resuming stream among subscribers with the same key.
   */
  public subscribe(
    key: string,
    contract: RouteContract,
    options: StreamTransportOptions,
    onEvent: StreamListener,
    onError?: StreamErrorListener,
  ): StreamSubscription {
    this.assertAvailable();
    validateKey(key);
    const subscriber: Subscriber = { onEvent, onError };
    let shared = this.streams.get(key);
    if (!shared) {
      const controller = new AbortController();
      const unlink = linkSignal(options.signal, controller);
      const subscribers = new Set<Subscriber>();
      const created: SharedStream = {
        controller,
        subscribers,
        done: Promise.resolve(),
      };
      const done = this.consumeShared(key, contract, options, created).finally(
        () => {
          unlink();
          this.tasks.delete(done);
          if (this.streams.get(key) === created) this.streams.delete(key);
        },
      );
      created.done = done;
      shared = created;
      this.streams.set(key, shared);
      this.tasks.add(done);
    }
    shared.subscribers.add(subscriber);
    let active = true;
    return {
      done: shared.done,
      dispose: () => {
        if (!active) return;
        active = false;
        shared?.subscribers.delete(subscriber);
        if (shared?.subscribers.size === 0) shared.controller.abort("unused");
      },
    };
  }

  /** Abort and await all feature-owned effects. Idempotent. */
  public async dispose(): Promise<void> {
    if (this.disposed) return;
    this.disposed = true;
    for (const controller of this.requests.values()) controller.abort("disposed");
    for (const stream of this.streams.values()) stream.controller.abort("disposed");
    await Promise.allSettled([...this.tasks]);
    this.requests.clear();
    this.streams.clear();
    this.tasks.clear();
  }

  private assertAvailable(): void {
    if (this.disposed) {
      throw new ApiClientError({
        message: "typed backend capability is unavailable",
        status: 0,
        code: "DEPENDENCY_UNAVAILABLE",
      });
    }
  }

  private async consumeShared(
    key: string,
    contract: RouteContract,
    options: StreamTransportOptions,
    shared: SharedStream,
  ): Promise<void> {
    let reconnects = 0;
    while (!shared.controller.signal.aborted) {
      try {
        for await (const event of this.streamTransport(contract, {
          ...options,
          resumeAfter: shared.lastSequence ?? options.resumeAfter,
          signal: shared.controller.signal,
        })) {
          shared.lastSequence = event.sequence;
          for (const subscriber of [...shared.subscribers]) {
            subscriber.onEvent(event);
          }
        }
        return;
      } catch (error) {
        if (shared.controller.signal.aborted) return;
        const typed = typedStreamError(error);
        if (typed.retryable && reconnects < MAX_STREAM_RECONNECTS) {
          reconnects += 1;
          continue;
        }
        for (const subscriber of [...shared.subscribers]) {
          subscriber.onError?.(typed);
        }
        return;
      }
    }
    if (this.streams.get(key) === shared) this.streams.delete(key);
  }
}
