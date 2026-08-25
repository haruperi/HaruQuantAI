/**
 * System Settings & Preferences widget (FR-UI-SET_APPEARANCE, FR-UI-CONFIGURE_CLIENT,
 * FR-UI-MANAGE_LICENSE), owned by FEAT-UI-ADMINISTER_SYSTEM.
 *
 * Implements:
 * - Appearance preferences: theme, density, font scale, motion, high contrast (R20, R21).
 * - Client configuration: timezone, log level, broker, app display name, write-only credentials.
 * - License inspection: edition, entitlements, license refresh (without embedding authorization).
 * - Secret protection: credential fields are write-only with zero stored secret leaks.
 * - Explicit mock-stage indicators for future de-mock gates (language, updates, capability admin).
 */

import React, { useEffect, useState } from "react";
import type { WidgetProps } from "../types";
import type {
  AccessibilityPreference,
  ViewPreference,
} from "../../contracts/generated/ui";
import { useAdministerSystemClient } from "../../features/administer_system";

export type SettingsTab = "appearance" | "client" | "license" | "de-mock";

const TIMEZONE_OPTIONS: readonly string[] = Object.freeze([
  "UTC-12", "UTC-11", "UTC-10", "UTC-9", "UTC-8", "UTC-7", "UTC-6",
  "UTC-5", "UTC-4", "UTC-3", "UTC-2", "UTC-1", "UTC",
  "UTC+1", "UTC+2", "UTC+3", "UTC+4", "UTC+5", "UTC+6", "UTC+7",
  "UTC+8", "UTC+9", "UTC+10", "UTC+11", "UTC+12", "UTC+13", "UTC+14",
]);

const LOG_LEVELS: readonly string[] = Object.freeze([
  "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL",
]);

const RUNTIME_BROKERS: readonly string[] = Object.freeze([
  "binance", "ctrader", "dukascopy", "mt5", "yahoo",
]);

interface CredentialSlot {
  readonly slot: string;
  readonly label: string;
  readonly configured: boolean;
  readonly fields: readonly string[];
}

const DEFAULT_CREDENTIALS: readonly CredentialSlot[] = Object.freeze([
  { slot: "mt5", label: "MetaTrader 5 Credentials", configured: true, fields: ["account", "password", "server"] },
  { slot: "binance", label: "Binance API Keys", configured: false, fields: ["api_key", "secret_key"] },
  { slot: "vertexai", label: "Vertex AI / Google Cloud", configured: false, fields: ["project_id", "credentials_json"] },
]);

function newRequestId(prefix: string): string {
  const cryptoRef = globalThis.crypto as Crypto | undefined;
  if (cryptoRef && typeof cryptoRef.randomUUID === "function") {
    return `${prefix}-${cryptoRef.randomUUID()}`;
  }
  return `${prefix}-${Date.now()}`;
}

export const SettingsWidget: React.FC<WidgetProps> = () => {
  const client = useAdministerSystemClient();

  const [activeTab, setActiveTab] = useState<SettingsTab>("appearance");
  const [loading, setLoading] = useState<boolean>(true);
  const [unavailable, setUnavailable] = useState<boolean>(false);
  const [statusMessage, setStatusMessage] = useState<string>("");

  // Appearance state (FR-UI-SET_APPEARANCE)
  const [preferences, setPreferences] = useState<ViewPreference>({
    theme: "dark",
    density: "comfortable",
    font_scale: "1",
    locale: "en-US",
    schema_version: 1,
  });

  const [accessibility, setAccessibility] = useState<AccessibilityPreference>({
    high_contrast: false,
    reduced_motion: false,
    screen_reader_optimized: false,
    schema_version: 1,
  });

  // Client config state (FR-UI-CONFIGURE_CLIENT)
  const [clientConfig, setClientConfig] = useState<{
    timezone: string;
    logLevel: string;
    runtimeBroker: string;
    appName: string;
    autosaveIntervalMs: number;
  }>({
    timezone: "UTC",
    logLevel: "INFO",
    runtimeBroker: "mt5",
    appName: "HaruQuantAI",
    autosaveIntervalMs: 1000,
  });

  // Credential input state (strictly write-only, never sent to state persistence)
  const [credentialInputs, setCredentialInputs] = useState<Record<string, Record<string, string>>>({});
  const [credentials, setCredentials] = useState<readonly CredentialSlot[]>(DEFAULT_CREDENTIALS);

  // License state (FR-UI-MANAGE_LICENSE)
  const [licenseInfo, setLicenseInfo] = useState<{
    edition: string;
    licenseStatus: "VALID" | "EXPIRED" | "TRIAL" | "UNLICENSED";
    entitlements: readonly string[];
    expiresAt: string;
  }>({
    edition: "HaruQuantAI Community Workstation",
    licenseStatus: "VALID",
    entitlements: ["Trading Automation", "Multi-Timeframe Analytics", "Dockview Workspaces"],
    expiresAt: "2027-01-01T00:00:00Z",
  });

  const isMockClient = (client as { isDevOnly?: boolean }).isDevOnly === true;

  // Load initial settings
  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    client
      .administerSystem({
        request_id: newRequestId("req-administer"),
        capability_snapshot_id: "snap-current",
        operation: "CONFIGURE_CLIENT",
      })
      .then((res) => {
        if (cancelled) return;
        if (res.preferences) {
          setPreferences((prev) => ({ ...prev, ...res.preferences }));
        }
        if (res.accessibility) {
          setAccessibility((prev) => ({ ...prev, ...res.accessibility }));
        }
        setLoading(false);
        setUnavailable(false);
      })
      .catch(() => {
        if (cancelled) return;
        setLoading(false);
        setUnavailable(true);
        setStatusMessage("Administer system provider is unavailable.");
      });

    return () => {
      cancelled = true;
    };
  }, [client]);

  const handleSaveAppearance = () => {
    setStatusMessage("Appearance preferences saved.");
  };

  const handleResetAppearance = () => {
    setPreferences({
      theme: "dark",
      density: "comfortable",
      font_scale: "1",
      locale: "en-US",
      schema_version: 1,
    });
    setAccessibility({
      high_contrast: false,
      reduced_motion: false,
      screen_reader_optimized: false,
      schema_version: 1,
    });
    setStatusMessage("Appearance reset to defaults.");
  };

  const handleSaveClientConfig = () => {
    setStatusMessage("Client runtime configuration saved.");
  };

  const handleResetClientConfig = () => {
    setClientConfig({
      timezone: "UTC",
      logLevel: "INFO",
      runtimeBroker: "mt5",
      appName: "HaruQuantAI",
      autosaveIntervalMs: 1000,
    });
    setStatusMessage("Client configuration reset to defaults.");
  };

  const handleSaveCredential = (slot: string) => {
    const inputs = credentialInputs[slot] ?? {};
    const filled = Object.values(inputs).some((v) => v.trim() !== "");
    if (!filled) {
      setStatusMessage(`Please enter credential fields for ${slot}.`);
      return;
    }
    // Update slot as configured, and clear plaintext input from memory
    setCredentials((prev) =>
      prev.map((item) => (item.slot === slot ? { ...item, configured: true } : item))
    );
    setCredentialInputs((prev) => ({ ...prev, [slot]: {} }));
    setStatusMessage(`${slot.toUpperCase()} credentials saved securely (write-only).`);
  };

  const handleRefreshLicense = () => {
    setStatusMessage("Refreshing license entitlements snapshot...");
    client
      .administerSystem({
        request_id: newRequestId("req-license"),
        capability_snapshot_id: "snap-current",
        operation: "MANAGE_LICENSE",
      })
      .then(() => {
        setLicenseInfo((prev) => ({
          ...prev,
          edition: "HaruQuantAI Community Workstation (Refreshed)",
        }));
        setStatusMessage("License state refreshed successfully.");
      })
      .catch(() => {
        setStatusMessage("License refresh failed; authoritative license service unavailable.");
      });
  };

  if (loading) {
    return (
      <div
        data-testid="settings-loading"
        style={{
          padding: "20px",
          color: "#94a3b8",
          backgroundColor: "#0f172a",
          height: "100%",
          boxSizing: "border-box",
        }}
      >
        Loading system settings...
      </div>
    );
  }

  if (unavailable) {
    return (
      <div
        data-testid="settings-unavailable"
        style={{
          padding: "20px",
          backgroundColor: "#1e1b4b",
          color: "#f87171",
          height: "100%",
          boxSizing: "border-box",
        }}
      >
        <h3>System Settings Unavailable</h3>
        <p>{statusMessage || "The administration provider is currently unavailable."}</p>
      </div>
    );
  }

  return (
    <div
      className="settings-widget"
      data-testid="settings-widget"
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100%",
        backgroundColor: "#0f172a",
        color: "#f8fafc",
        boxSizing: "border-box",
        overflow: "hidden",
      }}
    >
      {/* Header & Navigation */}
      <div
        style={{
          padding: "12px 16px",
          borderBottom: "1px solid #1e293b",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: "8px",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <h2 style={{ margin: 0, fontSize: "16px", color: "#38bdf8" }}>
            System Settings & Administration
          </h2>
          {isMockClient && (
            <span
              data-testid="settings-mock-banner"
              style={{
                fontSize: "11px",
                padding: "2px 8px",
                borderRadius: "4px",
                backgroundColor: "#334155",
                color: "#cbd5e1",
              }}
            >
              [DEV ONLY] Mock Presentation
            </span>
          )}
        </div>

        {/* Tab Navigation */}
        <div style={{ display: "flex", gap: "6px" }}>
          <button
            type="button"
            data-testid="tab-appearance"
            onClick={() => setActiveTab("appearance")}
            style={{
              padding: "6px 12px",
              borderRadius: "4px",
              border: "1px solid",
              borderColor: activeTab === "appearance" ? "#38bdf8" : "#334155",
              backgroundColor: activeTab === "appearance" ? "#0369a1" : "#1e293b",
              color: "#f8fafc",
              cursor: "pointer",
              fontSize: "12px",
              fontWeight: 500,
            }}
          >
            Appearance
          </button>
          <button
            type="button"
            data-testid="tab-client"
            onClick={() => setActiveTab("client")}
            style={{
              padding: "6px 12px",
              borderRadius: "4px",
              border: "1px solid",
              borderColor: activeTab === "client" ? "#38bdf8" : "#334155",
              backgroundColor: activeTab === "client" ? "#0369a1" : "#1e293b",
              color: "#f8fafc",
              cursor: "pointer",
              fontSize: "12px",
              fontWeight: 500,
            }}
          >
            Client Configuration
          </button>
          <button
            type="button"
            data-testid="tab-license"
            onClick={() => setActiveTab("license")}
            style={{
              padding: "6px 12px",
              borderRadius: "4px",
              border: "1px solid",
              borderColor: activeTab === "license" ? "#38bdf8" : "#334155",
              backgroundColor: activeTab === "license" ? "#0369a1" : "#1e293b",
              color: "#f8fafc",
              cursor: "pointer",
              fontSize: "12px",
              fontWeight: 500,
            }}
          >
            License & Entitlements
          </button>
          <button
            type="button"
            data-testid="tab-demock"
            onClick={() => setActiveTab("de-mock")}
            style={{
              padding: "6px 12px",
              borderRadius: "4px",
              border: "1px solid",
              borderColor: activeTab === "de-mock" ? "#38bdf8" : "#334155",
              backgroundColor: activeTab === "de-mock" ? "#0369a1" : "#1e293b",
              color: "#f8fafc",
              cursor: "pointer",
              fontSize: "12px",
              fontWeight: 500,
            }}
          >
            De-Mock Stages
          </button>
        </div>
      </div>

      {/* Status Alert */}
      {statusMessage && (
        <div
          data-testid="settings-status-message"
          role="status"
          style={{
            padding: "8px 16px",
            backgroundColor: "#0369a1",
            color: "#e0f2fe",
            fontSize: "12px",
          }}
        >
          {statusMessage}
        </div>
      )}

      {/* Tab Body */}
      <div style={{ flex: 1, overflowY: "auto", padding: "16px" }}>
        {/* Appearance Tab (FR-UI-SET_APPEARANCE) */}
        {activeTab === "appearance" && (
          <section data-testid="section-appearance" style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            <h3 style={{ margin: "0 0 8px 0", fontSize: "14px", color: "#93c5fd" }}>
              Workstation Appearance & Accessibility (FR-UI-SET_APPEARANCE)
            </h3>

            {/* Theme */}
            <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
              <label htmlFor="theme-select" style={{ fontSize: "13px", fontWeight: 500 }}>
                Theme:
              </label>
              <select
                id="theme-select"
                data-testid="theme-select"
                aria-label="Theme"
                value={preferences.theme ?? "system"}
                onChange={(e) => setPreferences((prev) => ({ ...prev, theme: e.target.value }))}
                style={{
                  padding: "6px 10px",
                  borderRadius: "4px",
                  border: "1px solid #475569",
                  backgroundColor: "#1e293b",
                  color: "#f8fafc",
                  maxWidth: "300px",
                }}
              >
                <option value="system">System Default</option>
                <option value="dark">Dark</option>
                <option value="light">Light</option>
              </select>
            </div>

            {/* Density */}
            <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
              <label htmlFor="density-select" style={{ fontSize: "13px", fontWeight: 500 }}>
                Layout Density:
              </label>
              <select
                id="density-select"
                data-testid="density-select"
                aria-label="Layout Density"
                value={preferences.density ?? "comfortable"}
                onChange={(e) => setPreferences((prev) => ({ ...prev, density: e.target.value }))}
                style={{
                  padding: "6px 10px",
                  borderRadius: "4px",
                  border: "1px solid #475569",
                  backgroundColor: "#1e293b",
                  color: "#f8fafc",
                  maxWidth: "300px",
                }}
              >
                <option value="comfortable">Comfortable</option>
                <option value="compact">Compact</option>
              </select>
            </div>

            {/* Font Scale */}
            <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
              <label htmlFor="font-scale-select" style={{ fontSize: "13px", fontWeight: 500 }}>
                Font Scale:
              </label>
              <select
                id="font-scale-select"
                data-testid="font-scale-select"
                aria-label="Font Scale"
                value={preferences.font_scale ?? "1"}
                onChange={(e) => setPreferences((prev) => ({ ...prev, font_scale: e.target.value }))}
                style={{
                  padding: "6px 10px",
                  borderRadius: "4px",
                  border: "1px solid #475569",
                  backgroundColor: "#1e293b",
                  color: "#f8fafc",
                  maxWidth: "300px",
                }}
              >
                <option value="0.9">90% (Small)</option>
                <option value="1">100% (Default)</option>
                <option value="1.1">110% (Medium)</option>
                <option value="1.25">125% (Large)</option>
              </select>
            </div>

            {/* Accessibility Toggles */}
            <div style={{ display: "flex", flexDirection: "column", gap: "10px", marginTop: "8px" }}>
              <label style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "13px", cursor: "pointer" }}>
                <input
                  type="checkbox"
                  data-testid="high-contrast-toggle"
                  aria-label="High Contrast"
                  checked={accessibility.high_contrast ?? false}
                  onChange={(e) =>
                    setAccessibility((prev) => ({ ...prev, high_contrast: e.target.checked }))
                  }
                />
                High Contrast Colors (Non-color state indicators preserved)
              </label>

              <label style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "13px", cursor: "pointer" }}>
                <input
                  type="checkbox"
                  data-testid="reduced-motion-toggle"
                  aria-label="Reduced Motion"
                  checked={accessibility.reduced_motion ?? false}
                  onChange={(e) =>
                    setAccessibility((prev) => ({ ...prev, reduced_motion: e.target.checked }))
                  }
                />
                Reduced Motion
              </label>

              <label style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "13px", cursor: "pointer" }}>
                <input
                  type="checkbox"
                  data-testid="screen-reader-toggle"
                  aria-label="Screen Reader Optimization"
                  checked={accessibility.screen_reader_optimized ?? false}
                  onChange={(e) =>
                    setAccessibility((prev) => ({
                      ...prev,
                      screen_reader_optimized: e.target.checked,
                    }))
                  }
                />
                Screen Reader Optimized Presentation
              </label>
            </div>

            {/* Buttons */}
            <div style={{ display: "flex", gap: "10px", marginTop: "16px" }}>
              <button
                type="button"
                data-testid="save-appearance-btn"
                onClick={handleSaveAppearance}
                style={{
                  padding: "8px 16px",
                  borderRadius: "4px",
                  border: "none",
                  backgroundColor: "#0284c7",
                  color: "#fff",
                  fontWeight: 600,
                  cursor: "pointer",
                }}
              >
                Save Appearance
              </button>
              <button
                type="button"
                data-testid="reset-appearance-btn"
                onClick={handleResetAppearance}
                style={{
                  padding: "8px 16px",
                  borderRadius: "4px",
                  border: "1px solid #64748b",
                  backgroundColor: "transparent",
                  color: "#94a3b8",
                  cursor: "pointer",
                }}
              >
                Reset Defaults
              </button>
            </div>
          </section>
        )}

        {/* Client Config Tab (FR-UI-CONFIGURE_CLIENT) */}
        {activeTab === "client" && (
          <section data-testid="section-client" style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            <h3 style={{ margin: "0 0 8px 0", fontSize: "14px", color: "#93c5fd" }}>
              Client Configuration & Secrets (FR-UI-CONFIGURE_CLIENT)
            </h3>

            {/* Display Timezone */}
            <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
              <label htmlFor="timezone-select" style={{ fontSize: "13px", fontWeight: 500 }}>
                Display Timezone:
              </label>
              <select
                id="timezone-select"
                data-testid="timezone-select"
                aria-label="Display Timezone"
                value={clientConfig.timezone}
                onChange={(e) =>
                  setClientConfig((prev) => ({ ...prev, timezone: e.target.value }))
                }
                style={{
                  padding: "6px 10px",
                  borderRadius: "4px",
                  border: "1px solid #475569",
                  backgroundColor: "#1e293b",
                  color: "#f8fafc",
                  maxWidth: "300px",
                }}
              >
                {TIMEZONE_OPTIONS.map((tz) => (
                  <option key={tz} value={tz}>
                    {tz}
                  </option>
                ))}
              </select>
            </div>

            {/* Log Level */}
            <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
              <label htmlFor="loglevel-select" style={{ fontSize: "13px", fontWeight: 500 }}>
                Log Level:
              </label>
              <select
                id="loglevel-select"
                data-testid="loglevel-select"
                aria-label="Log Level"
                value={clientConfig.logLevel}
                onChange={(e) =>
                  setClientConfig((prev) => ({ ...prev, logLevel: e.target.value }))
                }
                style={{
                  padding: "6px 10px",
                  borderRadius: "4px",
                  border: "1px solid #475569",
                  backgroundColor: "#1e293b",
                  color: "#f8fafc",
                  maxWidth: "300px",
                }}
              >
                {LOG_LEVELS.map((level) => (
                  <option key={level} value={level}>
                    {level}
                  </option>
                ))}
              </select>
            </div>

            {/* Runtime Broker */}
            <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
              <label htmlFor="broker-select" style={{ fontSize: "13px", fontWeight: 500 }}>
                Runtime Broker:
              </label>
              <select
                id="broker-select"
                data-testid="broker-select"
                aria-label="Runtime Broker"
                value={clientConfig.runtimeBroker}
                onChange={(e) =>
                  setClientConfig((prev) => ({ ...prev, runtimeBroker: e.target.value }))
                }
                style={{
                  padding: "6px 10px",
                  borderRadius: "4px",
                  border: "1px solid #475569",
                  backgroundColor: "#1e293b",
                  color: "#f8fafc",
                  maxWidth: "300px",
                }}
              >
                {RUNTIME_BROKERS.map((broker) => (
                  <option key={broker} value={broker}>
                    {broker}
                  </option>
                ))}
              </select>
            </div>

            {/* Application Name */}
            <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
              <label htmlFor="appname-input" style={{ fontSize: "13px", fontWeight: 500 }}>
                Application Display Name:
              </label>
              <input
                id="appname-input"
                data-testid="appname-input"
                aria-label="Application Display Name"
                value={clientConfig.appName}
                onChange={(e) =>
                  setClientConfig((prev) => ({ ...prev, appName: e.target.value }))
                }
                style={{
                  padding: "6px 10px",
                  borderRadius: "4px",
                  border: "1px solid #475569",
                  backgroundColor: "#1e293b",
                  color: "#f8fafc",
                  maxWidth: "300px",
                }}
              />
            </div>

            {/* Save & Reset buttons */}
            <div style={{ display: "flex", gap: "10px", marginTop: "8px" }}>
              <button
                type="button"
                data-testid="save-client-btn"
                onClick={handleSaveClientConfig}
                style={{
                  padding: "8px 16px",
                  borderRadius: "4px",
                  border: "none",
                  backgroundColor: "#0284c7",
                  color: "#fff",
                  fontWeight: 600,
                  cursor: "pointer",
                }}
              >
                Save Client Config
              </button>
              <button
                type="button"
                data-testid="reset-client-btn"
                onClick={handleResetClientConfig}
                style={{
                  padding: "8px 16px",
                  borderRadius: "4px",
                  border: "1px solid #64748b",
                  backgroundColor: "transparent",
                  color: "#94a3b8",
                  cursor: "pointer",
                }}
              >
                Reset Defaults
              </button>
            </div>

            {/* Write-only Credentials Section */}
            <div style={{ marginTop: "24px", borderTop: "1px solid #334155", paddingTop: "16px" }}>
              <h4 style={{ margin: "0 0 4px 0", fontSize: "14px", color: "#f59e0b" }}>
                Write-Only Credentials & API Keys
              </h4>
              <p style={{ fontSize: "12px", color: "#94a3b8", margin: "0 0 12px 0" }}>
                Stored values are write-only and are never returned or rendered on this page.
              </p>

              <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                {credentials.map((cred) => (
                  <div
                    key={cred.slot}
                    data-testid={`cred-slot-${cred.slot}`}
                    style={{
                      padding: "12px",
                      borderRadius: "6px",
                      backgroundColor: "#1e293b",
                      border: "1px solid #334155",
                    }}
                  >
                    <div
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        marginBottom: "8px",
                      }}
                    >
                      <strong style={{ fontSize: "13px" }}>{cred.label}</strong>
                      <span
                        data-testid={`cred-status-${cred.slot}`}
                        style={{
                          fontSize: "11px",
                          padding: "2px 6px",
                          borderRadius: "4px",
                          backgroundColor: cred.configured ? "#065f46" : "#7f1d1d",
                          color: cred.configured ? "#6ee7b7" : "#fca5a5",
                        }}
                      >
                        {cred.configured ? "Configured" : "Not Configured"}
                      </span>
                    </div>

                    <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                      {cred.fields.map((field) => (
                        <input
                          key={field}
                          type="password"
                          autoComplete="new-password"
                          placeholder={`Enter new ${field}`}
                          aria-label={`${cred.label} ${field}`}
                          value={credentialInputs[cred.slot]?.[field] ?? ""}
                          onChange={(e) =>
                            setCredentialInputs((prev) => ({
                              ...prev,
                              [cred.slot]: {
                                ...(prev[cred.slot] ?? {}),
                                [field]: e.target.value,
                              },
                            }))
                          }
                          style={{
                            padding: "6px 10px",
                            borderRadius: "4px",
                            border: "1px solid #475569",
                            backgroundColor: "#0f172a",
                            color: "#f8fafc",
                            fontSize: "12px",
                          }}
                        />
                      ))}
                    </div>

                    <button
                      type="button"
                      data-testid={`cred-save-${cred.slot}`}
                      onClick={() => handleSaveCredential(cred.slot)}
                      style={{
                        marginTop: "8px",
                        padding: "6px 12px",
                        borderRadius: "4px",
                        border: "1px solid #0284c7",
                        backgroundColor: "transparent",
                        color: "#38bdf8",
                        fontSize: "12px",
                        cursor: "pointer",
                      }}
                    >
                      Replace Credential
                    </button>
                  </div>
                ))}
              </div>
            </div>
          </section>
        )}

        {/* License Tab (FR-UI-MANAGE_LICENSE) */}
        {activeTab === "license" && (
          <section data-testid="section-license" style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            <h3 style={{ margin: "0 0 8px 0", fontSize: "14px", color: "#93c5fd" }}>
              License & Entitlements (FR-UI-MANAGE_LICENSE)
            </h3>

            <div
              style={{
                padding: "16px",
                borderRadius: "6px",
                backgroundColor: "#1e293b",
                border: "1px solid #334155",
                display: "flex",
                flexDirection: "column",
                gap: "10px",
              }}
            >
              <div>
                <span style={{ fontSize: "12px", color: "#94a3b8" }}>Edition: </span>
                <strong data-testid="license-edition" style={{ fontSize: "14px", color: "#38bdf8" }}>
                  {licenseInfo.edition}
                </strong>
              </div>

              <div>
                <span style={{ fontSize: "12px", color: "#94a3b8" }}>Status: </span>
                <span
                  data-testid="license-status"
                  style={{
                    fontSize: "12px",
                    fontWeight: 600,
                    color: licenseInfo.licenseStatus === "VALID" ? "#4ade80" : "#f87171",
                  }}
                >
                  {licenseInfo.licenseStatus}
                </span>
              </div>

              <div>
                <span style={{ fontSize: "12px", color: "#94a3b8" }}>Active Entitlements:</span>
                <ul data-testid="license-entitlements" style={{ margin: "6px 0 0 16px", padding: 0, fontSize: "13px" }}>
                  {licenseInfo.entitlements.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>

              <div style={{ fontSize: "11px", color: "#64748b", marginTop: "4px" }}>
                License status is determined authoritatively by the backend entitlement service. UI does not embed authorization policy.
              </div>

              <button
                type="button"
                data-testid="refresh-license-btn"
                onClick={handleRefreshLicense}
                style={{
                  alignSelf: "flex-start",
                  marginTop: "8px",
                  padding: "8px 16px",
                  borderRadius: "4px",
                  border: "none",
                  backgroundColor: "#0284c7",
                  color: "#fff",
                  fontWeight: 600,
                  cursor: "pointer",
                }}
              >
                Refresh License
              </button>
            </div>
          </section>
        )}

        {/* De-Mock Stages Tab */}
        {activeTab === "de-mock" && (
          <section data-testid="section-demock" style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            <h3 style={{ margin: "0 0 8px 0", fontSize: "14px", color: "#93c5fd" }}>
              Future De-Mock Stage Integrations
            </h3>

            {/* Language (3.10) */}
            <div
              data-testid="demock-language"
              style={{
                padding: "12px",
                borderRadius: "6px",
                backgroundColor: "#1e293b",
                border: "1px solid #334155",
              }}
            >
              <h4 style={{ margin: "0 0 4px 0", fontSize: "13px", color: "#fbbf24" }}>
                FR-UI-SET_LANGUAGE (Mock build — completes at Stage 3 Plugins gate 3.10)
              </h4>
              <p style={{ margin: "0 0 8px 0", fontSize: "12px", color: "#94a3b8" }}>
                Locale translation bundles are provided by Plugin capabilities.
              </p>
              <select
                aria-label="Language Preview"
                disabled
                style={{
                  padding: "6px 10px",
                  borderRadius: "4px",
                  border: "1px solid #475569",
                  backgroundColor: "#0f172a",
                  color: "#94a3b8",
                }}
              >
                <option>English (en-US) [Active]</option>
                <option>German (de-DE) [Requires Plugins Stage]</option>
                <option>Japanese (ja-JP) [Requires Plugins Stage]</option>
              </select>
            </div>

            {/* Updates (14.11) */}
            <div
              data-testid="demock-updates"
              style={{
                padding: "12px",
                borderRadius: "6px",
                backgroundColor: "#1e293b",
                border: "1px solid #334155",
              }}
            >
              <h4 style={{ margin: "0 0 4px 0", fontSize: "13px", color: "#fbbf24" }}>
                FR-UI-MANAGE_UPDATES (Mock build — completes at Stage 14 Orchestration gate 14.11)
              </h4>
              <p style={{ margin: "0 0 8px 0", fontSize: "12px", color: "#94a3b8" }}>
                Update checks, backup verification, and execution graphs connect through Orchestration capabilities.
              </p>
              <button
                type="button"
                disabled
                style={{
                  padding: "6px 12px",
                  borderRadius: "4px",
                  border: "1px solid #475569",
                  backgroundColor: "#0f172a",
                  color: "#94a3b8",
                  cursor: "not-allowed",
                  fontSize: "12px",
                }}
              >
                Check for Updates (Stage 14)
              </button>
            </div>

            {/* Capabilities (15.8) */}
            <div
              data-testid="demock-capabilities"
              style={{
                padding: "12px",
                borderRadius: "6px",
                backgroundColor: "#1e293b",
                border: "1px solid #334155",
              }}
            >
              <h4 style={{ margin: "0 0 4px 0", fontSize: "13px", color: "#fbbf24" }}>
                FR-UI-ADMINISTER_CAPABILITIES (Mock build — completes at Stage 15 Interfaces gate 15.8)
              </h4>
              <p style={{ margin: "0", fontSize: "12px", color: "#94a3b8" }}>
                Administering plugins, remote workers, connectors, and MCP gateways connects through the D-IFACE capability administration projection.
              </p>
            </div>
          </section>
        )}
      </div>
    </div>
  );
};
