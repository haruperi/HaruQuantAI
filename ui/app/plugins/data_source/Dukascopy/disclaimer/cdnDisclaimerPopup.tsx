import { Button, Modal } from '../../../../components/ui';
import { CdnDisclaimerPopup } from '../import/cdnDisclaimerPopup';
import { useDisclaimerController } from './dukascopyDataDisclaimerCtrl';

/** Retained distinct donor variant; no new application route is inferred. */
export function DisclaimerCdnDisclaimerPopup({ onClose }: { onClose: () => void }) {
  const { close } = useDisclaimerController(onClose);
  return (
    <Modal
      title="HaruQuantAI CDN Data Disclaimer"
      onClose={close}
      footer={<Button onClick={close}>Close</Button>}
      width={650}
    >
      <CdnDisclaimerPopup />
    </Modal>
  );
}
