/**
 * Dukascopy Data Import / Download Modal.
 *
 * 1:1 Parity with SQX Build 144:
 * C:\SQX\internal\plugins\DataSourceDukascopy\import (importPopup.html, importPopupCtrl.js).
 */
import { useEffect, useRef, useState } from 'react';
import { Button, TextInput } from '../../../components/ui';
import { useAppStore } from './localState';
import { useDukascopyDownloads } from './dukascopyStore';
import { availableStart, presetRange, today, validateDownload, type DownloadMode, type DownloadTarget, type Preset } from './dukascopyDownload';
import './dukascopyDownload.css';

export function DukascopyDownloadDialog({ targets, onClose, onStarted }: { targets: DownloadTarget[]; onClose: () => void; onStarted: () => void }) {
  const minimum = availableStart(targets[0]);
  const last = targets[0].to || minimum;
  const [from, setFrom] = useState(last);
  const [to, setTo] = useState(today());
  const [preset, setPreset] = useState<Preset>('sinceLast');
  const [overwrite, setOverwrite] = useState(false);
  const trial = useAppStore(state => state.settings.profile) === 'Starter';
  const preferred = useDukascopyDownloads(state => state.preferred);
  const start = useDukascopyDownloads(state => state.start);
  const available = useDukascopyDownloads(state => state.available);
  const [mode, setMode] = useState<DownloadMode>('standard');
  const [page, setPage] = useState<'download' | 'disclaimer' | 'confirm'>('download');
  const [error, setError] = useState('');
  const root = useRef<HTMLDivElement>(null);
  const confirmation = useRef<HTMLDivElement>(null);
  const disclaimerButton = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    void useDukascopyDownloads.getState().refresh();
    const previous = document.activeElement as HTMLElement | null;
    root.current?.querySelector<HTMLButtonElement>('button')?.focus();
    return () => previous?.focus();
  }, []);
  useEffect(() => { (page === 'confirm' ? confirmation : root).current?.querySelector<HTMLButtonElement>('button')?.focus(); }, [page]);
  function back() { const wasConfirm = page === 'confirm'; setPage('download'); window.setTimeout(() => (wasConfirm ? root.current?.querySelector<HTMLButtonElement>('[data-download-start]') : disclaimerButton.current)?.focus(), 0); }
  function choose(value: Preset) { const range = presetRange(value, last, minimum, from, to); setFrom(range.from); setTo(range.to); setPreset(value); setError(''); }
  async function submit(confirmed = false) {
    const request = { targets, dateFrom: from, dateTo: to, dateType: preset, overwrite, downloadType: mode };
    try {
      validateDownload(request);
      if (mode !== 'standard' && !confirmed) { setPage('confirm'); return; }
      await start(request); onStarted(); onClose();
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to start download'); setPage('download'); }
  }
  const title = page === 'disclaimer' ? 'StrategyQuant CDN status' : `Download Dukascopy data for ${targets.length > 1 ? 'multiple' : `'${targets[0].symbol}'`}`;
  const presetButton = (value: Preset, label: string) => <Button className={preset === value ? 'primary' : ''} aria-pressed={preset === value} onClick={() => choose(value)}>{label}</Button>;
  return <div className="modal-backdrop dukas-download-overlay"><div ref={root} inert={page === 'confirm'} aria-hidden={page === 'confirm' ? true : undefined} className="modal dukas-download-dialog" role="dialog" aria-modal="true" aria-labelledby="dukas-download-title" onKeyDown={event => {
    if (event.key === 'Escape') { event.stopPropagation(); if (page === 'download') onClose(); else back(); }
    if (event.key === 'Tab') {
      const controls = Array.from(root.current?.querySelectorAll<HTMLElement>('button:not(:disabled),input:not(:disabled)') ?? []);
      const first = controls[0]; const lastControl = controls.at(-1);
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); lastControl?.focus(); }
      else if (!event.shiftKey && document.activeElement === lastControl) { event.preventDefault(); first?.focus(); }
    }
  }}>
    <header><h2 id="dukas-download-title">{title}</h2><button className="icon-button" aria-label="Close" onClick={page === 'download' ? onClose : back}>×</button></header>
    <div className="modal-content">
      {page !== 'disclaimer' ? <>
        <fieldset><legend>Choose data range to download</legend>
          <div className="dukas-date-row"><label>From <TextInput aria-label="From" type="date" min={minimum} max={today()} value={from} onChange={event => { setFrom(event.target.value); setPreset('custom'); }}/></label>{presetButton('sinceLast', 'Since last date')}{presetButton('sixMonths', 'Last 6 months')}{presetButton('year', 'Last year')}</div>
          <div className="dukas-date-row"><label>To <TextInput aria-label="To" type="date" min={minimum} max={today()} value={to} onChange={event => { setTo(event.target.value); setPreset('custom'); }}/></label>{presetButton('fiveYears', 'Last 5 years')}{presetButton('tenYears', 'Last 10 years')}{presetButton('allTime', 'All time')}</div>
        </fieldset>
        <fieldset><legend>Redownload options</legend><div className="dukas-redownload"><label><input type="radio" name="dukas-overwrite" checked={!overwrite} onChange={() => setOverwrite(false)}/> Add only missing data</label><label><input type="radio" name="dukas-overwrite" checked={overwrite} onChange={() => setOverwrite(true)}/> Overwrite existing data</label></div></fieldset>
        <fieldset><legend>Fast Data Download</legend><div className="dukas-download-modes">
          <label><input type="radio" name="dukas-mode" checked={mode === 'standard'} onChange={() => setMode('standard')}/> Standard download - Dukascopy servers</label>
          <label><input type="radio" name="dukas-mode" checked={mode === 'cdn'} onChange={() => setMode('cdn')}/> StrategyQuant CDN (Fast)</label>
          <label><input type="radio" name="dukas-mode" checked={mode === 'cdn-cn'} onChange={() => setMode('cdn-cn')}/> StrategyQuant Hong Kong CDN (Fast)</label>
          <button ref={disclaimerButton} className="dukas-disclaimer-link" onClick={() => setPage('disclaimer')}>CDN availability details</button>
        </div></fieldset>
      </> : <section className="dukas-download-disclaimer"><h3>Fast Data Download (CDN)</h3><p>StrategyQuant CDN endpoints provide accelerated package delivery. If CDN data is missing or unreachable for any requested date range, HaruQuantAI will automatically fall back to standard Dukascopy servers.</p></section>}
      {error && page === 'download' && <p className="dukas-download-error" role="alert">{error}</p>}
    </div>
    <footer>{!available && <p role="status">Downloads are unavailable until the market catalog is provisioned.</p>}<Button onClick={page === 'download' ? onClose : back}>Close</Button>{page !== 'disclaimer' && <Button data-download-start className="primary" onClick={() => { void submit(); }} disabled={!available}>Start download</Button>}</footer>
  </div>{page === 'confirm' && <div className="modal-backdrop dukas-fast-overlay"><div ref={confirmation} className="modal dukas-fast-confirm" role="dialog" aria-modal="true" aria-labelledby="dukas-fast-title" aria-describedby="dukas-fast-message" onKeyDown={event => {
    if (event.key === 'Escape') { event.stopPropagation(); back(); }
    if (event.key === 'Tab') {
      const controls = Array.from(confirmation.current?.querySelectorAll<HTMLButtonElement>('button:not(:disabled)') ?? []);
      if (event.shiftKey && document.activeElement === controls[0]) { event.preventDefault(); controls.at(-1)?.focus(); }
      else if (!event.shiftKey && document.activeElement === controls.at(-1)) { event.preventDefault(); controls[0]?.focus(); }
    }
  }}>
    <header><h2 id="dukas-fast-title">Fast Data Download</h2><button className="icon-button" aria-label="Close" onClick={back}>×</button></header>
    <div className="modal-content" id="dukas-fast-message"><p><strong>Fast download is not available for all symbols or date ranges.</strong></p>{trial && <p>Fast downloading is possible only in full version or for some specific symbols in M1 timeframe.</p>}<p>If a symbol cannot be downloaded using fast mode, its download will automatically fall back to standard mode.</p></div>
    <footer><Button onClick={back}>Cancel</Button><Button className="primary" onClick={() => submit(true)}>OK</Button></footer>
  </div></div>}</div>;
}

export const DukascopyImportDialog = DukascopyDownloadDialog;
export default DukascopyDownloadDialog;
