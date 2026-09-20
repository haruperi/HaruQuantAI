import { Button, Modal } from '../../components/ui';
import { activeExternalLines, type ExternalIndicatorDefinition } from './externalIndicators';
import './externalIndicators.css';

export function ExternalIndicatorViewDialog({ item, onClose }: { item: ExternalIndicatorDefinition; onClose: () => void }) {
  const lines = activeExternalLines(item);
  return <div className="external-flow"><Modal title={`View custom data for '${item.name}'`} width={800} onClose={onClose} footer={<Button onClick={onClose}>Close</Button>}><div className="external-view-grid"><table className="plain-table" aria-label={`Data for ${item.name}`}><thead><tr><th>Date</th>{lines.map((_, index) => <th key={index}>Value {index + 1}</th>)}</tr></thead><tbody>{item.records.map(row => <tr key={row.timestamp}><td>{new Date(row.timestamp).toISOString().replace('T', ' ').slice(0, 16)}</td>{row.values.map((value, index) => <td key={index}>{value}</td>)}</tr>)}</tbody></table></div></Modal></div>;
}
