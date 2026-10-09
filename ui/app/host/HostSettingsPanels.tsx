/** Catalogue-driven host preference forms; secret drafts never enter global storage. */
import { useEffect, useState } from 'react';
import { Button, Modal } from '../components/ui';
import {
  changeHostAccount, readHostAccount, readSettingsCatalogue, saveCatalogueFields,
  type HostAccount, type SettingsCatalogue, type SettingsField,
} from './hostSettings';
import { setAuthToken } from './transport';
import type { HostSettingsSection } from './types';

const sections: Record<Exclude<HostSettingsSection, 'account'>, { title: string; tabs: [string, string][] }> = {
  notifications: { title: 'Notifications', tabs: [['Desktop', 'notify_desktop'], ['Email', 'notify_email'], ['Telegram', 'notify_telegram']] },
  credentials: { title: 'Credentials', tabs: [['MT5', 'config_metatrader5'], ['cTrader', 'config_ctrader'], ['AI agents', 'config_agents']] },
  advanced: { title: 'Advanced settings', tabs: [['General', 'app_general'], ['Workspace', 'workspace_paths'], ['Backtest', 'engine_backtest'], ['Calibration', 'calibration_indicators'], ['Runtime', 'runtime']] },
  smtp: { title: 'SMTP server', tabs: [['Email', 'notify_email']] },
  mcp: { title: 'MCP Server', tabs: [['Server', 'connect_mcp']] },
};
const fieldId = (field: SettingsField) => `${field.scope}/${field.key}`;
const labels: Record<string, string> = {
  smtp_server: 'SMTP server', smtp_port: 'Port', from_address: 'Sender email',
  password: 'Password', username: 'Username', use_ssl: 'Use SSL', use_tls: 'Use TLS',
  recipient_addresses: 'Recipient addresses', bot_token: 'Bot token', chat_id: 'Chat ID',
  client_id: 'Client ID', client_secret: 'Client secret', terminal_path: 'Terminal path',
  account_id: 'Account ID', timeout_ms: 'Timeout (ms)', auth_token: 'Auth token',
};
function labelFor(field: SettingsField): string { return labels[field.key] ?? field.label; }
function initialDraft(catalogue: SettingsCatalogue): Record<string, string | boolean> {
  return Object.fromEntries(catalogue.fields.map(field => [fieldId(field), field.secret ? '' :
    field.kind === 'bool' ? Boolean(field.value) : field.kind === 'list' ? JSON.stringify(field.value) : String(field.value ?? '')]));
}

export function HostSettingsPanel({ section, onClose }: { section: Exclude<HostSettingsSection, 'account'>; onClose: () => void }) {
  const config = sections[section];
  const [group, setGroup] = useState(config.tabs[0][1]);
  const [catalogue, setCatalogue] = useState<SettingsCatalogue | null>(null);
  const [draft, setDraft] = useState<Record<string, string | boolean>>({});
  const [cleared, setCleared] = useState<Record<string, boolean>>({});
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  useEffect(() => {
    let active = true;
    readSettingsCatalogue().then(value => { if (active) { setCatalogue(value); setDraft(initialDraft(value)); } })
      .catch(() => { if (active) setError('Could not load host settings. Reopen to retry.'); });
    return () => { active = false; };
  }, []);
  const save = async () => {
    if (!catalogue || saving) return;
    setError(''); setSaving(true);
    try {
      const changes: Record<string, Record<string, unknown>> = {};
      let includesSecrets = false;
      for (const field of catalogue.fields) {
        if (field.readonly || !config.tabs.some(([, name]) => name === field.group)) continue;
        const id = fieldId(field);
        let value: unknown = draft[id];
        if (field.secret) {
          if (!cleared[id] && value === '') continue;
          value = cleared[id] ? '' : value; includesSecrets = true;
        } else {
          if (field.kind === 'int' || field.kind === 'float') {
            if (value === '') throw new Error(`${labelFor(field)} requires a number.`);
            value = Number(value);
            if (!Number.isFinite(value) || (field.kind === 'int' && !Number.isInteger(value))) throw new Error(`${labelFor(field)} requires a valid number.`);
          }
          if (field.kind === 'list') {
            try { value = JSON.parse(String(value)); } catch { throw new Error(`${labelFor(field)} requires a JSON list.`); }
            if (!Array.isArray(value)) throw new Error(`${labelFor(field)} requires a JSON list.`);
          }
          if (JSON.stringify(value) === JSON.stringify(field.value)) continue;
        }
        (changes[field.scope] ??= {})[field.key] = value;
      }
      if (Object.keys(changes).length) await saveCatalogueFields(catalogue, changes, includesSecrets);
      onClose();
    } catch (issue) { setError(issue instanceof Error ? issue.message : 'Settings save failed.'); }
    finally { setSaving(false); }
  };
  const fields = catalogue?.fields.filter(field => field.group === group) ?? [];
  return <Modal title={config.title} width={720} onClose={onClose} footer={<><Button onClick={onClose}>Close</Button><Button className="primary" disabled={!catalogue || saving} onClick={() => { void save(); }}>Save</Button></>}>
    <div className="host-settings-tabs" role="tablist" aria-label={`${config.title} tabs`}>
      {config.tabs.map(([label, name]) => <button key={name} role="tab" aria-selected={name === group} onClick={() => setGroup(name)}>{label}</button>)}
    </div>
    <div className="host-settings-panel" role="tabpanel" aria-label={config.tabs.find(([, name]) => name === group)?.[0]}>
      {!catalogue && !error && <p role="status">Loading host settings…</p>}
      {fields.map(field => {
        const id = fieldId(field); const label = labelFor(field);
        return <div className="host-setting-field" key={id}>
          {field.kind === 'bool' && !field.secret ? <label><input type="checkbox" checked={Boolean(draft[id])} disabled={field.readonly || saving} onChange={event => setDraft({ ...draft, [id]: event.target.checked })}/>{label}</label> :
          <><label htmlFor={id}>{label}</label>
            {field.secret ? <><input id={id} aria-label={label} type="password" autoComplete="new-password" value={String(draft[id] ?? '')} disabled={field.readonly || saving || cleared[id]} placeholder="Leave blank to keep existing value" onChange={event => setDraft({ ...draft, [id]: event.target.value })}/><span className="host-secret-state">{field.configured ? 'Configured' : 'Not configured'}</span>{!field.readonly && <label className="host-secret-clear"><input type="checkbox" checked={Boolean(cleared[id])} disabled={saving} onChange={event => setCleared({ ...cleared, [id]: event.target.checked })}/>Clear {label}</label>}</> :
            field.options?.length ? <select id={id} value={String(draft[id] ?? '')} disabled={field.readonly || saving} onChange={event => setDraft({ ...draft, [id]: event.target.value })}>{!field.options.includes(String(draft[id])) && <option value={String(draft[id])}>{String(draft[id])} (stored)</option>}{field.options.map(option => <option key={option} value={option}>{option || 'Plain text'}</option>)}</select> :
            field.kind === 'list' ? <textarea id={id} value={String(draft[id] ?? '')} readOnly={field.readonly} disabled={saving} onChange={event => setDraft({ ...draft, [id]: event.target.value })}/> :
            <input id={id} type={field.kind === 'int' || field.kind === 'float' ? 'number' : 'text'} step={field.kind === 'float' ? 'any' : 1} value={String(draft[id] ?? '')} readOnly={field.readonly} disabled={saving} onChange={event => setDraft({ ...draft, [id]: event.target.value })}/>}</>}
          <small>{field.scope}.{field.key}{field.readonly ? ' · Read-only' : ''}</small>
        </div>;
      })}
      {group === 'runtime' && catalogue?.unknown.map(field => <p key={`${field.scope}/${field.key}`}>{field.scope}.{field.key} — {field.reason}</p>)}
    </div>
    <p className="dialog-note">Save updates the host database. Connection, delivery and engine actions are handled by their runtime capabilities. Secrets are replaced only when entered or explicitly cleared.</p>
    {group === 'app_general' && <p className="dialog-note">Host, ports and GPU settings require restart. Language is retained as read-only compatibility data.</p>}
    {group === 'workspace_paths' && <p className="dialog-note">Changing paths does not move or delete existing files.</p>}
    {error && <p role="alert" className="settings-error">{error}</p>}
  </Modal>;
}

export function UserAccessPanel({ onClose }: { onClose: () => void }) {
  const [account, setAccount] = useState<HostAccount | null>(null);
  const [legacy, setLegacy] = useState<SettingsField[]>([]);
  const [current, setCurrent] = useState(''); const [password, setPassword] = useState(''); const [confirmation, setConfirmation] = useState('');
  const [saving, setSaving] = useState(false); const [error, setError] = useState('');
  useEffect(() => { let active = true; Promise.all([readHostAccount(), readSettingsCatalogue()]).then(([value, catalogue]) => { if (active) { setAccount(value); setLegacy(catalogue.fields.filter(field => field.group === 'user_access')); } }).catch(() => { if (active) setError('Could not load account settings.'); }); return () => { active = false; }; }, []);
  const save = async () => {
    if (!account || saving) return;
    if (!current) { setError('Enter the current host password.'); return; }
    if (password !== confirmation) { setError('New passwords do not match.'); return; }
    setSaving(true); setError('');
    try { await changeHostAccount(account, current, password); setCurrent(''); setPassword(''); setConfirmation(''); setAuthToken(null); onClose(); window.location.reload(); }
    catch (issue) { setError(issue instanceof Error ? issue.message : 'Account change failed.'); }
    finally { setSaving(false); }
  };
  return <Modal title="User access" width={640} onClose={onClose} footer={<><Button onClick={onClose}>Close</Button><Button className="primary" disabled={!account || saving} onClick={() => { void save(); }}>Save</Button></>}>
    {account && <div className="host-settings-panel">
      <label>Username<input value={account.username} disabled={saving} onChange={event => setAccount({ ...account, username: event.target.value })}/></label>
      <label>Session duration (minutes)<input type="number" min={1440} max={43200} value={account.session_timeout_mins} disabled={saving} onChange={event => setAccount({ ...account, session_timeout_mins: Number(event.target.value) })}/></label>
      <label>Current host password<input type="password" autoComplete="current-password" value={current} disabled={saving} onChange={event => setCurrent(event.target.value)}/></label>
      <label>New host password<input type="password" autoComplete="new-password" placeholder="Leave blank to keep your password" value={password} disabled={saving} onChange={event => setPassword(event.target.value)}/></label>
      <label>Confirm new host password<input type="password" autoComplete="new-password" value={confirmation} disabled={saving} onChange={event => setConfirmation(event.target.value)}/></label>
      <p className="dialog-note">Authentication is required. Sessions last at least 24 hours. Saving signs out all existing sessions; sign in again with your updated credentials.</p>
      <details><summary>Account metadata (read-only)</summary>{legacy.map(field => <p key={field.key}>{field.label}: {field.secret ? (field.configured ? 'Configured' : 'Not configured') : String(field.value)}<small> application.user_access.{field.key}</small></p>)}</details>
    </div>}
    {error && <p role="alert" className="settings-error">{error}</p>}
  </Modal>;
}
