import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Bug, ChartArea, Grid2X2 } from 'lucide-react';
import { Button, Modal } from '../components/ui';
import { useAppStore } from './store';

export const HEADER_APPLICATION_ACTIONS = [
  { id: 'volume-profile', title: 'Volume & Market Profile Addon' },
  { id: 'debugconsole', title: 'Debug Console' },
  { id: 'gridcontrol', title: 'Grid Control' },
] as const;

export const VOLUME_PROFILE_ACTIONS = ['Learn more', 'Upgrade to Ultimate', 'Pro V&MP monthly subscription', 'Pro V&MP yearly subscription'] as const;

export function HeaderApplicationActions() {
  const module = useAppStore(s => s.module);
  const navigate = useNavigate();
  const [volumeOpen, setVolumeOpen] = useState(false);
  return <>
    <button className="top-action" title="Volume & Market Profile Addon" aria-label="Volume & Market Profile Addon" onClick={() => setVolumeOpen(true)}><ChartArea/></button>
    <button className={`top-action ${module === 'debugconsole' ? 'active' : ''}`} title="Debug Console" aria-label="Debug Console" onClick={() => navigate('/debugconsole')}><Bug/></button>
    <button className={`top-action ${module === 'gridcontrol' ? 'active' : ''}`} title="Grid Control" aria-label="Grid Control" onClick={() => navigate('/gridcontrol')}><Grid2X2/></button>
    {volumeOpen && <VolumeProfileDialog onClose={() => setVolumeOpen(false)}/>}
  </>;
}

function VolumeProfileDialog({ onClose }: { onClose: () => void }) {
  const notify = useAppStore(s => s.notify);
  const unavailable = (label: string) => notify(`${label} is not configured for this HaruQuantAI workspace`);
  return <Modal title="Volume & Market Profile Addon" onClose={onClose} width={650} footer={<Button onClick={onClose}>Close</Button>}>
    <div className="volume-profile-dialog">
      <h3>Volume &amp; Market Profile Addon</h3>
      <p>New HaruQuantAI addon that allows you to use Volume &amp; Market Profile indicators and building blocks.</p>
      <p>Available in HaruQuantAI Ultimate edition or as a paid addon in HaruQuantAI Pro edition.</p>
      <Button onClick={() => unavailable(VOLUME_PROFILE_ACTIONS[0])}>Learn more about Volume &amp; Market Profile in HaruQuantAI</Button>
      <p className="addon-inactive">🔒 <span>You don't have this addon active.</span></p>
      <div className="addon-actions">{VOLUME_PROFILE_ACTIONS.slice(1).map(label => <Button className="primary" key={label} onClick={() => unavailable(label)}>{label}</Button>)}</div>
    </div>
  </Modal>;
}
