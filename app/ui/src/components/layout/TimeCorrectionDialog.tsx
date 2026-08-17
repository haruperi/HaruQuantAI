"use client";

import React, { useEffect, useRef, useState } from "react";

import {
  dateTimeLocalValue,
  parseUtcOffset,
  utcMsFromLocalValue,
} from "./clock";

const TIMEZONE_OPTIONS: readonly string[] = Object.freeze([
  "UTC-12", "UTC-11", "UTC-10", "UTC-9", "UTC-8", "UTC-7", "UTC-6",
  "UTC-5", "UTC-4", "UTC-3", "UTC-2", "UTC-1", "UTC", "UTC+1",
  "UTC+2", "UTC+3", "UTC+4", "UTC+5", "UTC+6", "UTC+7", "UTC+8",
  "UTC+9", "UTC+10", "UTC+11", "UTC+12", "UTC+13", "UTC+14",
]);

export interface TimeCorrection {
  correctedUtcMs: number;
  timezone: string;
}

interface TimeCorrectionDialogProps {
  currentUtcMs: number;
  timezone: string;
  onApply: (correction: TimeCorrection) => Promise<boolean>;
  onClose: () => void;
  onReset: () => Promise<boolean>;
}

/** Accessible editor for the Header's session-local clock correction. */
export const TimeCorrectionDialog: React.FC<TimeCorrectionDialogProps> = ({
  currentUtcMs,
  timezone,
  onApply,
  onClose,
  onReset,
}) => {
  const initialOffset = parseUtcOffset(timezone) ?? 0;
  const [selectedTimezone, setSelectedTimezone] = useState(timezone);
  const [localValue, setLocalValue] = useState(
    dateTimeLocalValue(currentUtcMs, initialOffset),
  );
  const [message, setMessage] = useState("");
  const [pending, setPending] = useState(false);
  const closeButtonRef = useRef<HTMLButtonElement>(null);
  const onCloseRef = useRef(onClose);

  useEffect(() => {
    onCloseRef.current = onClose;
  }, [onClose]);

  useEffect(() => {
    closeButtonRef.current?.focus();
    const closeOnEscape = (event: KeyboardEvent): void => {
      if (event.key === "Escape") onCloseRef.current();
    };
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, []);

  const apply = async (): Promise<void> => {
    const offset = parseUtcOffset(selectedTimezone);
    const correctedUtcMs = offset === null
      ? null
      : utcMsFromLocalValue(localValue, offset);
    if (correctedUtcMs === null) {
      setMessage("Enter a valid date, time, and timezone.");
      return;
    }
    setPending(true);
    const applied = await onApply({ correctedUtcMs, timezone: selectedTimezone });
    setPending(false);
    if (!applied) setMessage("Time correction was not saved.");
  };

  const reset = async (): Promise<void> => {
    setPending(true);
    const applied = await onReset();
    setPending(false);
    if (!applied) setMessage("Time correction was not reset.");
  };

  return (
    <div className="modal-overlay time-correction-overlay" role="presentation" onClick={onClose}>
      <div
        className="modal-content time-correction-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="time-correction-title"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="modal-header">
          <span id="time-correction-title">Correct display time</span>
          <button ref={closeButtonRef} type="button" className="widget-btn" aria-label="Close time correction" onClick={onClose}>×</button>
        </div>
        <div className="modal-body">
          <label className="form-group">
            <span className="form-label">Date and time</span>
            <input
              className="form-input"
              type="datetime-local"
              value={localValue}
              onChange={(event) => setLocalValue(event.target.value)}
            />
          </label>
          <label className="form-group">
            <span className="form-label">Time zone</span>
            <select
              className="form-select"
              value={selectedTimezone}
              onChange={(event) => setSelectedTimezone(event.target.value)}
            >
              {TIMEZONE_OPTIONS.map((option) => <option key={option}>{option}</option>)}
            </select>
          </label>
          <p className="time-correction-note">Manual time applies to this session only. The time zone is saved in system settings.</p>
          {message && <div role="alert" className="time-correction-message">{message}</div>}
          <div className="time-correction-actions">
            <button type="button" className="widget-btn" onClick={onClose}>Cancel</button>
            <button type="button" className="widget-btn" disabled={pending} onClick={() => void reset()}>Reset to current time</button>
            <button type="button" className="widget-btn primary" disabled={pending} onClick={() => void apply()}>Apply</button>
          </div>
        </div>
      </div>
    </div>
  );
};
