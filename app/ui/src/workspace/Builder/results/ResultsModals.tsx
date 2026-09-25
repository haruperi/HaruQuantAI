import { useState, type ReactNode } from 'react';
import { SqdModal } from '../FitnessEvolutionModal';

/**
 * Modals for the Results tab parity (FEAT-UI-BUILDER_RESULTS_TAB),
 * mirroring ProjectResults/newCustomPluginModal.html, the rename popup and
 * the delete confirm from CustomResultsPluginActions.
 */

export function NewAnalysisModal({
  existingNames,
  onClose,
  onCreate,
}: {
  existingNames: string[];
  onClose: () => void;
  onCreate: (name: string) => void;
}) {
  const [name, setName] = useState('');
  const trimmed = name.trim();
  const taken = existingNames.some(
    n => n.toLowerCase() === trimmed.toLowerCase(),
  );
  return (
    <SqdModal title="Create new Result analysis plugin" onClose={onClose} width={640}>
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
        <p>Plugin code is available in user/extend/ResultsPlugin/&#123;YourName&#125; folder.</p>
        <p>
          <a
            href="https://strategyquant.com/doc/strategyquant/results-plugins"
            target="_blank"
            rel="noreferrer"
          >
            Learn more about new StrategyQuant Results plugins here
          </a>
        </p>
        <div>
          <div className="sqr-newanalysis-namelabel">Name of custom plugin tab (must be unique)</div>
          <input
            type="text"
            className="sqd-input sqr-text-input"
            aria-label="Name of custom plugin tab"
            value={name}
            onChange={e => setName(e.target.value)}
            placeholder="My Analysis"
            style={{ width: 280 }}
          />
          {trimmed.length > 0 && taken && (
            <div className="sqr-newanalysis-error" role="alert">
              This name is already used
            </div>
          )}
        </div>
      </div>
      <div className="sqr-modal-links">
        <a role="button" tabIndex={0} onClick={onClose} onKeyDown={e => e.key === 'Enter' && onClose()}>
          Close
        </a>
        <button
          type="button"
          className="sqd-btn sqd-btn-primary sqr-btn-create"
          disabled={trimmed.length === 0 || taken}
          onClick={() => onCreate(trimmed)}
        >
          Create
        </button>
      </div>
    </SqdModal>
  );
}

export function RenameAnalysisModal({
  currentName,
  existingNames,
  onClose,
  onRename,
}: {
  currentName: string;
  existingNames: string[];
  onClose: () => void;
  onRename: (name: string) => void;
}) {
  const [name, setName] = useState(currentName);
  const trimmed = name.trim();
  const taken = existingNames.some(
    n => n !== currentName && n.toLowerCase() === trimmed.toLowerCase(),
  );
  return (
    <SqdModal title={`Rename custom analysis '${currentName}'`} onClose={onClose}>
      <label className="sqr-rename-label">
        New name
        <input
          type="text"
          className="sqd-input sqr-text-input"
          aria-label="New name"
          value={name}
          onChange={e => setName(e.target.value)}
        />
      </label>
      {taken && (
        <div className="sqr-newanalysis-error" role="alert">
          This name is already used
        </div>
      )}
      <div className="sqr-modal-links">
        <a role="button" tabIndex={0} onClick={onClose} onKeyDown={e => e.key === 'Enter' && onClose()}>
          Close
        </a>
        <button
          type="button"
          className="sqd-btn sqd-btn-primary sqr-btn-create"
          disabled={trimmed.length === 0 || taken}
          onClick={() => onRename(trimmed)}
        >
          Rename
        </button>
      </div>
    </SqdModal>
  );
}

export function DeleteAnalysisModal({
  name,
  onClose,
  onDelete,
}: {
  name: string;
  onClose: () => void;
  onDelete: () => void;
}) {
  return (
    <SqdModal title="Remove custom analysis" onClose={onClose} width={420}>
      <p>Are you sure you want to remove &apos;{name}&apos;?</p>
      <div className="sqr-modal-links">
        <a role="button" tabIndex={0} onClick={onClose} onKeyDown={e => e.key === 'Enter' && onClose()}>
          Close
        </a>
        <button type="button" className="sqd-btn sqd-btn-primary sqr-btn-create" onClick={onDelete}>
          Delete
        </button>
      </div>
    </SqdModal>
  );
}

/** Manage Views modal fixture (tradelist views; Manage Views language strings). */
export function ManageViewsModal({ onClose }: { onClose: () => void }) {
  return (
    <SqdModal title="Manage Views" onClose={onClose} width={560}>
      <div className="sqr-manageviews">
        <div className="sqr-manageviews-label">Select view to edit</div>
        <div className="sqr-manageviews-or">or</div>
        <button type="button" className="sqd-btn">Create new view</button>
      </div>
      <div className="sqr-modal-links">
        <a role="button" tabIndex={0} onClick={onClose} onKeyDown={e => e.key === 'Enter' && onClose()}>
          Close
        </a>
        <button type="button" className="sqd-btn sqd-btn-primary sqr-btn-create">
          Save changes
        </button>
      </div>
    </SqdModal>
  );
}

/** Export modal fixture (exportModal language strings: CSV / XLSX choice). */
export function ExportTradesModal({ onClose }: { onClose: () => void }) {
  const [format, setFormat] = useState('csv');
  return (
    <SqdModal title="Export format" onClose={onClose} width={440}>
      <p>You can export contents either to classic CSV file or MS Office XLSX file.</p>
      <div className="sqr-export-question">Which file format do you prefer?</div>
      <label className="sqr-export-option">
        <input
          type="radio"
          name="sqr-export-format"
          checked={format === 'csv'}
          onChange={() => setFormat('csv')}
        />
        CSV file
      </label>
      <label className="sqr-export-option">
        <input
          type="radio"
          name="sqr-export-format"
          checked={format === 'xlsx'}
          onChange={() => setFormat('xlsx')}
        />
        MS Office XLSX file
      </label>
      <label className="sqr-export-option sqr-export-comma">
        <input type="checkbox" />
        Use comma in numeric values
      </label>
      <div className="sqr-modal-links">
        <a role="button" tabIndex={0} onClick={onClose} onKeyDown={e => e.key === 'Enter' && onClose()}>
          Close
        </a>
        <button type="button" className="sqd-btn sqd-btn-primary sqr-btn-create">
          Export
        </button>
      </div>
    </SqdModal>
  );
}

/** Small helper so modal footers share markup. */
export function ModalLinks({ children }: { children: ReactNode }) {
  return <div className="sqr-modal-links">{children}</div>;
}
