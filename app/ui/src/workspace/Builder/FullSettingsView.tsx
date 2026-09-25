import { useEffect, useState } from 'react';
import type { ReactNode } from 'react';
import type { EngineRunStatus } from './fixtures';
import { nextTabLabel, prevTabLabel, settingsTabs } from './settings/settingsFixtures';
import { WhatToBuildTab } from './settings/WhatToBuildTab';
import { PartsToImproveTab } from './settings/PartsToImproveTab';
import { GeneticOptionsTab } from './settings/GeneticOptionsTab';
import { DataTab } from './settings/DataTab';
import { TradingOptionsTab } from './settings/TradingOptionsTab';
import { BuildingBlocksTab } from './settings/BuildingBlocksTab';
import { AtmTab } from './settings/AtmTab';
import { MoneyManagementTab } from './settings/MoneyManagementTab';
import { CustomAnalysisTab } from './settings/CustomAnalysisTab';
import { CrossChecksTab } from './settings/CrossChecksTab';
import { RankingTab } from './settings/RankingTab';
import { NotesTab } from './settings/NotesTab';

/**
 * SQX-parity Full settings panel (donor evidence SQX144-EV-000038): the
 * "Advanced settings" window with the 12-tab Build strip, per-tab
 * description header with Help, lock overlay while the project runs, and
 * the prev/Close/next navigation. Close returns to the Progress panel.
 */

const TAB_CONTENT: Record<string, ReactNode> = {
  'what-to-build': <WhatToBuildTab />,
  'parts-to-improve': <PartsToImproveTab />,
  'genetic-options': <GeneticOptionsTab />,
  data: <DataTab />,
  'trading-options': <TradingOptionsTab />,
  'building-blocks': <BuildingBlocksTab />,
  atm: <AtmTab />,
  'money-management': <MoneyManagementTab />,
  'custom-analysis': <CustomAnalysisTab />,
  'cross-checks': <CrossChecksTab />,
  ranking: <RankingTab />,
  notes: <NotesTab />,
};

export function FullSettingsView({
  runStatus,
  onClose,
}: {
  runStatus: EngineRunStatus;
  onClose: () => void;
}) {
  const [activeId, setActiveId] = useState(settingsTabs[0].id);
  const index = settingsTabs.findIndex(tab => tab.id === activeId);
  const active = settingsTabs[index];

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      // Let an open dialog consume Escape first (donor: topmost modal closes).
      if (e.key === 'Escape' && !document.querySelector('.sqd-modal')) onClose();
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [onClose]);

  const locked = runStatus === 'running' || runStatus === 'paused';

  return (
    <div className="sqd-fullsettings">
      <div className="sqd-advanced-title">Advanced settings</div>
      <div className="sqd-settings-tabs">
        <div className="sqd-stabs-header" role="tablist" aria-label="Settings tabs">
          {settingsTabs.map(tab => (
            <div
              key={tab.id}
              role="tab"
              aria-selected={tab.id === activeId}
              className={tab.id === activeId ? 'active' : ''}
              onClick={() => setActiveId(tab.id)}
            >
              {tab.title}
            </div>
          ))}
        </div>
        <div className="sqd-stabs-body">
          <div className={`sqd-stab-panel ${active?.id === 'building-blocks' ? 'building-blocks' : ''}`}>
            <div className="sqd-settings-body-header">
              <div
                className="sqd-settings-tab-desc"
                title={active?.help.replace(/<br\s*\/?>/gm, '\r\n') ?? ''}
                dangerouslySetInnerHTML={{ __html: active?.help ?? '' }}
              />
              <button
                type="button"
                className="sqd-btn sqd-btn-help"
                onClick={() => active && window.open(active.helpUrl, '_blank', 'noopener')}
              >
                Help
              </button>
            </div>
            <div className={`sqd-settings-body-inner${locked ? ' disabled-panel' : ''}`}>
              <div className="sqd-disabled-placeholder" aria-hidden={!locked}>
                <svg width="14" height="14" viewBox="0 0 16 16" aria-hidden="true">
                  <path fill="currentColor" d="M8 1a3 3 0 0 0-3 3v2H4a1 1 0 0 0-1 1v7a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1V7a1 1 0 0 0-1-1h-1V4a3 3 0 0 0-3-3zm-1 3a1 1 0 0 1 2 0v2H7V4z" />
                </svg>
                <span>Setting changes locked, they will be applied next time you start the project.</span>
              </div>
              {TAB_CONTENT[activeId]}
            </div>
            <div className="sqd-settings-nextbtns">
              {prevTabLabel(index) !== null && (
                <button type="button" className="sqd-btn sqd-btn-primary sqd-prevtab" onClick={() => setActiveId(settingsTabs[index - 1].id)}>
                  {prevTabLabel(index)}
                </button>
              )}
              <button type="button" className="sqd-btn sqd-closetab" onClick={onClose}>Close</button>
              {nextTabLabel(index) !== null && (
                <button type="button" className="sqd-btn sqd-btn-primary sqd-nexttab" onClick={() => setActiveId(settingsTabs[index + 1].id)}>
                  {nextTabLabel(index)}
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
