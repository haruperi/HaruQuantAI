/**
 * Generic parameter form renderer driven by ParameterSpec declarations.
 */

import React from 'react';
import type { ParameterSpec } from '../../api/contracts.generated';

export interface ParameterFormProps {
  parameters: ParameterSpec[];
  values: Record<string, unknown>;
  onChange: (values: Record<string, unknown>) => void;
  disabled?: boolean;
}

export function ParameterForm({
  parameters,
  values,
  onChange,
  disabled = false,
}: ParameterFormProps) {
  const handleChange = (key: string, val: unknown) => {
    onChange({
      ...values,
      [key]: val,
    });
  };

  // Group parameters by presentation group
  const groups = React.useMemo(() => {
    const map = new Map<string, ParameterSpec[]>();
    for (const p of parameters) {
      const g = p.presentation?.group || 'General';
      if (!map.has(g)) {
        map.set(g, []);
      }
      map.get(g)!.push(p);
    }
    // Sort parameters inside groups by presentation.order
    for (const list of map.values()) {
      list.sort((a, b) => (a.presentation?.order ?? 0) - (b.presentation?.order ?? 0));
    }
    return Array.from(map.entries());
  }, [parameters]);

  return (
    <div className="parameter-form">
      {groups.map(([groupName, specs]) => (
        <fieldset key={groupName} className="parameter-group">
          {groups.length > 1 && <legend>{groupName}</legend>}
          {specs.map((spec) => {
            const currentVal = values[spec.key] !== undefined ? values[spec.key] : spec.default;
            const inputId = `param-${spec.key}`;

            let control = null;

            if (spec.constraint?.type === 'enum') {
              control = (
                <select
                  id={inputId}
                  disabled={disabled}
                  value={String(currentVal ?? '')}
                  onChange={(e) => handleChange(spec.key, e.target.value)}
                  className="text-input"
                >
                  {spec.constraint.choices.map((c) => (
                    <option key={c.value} value={c.value}>
                      {c.label || c.value}
                    </option>
                  ))}
                </select>
              );
            } else if (spec.kind === 'boolean') {
              control = (
                <input
                  id={inputId}
                  type="checkbox"
                  disabled={disabled}
                  checked={Boolean(currentVal)}
                  onChange={(e) => handleChange(spec.key, e.target.checked)}
                />
              );
            } else if (spec.kind === 'number' || spec.kind === 'integer') {
              const numConstraint = spec.constraint?.type === 'numeric' ? spec.constraint : null;
              control = (
                <input
                  id={inputId}
                  type="number"
                  disabled={disabled}
                  value={currentVal !== undefined && currentVal !== null ? String(currentVal) : ''}
                  min={numConstraint?.min_value ?? undefined}
                  max={numConstraint?.max_value ?? undefined}
                  step={numConstraint?.step ?? 'any'}
                  onChange={(e) => {
                    const parsed = e.target.value === '' ? null : Number(e.target.value);
                    handleChange(spec.key, parsed);
                  }}
                  className="text-input"
                />
              );
            } else {
              control = (
                <input
                  id={inputId}
                  type="text"
                  disabled={disabled}
                  value={String(currentVal ?? '')}
                  onChange={(e) => handleChange(spec.key, e.target.value)}
                  className="text-input"
                />
              );
            }

            return (
              <div key={spec.key} className="form-field">
                <label htmlFor={inputId}>
                  {spec.presentation?.label || spec.label || spec.key}
                  {spec.required && <span className="required-mark"> *</span>}
                </label>
                {control}
                {(spec.presentation?.help_text || spec.description) && (
                  <small className="help-text">
                    {spec.presentation?.help_text || spec.description}
                  </small>
                )}
              </div>
            );
          })}
        </fieldset>
      ))}
    </div>
  );
}
