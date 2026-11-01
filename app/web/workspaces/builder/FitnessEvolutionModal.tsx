import { SqdModal } from '../../common/project';
export { SqdModal };
export function FitnessEvolutionModal({ onClose }: { onClose: () => void }) {
  return <SqdModal title="Fitness evolution" onClose={onClose} width={860}>
    <p>Island evolution is unavailable for the supported random-generation mode.</p>
    <button className="sqd-btn" onClick={onClose}>Close</button>
  </SqdModal>;
}
