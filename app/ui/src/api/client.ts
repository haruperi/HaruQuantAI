/**
 * Typed client for HaruQuantAI versioned /api/v1 HTTP gateway.
 */

import type {
  ApiResponse,
  BatchExecutionRequest,
  BatchExecutionResult,
  CatalogView,
  ExportRequest,
  ExportResult,
  GraphDocument,
  GraphValidationResult,
  SingleExecutionRequest,
  SingleExecutionResult,
} from './contracts.generated';

export class ApiClientError extends Error {
  constructor(
    public readonly code: string,
    message: string,
    public readonly issues: Array<{ path: string; code: string; message: string }> = [],
    public readonly status?: number,
  ) {
    super(message);
    this.name = 'ApiClientError';
  }
}

export interface ApiClientConfig {
  baseUrl?: string;
  fetchFn?: typeof fetch;
}

export class HaruApiClient {
  private readonly baseUrl: string;
  private readonly fetchFn: typeof fetch;

  constructor(config: ApiClientConfig = {}) {
    this.baseUrl = config.baseUrl ?? '/api/v1';
    this.fetchFn =
      config.fetchFn ??
      (typeof window !== 'undefined' && window.fetch
        ? window.fetch.bind(window)
        : globalThis.fetch.bind(globalThis));
  }

  private async request<T>(
    path: string,
    options: RequestInit = {},
  ): Promise<T> {
    const url = `${this.baseUrl}${path}`;
    const requestId = `req-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
    const headers = new Headers(options.headers);
    headers.set('Accept', 'application/json');
    if (!headers.has('X-Request-Id')) {
      headers.set('X-Request-Id', requestId);
    }
    if (options.body && !headers.has('Content-Type')) {
      headers.set('Content-Type', 'application/json');
    }

    const response = await this.fetchFn(url, {
      ...options,
      headers,
    });

    let json: ApiResponse<T>;
    try {
      json = await response.json();
    } catch (err) {
      throw new ApiClientError(
        'MALFORMED_RESPONSE',
        `Failed to parse response as JSON: ${err}`,
        [],
        response.status,
      );
    }

    if (!response.ok || json.status === 'error') {
      const err = json.error ?? {
        code: `HTTP_${response.status}`,
        message: response.statusText || 'Request failed',
        issues: [],
      };
      throw new ApiClientError(err.code, err.message, err.issues ?? [], response.status);
    }

    return json.data as T;
  }

  async getHealth(): Promise<{
    status: string;
    version: string;
    services: Record<string, string>;
  }> {
    return this.request<{
      status: string;
      version: string;
      services: Record<string, string>;
    }>('/health', { method: 'GET' });
  }

  async getCatalog(): Promise<CatalogView> {
    return this.request<CatalogView>('/catalog', { method: 'GET' });
  }

  async selectCatalog(params: {
    enabled_refs?: string[];
    allowed_effects?: string[];
    allowed_kinds?: string[];
  }): Promise<{
    available_operations: Array<{ plugin_ref: string; operation_id: string }>;
    unavailable_reasons: Array<{ plugin_ref: string; operation_id: string; reason: string }>;
  }> {
    return this.request('/catalog/select', {
      method: 'POST',
      body: JSON.stringify(params),
    });
  }

  async validateGraph(graphDocument: GraphDocument): Promise<GraphValidationResult> {
    return this.request<GraphValidationResult>('/graphs/validate', {
      method: 'POST',
      body: JSON.stringify({ graph_document: graphDocument }),
    });
  }

  async evaluateExecution(
    request: SingleExecutionRequest,
  ): Promise<SingleExecutionResult> {
    return this.request<SingleExecutionResult>('/executions/evaluate', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async batchExecution(
    request: BatchExecutionRequest,
  ): Promise<BatchExecutionResult> {
    return this.request<BatchExecutionResult>('/executions/batch', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async exportExecution(request: ExportRequest): Promise<ExportResult> {
    return this.request<ExportResult>('/exports', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }
}

export const defaultApiClient = new HaruApiClient();
