/**
 * Settings client for the 2 user-settings operations (read + idempotent update).
 */

import { z } from "zod";

import type { ApiResponse } from "./contracts";
import { settingsRoutes } from "./routes";
import { request, type RequestOptions } from "./request";

/** Versioned user settings projection from the unified backend settings record. */
export const userSettingsSchema = z.object({
  user_id: z.string().min(1),
  settings: z.record(z.string(), z.string()),
  version: z.number().int().min(0),
  updated_at: z.string().min(1),
});
export type UserSettings = z.infer<typeof userSettingsSchema>;

export const systemSettingsSchema = z.object({
  scope: z.literal("system"),
  subject_id: z.string().min(1),
  user_id: z.null(),
  settings: z.record(z.string(), z.string()),
  version: z.number().int().min(0),
  updated_at: z.string().min(1),
  restart_required: z.boolean().default(false),
});
export type SystemSettings = z.infer<typeof systemSettingsSchema>;

export const systemSettingDefinitionSchema = z.object({
  key: z.string().min(1),
  label: z.string().min(1),
  description: z.string(),
  value_kind: z.string().min(1),
  allowed_values: z.array(z.string()),
  minimum: z.number().nullable(),
  maximum: z.number().nullable(),
  // `hot` settings take effect on the next read; `restart_required` ones do
  // not. ACCOUNT_MODE is the first hot definition the manifest declares.
  activation: z.enum(["hot", "restart_required"]),
});
export type SystemSettingDefinition = z.infer<typeof systemSettingDefinitionSchema>;

export const credentialStatusSchema = z.object({
  slot: z.string().min(1),
  label: z.string().min(1),
  fields: z.array(z.string()),
  activation: z.literal("restart_required"),
  configured: z.boolean(),
  version: z.number().int().min(0),
  updated_at: z.string().nullable(),
});
export type CredentialStatus = z.infer<typeof credentialStatusSchema>;

const credentialWriteResultSchema = z.object({
  slot: z.string().min(1),
  configured: z.literal(true),
  version: z.number().int().positive(),
  updated_at: z.string().min(1),
  activation: z.literal("restart_required"),
});

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

export function readSystem(options?: RequestOptions): Promise<ApiResponse<SystemSettings>> {
  return request<SystemSettings>(settingsRoutes.read, {
    schema: systemSettingsSchema,
    query: { scope: "system" },
    ...options,
  });
}

export function updateSystem(
  settings: Record<string, string>,
  expectedVersion: number,
  options?: RequestOptions,
): Promise<ApiResponse<SystemSettings>> {
  return request<SystemSettings>(settingsRoutes.update, {
    schema: systemSettingsSchema,
    body: { settings, expected_version: expectedVersion, scope: "system" },
    ...options,
  });
}

export function readManifest(options?: RequestOptions): Promise<ApiResponse<SystemSettingDefinition[]>> {
  return request<SystemSettingDefinition[]>(settingsRoutes.manifest, {
    schema: z.array(systemSettingDefinitionSchema),
    ...options,
  });
}

export function readCredentials(options?: RequestOptions): Promise<ApiResponse<CredentialStatus[]>> {
  return request<CredentialStatus[]>(settingsRoutes.credentials, {
    schema: z.array(credentialStatusSchema),
    ...options,
  });
}

export function updateCredential(
  slot: string,
  material: Record<string, string>,
  options?: RequestOptions,
): Promise<ApiResponse<z.infer<typeof credentialWriteResultSchema>>> {
  return request(settingsRoutes.updateCredential, {
    schema: credentialWriteResultSchema,
    pathParams: { slot },
    body: { material },
    ...options,
  });
}

/** Aggregated settings client. */
export const settings = {
  read,
  update,
  readSystem,
  updateSystem,
  readManifest,
  readCredentials,
  updateCredential,
};
