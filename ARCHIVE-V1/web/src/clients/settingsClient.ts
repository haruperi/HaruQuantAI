"use client"

import { agenticApiData } from "@/clients/agenticApi"
import { unknownRecordSchema } from "@/validators/agentic-generic"

export const settingsClient = {
  getAgenticFirmSnapshot() {
    return agenticApiData("/api/settings/agentic-firm", {
      schema: unknownRecordSchema,
      contractName: "AgenticFirmSettingsSnapshot",
      staleWarningLabel: "agentic firm settings",
    })
  },
}
