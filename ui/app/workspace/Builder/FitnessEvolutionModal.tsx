import { useProjectWorkbench } from './documents';
import { fitnessIslands } from './fixtures';

/**
 * SQX-parity modal shell and the donor "Fitness evolution" popup
 * (donor evidence SQX144-EV-000034). Escape and backdrop click close it,
 * matching the donor modal behavior.
 */


export function SqdModal(props: import('react').ComponentProps<import('./documents').WorkbenchPorts['SqdModal']>) {const View=useProjectWorkbench().SqdModal;return <View {...props}/>;}
function LinkClose({ onClose }: { onClose: () => void }) {
  return (
    <button type="button" className="sqd-modal-close-link" onClick={onClose}>
      Close
    </button>
  );
}

/**
 * Fitness evolution popup: the island generation/population table plus the
 * "Fitness charts for:" island selector. Chart bodies are demo placeholders;
 * the donor renders live engine fitness charts.
 */
export function FitnessEvolutionModal({ onClose }: { onClose: () => void }) {
const { SqdModal } = useProjectWorkbench();

  return (
    <SqdModal title="Fitness evolution" onClose={onClose} width={860}>
      <div className="sqd-fitness-table" aria-label="Island generations">
        <div>
          <span>Island</span>
          <span>Generation</span>
          <span>Population</span>
        </div>
        {fitnessIslands.map((island, i) => (
          <div key={i}>
            <span>#{i + 1}</span>
            <span>{island.generation}</span>
            <span>{island.population}</span>
          </div>
        ))}
      </div>
      <div className="sqd-fitness-charts-for">
        <label className="sqd-label">Fitness charts for:</label>
        <div className="sqd-btn-group">
          {fitnessIslands.map((_, i) => (
            <button key={i} type="button" className={i === 0 ? 'active' : ''}>
              Isl.{i + 1}
            </button>
          ))}
          <button type="button">Databank</button>
        </div>
      </div>
      <div className="sqd-fitness-charts">
        {[0, 1, 2].map(i => (
          <div key={i} className="sqd-fitness-chart-slot" aria-label="Fitness chart placeholder" />
        ))}
      </div>
      <footer className="sqd-modal-footer-links">
        <LinkClose onClose={onClose} />
      </footer>
    </SqdModal>
  );
}
