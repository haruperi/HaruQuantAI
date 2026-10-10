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
let activeSessionKey: string | null = null;
let persistenceWarning: string | null = null;
const authExpiredListeners = new Set<() => void>();

function sessionKey(baseUrl = hostBaseUrl()): string {
  const host = typeof window === 'undefined' ? baseUrl : new URL(baseUrl, window.location.origin).href;
  return `haruquantai.host-session.v1:${host}`;
}

export function getSessionPersistenceWarning(): string | null {
  return persistenceWarning;
}

function sessionStorage(): Storage | null {
  return typeof window === 'undefined' ? null : window.localStorage;
}

export function restoreSavedSession(baseUrl?: string): boolean {
  activeAuthToken = null;
  activeSessionKey = sessionKey(baseUrl);
  persistenceWarning = null;
  try {
    const serialized = sessionStorage()?.getItem(activeSessionKey);
    if (!serialized) return false;
    const saved: unknown = JSON.parse(serialized);
    if (typeof saved !== 'object' || saved === null) throw new Error('Invalid saved session');
    const record = saved as Record<string, unknown>;
    if (record.version !== 1 || typeof record.token !== 'string' || !record.token.trim() ||
        typeof record.expires_at !== 'string' || !Number.isFinite(Date.parse(record.expires_at)) ||
        Date.parse(record.expires_at) <= Date.now()) throw new Error('Invalid saved session');
    activeAuthToken = record.token;
    return true;
  } catch {
    setAuthToken(null);
    return false;
  }
}

function rememberSession(session: LoginResponse, baseUrl?: string): void {
  activeSessionKey = sessionKey(baseUrl);
  persistenceWarning = null;
  try {
    const storage = sessionStorage();
    if (session.expires_at) {
      storage?.setItem(activeSessionKey, JSON.stringify({ version: 1, token: session.token, expires_at: session.expires_at }));
    } else {
      storage?.removeItem(activeSessionKey);
    }
  } catch {
    persistenceWarning = 'Browser storage is unavailable. This session will end when the page is refreshed.';
  }
}

export function setAuthToken(token: string | null): void {
  activeAuthToken = token;
  if (token === null) {
    try {
      sessionStorage()?.removeItem(activeSessionKey ?? sessionKey());
    } catch {
      persistenceWarning = 'Browser storage is unavailable. The saved session could not be cleared.';
    }
  }
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
  expires_at?: string;
}

export interface LoginCredentials {
  password?: string;
}

export interface DomainClient {
  get<T>(path: string): Promise<T>;
  post<T>(path: string, body: unknown): Promise<T>;
  put<T>(path: string, body: unknown): Promise<T>;
  delete<T = unknown>(path: string): Promise<T>;
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

    if (config.signal?.aborted) throw new DOMException('Request canceled', 'AbortError');
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

    if (config.signal?.aborted) throw new DOMException('Request canceled', 'AbortError');
    return json.data as T;
  }

  return {
    get: <T>(path: string) => request<T>(path, { method: 'GET' }),
    post: <T>(path: string, body: unknown) => request<T>(path, { method: 'POST', body: JSON.stringify(body) }),
    put: <T>(path: string, body: unknown) => request<T>(path, { method: 'PUT', body: JSON.stringify(body) }),
    delete: <T>(path: string) => request<T>(path, { method: 'DELETE' }),
  };
}

export async function login(
  credentials: LoginCredentials = {},
  config: TransportConfig = {},
): Promise<LoginResponse> {
  const client = createDomainClient('/auth', config);
  const data = await client.post<LoginResponse>('/login', credentials);
  if (config.signal?.aborted) throw new DOMException('Login canceled', 'AbortError');
  if (!data || typeof data.token !== 'string' || !data.token.trim()) {
    setAuthToken(null);
    throw new ApiClientError('MALFORMED_RESPONSE', 'Host login returned no valid session', [], 502);
  }
  if (data.expires_at !== undefined && (typeof data.expires_at !== 'string' || !Number.isFinite(Date.parse(data.expires_at)) || Date.parse(data.expires_at) <= Date.now())) {
    setAuthToken(null);
    throw new ApiClientError('MALFORMED_RESPONSE', 'Host login returned an invalid session expiry', [], 502);
  }
  setAuthToken(data.token);
  rememberSession(data, config.baseUrl);
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
