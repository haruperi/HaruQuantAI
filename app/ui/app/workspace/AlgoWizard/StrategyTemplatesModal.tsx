import { BookOpen, Check, Sparkles } from 'lucide-react';
import { Button, Modal } from '../../components/ui';
import { STRATEGY_TEMPLATES, type StrategyTemplate } from './algoWizardTemplates';

interface Props {
  onClose: () => void;
  onSelectTemplate: (template: StrategyTemplate) => void;
}

export function StrategyTemplatesModal({ onClose, onSelectTemplate }: Props) {
  return (
    <Modal
      title="Strategy Templates Library (StrategyQuant X Presets)"
      onClose={onClose}
      footer={<Button onClick={onClose}>Close</Button>}
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', minWidth: '680px', maxHeight: '500px', overflowY: 'auto' }}>
        <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--text-muted)' }}>
          Choose a pre-built strategy template to load into the visual rule tree. Each template contains tested logic, parameters, and entry/exit actions.
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '0.75rem' }}>
          {STRATEGY_TEMPLATES.map(tpl => (
            <div
              key={tpl.id}
              style={{
                background: 'var(--bg-card)',
                border: '1px solid var(--border)',
                borderRadius: '6px',
                padding: '1rem',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                gap: '1rem',
              }}
            >
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem', flex: 1 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <strong style={{ fontSize: '1rem' }}>{tpl.name}</strong>
                  <span
                    style={{
                      fontSize: '0.75rem',
                      padding: '2px 8px',
                      borderRadius: '4px',
                      background: 'rgba(56, 189, 248, 0.15)',
                      color: '#38bdf8',
                      fontWeight: 600,
                    }}
                  >
                    {tpl.category}
                  </span>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    {tpl.symbol} · {tpl.timeframe} · {tpl.executionModel}
                  </span>
                </div>

                <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                  {tpl.description}
                </p>

                <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginTop: '0.25rem' }}>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Variables:</span>
                  {tpl.variables.map(v => (
                    <span
                      key={v.name}
                      style={{
                        fontSize: '0.75rem',
                        padding: '1px 6px',
                        borderRadius: '3px',
                        background: 'rgba(255, 255, 255, 0.05)',
                        fontFamily: 'monospace',
                      }}
                    >
                      {v.name}={v.value}
                    </span>
                  ))}
                </div>
              </div>

              <Button
                className="primary"
                onClick={() => {
                  onSelectTemplate(tpl);
                  onClose();
                }}
                style={{ flexShrink: 0 }}
              >
                <Sparkles size={14} /> Load Template
              </Button>
            </div>
          ))}
        </div>
      </div>
    </Modal>
  );
}
