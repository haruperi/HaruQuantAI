import { useState } from 'react';
import { AlertOctagon, Flame, ShieldAlert, XCircle } from 'lucide-react';
import { Button, Modal } from '../../../common/components/ui';
import { useTradingStore } from '../tradingStore';

export function EmergencyControls() {
  const store = useTradingStore();
  const [confirmFlattenOpen, setConfirmFlattenOpen] = useState(false);
  const [confirmCancelOpen, setConfirmCancelOpen] = useState(false);

  const handleFlatten = () => {
    store.closeAllPositions();
    setConfirmFlattenOpen(false);
  };

  const handleCancelAll = () => {
    store.cancelAllOrders();
    setConfirmCancelOpen(false);
  };

  const handleKillSwitch = () => {
    store.executeEmergencyKillSwitch();
    store.setKillSwitchModalOpen(false);
  };

  return (
    <div className="flex flex-wrap items-center gap-2">
      {/* Flatten All Button */}
      <Button
        onClick={() => setConfirmFlattenOpen(true)}
        className="danger gap-1.5"
      >
        <Flame className="w-4 h-4" />
        Flatten All ({store.positions.length})
      </Button>

      {/* Cancel All Orders Button */}
      <Button
        onClick={() => setConfirmCancelOpen(true)}
        className="secondary gap-1.5 text-warning border-warning/30 hover:bg-warning/10"
      >
        <XCircle className="w-4 h-4" />
        Cancel All Orders ({store.pendingOrders.length})
      </Button>

      {/* Full Kill Switch Trigger */}
      <Button
        onClick={() => store.setKillSwitchModalOpen(true)}
        className="danger gap-1.5 bg-red-700 hover:bg-red-800 text-white font-bold"
      >
        <ShieldAlert className="w-4 h-4" />
        Emergency Kill Switch
      </Button>

      {/* Confirm Flatten Modal */}
      {confirmFlattenOpen && (
        <Modal
          title="Confirm Emergency Flatten"
          onClose={() => setConfirmFlattenOpen(false)}
        >
          <div className="space-y-4">
            <div className="flex items-center gap-3 p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400">
              <AlertOctagon className="w-6 h-6 shrink-0" />
              <p className="text-sm">
                Are you sure you want to immediately close all <strong>{store.positions.length}</strong> active
                market positions at market price?
              </p>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button onClick={() => setConfirmFlattenOpen(false)}>
                Cancel
              </Button>
              <Button className="danger" onClick={handleFlatten}>
                Yes, Flatten All
              </Button>
            </div>
          </div>
        </Modal>
      )}

      {/* Confirm Cancel All Modal */}
      {confirmCancelOpen && (
        <Modal
          title="Confirm Cancel All Orders"
          onClose={() => setConfirmCancelOpen(false)}
        >
          <div className="space-y-4">
            <p className="text-sm text-text-muted">
              Are you sure you want to cancel all <strong>{store.pendingOrders.length}</strong> working
              pending orders?
            </p>
            <div className="flex justify-end gap-2 pt-2">
              <Button onClick={() => setConfirmCancelOpen(false)}>
                Back
              </Button>
              <Button className="danger" onClick={handleCancelAll}>
                Cancel All Working Orders
              </Button>
            </div>
          </div>
        </Modal>
      )}

      {/* Full Kill Switch Modal */}
      {store.killSwitchModalOpen && (
        <Modal
          title="EMERGENCY SYSTEM KILL SWITCH"
          onClose={() => store.setKillSwitchModalOpen(false)}
        >
          <div className="space-y-4">
            <div className="flex items-center gap-3 p-4 bg-red-600/20 border border-red-500 rounded-lg text-red-300">
              <ShieldAlert className="w-8 h-8 shrink-0 text-red-500" />
              <div className="text-xs space-y-1">
                <p className="font-bold text-sm text-red-200">IRREVERSIBLE ACTION</p>
                <p>1. Pauses all active algorithmic strategies.</p>
                <p>2. Immediately market-closes all {store.positions.length} open positions.</p>
                <p>3. Cancels all {store.pendingOrders.length} pending orders.</p>
                <p>4. Disarms live execution on all connected broker terminals.</p>
              </div>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button onClick={() => store.setKillSwitchModalOpen(false)}>
                Abort
              </Button>
              <Button onClick={handleKillSwitch} className="danger bg-red-700 hover:bg-red-800 font-bold">
                ENGAGE KILL SWITCH
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}
