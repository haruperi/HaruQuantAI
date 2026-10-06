import { Button, TextInput } from '../../../../components/ui';
import { today, type Preset } from '../dukascopyDownload';
import {
  useImportPopupController,
  type ImportPopupProps,
  type ImportPopupController,
} from './importPopupCtrl';
import { CdnDisclaimerPopup } from './cdnDisclaimerPopup';
import '../style.css';

export function ImportPopup(props: ImportPopupProps) {
  const { onClose } = props;
  const controller = useImportPopupController(props);
  const {
    minimum,
    from,
    to,
    preset,
    overwrite,
    mode,
    page,
    error,
    root,
    disclaimerButton,
    back,
    choose,
    submit,
    title,
    setFrom,
    setTo,
    setPreset,
    setOverwrite,
    setMode,
    setPage,
  } = controller;
  const presetButton = (value: Preset, label: string) => (
    <Button
      className={preset === value ? 'primary' : ''}
      aria-pressed={preset === value}
      onClick={() => choose(value)}
    >
      {label}
    </Button>
  );
  return (
    <div className="modal-backdrop dukas-download-overlay">
      <div
        ref={root}
        inert={page === 'confirm'}
        aria-hidden={page === 'confirm' ? true : undefined}
        className="modal dukas-download-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="dukas-download-title"
        onKeyDown={(event) => {
          if (event.key === 'Escape') {
            event.stopPropagation();
            if (page === 'download') onClose();
            else back();
          }
          if (event.key === 'Tab') {
            const controls = Array.from(
              root.current?.querySelectorAll<HTMLElement>(
                'button:not(:disabled),input:not(:disabled)',
              ) ?? [],
            );
            const first = controls[0];
            const lastControl = controls.at(-1);
            if (event.shiftKey && document.activeElement === first) {
              event.preventDefault();
              lastControl?.focus();
            } else if (!event.shiftKey && document.activeElement === lastControl) {
              event.preventDefault();
              first?.focus();
            }
          }
        }}
      >
        <header>
          <h2 id="dukas-download-title">{title}</h2>
          <button
            className="icon-button"
            aria-label="Close"
            onClick={page === 'download' ? onClose : back}
          >
            ×
          </button>
        </header>
        <div className="modal-content">
          {page !== 'disclaimer' ? (
            <>
              <fieldset>
                <legend>Choose data range to download</legend>
                <div className="dukas-date-row">
                  <label>
                    From{' '}
                    <TextInput
                      aria-label="From"
                      type="date"
                      min={minimum}
                      max={today()}
                      value={from}
                      onChange={(event) => {
                        setFrom(event.target.value);
                        setPreset('custom');
                      }}
                    />
                  </label>
                  {presetButton('sinceLast', 'Since last date')}
                  {presetButton('sixMonths', 'Last 6 months')}
                  {presetButton('year', 'Last year')}
                </div>
                <div className="dukas-date-row">
                  <label>
                    To{' '}
                    <TextInput
                      aria-label="To"
                      type="date"
                      min={minimum}
                      max={today()}
                      value={to}
                      onChange={(event) => {
                        setTo(event.target.value);
                        setPreset('custom');
                      }}
                    />
                  </label>
                  {presetButton('fiveYears', 'Last 5 years')}
                  {presetButton('tenYears', 'Last 10 years')}
                  {presetButton('allTime', 'All time')}
                </div>
              </fieldset>
              <fieldset>
                <legend>Redownload options</legend>
                <div className="dukas-redownload">
                  <label>
                    <input
                      type="radio"
                      name="dukas-overwrite"
                      checked={!overwrite}
                      onChange={() => setOverwrite(false)}
                    />{' '}
                    Add only missing data
                  </label>
                  <label>
                    <input
                      type="radio"
                      name="dukas-overwrite"
                      checked={overwrite}
                      onChange={() => setOverwrite(true)}
                    />{' '}
                    Overwrite existing data
                  </label>
                </div>
              </fieldset>
              <fieldset>
                <legend>Fast Data Download</legend>
                <div className="dukas-download-modes">
                  <label>
                    <input
                      type="radio"
                      name="dukas-mode"
                      checked={mode === 'standard'}
                      onChange={() => setMode('standard')}
                    />{' '}
                    Standard download - Dukascopy servers
                  </label>
                  <label>
                    <input
                      type="radio"
                      name="dukas-mode"
                      checked={mode === 'cdn'}
                      onChange={() => setMode('cdn')}
                    />{' '}
                    Fast download from HaruQuantAI CDN (10 x faster download)
                    <small>
                      If on, Dukascopy data will be downloaded from prepared packages on HaruQuantAI
                      CDN servers. Please note that pre-prepared packages are available only for
                      part of the data.
                    </small>
                  </label>
                  <label>
                    <input
                      type="radio"
                      name="dukas-mode"
                      checked={mode === 'cdn-cn'}
                      onChange={() => setMode('cdn-cn')}
                    />{' '}
                    Fast download from Hong Kong server
                    <small>
                      especially for Asia and China users, it might be more performant than CDN
                      option
                    </small>
                  </label>
                  <button
                    ref={disclaimerButton}
                    className="dukas-disclaimer-link"
                    onClick={() => setPage('disclaimer')}
                  >
                    HaruQuantAI CDN data disclaimer
                  </button>
                </div>
              </fieldset>
            </>
          ) : (
            <CdnDisclaimerPopup />
          )}
          {error && page === 'download' && (
            <p className="dukas-download-error" role="alert">
              {error}
            </p>
          )}
        </div>
        <footer>
          <Button onClick={page === 'download' ? onClose : back}>Close</Button>
          {page !== 'disclaimer' && (
            <Button data-download-start className="primary" onClick={() => submit()}>
              Start download
            </Button>
          )}
        </footer>
      </div>
      {page === 'confirm' && <FastDownloadConfirmation controller={controller} />}
    </div>
  );
}

function FastDownloadConfirmation({ controller }: { controller: ImportPopupController }) {
  const { confirmation, back, trial, submit } = controller;
  return (
    <div className="modal-backdrop dukas-fast-overlay">
      <div
        ref={confirmation}
        className="modal dukas-fast-confirm"
        role="dialog"
        aria-modal="true"
        aria-labelledby="dukas-fast-title"
        aria-describedby="dukas-fast-message"
        onKeyDown={(event) => {
          if (event.key === 'Escape') {
            event.stopPropagation();
            back();
          }
          if (event.key === 'Tab') {
            const controls = Array.from(
              confirmation.current?.querySelectorAll<HTMLButtonElement>('button:not(:disabled)') ??
                [],
            );
            if (event.shiftKey && document.activeElement === controls[0]) {
              event.preventDefault();
              controls.at(-1)?.focus();
            } else if (!event.shiftKey && document.activeElement === controls.at(-1)) {
              event.preventDefault();
              controls[0]?.focus();
            }
          }
        }}
      >
        <header>
          <h2 id="dukas-fast-title">Fast Data Download</h2>
          <button className="icon-button" aria-label="Close" onClick={back}>
            ×
          </button>
        </header>
        <div className="modal-content" id="dukas-fast-message">
          <p>
            <strong>Fast download is not available for all symbols or date ranges.</strong>
          </p>
          {trial && (
            <p>
              Fast downloading is possible only in full version or for some specific symbols in M1
              timeframe.
            </p>
          )}
          <p>
            If a symbol cannot be downloaded using fast mode, its download will automatically fall
            back to standard mode.
          </p>
        </div>
        <footer>
          <Button onClick={back}>Cancel</Button>
          <Button className="primary" onClick={() => submit(true)}>
            OK
          </Button>
        </footer>
      </div>
    </div>
  );
}
