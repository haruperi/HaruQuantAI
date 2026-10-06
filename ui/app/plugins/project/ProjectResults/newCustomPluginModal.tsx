import { useState } from 'react';
import { SqdModal } from '../ProjectWorkbench/ProjectModal';

export function NewAnalysisModal({ existingNames, onClose, onCreate, }: {
    existingNames: string[];
    onClose: () => void;
    onCreate: (name: string) => void;
}) {
    const [name, setName] = useState('');
    const trimmed = name.trim();
    const taken = existingNames.some(n => n.toLowerCase() === trimmed.toLowerCase());
    return (<SqdModal title="Create new Result analysis plugin" onClose={onClose} width={640}>
      <div className="sqr-newanalysis-body">
        <p>
          Adds a new custom plugin analytics tab to Results.
          <br />
          It will contain default example and explanation of interface. The
          plugin tab is a standalone HTML/Javascript application that can load
          and present backtest results.
        </p>
        <p>
          <strong>
            Use vibe coding or manual code editing to edit the tab and create
            something new.
          </strong>
        </p>
        <p>Local UI preview: the tab is kept in this session; no plugin files are created.</p>
        <p>
          <a href="https://strategyquant.com/doc/strategyquant/results-plugins" target="_blank" rel="noreferrer">
            Learn more about new StrategyQuant Results plugins here
          </a>
        </p>
        <div>
          <div className="sqr-newanalysis-namelabel">Name of custom plugin tab (must be unique)</div>
          <input type="text" className="sqd-input sqr-text-input" aria-label="Name of custom plugin tab" value={name} onChange={e => setName(e.target.value)} placeholder="My Analysis" style={{ width: 280 }}/>
          {trimmed.length > 0 && taken && (<div className="sqr-newanalysis-error" role="alert">
              This name is already used
            </div>)}
        </div>
      </div>
      <div className="sqr-modal-links">
        <a role="button" tabIndex={0} onClick={onClose} onKeyDown={e => e.key === 'Enter' && onClose()}>
          Close
        </a>
        <button type="button" className="sqd-btn sqd-btn-primary sqr-btn-create" disabled={trimmed.length === 0 || taken} onClick={() => onCreate(trimmed)}>
          Create
        </button>
      </div>
    </SqdModal>);
}
