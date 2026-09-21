import React, { useMemo, useState } from 'react';
import { CheckSquare, Filter, RotateCcw, Search, Square, X } from 'lucide-react';
import type { BuildingBlockCategory } from '../../app/types';
import { BUILDING_BLOCKS_CATALOG } from './BuildingBlocksCatalog';
import { Button, TextInput } from '../../components/ui';

interface BuildingBlocksModalProps {
  isOpen: boolean;
  onClose: () => void;
  customBlocks: Record<string, boolean>;
  onChange: (patch: Record<string, boolean>) => void;
}

export const BuildingBlocksModal: React.FC<BuildingBlocksModalProps> = ({
  isOpen,
  onClose,
  customBlocks,
  onChange,
}) => {
  const [selectedCategory, setSelectedCategory] = useState<BuildingBlockCategory>('all');
  const [searchQuery, setSearchQuery] = useState('');

  // Helper to determine whether a block is currently enabled
  const isEnabled = (id: string, defaultEnabled: boolean) => {
    return customBlocks[id] !== undefined ? customBlocks[id] : defaultEnabled;
  };

  const filteredBlocks = useMemo(() => {
    return BUILDING_BLOCKS_CATALOG.filter((b) => {
      const matchCategory = selectedCategory === 'all' || b.category === selectedCategory;
      const matchSearch =
        searchQuery === '' ||
        b.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        b.description.toLowerCase().includes(searchQuery.toLowerCase());
      return matchCategory && matchSearch;
    });
  }, [selectedCategory, searchQuery]);

  const totalSelected = useMemo(() => {
    return BUILDING_BLOCKS_CATALOG.filter((b) => isEnabled(b.id, b.enabled)).length;
  }, [customBlocks]);

  const handleToggle = (id: string, current: boolean) => {
    onChange({ ...customBlocks, [id]: !current });
  };

  const handleSelectAll = () => {
    const patch: Record<string, boolean> = { ...customBlocks };
    filteredBlocks.forEach((b) => {
      patch[b.id] = true;
    });
    onChange(patch);
  };

  const handleDeselectAll = () => {
    const patch: Record<string, boolean> = { ...customBlocks };
    filteredBlocks.forEach((b) => {
      patch[b.id] = false;
    });
    onChange(patch);
  };

  const handleResetDefaults = () => {
    onChange({});
  };

  if (!isOpen) return null;

  return (
    <div className="modal-backdrop" role="dialog" aria-modal="true">
      <div className="modal-window blocks-modal-dialog" style={{ maxWidth: 860, width: '92%', maxHeight: '88vh', display: 'flex', flexDirection: 'column' }}>
        <div className="modal-header">
          <div>
            <h3>Building Blocks Catalog</h3>
            <span className="subtitle">
              Select indicators, conditions, price channels, and exit rules available for strategy evolution
            </span>
          </div>
          <button className="icon-button" onClick={onClose} aria-label="Close dialog">
            <X size={18} />
          </button>
        </div>

        {/* Top Filter and Actions Toolbar */}
        <div style={{ display: 'flex', gap: 10, padding: '12px 18px', borderBottom: '1px solid var(--border)', flexWrap: 'wrap', alignItems: 'center' }}>
          <div style={{ flex: '1 1 240px', position: 'relative' }}>
            <TextInput
              placeholder="Search building blocks…"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{ width: '100%', paddingLeft: 30 }}
            />
            <Search size={14} style={{ position: 'absolute', left: 10, top: 10, color: 'var(--muted)', pointerEvents: 'none' }} />
          </div>

          <div style={{ display: 'flex', gap: 6 }}>
            <Button onClick={handleSelectAll} style={{ padding: '4px 10px', fontSize: '0.82rem' }}>
              <CheckSquare size={13} /> Select All
            </Button>
            <Button onClick={handleDeselectAll} style={{ padding: '4px 10px', fontSize: '0.82rem' }}>
              <Square size={13} /> Deselect All
            </Button>
            <Button onClick={handleResetDefaults} style={{ padding: '4px 10px', fontSize: '0.82rem' }}>
              <RotateCcw size={13} /> Reset Defaults
            </Button>
          </div>

          <span className="badge" style={{ marginLeft: 'auto', background: 'var(--accent-bg)', color: 'var(--accent)', fontWeight: 600 }}>
            {totalSelected} / {BUILDING_BLOCKS_CATALOG.length} enabled
          </span>
        </div>

        {/* Category Filter Pills */}
        <div style={{ display: 'flex', gap: 6, padding: '10px 18px', background: 'var(--bg-card)', borderBottom: '1px solid var(--border)', overflowX: 'auto' }}>
          {(
            [
              { id: 'all', label: 'All Categories' },
              { id: 'signals', label: 'Signals & Conditions' },
              { id: 'indicators', label: 'Indicators' },
              { id: 'candles', label: 'Candlestick Patterns' },
              { id: 'time', label: 'Time & Session' },
              { id: 'orders', label: 'Order Types' },
              { id: 'exits', label: 'Exit Rules' },
            ] as const
          ).map((cat) => {
            const active = selectedCategory === cat.id;
            const count = cat.id === 'all'
              ? BUILDING_BLOCKS_CATALOG.length
              : BUILDING_BLOCKS_CATALOG.filter((x) => x.category === cat.id).length;
            const enabledCount = cat.id === 'all'
              ? totalSelected
              : BUILDING_BLOCKS_CATALOG.filter((x) => x.category === cat.id && isEnabled(x.id, x.enabled)).length;

            return (
              <button
                key={cat.id}
                onClick={() => setSelectedCategory(cat.id)}
                style={{
                  padding: '5px 12px',
                  borderRadius: 14,
                  border: active ? '1px solid var(--accent)' : '1px solid var(--border)',
                  background: active ? 'rgba(48, 183, 232, 0.12)' : 'var(--bg-secondary)',
                  color: active ? 'var(--accent)' : 'var(--text)',
                  fontSize: '0.8rem',
                  cursor: 'pointer',
                  whiteSpace: 'nowrap',
                  fontWeight: active ? 600 : 400,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 5,
                }}
              >
                <span>{cat.label}</span>
                <small style={{ opacity: 0.7 }}>({enabledCount}/{count})</small>
              </button>
            );
          })}
        </div>

        {/* Blocks Catalog Grid */}
        <div style={{ flex: 1, overflowY: 'auto', padding: 18, display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: 12 }}>
          {filteredBlocks.map((block) => {
            const checked = isEnabled(block.id, block.enabled);
            return (
              <label
                key={block.id}
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 6,
                  padding: 12,
                  borderRadius: 6,
                  border: checked ? '1px solid rgba(48, 183, 232, 0.4)' : '1px solid var(--border)',
                  background: checked ? 'rgba(48, 183, 232, 0.04)' : 'var(--bg-card)',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 8 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={() => handleToggle(block.id, checked)}
                      style={{ accentColor: 'var(--accent)', cursor: 'pointer' }}
                    />
                    <strong style={{ fontSize: '0.88rem', color: checked ? 'var(--text)' : 'var(--muted)' }}>
                      {block.name}
                    </strong>
                  </div>
                  <span
                    style={{
                      fontSize: '0.68rem',
                      padding: '2px 6px',
                      borderRadius: 4,
                      background: 'var(--bg-secondary)',
                      color: 'var(--muted)',
                      textTransform: 'uppercase',
                      letterSpacing: '0.5px',
                    }}
                  >
                    {block.category}
                  </span>
                </div>
                <p style={{ margin: 0, fontSize: '0.78rem', color: 'var(--muted)', lineHeight: 1.35 }}>
                  {block.description}
                </p>
                {block.defaultParams && (
                  <div style={{ marginTop: 'auto', paddingTop: 6, borderTop: '1px dashed var(--border)', fontSize: '0.72rem', color: 'var(--muted)' }}>
                    Params: {Object.entries(block.defaultParams).map(([k, v]) => `${k}=${v}`).join(', ')}
                  </div>
                )}
              </label>
            );
          })}
          {filteredBlocks.length === 0 && (
            <div style={{ gridColumn: '1 / -1', textAlign: 'center', padding: '40px 0', color: 'var(--muted)' }}>
              <Filter size={24} style={{ opacity: 0.5, marginBottom: 8 }} />
              <p>No building blocks match your filter criteria.</p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="modal-actions" style={{ borderTop: '1px solid var(--border)', padding: '12px 18px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: '0.8rem', color: 'var(--muted)' }}>
            Changes are stored automatically in strategy research configuration.
          </span>
          <Button className="primary" onClick={onClose}>
            Apply & Close
          </Button>
        </div>
      </div>
    </div>
  );
};
