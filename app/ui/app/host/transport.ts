/**
 * Universal UI-host transport for HaruQuantAI domain pairs.
 *
 * The host owns the request/response envelope, error shape, request IDs, and
 * the domain-client factory — nothing else. Workspace and plugin folders own
 * their clients, route bases, and contracts with their backend counterparts.
 *
 * The default base URL and all route bases used by domain clients are
 * provisional until the backend host architecture ratifies the mounting scheme.
 */

export interface ApiErrorBody {
  code: string;
  message: string;
  issues?: ValidationIssue[];
}

export interface ApiResponse<T> {
  api_version?: string;
  request_id?: string;
  status: 'success' | 'error';
  data?: T;
  error?: ApiErrorBody;
}

export class ApiClientError extends Error {
  constructor(
    public readonly code: string,
    message: string,
    public readonly issues: ValidationIssue[] = [],
    public readonly status?: number,
  ) {
    super(message);
    this.name = 'ApiClientError';
  }
}

let activeAuthToken: string | null = null;
const authExpiredListeners = new Set<() => void>();

export function setAuthToken(token: string | null): void {
  activeAuthToken = token;
}

export function getAuthToken(): string | null {
  return activeAuthToken;
}

export function subscribeAuthExpired(listener: () => void): () => void {
  authExpiredListeners.add(listener);
  return () => { authExpiredListeners.delete(listener); };
}

export interface TransportConfig {
  baseUrl?: string;
  fetchFn?: typeof fetch;
  authToken?: string | (() => string | null);
  signal?: AbortSignal;
}

export interface LoginResponse {
  token: string;
}

export interface LoginCredentials {
  username?: string;
  password?: string;
}

export interface DomainClient {
  get<T>(path: string): Promise<T>;
  post<T>(path: string, body: unknown): Promise<T>;
  put<T>(path: string, body: unknown): Promise<T>;
}

export function hostBaseUrl(): string {
  if (typeof window !== 'undefined' && window.location.port === '3000' &&
      ['127.0.0.1', 'localhost'].includes(window.location.hostname)) {
    return `http://${window.location.hostname}:8000/api/v1`;
  }
  return '/api/v1';
}

export function createDomainClient(routeBase: string, config: TransportConfig = {}): DomainClient {
  const baseUrl = config.baseUrl ?? hostBaseUrl();
  const fetchFn =
    config.fetchFn ??
    (typeof window !== 'undefined' && window.fetch
      ? window.fetch.bind(window)
      : globalThis.fetch.bind(globalThis));

  async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const url = `${baseUrl}${routeBase}${path}`;
    const requestId = `req-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
    const headers = new Headers(options.headers);
    headers.set('Accept', 'application/json');
    if (!headers.has('X-Request-Id')) {
      headers.set('X-Request-Id', requestId);
    }
    if (options.body && !headers.has('Content-Type')) {
      headers.set('Content-Type', 'application/json');
    }
    if (!headers.has('Authorization')) {
      const resolvedToken =
        typeof config.authToken === 'function'
          ? config.authToken()
          : (config.authToken ?? activeAuthToken);
      if (resolvedToken) {
        headers.set('Authorization', `Bearer ${resolvedToken}`);
      }
    }

    const response = await fetchFn(url, { ...options, headers, signal: config.signal ?? options.signal });

    if (response.status === 401 && routeBase !== '/auth') {
      setAuthToken(null);
      for (const listener of authExpiredListeners) listener();
    }

    let json: ApiResponse<T>;
    try {
      json = await response.json();
    } catch (err) {
      throw new ApiClientError('MALFORMED_RESPONSE', `Failed to parse response as JSON: ${err}`, [], response.status);
    }

    if (!response.ok || json.status === 'error') {
      const err = json.error ?? {
        code: `HTTP_${response.status}`,
        message: response.statusText || 'Request failed',
      };
      throw new ApiClientError(err.code, err.message, err.issues ?? [], response.status);
    }

    return json.data as T;
  }

  return {
    get: <T>(path: string) => request<T>(path, { method: 'GET' }),
    post: <T>(path: string, body: unknown) => request<T>(path, { method: 'POST', body: JSON.stringify(body) }),
    put: <T>(path: string, body: unknown) => request<T>(path, { method: 'PUT', body: JSON.stringify(body) }),
  };
}

export async function login(
  credentials: LoginCredentials = { username: 'operator' },
  config: TransportConfig = {},
): Promise<LoginResponse> {
  const client = createDomainClient('/auth', config);
  const data = await client.post<LoginResponse>('/login', credentials);
  if (data?.token) {
    setAuthToken(data.token);
  }
  return data;
}

// ---------------------------------------------------------------------------
// Frozen transitional host execution documents (pre-reset gateway shapes).
//
// These documents are host-owned because they cross domain boundaries through
// the app store (Builder/Retester/Optimizer produce them; Results consumes
// them). They mirror the deleted /api/v1 gateway contract verbatim, are NOT
// extended, and will be replaced by the ratified host contract. Domain pairs
// must not add workspace-specific fields here.
// ---------------------------------------------------------------------------

export interface ValidationIssue {
  path: string;
  code: string;
  message: string;
}

export interface NumericalPolicy {
  tolerance: number;
  nan_policy: string;
  missing_policy: string;
}

export interface ExecutionReproducibilityRecord {
  graph_id: string;
  graph_fingerprint: string;
  catalog_fingerprint: string;
  dependency_fingerprint: string;
  plugin_versions: [string, string][];
  source_digests: [string, string][];
  normalized_parameters: Record<string, unknown>;
  input_hash: string;
  output_hash: string;
  seed?: number | null;
  numerical_policy: NumericalPolicy;
  engine_version: string;
  elapsed_seconds: number;
  status: string;
}

export interface SingleExecutionResult {
  success: boolean;
  outputs: Record<string, unknown>;
  reproducibility?: ExecutionReproducibilityRecord | null;
  issues: ValidationIssue[];
  elapsed_seconds: number;
}

export interface BatchTrial {
  trial_id: string;
  parameter_overrides?: Record<string, Record<string, unknown>>;
  metadata?: Record<string, unknown>;
}

export interface BatchTrialResult {
  trial_id: string;
  success: boolean;
  outputs: Record<string, unknown>;
  issues: ValidationIssue[];
  elapsed_seconds: number;
}

export interface BatchExecutionResult {
  success: boolean;
  trials: BatchTrialResult[];
  issues: ValidationIssue[];
  elapsed_seconds: number;
}


/** Backend-owned boot outcomes; unavailable contributions never count as successful. */
export interface BootStage {
  stage: string;
  label: string;
  outcome: 'pending' | 'running' | 'succeeded' | 'unavailable' | 'failed' | 'cancelled';
  reason: string;
  elapsed_ms: number;
}
export interface BootSnapshot {
  state: string;
  sequence: number;
  stages: BootStage[];
}
export interface InitializationData {
  settings: unknown;
  boot: BootSnapshot;
  first_run: boolean;
  requirements: string[];
  catalog: { domains: unknown[]; issues: unknown[] };
}
export interface BootStream {
  ready: Promise<void>;
  close: () => void;
}

/** Authenticate in the first frame so bearer tokens never enter URLs or logs. */
export function connectBootStream(
  signal: AbortSignal,
  onSnapshot: (snapshot: BootSnapshot) => void,
  onFailure: (message: string) => void,
  socketFactory: (url: string) => WebSocket = url => new WebSocket(url),
): BootStream {
  const base = new URL(hostBaseUrl(), typeof window === 'undefined' ? 'http://localhost' : window.location.href);
  base.protocol = base.protocol === 'https:' ? 'wss:' : 'ws:';
  base.pathname = '/ws/updates';
  const socket = socketFactory(base.toString());
  let current: BootSnapshot | null = null;
  let intentional = false;
  let settled = false;
  let resolveReady: () => void;
  let rejectReady: (error: Error) => void;
  const ready = new Promise<void>((resolve, reject) => { resolveReady = resolve; rejectReady = reject; });
  const timer = setTimeout(() => fail('Host handshake timed out'), 10000);
  const heartbeat = setInterval(() => { if (socket.readyState === 1) socket.send(JSON.stringify({ type: 'ping' })); }, 10000);
  const close = () => {
    intentional = true;
    clearTimeout(timer);
    clearInterval(heartbeat);
    signal.removeEventListener('abort', close);
    socket.close();
    if (!settled) { settled = true; rejectReady(new Error('Host connection cancelled')); }
  };
  const fail = (message: string) => {
    if (intentional) return;
    if (!settled) { settled = true; rejectReady(new Error(message)); }
    onFailure(message);
    close();
  };
  socket.onopen = () => socket.send(JSON.stringify({ token: getAuthToken(), topics: ['boot.progress'] }));
  socket.onmessage = event => {
    try {
      const payload = JSON.parse(String(event.data));
      if (payload.type === 'resync_required') { fail('Host progress overflow; reconnect'); return; }
      if (payload.type === 'snapshot') {
        if (!payload.boot || !Array.isArray(payload.boot.stages)) throw new Error('Invalid boot snapshot');
        current = payload.boot as BootSnapshot;
        onSnapshot(current);
        clearTimeout(timer);
        settled = true;
        resolveReady();
      } else if (payload.channel === 'boot.progress' && current) {
        current = { ...current, sequence: payload.sequence, stages: current.stages.map(stage => stage.stage === payload.data.stage ? payload.data : stage) };
        onSnapshot(current);
      } else if (payload.type === 'heartbeat' && current) {
        current = { ...current, state: payload.state };
        onSnapshot(current);
      }
    } catch { fail('Invalid host progress response'); }
  };
  socket.onerror = () => fail('Host progress connection failed');
  socket.onclose = () => fail('Host progress connection closed');
  signal.addEventListener('abort', close, { once: true });
  if (signal.aborted) close();
  return { ready, close };
}
