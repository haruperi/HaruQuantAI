import { useEffect, useRef, useState, type KeyboardEvent as ReactKeyboardEvent, type ReactNode } from 'react';
import { Activity, AtSign, BadgeInfo, Check, ChevronLeft, ChevronRight, ChevronUp, CircleHelp, Cloud, Expand, Gauge, Globe2, Languages, LogOut, Mail, Minus, MonitorCog, Palette, Plus, RefreshCw, Server, Settings, ShieldCheck } from 'lucide-react';
import { Button, Checkbox, Field, Modal, ProgressBar, Select, TextInput } from '../components/ui';
import { useAppStore } from './store';
import type { ConfigurationSettings, RemoteAccessSettings, SmtpSettings } from './types';
import { applicationLanguages, applicationSkins, benchmarkResults, clampZoom, configurationTabs, isEmail, safeRemoteSettings, safeSmtpSettings, validateConfiguration } from './globalSettings';
import { useHostConnection } from './HostConnection';

type DialogName = 'configuration' | 'benchmark' | 'remote' | 'mcp' | 'smtp' | 'license' | 'about' | 'exit' | null;

function Radio({ checked, label, onChange, disabled = false }: { checked: boolean; label: string; onChange: () => void; disabled?: boolean }) {
  return <label className={`settings-radio ${disabled ? 'disabled' : ''}`}><input type="radio" checked={checked} onChange={onChange} disabled={disabled}/><span>{label}</span></label>;
}

function SettingSection({ title, children }: { title: string; children: ReactNode }) {
  return <fieldset className="settings-section"><legend>{title}</legend>{children}</fieldset>;
}

function ConfigurationDialog({ onClose }: { onClose: () => void }) {
  const settings = useAppStore(s => s.settings);
  const { saveSettings } = useHostConnection();
  const [draft, setDraft] = useState<ConfigurationSettings>({ ...settings.configuration });
  const [tab, setTab] = useState<(typeof configurationTabs)[number]>('Global');
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  const patch = (value: Partial<ConfigurationSettings>) => setDraft(current => ({ ...current, ...value }));
  const save = async () => {
    const problem = validateConfiguration(draft);
    if (problem) { setError(problem); return; }
    setSaving(true);
    const result = await saveSettings({ configuration: draft });
    setSaving(false);
    if (result.ok) onClose(); else setError(result.message);
  };
  return <Modal title="Configuration" onClose={onClose} width={820} footer={<><Button onClick={onClose}>Close</Button><Button className="primary" disabled={saving} onClick={() => { void save(); }}>Save</Button></>}>
    <div className="configuration-dialog">
      <nav role="tablist" aria-label="Configuration sections">{configurationTabs.map(item => <button key={item} role="tab" aria-selected={tab === item} className={tab === item ? 'active' : ''} onClick={() => { setTab(item); setError(''); }}>{item}</button>)}</nav>
      <div className="configuration-page">
        {tab === 'Global' && <>
          <SettingSection title="Application"><Checkbox label="Turn off application sounds" checked={draft.soundsOff} onChange={soundsOff => patch({ soundsOff })}/><Checkbox label="Remember last used folder in file chooser" checked={draft.rememberFileChooser} onChange={rememberFileChooser => patch({ rememberFileChooser })}/><Checkbox label="Show control orders in trades" checked={draft.showControlOrders} onChange={showControlOrders => patch({ showControlOrders })}/></SettingSection>
          <SettingSection title="Application title"><div className="settings-grid"><Field label="Custom header text"><TextInput maxLength={30} value={draft.headerCustomText} onChange={e => patch({ headerCustomText: e.target.value })}/></Field><Field label="Custom footer text"><TextInput maxLength={30} value={draft.footerCustomText} onChange={e => patch({ footerCustomText: e.target.value })}/></Field></div></SettingSection>
          <SettingSection title="Default result"><Radio checked={draft.defaultResult === 'portfolio'} label="Show portfolio result" onChange={() => patch({ defaultResult: 'portfolio' })}/><Radio checked={draft.defaultResult === 'main'} label="Show main result" onChange={() => patch({ defaultResult: 'main' })}/></SettingSection>
        </>}
        {tab === 'CPU' && <><SettingSection title="CPU cores"><div className="setting-summary">Available logical cores: <strong>{draft.totalCores}</strong></div><Radio checked={draft.coreUsage === 'single'} label="Use a single core" onChange={() => patch({ coreUsage: 'single' })}/><Radio checked={draft.coreUsage === 'reserve-one'} label="Use all cores except one" onChange={() => patch({ coreUsage: 'reserve-one' })}/><Radio checked={draft.coreUsage === 'custom'} label="Use custom number of cores" onChange={() => patch({ coreUsage: 'custom' })}/><TextInput aria-label="Custom cores" type="number" min="1" max={draft.totalCores} disabled={draft.coreUsage !== 'custom'} value={draft.customCores} onChange={e => patch({ customCores: Number(e.target.value) })}/><Radio checked={draft.coreUsage === 'maximum'} label="Use maximum available cores" onChange={() => patch({ coreUsage: 'maximum' })}/></SettingSection><SettingSection title="Process"><Checkbox label="Run calculation tasks with high priority" checked={draft.highPriority} onChange={highPriority => patch({ highPriority })}/><Checkbox label="Use thread affinity" checked={draft.threadAffinity} onChange={threadAffinity => patch({ threadAffinity })}/></SettingSection></>}
        {tab === 'Performance' && <SettingSection title="Additional calculations"><Checkbox label="Compute metrics in pips" checked={draft.computePipsMetrics} onChange={computePipsMetrics => patch({ computePipsMetrics })}/><Checkbox label="Compute metrics in percent" checked={draft.computePercentMetrics} onChange={computePercentMetrics => patch({ computePercentMetrics })}/><Checkbox label="Compute separate long and short metrics" checked={draft.computeSeparateMetrics} onChange={computeSeparateMetrics => patch({ computeSeparateMetrics })}/></SettingSection>}
        {tab === 'Memory' && <><SettingSection title="Garbage collector"><Radio checked={draft.garbageCollector === 'parallel'} label="Parallel garbage collector" onChange={() => patch({ garbageCollector: 'parallel' })}/><Radio checked={draft.garbageCollector === 'g1'} label="G1 garbage collector" onChange={() => patch({ garbageCollector: 'g1' })}/><Radio checked={draft.garbageCollector === 'automatic'} label="Select automatically" onChange={() => patch({ garbageCollector: 'automatic' })}/></SettingSection><SettingSection title="Memory allocation"><Checkbox label="Set maximum memory automatically" checked={draft.automaticMemory} onChange={automaticMemory => patch({ automaticMemory })}/><Field label="Maximum memory (GB)"><TextInput type="number" min="2" max="1024" disabled={draft.automaticMemory} value={draft.memoryGb} onChange={e => patch({ memoryGb: Number(e.target.value) })}/></Field><Checkbox label="Don't store pending orders" checked={draft.dontStorePendingOrders} onChange={dontStorePendingOrders => patch({ dontStorePendingOrders })}/><Checkbox label="Enable automatic memory cleanup" checked={draft.memoryCleanup} onChange={memoryCleanup => patch({ memoryCleanup })}/><Field label="Cleanup interval"><Select disabled={!draft.memoryCleanup} value={draft.cleanupInterval} onChange={cleanupInterval => patch({ cleanupInterval: cleanupInterval as ConfigurationSettings['cleanupInterval'] })}>{['5 minutes','15 minutes','30 minutes','1 hour'].map(x => <option key={x}>{x}</option>)}</Select></Field></SettingSection></>}
        {tab === 'Databanks' && <SettingSection title="Databank synchronization"><Field label="Synchronize changes"><Select value={draft.databankSyncInterval} onChange={databankSyncInterval => patch({ databankSyncInterval: databankSyncInterval as ConfigurationSettings['databankSyncInterval'] })}>{['Never','Immediately','Every 5 minutes','Every 10 minutes','Every 15 minutes','Every hour'].map(x => <option key={x}>{x}</option>)}</Select></Field><Button disabled>Apply to all existing databanks</Button><p className="dialog-note">Applying to existing databanks awaits their backend owner.</p><Checkbox label="Synchronize databanks after task finishes" checked={draft.syncDatabanksAfterTask} onChange={syncDatabanksAfterTask => patch({ syncDatabanksAfterTask })}/><Checkbox label="Store chart data in databanks" checked={draft.storeChartData} onChange={storeChartData => patch({ storeChartData })}/></SettingSection>}
        {tab === 'Optimizations' && <SettingSection title="Optimization results"><Checkbox label="Don't store 3D chart data" checked={draft.dontStoreOptimization3d} onChange={dontStoreOptimization3d => patch({ dontStoreOptimization3d })}/></SettingSection>}
        {tab === 'Troubleshooting' && <SettingSection title="Diagnostics"><Checkbox label="Enable GPU acceleration when available" checked={draft.gpuAccelerated} onChange={gpuAccelerated => patch({ gpuAccelerated })}/><Checkbox label="Enable memory protection" checked={draft.memoryProtection} onChange={memoryProtection => patch({ memoryProtection })}/><Checkbox label="Enable debug logging" checked={draft.debugLevel} onChange={debugLevel => patch({ debugLevel })}/></SettingSection>}
        {error && <p className="settings-error" role="alert">{error}</p>}
      </div>
      <p className="restart-note">These preferences are saved by the host. Calculation behavior awaits its backend owner.</p>
    </div>
  </Modal>;
}

function BenchmarkDialog({ onClose }: { onClose: () => void }) {
  const [state, setState] = useState<'beforeStart' | 'running' | 'showResults'>('beforeStart');
  const [progress, setProgress] = useState(0);
  useEffect(() => { if (state !== 'running') return; const timer = window.setInterval(() => setProgress(current => { if (current >= 90) { window.clearInterval(timer); setState('showResults'); return 100; } return current + 10; }), 120); return () => window.clearInterval(timer); }, [state]);
  return <Modal title="Benchmark" onClose={state === 'running' ? () => undefined : onClose} width={610} footer={state !== 'running' && <><Button onClick={onClose}>Close</Button>{state === 'beforeStart' && <Button className="primary" onClick={() => setState('running')}>Start benchmark</Button>}</>}>
    <div className="benchmark-dialog">{state === 'beforeStart' && <><Gauge size={52}/><h3>Test the performance of this computer</h3><p>The benchmark runs a deterministic frontend simulation and does not start the native HaruQuantAI engine.</p></>}{state === 'running' && <><Activity className="benchmark-pulse" size={48}/><h3>Benchmark is running...</h3><ProgressBar value={progress}/><p>Please wait until the test finishes.</p></>}{state === 'showResults' && <><ShieldCheck size={48}/><h3>Benchmark finished</h3><dl>{Object.entries(benchmarkResults).map(([key, value]) => <div key={key}><dt>{key.replace(/([A-Z])/g, ' $1')}</dt><dd>{value}</dd></div>)}</dl></>}</div>
  </Modal>;
}

function RemoteDialog({ onClose }: { onClose: () => void }) {
  const value = useAppStore(s => s.settings.remoteAccess); const { saveSettings } = useHostConnection();
  const [draft, setDraft] = useState<RemoteAccessSettings & { password: string }>({ ...value, password: '' });
  const [error, setError] = useState('');
  const save = async () => { const result = await saveSettings({ remoteAccess: safeRemoteSettings(draft) }); if (result.ok) onClose(); else setError(result.message); };
  return <Modal title="Remote access" onClose={onClose} width={590} footer={<><Button onClick={onClose}>Close</Button><Button className="primary" onClick={() => { void save(); }}>Save</Button></>}><SettingSection title="Remote browser access"><Checkbox label="Allow remote access to this application" checked={draft.allow} onChange={allow => setDraft({ ...draft, allow })}/>{draft.allow && <><Field label="Address"><TextInput readOnly value={`${location.origin}/remote`}/></Field><Checkbox label="Require a password" checked={draft.requirePassword} onChange={requirePassword => setDraft({ ...draft, requirePassword })}/>{draft.requirePassword && <Field label="Password"><TextInput type="password" autoComplete="new-password" value={draft.password} onChange={e => setDraft({ ...draft, password: e.target.value })}/></Field>}</>}</SettingSection><p className="dialog-note">Preferences are saved, but no remote server is opened. The password is not saved; password-protected access is unavailable.</p>{error && <p role="alert" className="settings-error">{error}</p>}</Modal>;
}

function McpDialog({ onClose }: { onClose: () => void }) {
  const endpoint = `${location.origin}/mcp`; const config = JSON.stringify({ mcpServers: { haruquantai: { url: endpoint } } }, null, 2);
  return <Modal title="MCP Server" onClose={onClose} width={650} footer={<Button onClick={onClose}>Close</Button>}><div className="stacked-settings"><p>Connect an MCP-compatible client to the simulated HaruQuantAI endpoint.</p><Field label="MCP endpoint"><TextInput readOnly value={endpoint}/></Field><Field label="CLI command"><TextInput readOnly value={`mcp connect haruquantai ${endpoint}`}/></Field><Field label="Client configuration (JSON)"><textarea className="text-area settings-code" readOnly value={config}/></Field><p className="dialog-note">No server is started by this frontend control.</p></div></Modal>;
}

function SmtpDialog({ onClose }: { onClose: () => void }) {
  const value = useAppStore(s => s.settings.smtp); const { saveSettings } = useHostConnection();
  const [draft, setDraft] = useState<SmtpSettings & { password: string }>({ ...value, password: '' }); const [recipient, setRecipient] = useState(''); const [testing, setTesting] = useState(false); const [message, setMessage] = useState('');
  const save = async () => { if (draft.emailFrom && !isEmail(draft.emailFrom)) { setMessage('Enter a valid sender email address.'); return; } const result = await saveSettings({ smtp: safeSmtpSettings(draft) }); if (result.ok) onClose(); else setMessage(result.message); };
  const test = () => { if (!testing) { setTesting(true); setMessage(''); return; } if (!isEmail(recipient)) { setMessage('Enter a valid test recipient.'); return; } setMessage(`Test message simulated for ${recipient.trim()}.`); };
  return <Modal title="SMTP server" onClose={onClose} width={650} footer={<><Button onClick={onClose}>Close</Button><Button onClick={test}>Send test email</Button><Button className="primary" onClick={() => { void save(); }}>Save</Button></>}><div className="stacked-settings settings-grid"><Field label="SMTP server"><TextInput value={draft.server} onChange={e => setDraft({ ...draft, server: e.target.value })}/></Field><Field label="Port"><TextInput value={draft.port} onChange={e => setDraft({ ...draft, port: e.target.value })}/></Field><Checkbox label="Use SSL/TLS" checked={draft.ssl} onChange={ssl => setDraft({ ...draft, ssl })}/><Field label="Username"><TextInput autoComplete="username" value={draft.username} onChange={e => setDraft({ ...draft, username: e.target.value })}/></Field><Field label="Password"><TextInput type="password" autoComplete="new-password" value={draft.password} onChange={e => setDraft({ ...draft, password: e.target.value })}/></Field><Field label="Sender email"><TextInput value={draft.emailFrom} onChange={e => setDraft({ ...draft, emailFrom: e.target.value })}/></Field>{testing && <Field label="Test recipient"><TextInput value={recipient} onChange={e => setRecipient(e.target.value)}/></Field>}{message && <p role="status" className="dialog-note">{message}</p>}<p className="dialog-note">Non-secret SMTP preferences are saved. No email service is active; the password is not saved.</p></div></Modal>;
}

function LicenseDialog({ onClose }: { onClose: () => void }) { const [license, setLicense] = useState(''); const [result, setResult] = useState(''); return <Modal title="Update license" onClose={onClose} width={520} footer={<><Button onClick={onClose}>Close</Button><Button className="primary" disabled={!license.trim()} onClick={() => setResult('License verification simulated. No account or license service was contacted.')}>Update license</Button></>}><div className="stacked-settings"><p>Enter a license key to update the active application license.</p><Field label="License key"><TextInput type="password" autoComplete="off" value={license} onChange={e => setLicense(e.target.value)} maxLength={128}/></Field>{result && <p className="dialog-note" role="status">{result}</p>}</div></Modal>; }

function AboutDialog({ onClose }: { onClose: () => void }) { return <Modal title="About HaruQuantAI" onClose={onClose} width={520} footer={<Button onClick={onClose}>Close</Button>}><div className="about-dialog"><div className="about-mark"><Activity/></div><h2>HaruQuantAI</h2><strong>HaruQuantAI frontend recreation</strong><p>Build 144.2953 reference</p><p>Research workspaces use simulated data. The platform host connection is shown in the status bar.</p></div></Modal>; }

function ExitDialog({ onClose }: { onClose: () => void }) { const notify = useAppStore(s => s.notify); return <Modal title="Exit HaruQuantAI" onClose={onClose} width={470} footer={<><Button onClick={onClose}>Cancel</Button><Button className="danger" onClick={() => { notify('Exit is unavailable in the browser application'); onClose(); }}>Exit</Button></>}><p>Do you really want to exit the application?</p><p className="dialog-note">The browser-hosted frontend cannot close the desktop process.</p></Modal>; }

export function GlobalSettingsMenu() {
  const settings = useAppStore(s => s.settings); const notify = useAppStore(s => s.notify);
  const { saveSettings } = useHostConnection();
  const [open, setOpen] = useState(false); const [submenu, setSubmenu] = useState<'language' | 'skin' | null>(null); const [dialog, setDialog] = useState<DialogName>(null);
  const root = useRef<HTMLDivElement>(null); const trigger = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    if (!open) return;
    const close = (event: MouseEvent) => { if (!root.current?.contains(event.target as Node)) { setOpen(false); setSubmenu(null); } };
    const escape = (event: globalThis.KeyboardEvent) => { if (event.key === 'Escape') { setOpen(false); setSubmenu(null); trigger.current?.focus(); } };
    document.addEventListener('mousedown', close); document.addEventListener('keydown', escape);
    return () => { document.removeEventListener('mousedown', close); document.removeEventListener('keydown', escape); };
  }, [open]);
  const launch = (name: DialogName) => { setOpen(false); setSubmenu(null); setDialog(name); };
  const onMenuKeyDown = (event: ReactKeyboardEvent<HTMLDivElement>) => {
    const items = [...event.currentTarget.querySelectorAll<HTMLButtonElement>('[role="menuitem"]:not(:disabled)')]; const current = items.indexOf(document.activeElement as HTMLButtonElement);
    if (event.key === 'Escape') { event.preventDefault(); setOpen(false); setSubmenu(null); trigger.current?.focus(); }
    if (['ArrowDown','ArrowUp','Home','End'].includes(event.key)) { event.preventDefault(); const next = event.key === 'Home' ? 0 : event.key === 'End' ? items.length - 1 : (current + (event.key === 'ArrowDown' ? 1 : -1) + items.length) % items.length; items[next]?.focus(); }
  };
  const unavailable = (label: string) => { notify(`${label} is not configured for this HaruQuantAI workspace`); setOpen(false); setSubmenu(null); };
  const fullscreen = async () => { try { if (document.fullscreenElement) await document.exitFullscreen(); else await document.documentElement.requestFullscreen(); } catch { notify('Fullscreen is unavailable in this browser'); } };
  const item = (label: string, icon: ReactNode, action: () => void, suffix?: ReactNode) => <button role="menuitem" onClick={action}>{icon}<span>{label}</span>{suffix}</button>;
  return <div className="global-settings" ref={root}>
    <button ref={trigger} className="top-action" title="Settings" aria-label="Settings" aria-haspopup="menu" aria-expanded={open} onClick={() => { setOpen(value => !value); setSubmenu(null); }}><Settings/></button>
    {open && <div className="global-settings-menu" role="menu" aria-label="Application settings" onKeyDown={onMenuKeyDown}>
      <div className="settings-menu-group">{item('Configuration...', <Settings/>, () => launch('configuration'))}{item('Benchmark...', <Gauge/>, () => launch('benchmark'))}{item('Remote access...', <Cloud/>, () => launch('remote'))}{item('MCP Server...', <Server/>, () => launch('mcp'))}{item('SMTP server...', <Mail/>, () => launch('smtp'))}</div>
      <div className="settings-menu-group submenu-host">{item('Language', <Languages/>, () => setSubmenu(submenu === 'language' ? null : 'language'), <ChevronRight/>)}{submenu === 'language' && <div className="settings-submenu" role="menu" aria-label="Language">{applicationLanguages.map(language => <button role="menuitem" key={language} onClick={() => { void saveSettings({ language }); setOpen(false); setSubmenu(null); }}>{settings.language === language ? <Check/> : <span/>}<span>{language}</span></button>)}</div>}</div>
      <div className="settings-menu-group submenu-host">{item('Skin', <Palette/>, () => setSubmenu(submenu === 'skin' ? null : 'skin'), <ChevronRight/>)}{submenu === 'skin' && <div className="settings-submenu skin-submenu" role="menu" aria-label="Skin">{applicationSkins.map(skin => <button role="menuitem" key={skin} onClick={() => { void saveSettings({ theme: skin === 'Dark skin' ? 'dark' : 'light' }); setOpen(false); setSubmenu(null); }}>{settings.theme === (skin === 'Dark skin' ? 'dark' : 'light') ? <Check/> : <span/>}<span>{skin}</span></button>)}</div>}</div>
      <div className="settings-menu-group zoom-menu-row"><span><MonitorCog/>Zoom</span><button aria-label="Zoom out" onClick={() => { void saveSettings({ zoom: clampZoom(settings.zoom - .1) }); }}><Minus/></button><output>{Math.round(settings.zoom * 100)}%</output><button aria-label="Zoom in" onClick={() => { void saveSettings({ zoom: clampZoom(settings.zoom + .1) }); }}><Plus/></button><button aria-label="Toggle fullscreen" onClick={fullscreen}><Expand/></button></div>
      <div className="settings-menu-group">{item('HaruQuantAI Website', <Globe2/>, () => unavailable('Website'))}{item('Help center', <CircleHelp/>, () => unavailable('Help center'))}{item('Support', <AtSign/>, () => unavailable('Support'))}{item('Update license', <RefreshCw/>, () => launch('license'))}{item('About', <BadgeInfo/>, () => launch('about'))}</div>
      <div className="settings-menu-group">{item('Reload UI', <RefreshCw/>, () => window.location.reload())}{item('Exit', <LogOut/>, () => launch('exit'))}</div>
    </div>}
    {dialog === 'configuration' && <ConfigurationDialog onClose={() => setDialog(null)}/>} {dialog === 'benchmark' && <BenchmarkDialog onClose={() => setDialog(null)}/>} {dialog === 'remote' && <RemoteDialog onClose={() => setDialog(null)}/>} {dialog === 'mcp' && <McpDialog onClose={() => setDialog(null)}/>} {dialog === 'smtp' && <SmtpDialog onClose={() => setDialog(null)}/>} {dialog === 'license' && <LicenseDialog onClose={() => setDialog(null)}/>} {dialog === 'about' && <AboutDialog onClose={() => setDialog(null)}/>} {dialog === 'exit' && <ExitDialog onClose={() => setDialog(null)}/>}
  </div>;
}
