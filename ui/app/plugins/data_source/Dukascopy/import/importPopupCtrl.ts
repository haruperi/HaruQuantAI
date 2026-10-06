import { useEffect, useRef, useState } from 'react';
import { useAppStore } from '../../../../host/store';
import { useDukascopyDownloadService } from '../DukascopyService';
import {
  availableStart,
  presetRange,
  today,
  validateDownload,
  type DownloadMode,
  type DownloadTarget,
  type Preset,
} from '../dukascopyDownload';

export interface ImportPopupProps {
  targets: DownloadTarget[];
  onClose: () => void;
  onStarted: () => void;
}

export function useImportPopupController({ targets, onClose, onStarted }: ImportPopupProps) {
  const minimum = availableStart(targets[0]);
  const last = targets[0].to || minimum;
  const [from, setFrom] = useState(last);
  const [to, setTo] = useState(today());
  const [preset, setPreset] = useState<Preset>('sinceLast');
  const [overwrite, setOverwrite] = useState(false);
  const trial = useAppStore((state) => state.settings.profile) === 'Starter';
  const { preferred, start } = useDukascopyDownloadService();
  const [mode, setMode] = useState<DownloadMode>(trial ? 'standard' : (preferred ?? 'cdn'));
  const [page, setPage] = useState<'download' | 'disclaimer' | 'confirm'>('download');
  const [error, setError] = useState('');
  const root = useRef<HTMLDivElement>(null);
  const confirmation = useRef<HTMLDivElement>(null);
  const disclaimerButton = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    root.current?.querySelector<HTMLButtonElement>('button')?.focus();
    return () => previous?.focus();
  }, []);
  useEffect(() => {
    (page === 'confirm' ? confirmation : root).current
      ?.querySelector<HTMLButtonElement>('button')
      ?.focus();
  }, [page]);
  function back() {
    const wasConfirm = page === 'confirm';
    setPage('download');
    window.setTimeout(
      () =>
        (wasConfirm
          ? root.current?.querySelector<HTMLButtonElement>('[data-download-start]')
          : disclaimerButton.current
        )?.focus(),
      0,
    );
  }
  function choose(value: Preset) {
    const range = presetRange(value, last, minimum, from, to);
    setFrom(range.from);
    setTo(range.to);
    setPreset(value);
    setError('');
  }
  function submit(confirmed = false) {
    const request = {
      targets,
      dateFrom: from,
      dateTo: to,
      dateType: preset,
      overwrite,
      downloadType: mode,
    };
    try {
      validateDownload(request);
      if (mode !== 'standard' && !confirmed) {
        setPage('confirm');
        return;
      }
      start(request);
      onStarted();
      onClose();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Unable to start download');
      setPage('download');
    }
  }
  const title =
    page === 'disclaimer'
      ? 'HaruQuantAI CDN Data Disclaimer'
      : `Download Dukascopy data for ${targets.length > 1 ? 'multiple' : `'${targets[0].symbol}'`}`;
  return {
    minimum,
    from,
    to,
    preset,
    overwrite,
    trial,
    mode,
    page,
    error,
    root,
    confirmation,
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
  };
}
export type ImportPopupController = ReturnType<typeof useImportPopupController>;
