/** Source-backed SQX 145 capability presentation; no execution contract. */
import rawCapabilities from "./capabilities.json";

export interface CapabilityStarter {
  key: string;
  label: string;
  prompt?: string;
  action?: string;
}

export interface Capability {
  id: string;
  icon: string;
  title: string;
  shortDescription: string;
  description: string;
  inputPlaceholder: string;
  starters: CapabilityStarter[];
}

export const capabilities: readonly Capability[] = rawCapabilities;

export const serviceUnavailable =
  "Assistant service unavailable. Drafts stay in this workspace until you leave; messages and files are not sent.";

export const brainSections = [
  {
    name: "Memory",
    path: "MEMORY.md",
    description:
      "Facts and preferences the assistant remembers between conversations.",
  },
  {
    name: "Knowledge",
    path: "knowledge/",
    description: "Research notes, verdicts, profiles, backlogs and analyses.",
  },
  {
    name: "Skills",
    path: "skills/",
    description:
      "Reusable procedures, with drafts awaiting review before promotion.",
  },
  {
    name: "State",
    path: "state/",
    description:
      "Session and continuation state owned by the assistant service.",
  },
] as const;
