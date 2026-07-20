import { z } from "zod"

export const unknownRecordSchema = z.record(z.string(), z.unknown())
export const unknownRecordListSchema = z.array(unknownRecordSchema)
export const stringListSchema = z.array(z.string())
