import { useState } from 'react';
import { Check, Search } from 'lucide-react';
import { useAppStore } from '../../app/store';
import { Button, Modal } from '../../components/ui';

interface Props {
  onClose: () => void;
  onAdd: (strategyIds: string[]) => void;
  existingIds: string[];
}

export function PortfolioCandidatesModal({ onClose, onAdd, existingIds }: Props) {
  const store = useAppStore();
  const [selectedBank, setSelectedBank] = useState('all');
  const [query, setQuery] = useState('');
  const [selectedIds, setSelectedIds] = useState<string[]>([]);

  const filteredStrategies = store.strategies.filter(s => {
    if (selectedBank !== 'all' && s.bankId !== selectedBank) return false;
    if (query) {
      const q = query.toLowerCase();
      return s.name.toLowerCase().includes(q) || s.symbol.toLowerCase().includes(q);
    }
    return true;
  });

  const toggleSelect = (id: string) => {
    if (selectedIds.includes(id)) {
      setSelectedIds(selectedIds.filter(x => x !== id));
    } else {
      setSelectedIds([...selectedIds, id]);
    }
  };

  const handleSelectAll = () => {
    const unadded = filteredStrategies.filter(s => !existingIds.includes(s.id)).map(s => s.id);
    if (selectedIds.length === unadded.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(unadded);
    }
  };

  const handleConfirm = () => {
    onAdd(selectedIds);
    onClose();
  };

  return (
    <Modal
      title="Add Candidate Strategies to Portfolio"
      onClose={onClose}
      footer={
        <>
          <Button onClick={onClose}>Cancel</Button>
          <Button className="primary" disabled={selectedIds.length === 0} onClick={handleConfirm}>
            <Check size={14} /> Add {selectedIds.length} Selected
          </Button>
        </>
      }
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', minWidth: '600px' }}>
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <select
            className="text-input"
            style={{ width: '180px' }}
            value={selectedBank}
            onChange={e => setSelectedBank(e.target.value)}
          >
            <option value="all">All Databanks</option>
            {store.databanks.map(b => (
              <option key={b.id} value={b.id}>{b.name}</option>
            ))}
          </select>
          <div style={{ position: 'relative', flex: 1 }}>
            <Search size={14} style={{ position: 'absolute', left: '8px', top: '9px', opacity: 0.5 }} />
            <input
              type="text"
              className="text-input"
              placeholder="Search strategy or symbol..."
              value={query}
              onChange={e => setQuery(e.target.value)}
              style={{ paddingLeft: '28px', width: '100%' }}
            />
          </div>
          <Button onClick={handleSelectAll}>Toggle All</Button>
        </div>

        <div style={{ maxHeight: '340px', overflowY: 'auto', border: '1px solid var(--border)', borderRadius: '4px' }}>
          <table className="plain-table" style={{ width: '100%', fontSize: '0.85rem' }}>
            <thead>
              <tr>
                <th style={{ width: '36px' }}></th>
                <th>Strategy</th>
                <th>Symbol</th>
                <th>TF</th>
                <th>Net Profit</th>
                <th>Profit Factor</th>
                <th>Max DD</th>
                <th>Sharpe</th>
              </tr>
            </thead>
            <tbody>
              {filteredStrategies.map(s => {
                const alreadyAdded = existingIds.includes(s.id);
                const checked = selectedIds.includes(s.id);
                return (
                  <tr
                    key={s.id}
                    style={{
                      opacity: alreadyAdded ? 0.45 : 1,
                      cursor: alreadyAdded ? 'default' : 'pointer',
                      background: checked ? 'rgba(56, 189, 248, 0.08)' : undefined,
                    }}
                    onClick={() => !alreadyAdded && toggleSelect(s.id)}
                  >
                    <td>
                      <input
                        type="checkbox"
                        checked={checked}
                        disabled={alreadyAdded}
                        onChange={() => !alreadyAdded && toggleSelect(s.id)}
                      />
                    </td>
                    <td>
                      <strong>{s.name}</strong>
                      {alreadyAdded && <span style={{ marginLeft: '6px', fontSize: '0.75rem', opacity: 0.7 }}>(In portfolio)</span>}
                    </td>
                    <td>{s.symbol}</td>
                    <td>{s.timeframe}</td>
                    <td className="positive">${s.metrics.netProfit.toLocaleString()}</td>
                    <td>{s.metrics.profitFactor.toFixed(2)}</td>
                    <td className="negative">${s.metrics.maxDrawdown.toLocaleString()}</td>
                    <td>{s.metrics.sharpe.toFixed(2)}</td>
                  </tr>
                );
              })}
              {filteredStrategies.length === 0 && (
                <tr>
                  <td colSpan={8} style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                    No matching candidate strategies found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </Modal>
  );
}
