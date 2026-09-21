import { useMemo, useState } from 'react';
import { Button, Modal } from '../../../../components/ui';
import { parseStockGroupsJson, stockGroupLimits, type StockGroupDefinition } from './stockGroups';
import { useStockGroups } from './stockGroupsStore';
import './stockGroups.css';

export function StockGroupTransferDialog({ onClose, onSaved }: { onClose: () => void; onSaved: (message: string) => void }) {
  const existing = useStockGroups(state => state.groups); const [items, setItems] = useState<StockGroupDefinition[]>([]); const [index, setIndex] = useState(0); const [decisions, setDecisions] = useState<Record<string, 'skip'|'overwrite'>>({}); const [filename, setFilename] = useState(''); const [error, setError] = useState('');
  const conflicts = useMemo(() => items.filter(item => existing.some(row => row.name.toLowerCase() === item.name.toLowerCase())), [items, existing]); const conflict = conflicts[index];
  const read = async (file?: File) => { if (!file) return; try { if (!/\.json$/i.test(file.name)) throw new Error('Choose a Groups JSON file.'); if (file.size > stockGroupLimits.json) throw new Error('Groups file is invalid or too large.'); const parsed = parseStockGroupsJson(await file.text()); setFilename(file.name); setItems(parsed); setIndex(0); setDecisions({}); setError(''); } catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to load groups.'); setItems([]); } };
  const decide = (decision: 'skip'|'overwrite') => { if (!conflict) return; setDecisions(current => ({ ...current, [conflict.name]: decision })); setIndex(value => value + 1); };
  const apply = () => { try { useStockGroups.getState().applyImported(items, decisions); onSaved(`Groups (${items.filter(item => decisions[item.name] !== 'skip').length}) loaded.`); onClose(); } catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to load groups.'); } };
  const unresolved = Boolean(conflict);
  return <div className="stock-groups-flow"><Modal title="Load groups" width={620} onClose={onClose} footer={<><Button onClick={onClose}>Close</Button><Button className="primary" disabled={!items.length || unresolved} onClick={apply}>Load</Button></>}>
    {error && <p className="stock-group-error" role="alert">{error}</p>}
    <label className="stock-group-file"><span>Groups JSON file</span><input aria-label="Groups JSON file" type="file" accept=".json,application/json" onChange={event => void read(event.target.files?.[0])}/></label>
    <p>{filename ? `${filename} — ${items.length} group${items.length === 1 ? '' : 's'} found` : 'Choose Groups.json to import.'}</p>
  </Modal>{unresolved && <Modal title="Overwrite confirm" width={540} onClose={onClose} footer={<><Button onClick={onClose}>Cancel</Button><Button onClick={() => decide('skip')}>Skip</Button><Button className="primary" disabled={existing.find(item => item.name.toLowerCase() === conflict.name.toLowerCase())?.system} onClick={() => decide('overwrite')}>Overwrite</Button></>}><p>Group '{conflict.name}' already exists, do you want to overwrite it with the imported one?</p></Modal>}</div>;
}
