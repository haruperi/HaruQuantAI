/**
 * Authentication client for the 3 auth operations.
 *
 * Each call delegates through the single `request` transport. Credentials are
 * sent only as request bodies; the opaque session is established via the
 * `hq_session` / `hq_csrf` cookies set by the backend response.
 */

import { z } from "zod";

import type { ApiResponse } from "./contracts";
import { authRoutes } from "./routes";
import { request, type RequestOptions } from "./request";

/** Request body for register/login (backend `_Credentials`). */
export interface Credentials {
  username: string;
  password: string;
}

/**
 * Response data for register/login (backend returns this dict literal).
 *
 * `runtime_profile` is optional: the backend's `AuthenticatedUser` model
 * already carries it (`"research"|"simulation"|"demo"|"live"`), but no
 * route returns it to the UI yet. It is declared here so account-mode
 * presentation (FR-UI-016) starts working the moment a route adds it,
 * without any further UI change; until then it is simply absent.
 */
export const sessionSchema = z.object({
  user_id: z.string().min(1),
  username: z.string().min(1),
  expires_at: z.string().min(1),
  runtime_profile: z.string().optional(),
});
export type Session = z.infer<typeof sessionSchema>;

/** Identity recovered from the server-side session via `GET /api/v1/auth/me`. */
export const identitySchema = sessionSchema;
export type Identity = z.infer<typeof identitySchema>;

/** Build common options for an auth write. */
function authOptions(
  body: unknown,
  overrides?: RequestOptions
): RequestOptions {
  return { schema: sessionSchema, body, ...overrides };
}

/** Register a new account and establish a session (HTTP 201). */
export function register(
  credentials: Credentials,
  options?: RequestOptions
): Promise<ApiResponse<Session>> {
  return request<Session>(authRoutes.register, authOptions(credentials, options));
}

/** Authenticate an existing account and establish a session (HTTP 200). */
export function login(
  credentials: Credentials,
  options?: RequestOptions
): Promise<ApiResponse<Session>> {
  return request<Session>(authRoutes.login, authOptions(credentials, options));
}

/** Revoke the caller's session (HTTP 204, bodyless success). */
export function logout(options?: RequestOptions): Promise<ApiResponse<null>> {
  return request<null>(authRoutes.logout, options);
}

/**
 * Recover the caller's non-secret identity from the server-side session.
 *
 * Hits `GET /api/v1/auth/me`: returns `{user_id, username, expires_at}` when
 * the cookie session is valid, 401 when missing/expired. This is the
 * server-authoritative identity source for `AuthProvider` recovery.
 */
export function me(options?: RequestOptions): Promise<ApiResponse<Identity>> {
  return request<Identity>(authRoutes.me, {
    schema: identitySchema,
    ...options,
  });
}

/** Aggregated auth client. */
export const auth = { register, login, logout, me };
