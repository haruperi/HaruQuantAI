import React from 'react';
import { useDatabankViewsDialog } from './DatabankViewsCtrl';
import './styles.css';
import {
  ChevronUp,
  ChevronDown,
  Trash2,
  Plus,
  Copy,
  Settings,
  X,
  Search,
  RotateCcw,
} from 'lucide-react';
import { Button, Modal } from '../../../components/ui';
import type { MetricCategory } from '../ProjectDatabanks/databankColumns';

interface ManageViewsDialogProps {
  isOpen: boolean;
  onClose: () => void;
}

const CATEGORIES: MetricCategory[] = [
  'General',
  'Performance',
  'Risk & Drawdown',
  'Trade Counts',
  'Durations & Quality',
  'Visual',
];

export function ManageViewsDialog({ isOpen, onClose }: ManageViewsDialogProps) {
  const { views, setActiveView, resetViews, selectedViewId, newViewName, setNewViewName, cloneViewName, setCloneViewName, showAddColumns, setShowAddColumns, colSearch, setColSearch, selectedCat, setSelectedCat, selectedPropsCol, setSelectedPropsCol, activeView, editedColumns, setEditedColumns, isDirty, setIsDirty, handleSelectView, metricMap, moveColumn, removeColumn, handleCreateView, handleCloneView, handleSave, handleDelete, handleAddColumn, filteredMetrics } = useDatabankViewsDialog();

  if (!isOpen) return null;

  return (
    <Modal
      title="Manage views"
      onClose={onClose}
      footer={
        <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}>
          <Button
            onClick={() => {
              resetViews();
              handleSelectView(views[0].id);
            }}
            title="Reset to factory preset views"
          >
            <RotateCcw size={14} /> Reset all
          </Button>
          <div style={{ display: 'flex', gap: 8 }}>
            <Button
              className="danger"
              disabled={activeView.isDefault}
              onClick={handleDelete}
            >
              <Trash2 size={14} /> Delete this view
            </Button>
            <Button
              className="primary"
              disabled={activeView.isDefault || !isDirty}
              onClick={handleSave}
            >
              Save changes
            </Button>
            <Button
              onClick={() => {
                setActiveView(selectedViewId);
                onClose();
              }}
            >
              Close & Apply
            </Button>
          </div>
        </div>
      }
    >
      <div className="hq-databank-views-editor">
        {/* Top View Selector Bar */}
        <div className="hq-databank-views-selector">
          <div>
            <label style={{ fontSize: 11, fontWeight: 600, color: 'var(--sqx-text-muted)', display: 'block', marginBottom: 4 }}>
              Selected view
            </label>
            <select
              className="text-input"
              style={{ width: '100%' }}
              value={selectedViewId}
              onChange={e => handleSelectView(e.target.value)}
            >
              {views.map(v => (
                <option key={v.id} value={v.id}>
                  {v.name} {v.isDefault ? '(Default)' : ''}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label style={{ fontSize: 11, fontWeight: 600, color: 'var(--sqx-text-muted)', display: 'block', marginBottom: 4 }}>
              Create a new view
            </label>
            <div style={{ display: 'flex', gap: 4 }}>
              <input
                className="text-input"
                style={{ flex: 1 }}
                placeholder="View name"
                value={newViewName}
                onChange={e => setNewViewName(e.target.value)}
              />
              <Button onClick={handleCreateView} disabled={!newViewName.trim()}>
                Create
              </Button>
            </div>
          </div>

          <div>
            <label style={{ fontSize: 11, fontWeight: 600, color: 'var(--sqx-text-muted)', display: 'block', marginBottom: 4 }}>
              Clone current view
            </label>
            <div style={{ display: 'flex', gap: 4 }}>
              <input
                className="text-input"
                style={{ flex: 1 }}
                placeholder="Clone name"
                value={cloneViewName}
                onChange={e => setCloneViewName(e.target.value)}
              />
              <Button onClick={handleCloneView} disabled={!cloneViewName.trim()}>
                <Copy size={13} /> Clone
              </Button>
            </div>
          </div>
        </div>

        {activeView.isDefault && (
          <div
            style={{
              padding: '6px 10px',
              fontSize: 12,
              color: '#f0883e',
              background: 'rgba(240, 136, 62, 0.1)',
              border: '1px solid rgba(240, 136, 62, 0.3)',
              borderRadius: 4,
            }}
          >
            <strong>Note:</strong> Default preset views cannot be edited directly. To customize columns, clone this view first.
          </div>
        )}

        {/* Columns Management Table */}
        <div style={{ display: 'flex', flexDirection: 'column', flex: 1 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
            <span style={{ fontWeight: 600, fontSize: 13 }}>
              Columns in this view ({editedColumns.length})
            </span>
            <Button
              className="primary"
              disabled={activeView.isDefault}
              onClick={() => setShowAddColumns(true)}
            >
              <Plus size={14} /> Add columns
            </Button>
          </div>

          <div
            style={{
              border: '1px solid var(--sqx-fieldset-border)',
              borderRadius: 4,
              overflowY: 'auto',
              maxHeight: 280,
              background: 'var(--surface-color, #12161c)',
            }}
          >
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
              <thead>
                <tr style={{ background: 'var(--sqx-chrome-bg)', textAlign: 'left', borderBottom: '1px solid var(--sqx-fieldset-border)' }}>
                  <th style={{ padding: '6px 10px', width: 40 }}>#</th>
                  <th style={{ padding: '6px 10px' }}>Column name</th>
                  <th style={{ padding: '6px 10px', width: 120 }}>Category</th>
                  <th style={{ padding: '6px 10px', width: 80 }}>Width</th>
                  <th style={{ padding: '6px 10px', width: 120, textAlign: 'center' }}>Reorder / Actions</th>
                </tr>
              </thead>
              <tbody>
                {editedColumns.map((c, idx) => {
                  const metric = metricMap.get(c.columnId);
                  return (
                    <tr
                      key={`${c.columnId}-${idx}`}
                      style={{
                        borderBottom: '1px solid var(--border-subtle, var(--sqx-grid-row-border))',
                        background: idx % 2 === 0 ? 'transparent' : 'rgba(255, 255, 255, 0.01)',
                      }}
                    >
                      <td style={{ padding: '6px 10px', color: 'var(--sqx-text-muted)' }}>{idx + 1}</td>
                      <td style={{ padding: '6px 10px', fontWeight: 500 }}>
                        {metric ? metric.name : c.columnId}
                      </td>
                      <td style={{ padding: '6px 10px', color: 'var(--sqx-text-muted)' }}>
                        {metric?.category || 'General'}
                      </td>
                      <td style={{ padding: '6px 10px' }}>
                        <input
                          type="number"
                          className="text-input"
                          style={{ width: 65, padding: '2px 4px', fontSize: 11 }}
                          disabled={activeView.isDefault}
                          value={c.width || metric?.defaultWidth || 90}
                          onChange={e => {
                            const val = parseInt(e.target.value, 10);
                            if (isNaN(val) || val <= 0) return;
                            const updated = [...editedColumns];
                            updated[idx] = { ...updated[idx], width: val };
                            setEditedColumns(updated);
                            setIsDirty(true);
                          }}
                        />
                      </td>
                      <td style={{ padding: '4px 10px', textAlign: 'center' }}>
                        <div style={{ display: 'inline-flex', gap: 4 }}>
                          <button
                            className="btn btn-sm"
                            disabled={activeView.isDefault || idx === 0}
                            onClick={() => moveColumn(idx, 'up')}
                            title="Move Up"
                            style={{ padding: '2px 6px', background: 'transparent', border: '1px solid var(--sqx-fieldset-border)', borderRadius: 3, cursor: 'pointer', color: 'var(--sqx-text)' }}
                          >
                            <ChevronUp size={12} />
                          </button>
                          <button
                            className="btn btn-sm"
                            disabled={activeView.isDefault || idx === editedColumns.length - 1}
                            onClick={() => moveColumn(idx, 'down')}
                            title="Move Down"
                            style={{ padding: '2px 6px', background: 'transparent', border: '1px solid var(--sqx-fieldset-border)', borderRadius: 3, cursor: 'pointer', color: 'var(--sqx-text)' }}
                          >
                            <ChevronDown size={12} />
                          </button>
                          <button
                            className="btn btn-sm"
                            onClick={() => setSelectedPropsCol(metric || null)}
                            title="Column Properties"
                            style={{ padding: '2px 6px', background: 'transparent', border: '1px solid var(--sqx-fieldset-border)', borderRadius: 3, cursor: 'pointer', color: 'var(--sqx-link)' }}
                          >
                            <Settings size={12} />
                          </button>
                          <button
                            className="btn btn-sm"
                            disabled={activeView.isDefault}
                            onClick={() => removeColumn(idx)}
                            title="Remove Column"
                            style={{ padding: '2px 6px', background: 'transparent', border: '1px solid var(--sqx-fieldset-border)', borderRadius: 3, cursor: 'pointer', color: '#f85149' }}
                          >
                            <Trash2 size={12} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Add Columns Chooser Modal */}
      {showAddColumns && (
        <Modal
          title="Add columns to view"
          onClose={() => setShowAddColumns(false)}
          footer={
            <Button onClick={() => setShowAddColumns(false)} className="primary">
              Done
            </Button>
          }
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12, width: '100%', minWidth: 0, maxHeight: 420 }}>
            <div style={{ display: 'flex', gap: 8 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, flex: 1, border: '1px solid var(--sqx-fieldset-border)', borderRadius: 4, padding: '4px 8px', background: 'var(--sqx-input-bg)' }}>
                <Search size={14} color="var(--sqx-text-muted)" />
                <input
                  type="text"
                  placeholder="Filter 100+ metrics..."
                  value={colSearch}
                  onChange={e => setColSearch(e.target.value)}
                  style={{ background: 'transparent', border: 'none', color: 'inherit', outline: 'none', width: '100%', fontSize: 12 }}
                />
              </div>
              <select
                className="text-input"
                value={selectedCat}
                onChange={e => setSelectedCat(e.target.value as MetricCategory | 'All')}
                style={{ width: 160 }}
              >
                <option value="All">All categories</option>
                {CATEGORIES.map(cat => (
                  <option key={cat} value={cat}>
                    {cat}
                  </option>
                ))}
              </select>
            </div>

            <div
              style={{
                border: '1px solid var(--sqx-fieldset-border)',
                borderRadius: 4,
                overflowY: 'auto',
                maxHeight: 300,
                background: '#12161c',
              }}
            >
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
                <thead>
                  <tr style={{ background: 'var(--sqx-chrome-bg)', textAlign: 'left', borderBottom: '1px solid var(--sqx-fieldset-border)' }}>
                    <th style={{ padding: '6px 10px' }}>Name</th>
                    <th style={{ padding: '6px 10px' }}>Category</th>
                    <th style={{ padding: '6px 10px' }}>Format</th>
                    <th style={{ padding: '6px 10px', textAlign: 'right' }}>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredMetrics.map(metric => {
                    const alreadyAdded = editedColumns.some(c => c.columnId === metric.id);
                    return (
                      <tr
                        key={metric.id}
                        style={{
                          borderBottom: '1px solid var(--sqx-grid-row-border)',
                          background: alreadyAdded ? 'rgba(56, 139, 253, 0.05)' : 'transparent',
                        }}
                      >
                        <td style={{ padding: '6px 10px' }}>
                          <div style={{ fontWeight: 500 }}>{metric.name}</div>
                          <div style={{ fontSize: 10, color: 'var(--sqx-text-muted)' }}>{metric.description}</div>
                        </td>
                        <td style={{ padding: '6px 10px', color: 'var(--sqx-text-muted)' }}>{metric.category}</td>
                        <td style={{ padding: '6px 10px', color: 'var(--sqx-text-muted)' }}>{metric.format}</td>
                        <td style={{ padding: '6px 10px', textAlign: 'right' }}>
                          <Button
                            className={alreadyAdded ? '' : 'primary'}
                            disabled={alreadyAdded}
                            onClick={() => handleAddColumn(metric.id)}
                            style={{ padding: '2px 8px', fontSize: 11 }}
                          >
                            {alreadyAdded ? 'Added' : '+ Add'}
                          </Button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </Modal>
      )}

      {/* Column Properties Modal */}
      {selectedPropsCol && (
        <Modal
          title="Column properties"
          onClose={() => setSelectedPropsCol(null)}
          footer={<Button onClick={() => setSelectedPropsCol(null)}>Close</Button>}
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12, minWidth: 360 }}>
            <div>
              <label style={{ fontSize: 11, color: 'var(--sqx-text-muted)', display: 'block' }}>Column ID</label>
              <div style={{ fontWeight: 600, fontSize: 13, color: 'var(--sqx-link)' }}>{selectedPropsCol.id}</div>
            </div>
            <div>
              <label style={{ fontSize: 11, color: 'var(--sqx-text-muted)', display: 'block' }}>Name</label>
              <div style={{ fontWeight: 600, fontSize: 14 }}>{selectedPropsCol.name}</div>
            </div>
            <div>
              <label style={{ fontSize: 11, color: 'var(--sqx-text-muted)', display: 'block' }}>Category</label>
              <div>{selectedPropsCol.category}</div>
            </div>
            <div>
              <label style={{ fontSize: 11, color: 'var(--sqx-text-muted)', display: 'block' }}>Description</label>
              <div style={{ color: 'var(--sqx-text-muted)', fontSize: 12 }}>{selectedPropsCol.description}</div>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
              <div>
                <label style={{ fontSize: 11, color: 'var(--sqx-text-muted)', display: 'block' }}>Default Width</label>
                <div>{selectedPropsCol.defaultWidth} px</div>
              </div>
              <div>
                <label style={{ fontSize: 11, color: 'var(--sqx-text-muted)', display: 'block' }}>Alignment</label>
                <div style={{ textTransform: 'capitalize' }}>{selectedPropsCol.align}</div>
              </div>
            </div>
          </div>
        </Modal>
      )}
    </Modal>
  );
}
