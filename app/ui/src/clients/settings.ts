/**
 * Settings client for the 2 user-settings operations (read + idempotent update).
 */

import { z } from "zod";

import type { ApiResponse } from "./contracts";
import { settingsRoutes } from "./routes";
import { request, type RequestOptions } from "./request";

/** Versioned user settings record (backend `UserSettingsRecord`). */
export const userSettingsSchema = z.object({
  user_id: z.string().min(1),
  settings: z.record(z.string(), z.string()),
  version: z.number().int().min(0),
  updated_at: z.string().min(1),
});
export type UserSettings = z.infer<typeof userSettingsSchema>;

/** Update request body (backend `_SettingsUpdate`). */
export interface SettingsUpdate {
  settings: Record<string, string>;
  expected_version: number;
}

/** Read the caller's versioned settings (requires `settings:read`). */
export function read(
  options?: RequestOptions
): Promise<ApiResponse<UserSettings>> {
  return request<UserSettings>(settingsRoutes.read, {
    schema: userSettingsSchema,
    ...options,
  });
}

/**
 * Update the caller's settings (requires `settings:write`).
 *
 * The route requires an idempotency key; when none is supplied the transport
 * generates one automatically.
 */
export function update(
  updateBody: SettingsUpdate,
  options?: RequestOptions
): Promise<ApiResponse<UserSettings>> {
  return request<UserSettings>(settingsRoutes.update, {
    schema: userSettingsSchema,
    body: updateBody,
    ...options,
  });
}

/** Aggregated settings client. */
export const settings = { read, update };
