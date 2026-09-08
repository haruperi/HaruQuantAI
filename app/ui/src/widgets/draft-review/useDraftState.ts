import { useCallback, useMemo, useState } from "react";

import type {
  DraftDiffEntry,
  DraftFieldValidation,
  DraftState,
  ValidationSummary,
} from "./contracts";

/** Computes a simple deterministic pseudo-hash for object comparison. */
export function computeObjectHash(value: unknown): string {
  if (value === null) return "null";
  if (value === undefined) return "undefined";
  if (typeof value !== "object") return `${typeof value}:${String(value)}`;

  if (Array.isArray(value)) {
    return `[${value.map(computeObjectHash).join(",")}]`;
  }

  const sortedKeys = Object.keys(value as Record<string, unknown>).sort();
  const entries = sortedKeys.map(
    (k) => `${k}:${computeObjectHash((value as Record<string, unknown>)[k])}`,
  );
  return `{${entries.join(";")}}`;
}

export interface UseDraftStateOptions<T extends Record<string, unknown>> {
  readonly initialData: T;
  readonly clientValidators?: Partial<
    Record<keyof T, (value: unknown, allDraft: T) => string | undefined>
  >;
  readonly authoritativeErrors?: readonly DraftFieldValidation[];
  readonly warnOnUnsavedChanges?: boolean;
}

export interface UseDraftStateReturn<T extends Record<string, unknown>> {
  readonly state: DraftState<T>;
  readonly diffs: readonly DraftDiffEntry[];
  readonly validation: ValidationSummary;
  readonly updateField: <K extends keyof T>(field: K, value: T[K]) => void;
  readonly resetDraft: () => void;
  readonly commitDraft: () => void;
  readonly canSafelyClose: () => boolean;
}

export function useDraftState<T extends Record<string, unknown>>({
  initialData,
  clientValidators = {},
  authoritativeErrors = [],
  warnOnUnsavedChanges = true,
}: UseDraftStateOptions<T>): UseDraftStateReturn<T> {
  const [original, setOriginal] = useState<T>(initialData);
  const [draft, setDraft] = useState<T>(initialData);

  // Compute dirty fields by comparing draft to original
  const { dirtyFields, isDirty } = useMemo(() => {
    const dirty: string[] = [];
    const keys = Array.from(
      new Set([...Object.keys(original), ...Object.keys(draft)]),
    );

    for (const key of keys) {
      const origVal = original[key];
      const draftVal = draft[key];
      if (computeObjectHash(origVal) !== computeObjectHash(draftVal)) {
        dirty.push(key);
      }
    }

    return { dirtyFields: dirty, isDirty: dirty.length > 0 };
  }, [original, draft]);

  const candidateHash = useMemo(() => computeObjectHash(draft), [draft]);

  const state: DraftState<T> = useMemo(
    () => ({
      original,
      draft,
      isDirty,
      dirtyFields,
      candidateHash,
    }),
    [original, draft, isDirty, dirtyFields, candidateHash],
  );

  // Generate structured diff entries
  const diffs: readonly DraftDiffEntry[] = useMemo(() => {
    const keys = Array.from(
      new Set([...Object.keys(original), ...Object.keys(draft)]),
    );
    return keys.map((key) => {
      const origVal = original[key];
      const draftVal = draft[key];
      const fieldDirty = dirtyFields.includes(key);

      return {
        field: key,
        label: key.charAt(0).toUpperCase() + key.slice(1),
        originalValue: origVal,
        draftValue: draftVal,
        isDirty: fieldDirty,
      };
    });
  }, [original, draft, dirtyFields]);

  // Compute validation summary combining client hints and authoritative errors
  const validation: ValidationSummary = useMemo(() => {
    const clientErrors: DraftFieldValidation[] = [];
    const clientHints: DraftFieldValidation[] = [];

    for (const [key, validator] of Object.entries(clientValidators)) {
      if (typeof validator === "function") {
        const errorMsg = validator(draft[key], draft);
        if (errorMsg) {
          clientErrors.push({
            field: key,
            message: errorMsg,
            severity: "error",
            source: "client",
          });
        } else if (dirtyFields.includes(key)) {
          clientHints.push({
            field: key,
            message: "Field modified in current draft",
            severity: "hint",
            source: "client",
          });
        }
      }
    }

    const allErrors = [
      ...clientErrors,
      ...authoritativeErrors.filter((e) => e.severity === "error"),
    ];
    const allWarnings = authoritativeErrors.filter(
      (e) => e.severity === "warning",
    );
    const allHints = [
      ...clientHints,
      ...authoritativeErrors.filter((e) => e.severity === "hint"),
    ];

    return {
      isValid: allErrors.length === 0,
      errors: allErrors,
      warnings: allWarnings,
      hints: allHints,
    };
  }, [clientValidators, draft, authoritativeErrors, dirtyFields]);

  const updateField = useCallback(<K extends keyof T>(field: K, value: T[K]) => {
    setDraft((prev) => ({
      ...prev,
      [field]: value,
    }));
  }, []);

  const resetDraft = useCallback(() => {
    setDraft(original);
  }, [original]);

  const commitDraft = useCallback(() => {
    setOriginal(draft);
  }, [draft]);

  const canSafelyClose = useCallback(() => {
    if (!isDirty || !warnOnUnsavedChanges) return true;
    return false;
  }, [isDirty, warnOnUnsavedChanges]);

  return {
    state,
    diffs,
    validation,
    updateField,
    resetDraft,
    commitDraft,
    canSafelyClose,
  };
}
