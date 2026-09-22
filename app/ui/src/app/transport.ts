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

export interface TransportConfig {
  baseUrl?: string;
  fetchFn?: typeof fetch;
}

export interface DomainClient {
  get<T>(path: string): Promise<T>;
  post<T>(path: string, body: unknown): Promise<T>;
}

export function createDomainClient(routeBase: string, config: TransportConfig = {}): DomainClient {
  const baseUrl = config.baseUrl ?? '/api/v1';
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

    const response = await fetchFn(url, { ...options, headers });

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
  };
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
