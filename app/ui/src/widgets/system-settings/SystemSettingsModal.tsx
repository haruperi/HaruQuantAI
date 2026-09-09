"use client";

import React, { useEffect, useMemo, useState } from "react";
import { X } from "lucide-react";

import {
  ApiClientError,
  apiClients,
  unwrapData,
  type CredentialStatus,
  type SystemSettingDefinition,
} from "@/clients";
import { useTradingStore } from "@/store/useTradingStore";

import {
  diffSettings,
  isSettingsDirty,
  settingsFailureMessage,
} from "./state";

export const SystemSettingsModal: React.FC = () => {
  const { isSettingsOpen, closeSettings } = useTradingStore();
  const [manifest, setManifest] = useState<SystemSettingDefinition[]>([]);
  const [baseline, setBaseline] = useState<Record<string, string>>({});
  const [values, setValues] = useState<Record<string, string>>({});
  const [version, setVersion] = useState(0);
  const [credentials, setCredentials] = useState<CredentialStatus[]>([]);
  const [credentialValues, setCredentialValues] = useState<
    Record<string, Record<string, string>>
  >({});
  const [message, setMessage] = useState("");

  const diff = useMemo(() => diffSettings(baseline, values), [baseline, values]);
  const dirty = isSettingsDirty(baseline, values);

  useEffect(() => {
    if (!isSettingsOpen) return;
    let cancelled = false;
    setMessage("Loading settings…");
    void Promise.all([
      apiClients.settings.readManifest(),
      apiClients.settings.readSystem(),
      apiClients.settings.readCredentials(),
    ])
      .then(([manifestResponse, settingsResponse, credentialResponse]) => {
        if (cancelled) return;
        const current = unwrapData(settingsResponse);
        setManifest(unwrapData(manifestResponse));
        setBaseline({ ...current.settings });
        setValues({ ...current.settings });
        setVersion(current.version);
        setCredentials(unwrapData(credentialResponse));
        setMessage("");
      })
      .catch(() => {
        if (!cancelled) setMessage("Unable to load administrator settings.");
      });
    return () => {
      cancelled = true;
    };
  }, [isSettingsOpen]);

  useEffect(() => {
    if (!isSettingsOpen) return;
    const onKey = (event: KeyboardEvent): void => {
      if (event.key === "Escape" && !dirty) closeSettings();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [isSettingsOpen, closeSettings, dirty]);

  if (!isSettingsOpen) return null;

  const requestClose = (): void => {
    if (!dirty || window.confirm("Discard unsaved settings changes?")) closeSettings();
  };

  const saveSettings = async (): Promise<void> => {
    try {
      const updated = unwrapData(
        await apiClients.settings.updateSystem(values, version),
      );
      setBaseline({ ...updated.settings });
      setValues({ ...updated.settings });
      setVersion(updated.version);
      setMessage("Settings saved. Effective owner policy remains authoritative.");
    } catch (cause) {
      const code = cause instanceof ApiClientError ? cause.code : "UNKNOWN";
      setMessage(settingsFailureMessage(code));
    }
  };

  const saveCredential = async (status: CredentialStatus): Promise<void> => {
    try {
      await apiClients.settings.updateCredential(
        status.slot,
        credentialValues[status.slot] ?? {},
      );
      setCredentialValues((current) => ({ ...current, [status.slot]: {} }));
      setMessage(`${status.label} replaced securely; stored material remains write-only.`);
    } catch {
      setMessage(`${status.label} was not saved.`);
    }
  };

  return (
    <div className="modal-overlay" onClick={requestClose} role="presentation">
      <div
        className="modal-content system-settings-modal"
        onClick={(event) => event.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="system-settings-title"
      >
        <div className="modal-header">
          <span id="system-settings-title">System Settings</span>
          <button type="button" className="widget-btn" onClick={requestClose} aria-label="Close settings">
            <X size={16} />
          </button>
        </div>
        <div className="modal-body">
          <p>
            Revision {version}. Current settings affect future eligible operations only;
            historical runs keep their pinned configuration.
          </p>
          {message && <p role="status">{message}</p>}
          {diff.length > 0 && (
            <section aria-label="Unsaved setting differences">
              <strong>{diff.length} unsaved change{diff.length === 1 ? "" : "s"}</strong>
              <ul>
                {diff.map((item) => (
                  <li key={item.key}>{item.key}: {item.before ?? "(unset)"} → {item.after ?? "(unset)"}</li>
                ))}
              </ul>
            </section>
          )}
          <section className="system-settings-section">
            {manifest.map((definition) => (
              <label key={definition.key} className="system-settings-field">
                <span>{definition.label}</span>
                <small>{definition.description}</small>
                {definition.allowed_values.length > 0 ? (
                  <select
                    aria-label={definition.label}
                    value={values[definition.key] ?? ""}
                    onChange={(event) =>
                      setValues((current) => ({
                        ...current,
                        [definition.key]: event.target.value,
                      }))
                    }
                  >
                    {definition.allowed_values.map((value) => (
                      <option key={value} value={value}>{value}</option>
                    ))}
                  </select>
                ) : (
                  <input
                    aria-label={definition.label}
                    value={values[definition.key] ?? ""}
                    onChange={(event) =>
                      setValues((current) => ({
                        ...current,
                        [definition.key]: event.target.value,
                      }))
                    }
                  />
                )}
              </label>
            ))}
            <div>
              <button type="button" onClick={() => setValues({ ...baseline })} disabled={!dirty}>
                Reset draft
              </button>
              <button type="button" onClick={() => void saveSettings()} disabled={!dirty}>
                Save system settings
              </button>
            </div>
          </section>
          <section className="system-settings-section">
            <h3>Credentials</h3>
            <p>Credential values are write-only and never returned to this page.</p>
            {credentials.map((status) => (
              <div key={status.slot} className="system-settings-credential">
                <strong>{status.label}</strong>
                <span>{status.configured ? "configured" : "not configured"}</span>
                {status.fields.map((field) => (
                  <input
                    key={field}
                    type="password"
                    autoComplete="new-password"
                    aria-label={`${status.label} ${field}`}
                    value={credentialValues[status.slot]?.[field] ?? ""}
                    onChange={(event) =>
                      setCredentialValues((current) => ({
                        ...current,
                        [status.slot]: {
                          ...(current[status.slot] ?? {}),
                          [field]: event.target.value,
                        },
                      }))
                    }
                  />
                ))}
                <button type="button" onClick={() => void saveCredential(status)}>
                  Replace credential
                </button>
              </div>
            ))}
          </section>
          <section aria-label="Service actions">
            <h3>Service status</h3>
            <p>SMTP test and remote/MCP actions remain unavailable unless their typed providers are configured and qualified.</p>
          </section>
        </div>
      </div>
    </div>
  );
};
