import { Button } from '../../../../components/ui';
import { DarwinexModal } from '../add/addPopup';
import { useDarwinexDisclaimer } from './darwinexDisclaimerCtrl';

export function DarwinexConsent({ agreed, setAgreed }: { agreed: boolean; setAgreed: (value: boolean) => void }) {
  return <label className="darwinex-consent"><input type="checkbox" checked={agreed} onChange={event => setAgreed(event.target.checked)}/> I confirm that I understand the following: Data are provided for free by Darwinex. HaruQuantAI Data Manager is only a tool to download the data directly to the program. HaruQuantAI is not responsible for quality or availability of the data.</label>;
}

/** Exported unmounted composition of retained target consent, not donor legal text. */
export function DarwinexDisclaimerPopup({ agreed, setAgreed, onClose }: { agreed: boolean; setAgreed: (value: boolean) => void; onClose: () => void }) {
  const close = useDarwinexDisclaimer(onClose);
  return <DarwinexModal title="Darwinex data disclaimer" onClose={close} footer={<Button onClick={close}>Close</Button>}><DarwinexConsent agreed={agreed} setAgreed={setAgreed}/></DarwinexModal>;
}
