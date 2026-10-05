import { Modal } from '../Modal';
import { shortcuts } from '../../hooks/useShortcuts';
export function HelpDialog() {
  return (
    <Modal title="Keyboard shortcuts">
      <div className="cq-shortcuts">
        {shortcuts.map(([key, label]) => (
          <div key={key}>
            <span>{label}</span>
            <kbd>{key}</kbd>
          </div>
        ))}
      </div>
    </Modal>
  );
}
