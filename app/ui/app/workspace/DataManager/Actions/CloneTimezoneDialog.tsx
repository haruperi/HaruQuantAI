import { useState, type ChangeEvent } from 'react';
import { Button, Checkbox, Field, Modal, Select, TextInput } from '../../../components/ui';
import { actionsClient } from './actionsClient';
import './actions.css';

export interface CloneTarget {
  id: string;
  symbol: string;
  source?: string;
  sourceDataId?: string;
}

export function CloneTimezoneDialog({
  targets,
  onClose,
  onComplete,
}: {
  targets: CloneTarget[];
  onClose: () => void;
  onComplete: (message: string) => void;
}) {
  const [shiftHours, setShiftHours] = useState<number>(2);
  const [mode, setMode] = useState<'shift' | 'zone'>('shift');
  const [timezone, setTimezone] = useState<string>('UTC+2');
  const [postfix, setPostfix] = useState<string>('_{timeframe}_{cloneTime}');
  const [removeWeekends, setRemoveWeekends] = useState<boolean>(true);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');

  const target = targets[0];
  const isCloned = targets.some(t => t.source === 'Clone' || Boolean(t.sourceDataId));

  async function handleClone(): Promise<void> {
    if (isCloned) {
      setError('Cloned data cannot be cloned again.');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const clonedSymbols: string[] = [];
      for (const t of targets) {
        const computedShift = mode === 'shift' ? shiftHours : parseInt(timezone.replace('UTC', '').replace('+', '')) || 0;
        const res = await actionsClient.cloneToTimezone({
          symbol: t.symbol,
          shift_hours: computedShift,
          timezone: mode === 'shift' ? `UTC${shiftHours >= 0 ? '+' : ''}${shiftHours}` : timezone,
          postfix,
          remove_weekends: removeWeekends,
        });
        clonedSymbols.push(res.clonedSymbol);
      }
      onComplete(`Cloned ${targets.length} dataset(s): ${clonedSymbols.join(', ')}.`);
      onClose();
    } catch (exc: any) {
      setError(exc?.message || 'Failed to clone dataset');
    } finally {
      setLoading(false);
    }
  }

  const selectedTitle = targets.length === 1 ? targets[0].symbol : `${targets.length} datasets`;

  return (
    <div className="data-tools-flow">
      <Modal
        title={`Clone to Timezone for '${selectedTitle}'`}
        width={600}
        onClose={onClose}
        footer={
          <>
            <Button onClick={onClose} disabled={loading}>
              Cancel
            </Button>
            <Button className="primary" onClick={handleClone} disabled={loading || isCloned || !targets.length}>
              {loading ? 'Cloning…' : 'Proceed'}
            </Button>
          </>
        }
      >
        {isCloned && (
          <p role="alert" className="actions-error">
            One or more selected datasets are already cloned data. You cannot clone cloned data.
          </p>
        )}
        {error && (
          <p role="alert" className="actions-error">
            {error}
          </p>
        )}
        <p className="tools-copy">
          Clone to Timezone creates a new dataset with all bar timestamps shifted to a different timezone.
          This allows you to test strategies across different session closes (e.g. New York 17:00 close / UTC+2).
        </p>
        <fieldset>
          <legend>Clone Settings</legend>
          <Field label="Source Symbol">
            <TextInput value={target?.symbol || ''} readOnly />
          </Field>
          <Field label="Cloned Symbol Postfix" hint="Constants: {timeframe}, {cloneTime}">
            <TextInput value={postfix} onChange={(e: ChangeEvent<HTMLInputElement>) => setPostfix(e.target.value)} />
          </Field>
        </fieldset>
        <fieldset>
          <legend>Cloned Data Timezone</legend>
          <div className="clone-timezone-options">
            <label>
              <input
                type="radio"
                name="tz-mode"
                checked={mode === 'shift'}
                onChange={() => setMode('shift')}
              />
              <span>Add Fixed Shift</span>
              <TextInput
                type="number"
                min={-23}
                max={23}
                disabled={mode !== 'shift'}
                value={String(shiftHours)}
                onChange={(e: ChangeEvent<HTMLInputElement>) => setShiftHours(Number(e.target.value) || 0)}
              />
              <small>hours</small>
            </label>
            <label>
              <input
                type="radio"
                name="tz-mode"
                checked={mode === 'zone'}
                onChange={() => setMode('zone')}
              />
              <span>Choose Timezone</span>
              <Select disabled={mode !== 'zone'} value={timezone} onChange={setTimezone}>
                <option value="UTC-5">UTC-5 (EST New York)</option>
                <option value="UTC+0">UTC+0 (London GMT)</option>
                <option value="UTC+1">UTC+1 (CET)</option>
                <option value="UTC+2">UTC+2 (EET / Server)</option>
                <option value="UTC+3">UTC+3 (MSK)</option>
                <option value="UTC+8">UTC+8 (Singapore / HK)</option>
                <option value="UTC+9">UTC+9 (Tokyo JST)</option>
              </Select>
            </label>
            <Checkbox
              label="Remove weekend bars outside market opening"
              checked={removeWeekends}
              onChange={setRemoveWeekends}
            />
          </div>
        </fieldset>
      </Modal>
    </div>
  );
}
