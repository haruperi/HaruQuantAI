import { SqdModal } from '../ProjectWorkbench/ProjectModal';

/** Current generic local configuration/statistics detail preview. */
export function ProjectConfigHelpPopup({ detail, title, stats, onClose, onSettings }: {
  detail: string; title: string; stats: [string, string][];
  onClose: () => void; onSettings: () => void;
}) {
  return <SqdModal title={detail} onClose={onClose}><p>Local {title} preview</p><table className="sqr-data-table"><tbody>{stats.map(([k,v])=><tr key={k}><th>{k}</th><td>{v}</td></tr>)}</tbody></table><button className="sqd-btn" onClick={()=>{onClose();onSettings();}}>Open Full settings</button></SqdModal>;
}
