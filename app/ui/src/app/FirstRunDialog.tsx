/**
 * Disclose backend-reported research setup requirements after host startup.
 * The dialog distinguishes a running host from available research functionality.
 * Dismissing it does not install providers, authorize commands, or persist setup.
 */
import { Button, Modal } from '../components/ui';

/**
 * Display unmet requirements and delegate dismissal to the owning view.
 * @param props.requirements - Backend-provided explanations shown as list entries.
 * @param props.onClose - Called by Continue or the modal's close action.
 * @returns Setup disclosure modal; the parent controls whether it remains mounted.
 */
export function FirstRunDialog({ requirements, onClose }: { requirements: string[]; onClose: () => void }) {
  return <Modal title="Host ready — research setup required" onClose={onClose} footer={<Button onClick={onClose}>Continue</Button>}>
    <p>The host is running. Research actions require compatible installed providers.</p>
    <ul>{requirements.map(requirement => <li key={requirement}>{requirement}</li>)}</ul>
  </Modal>;
}
