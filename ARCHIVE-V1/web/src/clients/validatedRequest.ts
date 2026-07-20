"use client"

import type { z } from "zod"

import { request } from "@/lib/api/request"
import { validateContract } from "@/validators/agentic-contracts"

export async function validatedRequest<T>(
  path: string,
  schema: z.ZodType<T>,
  contractName: string,
  init?: RequestInit,
): Promise<T> {
  const payload = await request<unknown>(path, init)
  return validateContract(schema, payload, contractName)
}
