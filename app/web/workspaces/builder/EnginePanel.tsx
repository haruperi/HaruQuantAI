import { useEffect, useRef, useState } from 'react';
import type { ReactNode } from 'react';
import { CirclePause, CirclePlay, CircleStop, Cog, FolderOpen, LineChart, Save } from 'lucide-react';
import { EngineCharts } from './EngineCharts';
import { FitnessEvolutionModal, SqdModal } from './FitnessEvolutionModal';
import type { EngineRunStatus, ProgressStats } from './fixtures';

/**
 * SQX-style engine column of the Builder Progress tab (donor evidence
 * retained target UI; current donor equivalence unverified). Stop/Pause/Start flow on the left of the control
 * card while the config dropdowns and the fitness-evolution launcher float
 * right; below are the infinite progress bar, the Task line, the engine log
 * with its three log actions, the Build stats table with Detailed popups,
 * and the two engine chart cards. All data is demo fixture truth.
 */

function Dropdown({
  buttonLabel,
  title,
  disabled,
  children,
}: {
  buttonLabel: ReactNode;
  title: string;
  disabled?: boolean;
  children: ReactNode;
}) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!open) return;
    const onDocClick = (e: MouseEvent) => {
      if (rootRef.current && !rootRef.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('click', onDocClick);
    return () => document.removeEventListener('click', onDocClick);
  }, [open]);

  return (
    <div className="sqd-dropdown" ref={rootRef}>
      <button
        type="button"
        className="sqd-btn sqd-icon-btn"
        title={title}
        aria-label={title}
        aria-haspopup="menu"
        aria-expanded={open}
        disabled={disabled}
        onClick={() => setOpen(!open)}
      >
        {buttonLabel}
      </button>
      {open && (
        <div className="sqx-menu sqd-menu" role="menu">
          {children}
        </div>
      )}
    </div>
  );
}

const SAVE_MENU = [
  { label: 'Save', icon: <Save size={13} /> },
  { label: 'Save as...', icon: <Save size={13} /> },
];

const LOAD_MENU = [
  { label: 'Load from file...', icon: <FolderOpen size={13} /> },
  { label: 'Load Saved config', icon: null, submenu: true },
  { label: 'Reset to default (forex)', icon: <Cog size={13} /> },
  { label: 'Reset to default (futures)', icon: <Cog size={13} /> },
  { label: 'Reset to default (stockpicker)', icon: <Cog size={13} /> },
];

function menuButton(label: string, onDeferred: (label: string) => void) {
  return (
    <button
      key={label}
      type="button"
      role="menuitem"
      onClick={() => onDeferred(label)}
    >
      <span>{label}</span>
    </button>
  );
}

type StatsModalKind = 'dismissal' | 'accepted' | 'duration' | null;

const STATS_MODALS: Record<Exclude<StatsModalKind, null>, { title: string; columns: string[] }> = {
  dismissal: {
    title: 'Strategy dismissal stats',
    columns: ['Reason to dismiss', 'Count', '% of all'],
  },
  accepted: {
    title: 'Strategy accepted stats',
    columns: ['Reason to accept', 'Count', '% of all'],
  },
  duration: {
    title: 'Total test times per elements',
    columns: ['Name', 'Count', 'Avg. time', 'Total time', '% of all'],
  },
};

export function EnginePanel({
  runStatus,
  stats,
  lastEvent,
  log,
  clearOnStart,
  onStart,
  onPause,
  onStop,
  onClearLog,
  onToggleClearOnStart,
  onNotify,
}: {
  runStatus: EngineRunStatus;
  stats: ProgressStats;
  lastEvent: string;
  log: string[];
  clearOnStart: boolean;
  onStart: () => void;
  onPause: () => void;
  onStop: () => void;
  onClearLog: () => void;
  onToggleClearOnStart: (value: boolean) => void;
  onNotify: (message: string) => void;
}) {
  const [fitnessOpen, setFitnessOpen] = useState(false);
  const [statsModal, setStatsModal] = useState<StatsModalKind>(null);

  const running = runStatus === 'running';
  const controlsLocked = running;
  const deferred = (label: string) => onNotify(`"${label}" is deferred — UI prototype`);

  const detailedLink = (kind: Exclude<StatsModalKind, null>) => (
    <em>
      {' [ '}
      <a
        href=""
        onClick={e => {
          e.preventDefault();
          setStatsModal(kind);
        }}
      >
        Detailed
      </a>
      {' ]'}
    </em>
  );

  return (
    <div className="sqd-engine">
      <div className="sqd-card sqd-control-card">
        <div className="sqd-control-buttons">
          <button type="button" className="sqd-btn" onClick={onStop} disabled={runStatus === 'idle'} title="Stop">
            <CircleStop size={15} className="sqd-ico-stop" />
            Stop
          </button>
          <button type="button" className="sqd-btn" onClick={onPause} disabled={runStatus !== 'running'} title="Pause">
            <CirclePause size={15} className="sqd-ico-pause" />
            Pause
          </button>
          <button type="button" className="sqd-btn sqd-btn-start" onClick={onStart} disabled={controlsLocked} title="Start">
            <CirclePlay size={15} />
            Start
          </button>
        </div>
        <div className="sqd-control-icons">
          <Dropdown buttonLabel={<Save size={14} />} title="Save config" disabled={controlsLocked}>
            {SAVE_MENU.map(item => menuButton(item.label, deferred))}
          </Dropdown>
          <Dropdown buttonLabel={<FolderOpen size={14} />} title="Load config" disabled={controlsLocked}>
            {LOAD_MENU.filter(item => !item.submenu).map(item => menuButton(item.label, deferred))}
            <div className="sqd-menu-sep" />
            <div className="sqx-menu-group">
              <button type="button" role="menuitem" onClick={() => deferred('Load Saved config')}>
                <span>Load Saved config</span>
                <span className="sqx-caret right" />
              </button>
              <div className="sqx-submenu">
                <label className="sqd-menu-no-items">No config files found</label>
                <div className="sqd-menu-sep" />
                <button type="button" onClick={() => deferred('How to add config here')}>
                  <span>How to add config here</span>
                </button>
              </div>
            </div>
          </Dropdown>
          <button
            type="button"
            className="sqd-btn sqd-icon-btn"
            title="Fitness evolution"
            onClick={() => setFitnessOpen(true)}
          >
            <LineChart size={14} />
          </button>
        </div>
      </div>

      <div className="sqd-progress" role="progressbar" aria-label="Build progress">
        <div className={`sqd-progress-bar${running ? ' sqd-infinite' : ''}`} />
      </div>
      <div className="sqd-task-desc" title={lastEvent}>
        Task: {lastEvent}
      </div>

      <div className="sqd-log-card">
        <div className="sqd-log-scroll">
          {log.map((line, i) => (
            <div key={i}>{line}</div>
          ))}
        </div>
        <div className="sqd-log-buttons">
          <a
            href=""
            className="sqd-log-clear"
            onClick={e => {
              e.preventDefault();
              onClearLog();
            }}
          >
            Clear log
          </a>
          <label className="sqd-clear-on-start" title="Delete log on start">
            Clear log on start
            <span className={`sqd-switch${clearOnStart ? ' on' : ''}`}>
              <input
                type="checkbox"
                checked={clearOnStart}
                onChange={e => onToggleClearOnStart(e.target.checked)}
              />
              <i />
            </span>
          </label>
          <a
            href=""
            className="sqd-memory-cleanup"
            onClick={e => {
              e.preventDefault();
              onNotify('Memory cleanup requested — deferred (UI prototype)');
            }}
          >
            Memory cleanup
          </a>
        </div>
      </div>

      <div className="sqd-card sqd-stats-card">
        <table className="sqd-stats-table">
          <tbody>
            <tr>
              <td>
                Strategies generated: <span>{stats.strategiesGenerated}</span>
              </td>
              <td>
                <a
                  href=""
                  className="sqd-troubleshooting"
                  onClick={e => {
                    e.preventDefault();
                    onNotify('Help "No strategies generated?" — deferred (UI prototype)');
                  }}
                >
                  <Cog size={14} className="sqd-troubleshooting-ico" />
                  No strategies generated?
                </a>
              </td>
            </tr>
            <tr>
              <td>
                Time per strategy {detailedLink('duration')}: <span>{stats.timePerStrategy}</span>
              </td>
              <td>
                Time per accepted strategy: <span>{stats.timePerAcceptedStrategy}</span>
              </td>
            </tr>
            <tr>
              <td>
                Rejected {detailedLink('dismissal')}: <span>{stats.rejected}</span>
              </td>
              <td>
                Accepted {detailedLink('accepted')}: <span>{stats.accepted}</span>
              </td>
            </tr>
            <tr>
              <td>
                Strategies per hour: <span>{stats.strategiesPerHour}</span>
              </td>
              <td>
                Accepted strategies per hour: <span>{stats.acceptedPerHour}</span>
              </td>
            </tr>
            <tr>
              <td>
                Running time so far: <span>{stats.runningTime}</span>
              </td>
              <td>
                In databank: <span>{stats.inDatabank}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <EngineCharts />

      {fitnessOpen && <FitnessEvolutionModal onClose={() => setFitnessOpen(false)} />}
      {statsModal && (
        <SqdModal
          title={STATS_MODALS[statsModal].title}
          onClose={() => setStatsModal(null)}
          width={statsModal === 'duration' ? 640 : 480}
        >
          <div className="sqd-stats-grid" role="table" aria-label={STATS_MODALS[statsModal].title}>
            <div className="sqd-stats-grid-head" role="row">
              {STATS_MODALS[statsModal].columns.map(column => (
                <span key={column} role="columnheader">{column}</span>
              ))}
            </div>
            <div className="sqd-stats-grid-empty" role="row">N/A</div>
          </div>
        </SqdModal>
      )}
    </div>
  );
}
