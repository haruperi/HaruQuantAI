/**
 * FEAT-UI-EDIT_INPUTS feature instance (Partial slice: FR-UI-PRESERVE_DRAFTS).
 *
 * Registers the `ui.edit-inputs@1` capability manifest and owns the local
 * draft store. No widgets or workspaces this slice — `schema_form`,
 * `selection_table`, and `confirmation` remain mock-build lines completing
 * at the Stage 6 Data de-mock gate (6.15).
 */

import type { UiFeatureInstance } from "../../runtime/composition_bridge";
import { SPEC } from "./manifest";
import { DraftStore } from "./draft_store";

export class EditInputsFeature implements UiFeatureInstance {
  public readonly manifest = SPEC;
  public readonly draftStore: DraftStore;

  constructor() {
    this.draftStore = new DraftStore();
  }
}

export function createFeature(): EditInputsFeature {
  return new EditInputsFeature();
}
