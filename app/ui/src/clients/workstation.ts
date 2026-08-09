"";
import { z } from "zod";
import type { ApiResponse } from "./contracts";
import { request, type RequestOptions } from "./request";
import { workstationRoutes } from "./routes";

export const workstationSchema = z.object({
  schema: z.literal("OperationalWorkstation"), contract_version: z.literal("v1"),
  version: z.number().int().nonnegative(), as_of: z.string(),
  freshness: z.record(z.string(), z.unknown()), panels: z.record(z.string(), z.unknown()),
});
export type WorkstationReadModel = z.infer<typeof workstationSchema>;

export function readWorkstation(options?: RequestOptions): Promise<ApiResponse<WorkstationReadModel>> {
  return request(workstationRoutes.read, { schema: workstationSchema, ...options });
}

export function sendWorkstationCommand(body: Record<string, unknown>, options?: RequestOptions): Promise<ApiResponse<Record<string, unknown>>> {
  return request(workstationRoutes.command, { schema: z.record(z.string(), z.unknown()), body, ...options });
}

export const workstation = { read: readWorkstation, command: sendWorkstationCommand };
