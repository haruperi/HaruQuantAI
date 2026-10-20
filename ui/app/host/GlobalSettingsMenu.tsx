import { useEffect, useRef, useState, type KeyboardEvent as ReactKeyboardEvent, type ReactNode } from 'react';
import { Activity, Check, ChevronLeft, ChevronRight, ChevronUp, Cloud, Expand, Gauge, LogOut, Mail, Minus, MonitorCog, Palette, Plus, RefreshCw, Server, Settings, ShieldCheck } from 'lucide-react';
import { Button, Checkbox, Field, Modal, ProgressBar, TextInput } from '../components/ui';
import { useAppStore } from './store';
import type { ConfigurationSettings, RemoteAccessSettings } from './types';
import { applicationSkins, benchmarkResults, clampZoom, configurationTabs, safeRemoteSettings, validateConfiguration } from './globalSettings';
import { HostSettingsModal, UserAccessPanel } from './HostSettingsModal';
import { useHostConnection } from './HostConnection';

type DialogName = 'configuration' | 'benchmark' | 'remote' | 'mcp' | 'smtp' | 'notifications' | 'credentials' | 'advanced' | 'account' | 'exit' | null;

function Radio({ checked, label, onChange, disabled = false }: { checked: boolean; label: string; onChange: () => void; disabled?: boolean }) {
  return <label className={`settings-radio ${disabled ? 'disabled' : ''}`}><input type="radio" checked={checked} onChange={onChange} disabled={disabled}/><span>{label}</span></label>;
}

function SettingSection({ title, children }: { title: string; children: ReactNode }) {
  return <fieldset className="settings-section"><legend>{title}</legend>{children}</fieldset>;
}

function ConfigurationDialog({ onClose }: { onClose: () => void }) {
  const settings = useAppStore(s => s.settings);
  const { saveSettings, settingsRevision } = useHostConnection();
  const openingRevision = useRef(settingsRevision).current;
  const savingRef = useRef(false);
  const [draft, setDraft] = useState<ConfigurationSettings>({ ...settings.configuration });
  const [tab, setTab] = useState<(typeof configurationTabs)[number]>('Global');
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  const patch = (value: Partial<ConfigurationSettings>) => setDraft(current => ({ ...current, ...value }));
  const save = async () => {
    if (savingRef.current) return;
    const problem = validateConfiguration(draft);
    if (problem) { setError(problem); return; }
    savingRef.current = true;
    setSaving(true);
    const result = await saveSettings({ configuration: draft }, openingRevision);
    savingRef.current = false;
    setSaving(false);
    if (result.ok) onClose(); else setError(result.message);
  };
  const hint = (children: ReactNode) => <p className="sqx-config-hint">{children}</p>;
  const spinner = (label: string, value: number, min: number, max: number, disabled: boolean, update: (value: number) => void) => <span className="sqx-config-spinner"><input aria-label={label} type="number" min={min} max={max} disabled={disabled} value={value} onChange={e => update(Number(e.target.value))}/><button type="button" aria-label={`Decrease ${label}`} disabled={disabled || value <= min} onClick={() => update(Math.max(min, value - 1))}>−</button><button type="button" aria-label={`Increase ${label}`} disabled={disabled || value >= max} onClick={() => update(Math.min(max, value + 1))}>+</button></span>;
  return <Modal title="Configuration" onClose={onClose} width={700} className="sqx-configuration-modal" showHeaderClose={false} footer={<><span className="sqx-config-capability" title="Settings are stored by the host. Engine, Java GC, scheduling, file synchronization and browser GPU behavior require their backend owners.">Preferences are saved by the host; runtime effects depend on backend support.</span><Button className="sqx-config-close" onClick={onClose}>Close</Button><Button className="primary" disabled={saving} onClick={() => { void save(); }}>Save</Button></>}>
    <div className="configuration-dialog sqx-configuration">
      <nav role="tablist" aria-label="Configuration sections">{configurationTabs.map(item => <button key={item} id={`configuration-tab-${item}`} role="tab" aria-controls="configuration-panel" aria-selected={tab === item} className={tab === item ? 'active' : ''} onClick={() => { setTab(item); setError(''); }}>{item}</button>)}</nav>
      <div id="configuration-panel" role="tabpanel" aria-labelledby={`configuration-tab-${tab}`} className={`configuration-page sqx-config-${tab.toLowerCase()}`}>
        {tab === 'Global' && <>
          <Checkbox label="Turn off notification sounds" checked={draft.soundsOff} onChange={soundsOff => patch({ soundsOff })}/>
          <Checkbox label="Remember View type and Sorting in File chooser" checked={draft.rememberFileChooser} onChange={rememberFileChooser => patch({ rememberFileChooser })}/>
          <Checkbox label="Show control orders when using MT5 netting engine" checked={draft.showControlOrders} onChange={showControlOrders => patch({ showControlOrders })}/>
          <div className="sqx-config-texts"><Field label="Window Header custom text"><TextInput maxLength={30} value={draft.headerCustomText} onChange={e => patch({ headerCustomText: e.target.value })}/></Field><Field label="Window Footer custom text"><TextInput maxLength={30} value={draft.footerCustomText} onChange={e => patch({ footerCustomText: e.target.value })}/></Field></div>
          <div className="sqx-config-columns"><span>What result to display on default</span><div><div className="sqx-config-result"><Radio checked={draft.defaultResult === 'portfolio'} label="Portfolio (if exists)" onChange={() => patch({ defaultResult: 'portfolio' })}/><Radio checked={draft.defaultResult === 'main'} label="Main backtest result" onChange={() => patch({ defaultResult: 'main' })}/></div>{hint('This affects which of the results are displayed by default in databank and in Results screen')}</div></div>
          <div className="sqx-config-columns"><span>Check the data frame when a project starts</span><div><Radio checked={draft.dataFrameGuard === 'warn'} label="Warn in the project log" onChange={() => patch({ dataFrameGuard: 'warn' })}/><Radio checked={draft.dataFrameGuard === 'stop'} label="Stop the project" onChange={() => patch({ dataFrameGuard: 'stop' })}/><Radio checked={draft.dataFrameGuard === 'off'} label="Off" onChange={() => patch({ dataFrameGuard: 'off' })}/>{hint('A bar timestamp means either the moment the bar opened or the moment it closed. If a symbol is declared the wrong way round, every backtest on it is shifted by one bar. This reads a small sample of the stored data when a project starts and says so. Healthy data produces no message.')}</div></div>
        </>}
        {tab === 'CPU' && <>
          <p className="sqx-config-cores">Total cores available {draft.totalCores}</p>
          <Radio checked={draft.coreUsage === 'single'} label="Single threaded - program runs tasks sequentially, one after another." onChange={() => patch({ coreUsage: 'single' })}/><p className="sqx-config-single-help">This is slower, but consumes less memory.</p>
          <Radio checked={draft.coreUsage === 'reserve-one'} label="Reserve 1 core for UI, compute tasks in parallel on all remaining cores." onChange={() => patch({ coreUsage: 'reserve-one' })}/>
          <div className="sqx-config-inline"><Radio checked={draft.coreUsage === 'custom'} label="Custom number of cores" onChange={() => patch({ coreUsage: 'custom' })}/>{spinner('Custom cores', draft.customCores, 1, draft.totalCores, draft.coreUsage !== 'custom', customCores => patch({ customCores }))}</div>
          <Radio checked={draft.coreUsage === 'maximum'} label="Max performance - running multiple tasks in parallel, using all processor cores." onChange={() => patch({ coreUsage: 'maximum' })}/>
          <div className="sqx-config-block"><Checkbox label="Run StrategyQuant in high priority mode" checked={draft.highPriority} onChange={highPriority => patch({ highPriority })}/><Checkbox label="Thread affinity" checked={draft.threadAffinity} onChange={threadAffinity => patch({ threadAffinity })}/>{hint(<>Use this option ONLY if your SQX doesn't fully utilize your CPU in maximum settings - this could happen with newest processors with P and E-cores.<br/>By using it, SQX process will run in high priority mode, overcoming the efficiency limitations of the system.</>)}</div>
        </>}
        {tab === 'Performance' && <>
          <Checkbox label="Compute metrics in pips (Recommended turned off)" checked={draft.computePipsMetrics} onChange={computePipsMetrics => patch({ computePipsMetrics })}/><Checkbox label="Compute metrics in percent (Recommended turned off)" checked={draft.computePercentMetrics} onChange={computePercentMetrics => patch({ computePercentMetrics })}/>
          {hint("In addition to metrics in money, also metrics for % and pips results can be computed. It is generally recommended to have it turned off. Most people don't need these results and not computing and storing them will improve speed and memory consumption.")}
          <div className="sqx-config-block"><Checkbox label="Compute metrics separate for every data part of the same type" checked={draft.computeSeparateMetrics} onChange={computeSeparateMetrics => patch({ computeSeparateMetrics })}/>{hint('Turning this on means that if you have your data divided into multiple OOS parts, for example OOS1, OOS2, OOS3, OOS4 - then the metrics like Net profit etc. will be computed also separately for each of these parts.')}{hint('This enables you to see these metrics separately in Results or databank, or use them in conditions but it also slows down the program and uses more memory.')}{hint("On by default, turn it off if you don't use it. Whole OOS metrics are always computed.")}</div>
        </>}
        {tab === 'Memory' && <>
          <div className="sqx-config-gc"><span>Garbage collector:</span><Radio checked={draft.garbageCollector === 'parallel'} label="ParallelGC (Recommended)" onChange={() => patch({ garbageCollector: 'parallel' })}/><Radio checked={draft.garbageCollector === 'g1'} label="G1" onChange={() => patch({ garbageCollector: 'g1' })}/><Radio checked={draft.garbageCollector === 'automatic'} label="Let Java decide" onChange={() => patch({ garbageCollector: 'automatic' })}/></div>
          <div className="sqx-config-memory-mode"><Radio checked={draft.automaticMemory} label="Let program determine maximum memory" onChange={() => patch({ automaticMemory: true })}/><div className="sqx-config-inline"><Radio checked={!draft.automaticMemory} label="Set maximum memory to" onChange={() => patch({ automaticMemory: false })}/>{spinner('Maximum memory (GB)', draft.memoryGb, 2, 1024, draft.automaticMemory, memoryGb => patch({ memoryGb }))}<span>GB</span></div></div>
          <div className="sqx-config-block"><Checkbox label="Don't store unfilled pending orders (Recommended)" checked={draft.dontStorePendingOrders} onChange={dontStorePendingOrders => patch({ dontStorePendingOrders })}/>{hint('It is usually not necessary to keep unfilled pending orders(orders that expired or were replaced). This would make the resulting strategy files smaller.')}</div>
          <div className="sqx-config-block"><div className="sqx-config-inline"><Checkbox label="Perform memory cleanup periodically -" checked={draft.memoryCleanup} onChange={memoryCleanup => patch({ memoryCleanup })}/><label className="sqx-config-select"><span className="sr-only">Cleanup interval</span><select className="text-input" aria-label="Cleanup interval" value={draft.cleanupInterval} onChange={e => patch({ cleanupInterval: e.target.value as ConfigurationSettings['cleanupInterval'] })}>{['never','5 minutes','15 minutes','30 minutes','1 hour'].map(x => <option key={x}>{x}</option>)}</select></label></div>{hint(<>Clean memory periodically by explicitly calling Java Garbage Collector.<br/>Use it if you experience problems with memory, otherwise keep it turned off.<br/>Java does this automatically and it usually does a very good job.<br/>Turning it on without reason might slow down the application.</>)}</div>
        </>}
        {tab === 'Databanks' && <>
          <div className="sqx-config-sync"><label className="sqx-config-inline">Default auto-sync interval<select className="text-input" aria-label="Default auto-sync interval" value={draft.databankSyncInterval} onChange={event => patch({ databankSyncInterval: event.target.value as ConfigurationSettings['databankSyncInterval'] })}>{['Never','Immediately','Every 5 minutes','Every 10 minutes','Every 15 minutes','Every hour'].map(x => <option key={x} value={x}>{x === 'Every hour' ? 'Auto-sync every 1 hour' : x.startsWith('Every') ? `Auto-sync ${x.toLowerCase()}` : x}</option>)}</select></label><Button disabled aria-describedby="databank-apply-limit">Apply to all existing databanks</Button></div>
          {hint(<>Databanks keep strategies in memory for fast access.<br/>They can be automatically synchronized to the disc in a preconfigured interval so that there is a backup in in case of program crash. Don't synchronize them too often though, it negatively impacts the performance.</>)}
          {hint('Settings are applied to all newly created databanks. If you want to apply them to all the existing databanks click on the button below.')}
          <p id="databank-apply-limit" className="sqx-config-limit">Apply-to-all is unavailable until backend databank support exists.</p>
          <div className="sqx-config-block"><Checkbox label="Synchronize to files automatically after task completion" checked={draft.syncDatabanksAfterTask} onChange={syncDatabanksAfterTask => patch({ syncDatabanksAfterTask })}/>{hint(<>If on, strategies in task's output databank will be saved to files automatically after the task is done.<br/>No restart needed for this setting to take effect.</>)}</div>
          <div className="sqx-config-block"><Checkbox label="Save chart data to .sq4 file (not recommended)" checked={draft.storeChartData} onChange={storeChartData => patch({ storeChartData })}/>{hint('If on and you have configured to Store Chart Data in Trading Options, trades on chart are saved to .sq4 file. This makes the resulting file much bigger, but it allows you to view Trades on chart later.')}{hint(<>If off, chart data are kept only temporarily and will be thrown away when not used.<br/>You'll have to retest the strategy to get the chart data again.</>)}</div>
        </>}
        {tab === 'Optimizations' && <>
          <Checkbox label="Don't store data for 3D charts in Optimization profile" checked={draft.dontStoreOptimization3d} onChange={dontStoreOptimization3d => patch({ dontStoreOptimization3d })}/>
          {hint('Turned on by default, it saves a lot of memory both in RAM and in disk files when working with Optimizations (simple or WF).')}
          {hint(<>Data required for 3D optimization charts are very big and are usually not needed at all.<br/>This does not affect other functionality of Optimization profile - filtering and conditions will work as usual.<br/>It also has nothing to do with Walk-Forward results charts.</>)}
          {hint('To show 3D optimization charts just reoptimize the strategy with this setting off.')}
        </>}
        {tab === 'Troubleshooting' && <>
          <Checkbox label="Accelerate internal browser using GPU" checked={draft.gpuAccelerated} onChange={gpuAccelerated => patch({ gpuAccelerated })}/>{hint("If you experience problems with GUI, such as freezing or black screen, try turning this off. It will switch to a different rendering method.")}
          <div className="sqx-config-block"><Checkbox label="Use memory protection - stop projects when 85% of memory is reached" checked={draft.memoryProtection} onChange={memoryProtection => patch({ memoryProtection })}/>{hint(<>This will stop your projects when SQ reaches 85% of memory usage.<br/>It prevents program from freezing and being unresponsive.<br/>Turn it on if you experience program freezes.</>)}</div>
          <div className="sqx-config-block"><Checkbox label="Activate debug level" checked={draft.debugLevel} onChange={debugLevel => patch({ debugLevel })}/>{hint('By turning this on you’ll activate debug logging level. Debug level should be used only when investigating some problem, it is much slower and produces very large log files.')}</div>
        </>}
        {error && <p className="settings-error" role="alert">{error}</p>}
      </div>
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
  const value = useAppStore(s => s.settings.remoteAccess); const { saveSettings, settingsRevision } = useHostConnection();
  const openingRevision = useRef(settingsRevision).current;
  const savingRef = useRef(false);
  const [saving, setSaving] = useState(false);
  const [draft, setDraft] = useState<RemoteAccessSettings & { password: string }>({ ...value, password: '' });
  const [error, setError] = useState('');
  const save = async () => { if (savingRef.current) return; savingRef.current = true; setSaving(true); const result = await saveSettings({ remoteAccess: safeRemoteSettings(draft) }, openingRevision); savingRef.current = false; setSaving(false); if (result.ok) onClose(); else setError(result.message); };
  return <Modal title="Remote access" onClose={onClose} width={590} footer={<><Button onClick={onClose}>Close</Button><Button className="primary" disabled={saving} onClick={() => { void save(); }}>Save</Button></>}><SettingSection title="Remote browser access"><Checkbox label="Allow remote access to this application" checked={draft.allow} onChange={allow => setDraft({ ...draft, allow })}/>{draft.allow && <><Field label="Address"><TextInput readOnly value={`${location.origin}/remote`}/></Field><Checkbox label="Require a password" checked={draft.requirePassword} onChange={requirePassword => setDraft({ ...draft, requirePassword })}/>{draft.requirePassword && <Field label="Password"><TextInput type="password" readOnly disabled value="" aria-label="Remote password unavailable"/></Field>}</>}</SettingSection><p className="dialog-note">Preferences are saved, but no remote server is opened. The password is not saved; password-protected access is unavailable.</p>{error && <p role="alert" className="settings-error">{error}</p>}</Modal>;
}

function ExitDialog({ onClose }: { onClose: () => void }) { const notify = useAppStore(s => s.notify); return <Modal title="Exit HaruQuantAI" onClose={onClose} width={470} footer={<><Button onClick={onClose}>Cancel</Button><Button className="danger" onClick={() => { notify('Exit is unavailable in the browser application'); onClose(); }}>Exit</Button></>}><p>Do you really want to exit the application?</p><p className="dialog-note">The browser-hosted frontend cannot close the desktop process.</p></Modal>; }

export function GlobalSettingsMenu() {
  const settings = useAppStore(s => s.settings); const notify = useAppStore(s => s.notify);
  const { saveSettings } = useHostConnection();
  const [open, setOpen] = useState(false); const [submenu, setSubmenu] = useState<'skin' | null>(null); const [dialog, setDialog] = useState<DialogName>(null);
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
  const fullscreen = async () => { try { if (document.fullscreenElement) await document.exitFullscreen(); else await document.documentElement.requestFullscreen(); } catch { notify('Fullscreen is unavailable in this browser'); } };
  const item = (label: string, icon: ReactNode, action: () => void, suffix?: ReactNode) => <button role="menuitem" onClick={action}>{icon}<span>{label}</span>{suffix}</button>;
  return <div className="global-settings" ref={root}>
    <button ref={trigger} className="top-action" title="Settings" aria-label="Settings" aria-haspopup="menu" aria-expanded={open} onClick={() => { setOpen(value => !value); setSubmenu(null); }}><Settings/></button>
    {open && <div className="global-settings-menu" role="menu" aria-label="Application settings" onKeyDown={onMenuKeyDown}>
      <div className="settings-menu-group">{item('Configuration...', <Settings/>, () => launch('configuration'))}{item('Benchmark...', <Gauge/>, () => launch('benchmark'))}{item('Remote access...', <Cloud/>, () => launch('remote'))}{item('MCP Server...', <Server/>, () => launch('mcp'))}{item('SMTP server...', <Mail/>, () => launch('smtp'))}</div>
      <div className="settings-menu-group">{item('Notifications...', <Mail/>, () => launch('notifications'))}{item('User access...', <ShieldCheck/>, () => launch('account'))}{item('Credentials...', <Server/>, () => launch('credentials'))}{item('Advanced settings...', <Settings/>, () => launch('advanced'))}</div>
      <div className="settings-menu-group submenu-host">{item('Skin', <Palette/>, () => setSubmenu(submenu === 'skin' ? null : 'skin'), <ChevronRight/>)}{submenu === 'skin' && <div className="settings-submenu skin-submenu" role="menu" aria-label="Skin">{applicationSkins.map(skin => <button role="menuitem" key={skin} onClick={() => { void saveSettings({ theme: skin === 'Dark skin' ? 'dark' : 'light' }); setOpen(false); setSubmenu(null); }}>{settings.theme === (skin === 'Dark skin' ? 'dark' : 'light') ? <Check/> : <span/>}<span>{skin}</span></button>)}</div>}</div>
      <div className="settings-menu-group zoom-menu-row"><span><MonitorCog/>Zoom</span><button aria-label="Zoom out" onClick={() => { void saveSettings(current => ({ zoom: clampZoom(current.zoom - .1) })); }}><Minus/></button><output>{Math.round(settings.zoom * 100)}%</output><button aria-label="Zoom in" onClick={() => { void saveSettings(current => ({ zoom: clampZoom(current.zoom + .1) })); }}><Plus/></button><button aria-label="Toggle fullscreen" onClick={fullscreen}><Expand/></button></div>
      <div className="settings-menu-group">{item('Reload UI', <RefreshCw/>, () => window.location.reload())}{item('Exit', <LogOut/>, () => launch('exit'))}</div>
    </div>}
    {dialog === 'configuration' && <ConfigurationDialog onClose={() => setDialog(null)}/>} {dialog === 'benchmark' && <BenchmarkDialog onClose={() => setDialog(null)}/>} {dialog === 'remote' && <RemoteDialog onClose={() => setDialog(null)}/>} {(dialog === 'mcp' || dialog === 'smtp' || dialog === 'notifications' || dialog === 'credentials' || dialog === 'advanced') && <HostSettingsModal section={dialog} onClose={() => setDialog(null)}/>} {dialog === 'account' && <UserAccessPanel onClose={() => setDialog(null)}/>} {dialog === 'exit' && <ExitDialog onClose={() => setDialog(null)}/>}
  </div>;
}
