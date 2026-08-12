'use client';

import React, { useEffect, useState } from 'react';
import { X } from 'lucide-react';

import { useTradingStore } from '../../../store/useTradingStore';
import {
  apiClients,
  unwrapData,
  type CredentialStatus,
  type SystemSettingDefinition,
} from '@/clients';

/**
 * UTC-offset options for the display-timezone setting.
 *
 * The backend TIMEZONE definition validates as a free string (no
 * allowed_values), so the offset label is stored directly as the value
 * (e.g. "UTC+2"). Range covers all real-world offsets from UTC-12 to UTC+14,
 * with UTC kept at its natural position in the list.
 */
const TIMEZONE_OPTIONS: readonly string[] = Object.freeze([
  "UTC-12", "UTC-11", "UTC-10", "UTC-9", "UTC-8", "UTC-7", "UTC-6",
  "UTC-5", "UTC-4", "UTC-3", "UTC-2", "UTC-1", "UTC",
  "UTC+1", "UTC+2", "UTC+3", "UTC+4", "UTC+5", "UTC+6", "UTC+7",
  "UTC+8", "UTC+9", "UTC+10", "UTC+11", "UTC+12", "UTC+13", "UTC+14",
]);

/** Boolean select option pairs: display label -> canonical stored value. */
const BOOLEAN_OPTIONS: ReadonlyArray<{ label: string; value: string }> = Object.freeze([
  { label: "Disabled", value: "false" },
  { label: "Enabled", value: "true" },
]);

/** Manifest key for the display-timezone setting (curated UTC dropdown). */
const TIMEZONE_KEY = "TIMEZONE";

/**
 * Classify a manifest definition into a field-control kind.
 *
 * Args:
 *   definition: One system-setting definition from the backend manifest.
 *
 * Returns:
 *   "enum" for manifest-provided allowed values, "boolean" for value_kind
 *   boolean, "timezone" for the curated UTC-offset list, else "text".
 */
function fieldKind(definition: SystemSettingDefinition): "enum" | "boolean" | "timezone" | "text" {
  if (definition.allowed_values.length > 0) return "enum";
  if (definition.value_kind === "boolean") return "boolean";
  if (definition.key === TIMEZONE_KEY) return "timezone";
  return "text";
}

/**
 * System Settings modal popup.
 *
 * Opens in-place over the workstation (no route change), mirroring the
 * CME-style cookie-settings interaction. Renders the database-backed system
 * settings and credential slots previously hosted on the standalone
 * `/workstation/settings` route. Visibility is driven by the zustand store
 * (`isSettingsOpen`), following the same pattern as `OrderTicketModal`.
 *
 * Credentials are write-only: stored values are never returned to this modal.
 */
export const SystemSettingsModal: React.FC = () => {
  const { isSettingsOpen, closeSettings } = useTradingStore();

  const [manifest, setManifest] = useState<SystemSettingDefinition[]>([]);
  const [values, setValues] = useState<Record<string, string>>({});
  const [version, setVersion] = useState(0);
  const [credentials, setCredentials] = useState<CredentialStatus[]>([]);
  const [credentialValues, setCredentialValues] = useState<Record<string, Record<string, string>>>({});
  const [message, setMessage] = useState('');
  const [loaded, setLoaded] = useState(false);

  // Load settings only when the modal is first opened; avoid fetching while hidden.
  useEffect(() => {
    if (!isSettingsOpen || loaded) return;
    setMessage('Loading settings…');
    void Promise.all([
      apiClients.settings.readManifest(),
      apiClients.settings.readSystem(),
      apiClients.settings.readCredentials(),
    ]).then(([manifestResponse, settingsResponse, credentialResponse]) => {
      setManifest(unwrapData(manifestResponse));
      const current = unwrapData(settingsResponse);
      setValues({ ...current.settings });
      setVersion(current.version);
      setCredentials(unwrapData(credentialResponse));
      setMessage('');
      setLoaded(true);
    }).catch(() => setMessage('Unable to load administrator settings.'));
  }, [isSettingsOpen, loaded]);

  // Close on Escape.
  useEffect(() => {
    if (!isSettingsOpen) return;
    const onKey = (e: KeyboardEvent): void => {
      if (e.key === 'Escape') closeSettings();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [isSettingsOpen, closeSettings]);

  if (!isSettingsOpen) return null;

  async function saveSettings(): Promise<void> {
    try {
      const updated = unwrapData(await apiClients.settings.updateSystem(values, version));
      setVersion(updated.version);
      setMessage('Settings saved. Restart required before they become active.');
    } catch {
      setMessage('Settings were not saved. Refresh to resolve a version conflict.');
    }
  }

  async function saveCredential(status: CredentialStatus): Promise<void> {
    try {
      await apiClients.settings.updateCredential(status.slot, credentialValues[status.slot] ?? {});
      setMessage(`${status.label} saved securely. Restart required.`);
      setCredentialValues((current) => ({ ...current, [status.slot]: {} }));
    } catch {
      setMessage(`${status.label} was not saved.`);
    }
  }

  /** Render the appropriate control for one manifest definition. */
  function renderField(definition: SystemSettingDefinition): React.ReactNode {
    const kind = fieldKind(definition);
    const value = values[definition.key] ?? '';

    // Shared updater keeps canonical string storage identical to text input.
    const update = (next: string): void =>
      setValues((current) => ({ ...current, [definition.key]: next }));

    if (kind === "enum") {
      return (
        <select
          className="form-select"
          aria-label={definition.label}
          value={value}
          onChange={(e) => update(e.target.value)}
        >
          {definition.allowed_values.map((opt) => (
            <option key={opt} value={opt}>{opt}</option>
          ))}
        </select>
      );
    }

    if (kind === "boolean") {
      return (
        <select
          className="form-select"
          aria-label={definition.label}
          value={value}
          onChange={(e) => update(e.target.value)}
        >
          {BOOLEAN_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
      );
    }

    if (kind === "timezone") {
      // Preserve a stored offset that falls outside the curated list.
      const options = TIMEZONE_OPTIONS.includes(value) ? TIMEZONE_OPTIONS : [value, ...TIMEZONE_OPTIONS];
      return (
        <select
          className="form-select"
          aria-label={definition.label}
          value={value}
          onChange={(e) => update(e.target.value)}
        >
          {options.map((opt) => (
            <option key={opt} value={opt}>{opt}</option>
          ))}
        </select>
      );
    }

    return (
      <input
        aria-label={definition.label}
        className="form-input"
        value={value}
        onChange={(e) => update(e.target.value)}
      />
    );
  }

  return (
    <div className="modal-overlay" onClick={closeSettings} role="presentation">
      <div
        className="modal-content system-settings-modal"
        onClick={(e: React.MouseEvent) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="system-settings-title"
      >
        <div className="modal-header">
          <span id="system-settings-title">System Settings</span>
          <button
            type="button"
            className="widget-btn"
            onClick={closeSettings}
            aria-label="Close settings"
          >
            <X size={16} />
          </button>
        </div>

        <div className="modal-body">
          <p className="system-settings-intro">
            Changes are versioned in the database and become active after restart.
          </p>
          {message && <p className="system-settings-message" role="status">{message}</p>}

          <section className="system-settings-section">
            {manifest.map((definition) => (
              <label key={definition.key} className="system-settings-field">
                <span className="system-settings-field-label">{definition.label}</span>
                <small className="system-settings-field-desc">{definition.description}</small>
                {renderField(definition)}
              </label>
            ))}
            <button
              type="button"
              className="btn-cme btn-primary system-settings-save"
              onClick={() => void saveSettings()}
            >
              Save system settings
            </button>
          </section>

          <section className="system-settings-section">
            <h3 className="system-settings-subheading">Credentials</h3>
            <p className="system-settings-cred-note">
              Stored values are write-only and are never returned to this page.
            </p>
            {credentials.map((status) => (
              <div key={status.slot} className="system-settings-credential">
                <div className="system-settings-cred-head">
                  <strong>{status.label}</strong>
                  <span className={status.configured ? 'cred-on' : 'cred-off'}>
                    {status.configured ? 'configured' : 'not configured'}
                  </span>
                </div>
                <div className="system-settings-cred-fields">
                  {status.fields.map((field) => (
                    <input
                      key={field}
                      className="form-input"
                      type="password"
                      autoComplete="new-password"
                      placeholder={field}
                      aria-label={`${status.label} ${field}`}
                      value={credentialValues[status.slot]?.[field] ?? ''}
                      onChange={(event) => setCredentialValues((current) => ({
                        ...current,
                        [status.slot]: { ...(current[status.slot] ?? {}), [field]: event.target.value },
                      }))}
                    />
                  ))}
                </div>
                <button
                  type="button"
                  className="btn-cme btn-outline system-settings-cred-save"
                  onClick={() => void saveCredential(status)}
                >
                  Replace credential
                </button>
              </div>
            ))}
          </section>
        </div>
      </div>
    </div>
  );
};
