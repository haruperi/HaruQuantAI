import { useEffect, useRef, useState, type ChangeEvent, type KeyboardEvent as ReactKeyboardEvent, type ReactNode } from 'react';
import {
  Activity,
  Bell,
  Check,
  ChevronLeft,
  ChevronRight,
  ChevronUp,
  Cloud,
  Expand,
  Eye,
  EyeOff,
  Gauge,
  KeyRound,
  LogOut,
  Mail,
  Minus,
  MonitorCog,
  Palette,
  Plus,
  RefreshCw,
  Server,
  Settings,
  ShieldCheck,
} from 'lucide-react';
import { Button, Checkbox, Field, Modal, ProgressBar, Select, TextInput } from '../components/ui';
import { useAppStore } from './store';
import type {
  AgentSettings,
  BacktestEngineSettings,
  ConfigurationSettings,
  CtraderSettings,
  DesktopNotificationSettings,
  DirectoriesSettings,
  GeminiAgentConfig,
  McpSettings,
  Mt5Settings,
  OllamaAgentConfig,
  OpenAiAgentConfig,
  RemoteAccessSettings,
  SmtpSettings,
  TelegramSettings,
} from './types';
import {
  applicationSkins,
  benchmarkResults,
  clampZoom,
  configurationTabs,
  credentialsTabs,
  isEmail,
  safeMcpSettings,
  safeRemoteSettings,
  safeSmtpSettings,
  safeTelegramSettings,
  validateConfiguration,
} from './globalSettings';
import { useHostConnection } from './HostConnection';
import { readHostPreferences } from './hostSettings';

type DialogName = 'configuration' | 'credentials' | 'benchmark' | 'remote' | 'mcp' | 'notifications' | 'exit' | null;

function SecretInput({
  value,
  onChange,
  placeholder,
  autoComplete = 'off',
  maxLength,
}: {
  value: string;
  onChange: (e: ChangeEvent<HTMLInputElement>) => void;
  placeholder?: string;
  autoComplete?: string;
  maxLength?: number;
}) {
  const [visible, setVisible] = useState(false);
  return (
    <div className="secret-input-wrapper">
      <TextInput
        type={visible ? 'text' : 'password'}
        autoComplete={autoComplete}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        maxLength={maxLength}
      />
      <button
        type="button"
        className="secret-toggle-btn"
        aria-label={visible ? 'Hide secret' : 'Show secret'}
        title={visible ? 'Hide secret' : 'Show secret'}
        onClick={() => setVisible(v => !v)}
      >
        {visible ? <EyeOff size={15} /> : <Eye size={15} />}
      </button>
    </div>
  );
}

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

  useEffect(() => {
    void readHostPreferences().then(snap => {
      useAppStore.getState().updateSettings({
        ...snap.preferences,
        configuration: snap.preferences.configuration,
        memoryGb: snap.preferences.configuration.memoryGb,
      });
      setDraft({ ...snap.preferences.configuration });
    }).catch(() => {});
  }, []);

  useEffect(() => {
    setDraft({ ...settings.configuration });
  }, [settings.configuration]);
  const patch = (value: Partial<ConfigurationSettings>) => setDraft(current => ({ ...current, ...value }));
  const patchDirs = (value: Partial<DirectoriesSettings>) => setDraft(current => ({ ...current, directories: { ...current.directories, ...value } }));
  const patchEngine = (value: Partial<BacktestEngineSettings>) => setDraft(current => ({ ...current, backtestEngine: { ...current.backtestEngine, ...value } }));

  const save = async () => {
    const problem = validateConfiguration(draft);
    if (problem) { setError(problem); return; }
    setSaving(true);
    const result = await saveSettings({ configuration: draft });
    setSaving(false);
    if (result.ok) onClose(); else setError(result.message);
  };
  return <Modal title="Configuration" onClose={onClose} width={860} footer={<><Button onClick={onClose}>Close</Button><Button className="primary" disabled={saving} onClick={() => { void save(); }}>Save</Button></>}>
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
        {tab === 'Directories' && <SettingSection title="Workspace Directory Paths">
          <Field label="Configs / Presets directory"><TextInput value={draft.directories.configsDir} onChange={e => patchDirs({ configsDir: e.target.value })} placeholder="data/user/presets"/></Field>
          <Field label="Projects directory"><TextInput value={draft.directories.projectsDir} onChange={e => patchDirs({ projectsDir: e.target.value })} placeholder="data/user/projects"/></Field>
          <Field label="Strategies directory"><TextInput value={draft.directories.strategiesDir} onChange={e => patchDirs({ strategiesDir: e.target.value })} placeholder="data/user/strategies"/></Field>
          <Field label="Custom Data directory"><TextInput value={draft.directories.customdataDir} onChange={e => patchDirs({ customdataDir: e.target.value })} placeholder="data/user/customdata"/></Field>
        </SettingSection>}
        {tab === 'Backtest Engine' && <>
          <SettingSection title="Concurrency & Resource Limits">
            <div className="settings-grid">
              <Field label="Max Worker Threads"><TextInput type="number" min="1" max="128" value={draft.backtestEngine.maxThreads} onChange={e => patchEngine({ maxThreads: Number(e.target.value) })}/></Field>
              <Field label="Memory Limit (MB)"><TextInput type="number" min="512" max="131072" value={draft.backtestEngine.memoryLimitMb} onChange={e => patchEngine({ memoryLimitMb: Number(e.target.value) })}/></Field>
            </div>
            <div className="settings-grid">
              <Field label="Benchmark Time Per Tick (ms)"><TextInput type="number" step="0.000001" min="0.000001" value={draft.backtestEngine.benchmarkTimePerTickMs} onChange={e => patchEngine({ benchmarkTimePerTickMs: Number(e.target.value) })}/></Field>
              <Field label="Simulation Precision">
                <Select value={draft.backtestEngine.precisionMode} onChange={precisionMode => patchEngine({ precisionMode: precisionMode as BacktestEngineSettings['precisionMode'] })}>
                  <option value="high">High Precision</option>
                  <option value="standard">Standard</option>
                  <option value="low">Low (Fast)</option>
                </Select>
              </Field>
            </div>
          </SettingSection>
          <SettingSection title="Engine Calculation Features">
            <Checkbox label="Enable results and data caching" checked={draft.backtestEngine.enableCaching} onChange={enableCaching => patchEngine({ enableCaching })}/>
            <Checkbox label="Don't store pending orders" checked={draft.backtestEngine.dontStorePendingOrders} onChange={dontStorePendingOrders => patchEngine({ dontStorePendingOrders })}/>
            <Checkbox label="Don't store 3D optimization charts" checked={draft.backtestEngine.dontStoreOp3dCharts} onChange={dontStoreOp3dCharts => patchEngine({ dontStoreOp3dCharts })}/>
            <Checkbox label="Compute separate long and short metrics" checked={draft.backtestEngine.computeSeparateMetrics} onChange={computeSeparateMetrics => patchEngine({ computeSeparateMetrics })}/>
            <Checkbox label="Compute percentage metrics" checked={draft.backtestEngine.computePctsMetrics} onChange={computePctsMetrics => patchEngine({ computePctsMetrics })}/>
            <Checkbox label="Compute pips metrics" checked={draft.backtestEngine.computePipsMetrics} onChange={computePipsMetrics => patchEngine({ computePipsMetrics })}/>
            <Checkbox label="Emit source code constants as parameters" checked={draft.backtestEngine.sourceCodeConstantsParams} onChange={sourceCodeConstantsParams => patchEngine({ sourceCodeConstantsParams })}/>
          </SettingSection>
        </>}
        {error && <p className="settings-error" role="alert">{error}</p>}
      </div>
      <p className="restart-note">These preferences are saved by the host. Calculation behavior awaits its backend owner.</p>
    </div>
  </Modal>;
}

function CredentialsDialog({ onClose }: { onClose: () => void }) {
  const settings = useAppStore(s => s.settings);
  const { saveSettings } = useHostConnection();
  const [draft, setDraft] = useState<ConfigurationSettings>({ ...settings.configuration });
  const [tab, setTab] = useState<(typeof credentialsTabs)[number]>('MetaTrader 5');
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    void readHostPreferences().then(snap => {
      useAppStore.getState().updateSettings({
        ...snap.preferences,
        configuration: snap.preferences.configuration,
      });
      setDraft({ ...snap.preferences.configuration });
    }).catch(() => {});
  }, []);

  useEffect(() => {
    setDraft({ ...settings.configuration });
  }, [settings.configuration]);

  const patchMt5 = (value: Partial<Mt5Settings>) => setDraft(current => ({ ...current, mt5: { ...current.mt5, ...value } }));
  const patchCtrader = (value: Partial<CtraderSettings>) => setDraft(current => ({ ...current, ctrader: { ...current.ctrader, ...value } }));
  const patchAgents = (value: Partial<AgentSettings>) => setDraft(current => ({ ...current, agents: { ...current.agents, ...value } }));
  const patchGemini = (value: Partial<GeminiAgentConfig>) => setDraft(current => ({ ...current, agents: { ...current.agents, gemini: { ...current.agents.gemini, ...value } } }));
  const patchOpenAi = (value: Partial<OpenAiAgentConfig>) => setDraft(current => ({ ...current, agents: { ...current.agents, openai: { ...current.agents.openai, ...value } } }));
  const patchOllama = (value: Partial<OllamaAgentConfig>) => setDraft(current => ({ ...current, agents: { ...current.agents, ollama: { ...current.agents.ollama, ...value } } }));

  const save = async () => {
    setSaving(true);
    const result = await saveSettings({ configuration: draft });
    setSaving(false);
    if (result.ok) onClose(); else setError(result.message);
  };

  return <Modal title="Credentials" onClose={onClose} width={820} footer={<><Button onClick={onClose}>Close</Button><Button className="primary" disabled={saving} onClick={() => { void save(); }}>Save</Button></>}>
    <div className="configuration-dialog">
      <nav role="tablist" aria-label="Credentials sections">{credentialsTabs.map(item => <button key={item} role="tab" aria-selected={tab === item} className={tab === item ? 'active' : ''} onClick={() => { setTab(item); setError(''); }}>{item}</button>)}</nav>
      <div className="configuration-page">
        {tab === 'MetaTrader 5' && <>
          <SettingSection title="Terminal Connection">
            <Checkbox label="Enable MetaTrader 5 integration" checked={draft.mt5.enabled} onChange={enabled => patchMt5({ enabled })}/>
            <Checkbox label="Portable mode" checked={draft.mt5.portable} onChange={portable => patchMt5({ portable })}/>
            <Checkbox label="Use real ticks for backtesting" checked={draft.mt5.useTicks} onChange={useTicks => patchMt5({ useTicks })}/>
            <Field label="Terminal executable path"><TextInput value={draft.mt5.terminalPath} onChange={e => patchMt5({ terminalPath: e.target.value })} placeholder="e.g. C:\Program Files\Pepperstone MetaTrader 5\terminal64.exe"/></Field>
            <Field label="Connection timeout (ms)"><TextInput type="number" min="1000" max="300000" value={draft.mt5.timeoutMs} onChange={e => patchMt5({ timeoutMs: Number(e.target.value) })}/></Field>
          </SettingSection>
          <SettingSection title="Account & Server">
            <div className="settings-grid">
              <Field label="Account ID"><TextInput value={draft.mt5.accountId} onChange={e => patchMt5({ accountId: e.target.value })} placeholder="Account login number"/></Field>
              <Field label="Password"><SecretInput value={draft.mt5.password} onChange={e => patchMt5({ password: e.target.value })} placeholder="Account password"/></Field>
            </div>
            <div className="settings-grid">
              <Field label="Broker / Server"><TextInput value={draft.mt5.server} onChange={e => patchMt5({ server: e.target.value })} placeholder="e.g. Pepperstone-Demo"/></Field>
              <Field label="Environment">
                <Select value={draft.mt5.environment} onChange={environment => patchMt5({ environment: environment as Mt5Settings['environment'] })}>
                  <option value="demo">Demo</option>
                  <option value="live">Live</option>
                  <option value="real">Real</option>
                </Select>
              </Field>
            </div>
          </SettingSection>
        </>}
        {tab === 'cTrader' && <>
          <SettingSection title="Gateway & Connection">
            <Checkbox label="Enable cTrader integration" checked={draft.ctrader.enabled} onChange={enabled => patchCtrader({ enabled })}/>
            <div className="settings-grid">
              <Field label="Gateway Host"><TextInput value={draft.ctrader.gatewayHost} onChange={e => patchCtrader({ gatewayHost: e.target.value })} placeholder="live.ctraderapi.com"/></Field>
              <Field label="Gateway Port"><TextInput type="number" min="1" max="65535" value={draft.ctrader.gatewayPort} onChange={e => patchCtrader({ gatewayPort: Number(e.target.value) })}/></Field>
            </div>
            <div className="settings-grid">
              <Field label="Account ID"><TextInput value={draft.ctrader.accountId} onChange={e => patchCtrader({ accountId: e.target.value })} placeholder="Trading Account ID"/></Field>
              <Field label="Environment">
                <Select value={draft.ctrader.environment} onChange={environment => patchCtrader({ environment: environment as CtraderSettings['environment'] })}>
                  <option value="demo">Demo</option>
                  <option value="live">Live</option>
                  <option value="real">Real</option>
                </Select>
              </Field>
            </div>
          </SettingSection>
          <SettingSection title="Open API Authentication & Secrets">
            <Field label="Client ID"><TextInput value={draft.ctrader.clientId} onChange={e => patchCtrader({ clientId: e.target.value })} placeholder="Spotware Open API Client ID"/></Field>
            <div className="settings-grid">
              <Field label="Client Secret"><SecretInput value={draft.ctrader.clientSecret} onChange={e => patchCtrader({ clientSecret: e.target.value })} placeholder="Spotware Open API Client Secret"/></Field>
              <Field label="Redirect URL"><TextInput value={draft.ctrader.redirectUrl} onChange={e => patchCtrader({ redirectUrl: e.target.value })}/></Field>
            </div>
            <div className="settings-grid">
              <Field label="Access Token"><SecretInput value={draft.ctrader.accessToken} onChange={e => patchCtrader({ accessToken: e.target.value })} placeholder="OAuth Access Token"/></Field>
              <Field label="Refresh Token"><SecretInput value={draft.ctrader.refreshToken} onChange={e => patchCtrader({ refreshToken: e.target.value })} placeholder="OAuth Refresh Token"/></Field>
            </div>
          </SettingSection>
        </>}
        {tab === 'AI Agents' && <>
          <SettingSection title="Agent Core Configuration">
            <div className="settings-grid">
              <Field label="Active AI Provider">
                <Select value={draft.agents.activeProvider} onChange={activeProvider => patchAgents({ activeProvider: activeProvider as AgentSettings['activeProvider'] })}>
                  <option value="gemini">Google Gemini</option>
                  <option value="openai">OpenAI Compatible</option>
                  <option value="ollama">Local Ollama</option>
                </Select>
              </Field>
              <Field label="System Prompt Preset">
                <Select value={draft.agents.systemPromptPreset} onChange={systemPromptPreset => patchAgents({ systemPromptPreset })}>
                  <option value="quant_researcher">Quantitative Researcher</option>
                  <option value="code_reviewer">Code Reviewer</option>
                  <option value="risk_manager">Risk Manager</option>
                  <option value="strategy_designer">Strategy Designer</option>
                </Select>
              </Field>
            </div>
            <Field label="Agent Timeout (seconds)"><TextInput type="number" min="10" max="600" value={draft.agents.agentTimeoutSeconds} onChange={e => patchAgents({ agentTimeoutSeconds: Number(e.target.value) })}/></Field>
          </SettingSection>
          {draft.agents.activeProvider === 'gemini' && <SettingSection title="Google Gemini Settings">
            <Field label="API Key"><SecretInput placeholder="Gemini API Key" value={draft.agents.gemini.apiKey} onChange={e => patchGemini({ apiKey: e.target.value })}/></Field>
            <div className="settings-grid">
              <Field label="Primary Model"><TextInput value={draft.agents.gemini.model} onChange={e => patchGemini({ model: e.target.value })} placeholder="gemini-3.6-flash"/></Field>
              <Field label="Fast Model"><TextInput value={draft.agents.gemini.fastModel} onChange={e => patchGemini({ fastModel: e.target.value })} placeholder="gemini-3.6-flash"/></Field>
            </div>
            <div className="settings-grid">
              <Field label="Premium Model"><TextInput value={draft.agents.gemini.premiumModel} onChange={e => patchGemini({ premiumModel: e.target.value })} placeholder="gemini-3.6-pro"/></Field>
              <Field label="Fallback Model"><TextInput value={draft.agents.gemini.fallbackModel} onChange={e => patchGemini({ fallbackModel: e.target.value })} placeholder="gemini-3.6-flash"/></Field>
            </div>
            <div className="settings-grid">
              <Field label="Temperature (0.0 - 2.0)"><TextInput type="number" step="0.1" min="0" max="2" value={draft.agents.gemini.temperature} onChange={e => patchGemini({ temperature: Number(e.target.value) })}/></Field>
              <Field label="Max Tokens"><TextInput type="number" min="128" max="65536" value={draft.agents.gemini.maxTokens} onChange={e => patchGemini({ maxTokens: Number(e.target.value) })}/></Field>
            </div>
            <Checkbox label="Use Vertex AI endpoint" checked={draft.agents.gemini.useVertexAi} onChange={useVertexAi => patchGemini({ useVertexAi })}/>
          </SettingSection>}
          {draft.agents.activeProvider === 'openai' && <SettingSection title="OpenAI Settings">
            <Field label="API Key"><SecretInput placeholder="OpenAI API Key" value={draft.agents.openai.apiKey} onChange={e => patchOpenAi({ apiKey: e.target.value })}/></Field>
            <Field label="API Base URL"><TextInput value={draft.agents.openai.baseUrl} onChange={e => patchOpenAi({ baseUrl: e.target.value })} placeholder="https://api.openai.com/v1"/></Field>
            <div className="settings-grid">
              <Field label="Model"><TextInput value={draft.agents.openai.model} onChange={e => patchOpenAi({ model: e.target.value })} placeholder="gpt-5.4-mini"/></Field>
              <Field label="Temperature (0.0 - 2.0)"><TextInput type="number" step="0.1" min="0" max="2" value={draft.agents.openai.temperature} onChange={e => patchOpenAi({ temperature: Number(e.target.value) })}/></Field>
            </div>
            <Field label="Max Tokens"><TextInput type="number" min="128" max="65536" value={draft.agents.openai.maxTokens} onChange={e => patchOpenAi({ maxTokens: Number(e.target.value) })}/></Field>
          </SettingSection>}
          {draft.agents.activeProvider === 'ollama' && <SettingSection title="Ollama Settings">
            <Field label="Ollama Server URL"><TextInput value={draft.agents.ollama.baseUrl} onChange={e => patchOllama({ baseUrl: e.target.value })} placeholder="http://127.0.0.1:11434"/></Field>
            <div className="settings-grid">
              <Field label="Model"><TextInput value={draft.agents.ollama.model} onChange={e => patchOllama({ model: e.target.value })} placeholder="llama3.1:8b"/></Field>
              <Field label="Temperature (0.0 - 2.0)"><TextInput type="number" step="0.1" min="0" max="2" value={draft.agents.ollama.temperature} onChange={e => patchOllama({ temperature: Number(e.target.value) })}/></Field>
            </div>
            <Field label="Timeout (seconds)"><TextInput type="number" min="10" max="600" value={draft.agents.ollama.timeoutSeconds} onChange={e => patchOllama({ timeoutSeconds: Number(e.target.value) })}/></Field>
          </SettingSection>}
        </>}
        {error && <p className="settings-error" role="alert">{error}</p>}
      </div>
      <p className="restart-note">Credentials are securely stored in the local host database.</p>
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

  useEffect(() => {
    void readHostPreferences().then(snap => {
      useAppStore.getState().updateSettings({
        ...snap.preferences,
        remoteAccess: snap.preferences.remoteAccess,
      });
      setDraft({ ...snap.preferences.remoteAccess, password: '' });
    }).catch(() => {});
  }, []);

  useEffect(() => {
    setDraft({ ...value, password: '' });
  }, [value]);
  const save = async () => { const result = await saveSettings({ remoteAccess: safeRemoteSettings(draft) }); if (result.ok) onClose(); else setError(result.message); };
  return <Modal title="Remote access" onClose={onClose} width={590} footer={<><Button onClick={onClose}>Close</Button><Button className="primary" onClick={() => { void save(); }}>Save</Button></>}><SettingSection title="Remote browser access"><Checkbox label="Allow remote access to this application" checked={draft.allow} onChange={allow => setDraft({ ...draft, allow })}/>{draft.allow && <><Field label="Address"><TextInput readOnly value={`${location.origin}/remote`}/></Field><Checkbox label="Require a password" checked={draft.requirePassword} onChange={requirePassword => setDraft({ ...draft, requirePassword })}/>{draft.requirePassword && <Field label="Password"><TextInput type="password" autoComplete="new-password" value={draft.password} onChange={e => setDraft({ ...draft, password: e.target.value })}/></Field>}</>}</SettingSection><p className="dialog-note">Preferences are saved, but no remote server is opened. The password is not saved; password-protected access is unavailable.</p>{error && <p role="alert" className="settings-error">{error}</p>}</Modal>;
}

function McpDialog({ onClose }: { onClose: () => void }) {
  const mcp = useAppStore(s => s.settings.mcp);
  const { saveSettings } = useHostConnection();
  const [draft, setDraft] = useState<McpSettings & { authToken: string }>({ ...mcp, authToken: '' });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    void readHostPreferences().then(snap => {
      useAppStore.getState().updateSettings({
        ...snap.preferences,
        mcp: snap.preferences.mcp,
      });
      setDraft({ ...snap.preferences.mcp, authToken: '' });
    }).catch(() => {});
  }, []);

  useEffect(() => {
    setDraft({ ...mcp, authToken: '' });
  }, [mcp]);

  const endpoint = `http://${draft.host || '127.0.0.1'}:${draft.port || 5055}/mcp`;
  const config = JSON.stringify({ mcpServers: { haruquantai: { url: endpoint } } }, null, 2);

  const save = async () => {
    setSaving(true);
    const result = await saveSettings({ mcp: safeMcpSettings(draft) });
    setSaving(false);
    if (result.ok) {
      onClose();
    } else {
      setError(result.message);
    }
  };

  return (
    <Modal
      title="MCP Server"
      onClose={onClose}
      width={680}
      footer={
        <>
          <Button onClick={onClose}>Close</Button>
          <Button className="primary" disabled={saving} onClick={() => { void save(); }}>Save</Button>
        </>
      }
    >
      <div className="stacked-settings">
        <SettingSection title="Model Context Protocol Server">
          <Checkbox label="Enable MCP server endpoint" checked={draft.enabled} onChange={enabled => setDraft(d => ({ ...d, enabled }))}/>
          <div className="settings-grid">
            <Field label="Host / Bind Address"><TextInput value={draft.host} onChange={e => setDraft(d => ({ ...d, host: e.target.value }))} placeholder="127.0.0.1"/></Field>
            <Field label="Port"><TextInput type="number" min="1024" max="65535" value={draft.port} onChange={e => setDraft(d => ({ ...d, port: Number(e.target.value) }))}/></Field>
          </div>
          <div className="settings-grid">
            <Field label="Transport">
              <Select value={draft.transport} onChange={transport => setDraft(d => ({ ...d, transport: transport as McpSettings['transport'] }))}>
                <option value="sse">Server-Sent Events (SSE)</option>
                <option value="stdio">Standard I/O (stdio)</option>
                <option value="websocket">WebSocket</option>
                <option value="http">HTTP POST</option>
              </Select>
            </Field>
            <Field label="Max Context Items"><TextInput type="number" min="1" max="500" value={draft.maxContextItems} onChange={e => setDraft(d => ({ ...d, maxContextItems: Number(e.target.value) }))}/></Field>
          </div>
          <Field label="Allowed Tools (comma-separated)">
            <TextInput
              value={draft.allowedTools.join(', ')}
              onChange={e => setDraft(d => ({
                ...d,
                allowedTools: e.target.value.split(',').map(s => s.trim()).filter(Boolean),
              }))}
              placeholder="strategies, projects, databanks, backtest, optimizer"
            />
          </Field>
          <Field label="Authentication Token (optional)">
            <SecretInput placeholder="Leave empty to keep unchanged" value={draft.authToken} onChange={e => setDraft(d => ({ ...d, authToken: e.target.value }))}/>
          </Field>
        </SettingSection>
        <SettingSection title="Client Connection">
          <Field label="MCP Endpoint URL"><TextInput readOnly value={endpoint}/></Field>
          <Field label="CLI Command"><TextInput readOnly value={`mcp connect haruquantai ${endpoint}`}/></Field>
          <Field label="Client Configuration (JSON)"><textarea className="text-area settings-code" readOnly value={config}/></Field>
        </SettingSection>
        {error && <p role="alert" className="settings-error">{error}</p>}
      </div>
    </Modal>
  );
}

function NotificationsDialog({ onClose }: { onClose: () => void }) {
  const settings = useAppStore(s => s.settings);
  const { saveSettings } = useHostConnection();
  const [tab, setTab] = useState<'Email' | 'Telegram' | 'Desktop'>('Email');
  const [emailDraft, setEmailDraft] = useState<SmtpSettings & { password: string }>({ ...settings.smtp, password: '' });
  const [telegramDraft, setTelegramDraft] = useState<TelegramSettings & { botToken: string }>({ ...settings.telegram, botToken: '' });
  const [desktopDraft, setDesktopDraft] = useState<DesktopNotificationSettings>({ ...settings.desktopNotification });
  const [recipient, setRecipient] = useState('');
  const [testing, setTesting] = useState(false);
  const [message, setMessage] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    void readHostPreferences().then(snap => {
      useAppStore.getState().updateSettings({
        ...snap.preferences,
        smtp: snap.preferences.smtp,
        telegram: snap.preferences.telegram,
        desktopNotification: snap.preferences.desktopNotification,
      });
      setEmailDraft({ ...snap.preferences.smtp, password: '' });
      setTelegramDraft({ ...snap.preferences.telegram, botToken: '' });
      setDesktopDraft({ ...snap.preferences.desktopNotification });
    }).catch(() => {});
  }, []);

  useEffect(() => {
    setEmailDraft({ ...settings.smtp, password: '' });
    setTelegramDraft({ ...settings.telegram, botToken: '' });
    setDesktopDraft({ ...settings.desktopNotification });
  }, [settings.smtp, settings.telegram, settings.desktopNotification]);

  const save = async () => {
    if (emailDraft.emailFrom && !isEmail(emailDraft.emailFrom)) {
      setMessage('Enter a valid sender email address.');
      return;
    }
    setSaving(true);
    const result = await saveSettings({
      smtp: safeSmtpSettings(emailDraft),
      telegram: safeTelegramSettings(telegramDraft),
      desktopNotification: desktopDraft,
    });
    setSaving(false);
    if (result.ok) {
      onClose();
    } else {
      setMessage(result.message);
    }
  };

  const testEmail = () => {
    if (!testing) {
      setTesting(true);
      setMessage('');
      return;
    }
    if (!isEmail(recipient)) {
      setMessage('Enter a valid test recipient email address.');
      return;
    }
    setMessage(`Test message simulated for ${recipient.trim()}.`);
  };

  const testTelegram = () => {
    if (!telegramDraft.chatId.trim()) {
      setMessage('Enter a chat ID to test Telegram delivery.');
      return;
    }
    setMessage(`Test message simulated for Telegram chat ${telegramDraft.chatId.trim()}.`);
  };

  const testDesktop = () => {
    setMessage(`Test desktop notification simulated with ${desktopDraft.minPriority} priority.`);
  };

  return (
    <Modal
      title="Notifications"
      onClose={onClose}
      width={720}
      footer={
        <>
          <Button onClick={onClose}>Close</Button>
          {tab === 'Email' && <Button onClick={testEmail}>Send test email</Button>}
          {tab === 'Telegram' && <Button onClick={testTelegram}>Send test message</Button>}
          {tab === 'Desktop' && <Button onClick={testDesktop}>Test notification</Button>}
          <Button className="primary" disabled={saving} onClick={() => { void save(); }}>Save</Button>
        </>
      }
    >
      <div className="configuration-dialog">
        <nav role="tablist" aria-label="Notification channels">
          {(['Email', 'Telegram', 'Desktop'] as const).map(item => (
            <button
              key={item}
              role="tab"
              aria-selected={tab === item}
              className={tab === item ? 'active' : ''}
              onClick={() => { setTab(item); setMessage(''); }}
            >
              {item}
            </button>
          ))}
        </nav>
        <div className="configuration-page">
          {tab === 'Email' && (
            <div className="stacked-settings">
              <Checkbox label="Enable email notifications" checked={emailDraft.enabled} onChange={enabled => setEmailDraft(d => ({ ...d, enabled }))}/>
              <div className="settings-grid">
                <Field label="SMTP server"><TextInput value={emailDraft.server} onChange={e => setEmailDraft(d => ({ ...d, server: e.target.value }))}/></Field>
                <Field label="Port"><TextInput value={emailDraft.port} onChange={e => setEmailDraft(d => ({ ...d, port: e.target.value }))}/></Field>
              </div>
              <Checkbox label="Use SSL/TLS" checked={emailDraft.ssl} onChange={ssl => setEmailDraft(d => ({ ...d, ssl }))}/>
              <div className="settings-grid">
                <Field label="Username"><TextInput autoComplete="username" value={emailDraft.username} onChange={e => setEmailDraft(d => ({ ...d, username: e.target.value }))}/></Field>
                <Field label="Password"><SecretInput autoComplete="new-password" placeholder="Leave empty to keep unchanged" value={emailDraft.password} onChange={e => setEmailDraft(d => ({ ...d, password: e.target.value }))}/></Field>
              </div>
              <Field label="Sender email"><TextInput value={emailDraft.emailFrom} onChange={e => setEmailDraft(d => ({ ...d, emailFrom: e.target.value }))}/></Field>
              {testing && <Field label="Test recipient"><TextInput value={recipient} onChange={e => setRecipient(e.target.value)}/></Field>}
            </div>
          )}
          {tab === 'Telegram' && (
            <div className="stacked-settings">
              <Checkbox label="Enable Telegram notifications" checked={telegramDraft.enabled} onChange={enabled => setTelegramDraft(d => ({ ...d, enabled }))}/>
              <Field label="Bot token"><SecretInput placeholder="Bot token from @BotFather (leave empty to keep unchanged)" value={telegramDraft.botToken} onChange={e => setTelegramDraft(d => ({ ...d, botToken: e.target.value }))}/></Field>
              <div className="settings-grid">
                <Field label="Chat ID"><TextInput value={telegramDraft.chatId} onChange={e => setTelegramDraft(d => ({ ...d, chatId: e.target.value }))} placeholder="e.g. 123456789 or @channelname"/></Field>
                <Field label="Parse Mode">
                  <Select value={telegramDraft.parseMode} onChange={parseMode => setTelegramDraft(d => ({ ...d, parseMode: parseMode as TelegramSettings['parseMode'] }))}>
                    <option value="HTML">HTML</option>
                    <option value="Markdown">Markdown</option>
                    <option value="MarkdownV2">MarkdownV2</option>
                  </Select>
                </Field>
              </div>
              <Checkbox label="Silent messages (disable audible push notification)" checked={telegramDraft.disableNotification} onChange={disableNotification => setTelegramDraft(d => ({ ...d, disableNotification }))}/>
            </div>
          )}
          {tab === 'Desktop' && (
            <div className="stacked-settings">
              <Checkbox label="Enable desktop notifications" checked={desktopDraft.enabled} onChange={enabled => setDesktopDraft(d => ({ ...d, enabled }))}/>
              <Checkbox label="Play audio notification sound" checked={desktopDraft.soundEnabled} onChange={soundEnabled => setDesktopDraft(d => ({ ...d, soundEnabled }))}/>
              <div className="settings-grid">
                <Field label="Display duration (seconds)"><TextInput type="number" min="1" max="60" value={desktopDraft.durationSeconds} onChange={e => setDesktopDraft(d => ({ ...d, durationSeconds: Number(e.target.value) }))}/></Field>
                <Field label="Minimum Event Priority">
                  <Select value={desktopDraft.minPriority} onChange={minPriority => setDesktopDraft(d => ({ ...d, minPriority: minPriority as DesktopNotificationSettings['minPriority'] }))}>
                    <option value="low">Low (all notifications)</option>
                    <option value="normal">Normal (standard updates)</option>
                    <option value="high">High (warnings & errors)</option>
                    <option value="critical">Critical (fatal errors only)</option>
                  </Select>
                </Field>
              </div>
            </div>
          )}
          {message && <p role="status" className="dialog-note">{message}</p>}
        </div>
        <p className="restart-note">Non-secret notification preferences are saved in the host database.</p>
      </div>
    </Modal>
  );
}

function ExitDialog({ onClose }: { onClose: () => void }) { const notify = useAppStore(s => s.notify); return <Modal title="Exit HaruQuantAI" onClose={onClose} width={470} footer={<><Button onClick={onClose}>Cancel</Button><Button className="danger" onClick={() => { notify('Exit is unavailable in the browser application'); onClose(); }}>Exit</Button></>}><p>Do you really want to exit the application?</p><p className="dialog-note">The browser-hosted frontend cannot close the desktop process.</p></Modal>; }

export function GlobalSettingsMenu() {
  const settings = useAppStore(s => s.settings);
  const { saveSettings } = useHostConnection();
  const [open, setOpen] = useState(false); const [submenu, setSubmenu] = useState<'skin' | null>(null); const [dialog, setDialog] = useState<DialogName>(null);
  const root = useRef<HTMLDivElement>(null); const trigger = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    if (!open) return;
    void readHostPreferences().then(snap => {
      useAppStore.getState().updateSettings({
        ...snap.preferences,
        configuration: snap.preferences.configuration,
        memoryGb: snap.preferences.configuration.memoryGb,
        workers: snap.preferences.configuration.coreUsage === 'custom' ? snap.preferences.configuration.customCores :
          snap.preferences.configuration.coreUsage === 'single' ? 1 :
          Math.max(1, snap.preferences.configuration.totalCores - (snap.preferences.configuration.coreUsage === 'reserve-one' ? 1 : 0)),
      });
    }).catch(() => {});
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
  const fullscreen = async () => { try { if (document.fullscreenElement) await document.exitFullscreen(); else await document.documentElement.requestFullscreen(); } catch { useAppStore.getState().notify('Fullscreen is unavailable in this browser'); } };
  const item = (label: string, icon: ReactNode, action: () => void, suffix?: ReactNode) => <button role="menuitem" onClick={action}>{icon}<span>{label}</span>{suffix}</button>;
  return <div className="global-settings" ref={root}>
    <button ref={trigger} className="top-action" title="Settings" aria-label="Settings" aria-haspopup="menu" aria-expanded={open} onClick={() => { setOpen(value => !value); setSubmenu(null); }}><Settings/></button>
    {open && <div className="global-settings-menu" role="menu" aria-label="Application settings" onKeyDown={onMenuKeyDown}>
      <div className="settings-menu-group">{item('Configuration...', <Settings/>, () => launch('configuration'))}{item('Credentials...', <KeyRound/>, () => launch('credentials'))}{item('Benchmark...', <Gauge/>, () => launch('benchmark'))}{item('Remote access...', <Cloud/>, () => launch('remote'))}{item('MCP Server...', <Server/>, () => launch('mcp'))}{item('Notifications...', <Bell/>, () => launch('notifications'))}</div>
      <div className="settings-menu-group submenu-host">{item('Skin', <Palette/>, () => setSubmenu(submenu === 'skin' ? null : 'skin'), <ChevronRight/>)}{submenu === 'skin' && <div className="settings-submenu skin-submenu" role="menu" aria-label="Skin">{applicationSkins.map(skin => <button role="menuitem" key={skin} onClick={() => { void saveSettings({ theme: skin === 'Dark skin' ? 'dark' : 'light' }); setOpen(false); setSubmenu(null); }}>{settings.theme === (skin === 'Dark skin' ? 'dark' : 'light') ? <Check/> : <span/>}<span>{skin}</span></button>)}</div>}</div>
      <div className="settings-menu-group zoom-menu-row"><span><MonitorCog/>Zoom</span><button aria-label="Zoom out" onClick={() => { void saveSettings({ zoom: clampZoom(settings.zoom - .1) }); }}><Minus/></button><output>{Math.round(settings.zoom * 100)}%</output><button aria-label="Zoom in" onClick={() => { void saveSettings({ zoom: clampZoom(settings.zoom + .1) }); }}><Plus/></button><button aria-label="Toggle fullscreen" onClick={fullscreen}><Expand/></button></div>
      <div className="settings-menu-group">{item('Reload UI', <RefreshCw/>, () => window.location.reload())}{item('Exit', <LogOut/>, () => launch('exit'))}</div>
    </div>}
    {dialog === 'configuration' && <ConfigurationDialog onClose={() => setDialog(null)}/>} {dialog === 'credentials' && <CredentialsDialog onClose={() => setDialog(null)}/>} {dialog === 'benchmark' && <BenchmarkDialog onClose={() => setDialog(null)}/>} {dialog === 'remote' && <RemoteDialog onClose={() => setDialog(null)}/>} {dialog === 'mcp' && <McpDialog onClose={() => setDialog(null)}/>} {dialog === 'notifications' && <NotificationsDialog onClose={() => setDialog(null)}/>} {dialog === 'exit' && <ExitDialog onClose={() => setDialog(null)}/>}
  </div>;
}
