import { memo } from 'react';
import { PortfolioComposition } from './PortfolioComposition';
import { PortfolioConfiguration } from './PortfolioConfiguration';
import type { ComposerDraft, ComposerMember } from './composerModel';

export interface PortfolioComposerProps {
  draft: ComposerDraft;
  onMembersChange: (members: ComposerMember[]) => void;
  onConfigChange: (config: ComposerDraft['config']) => void;
  onLoad: () => void;
  onSave: () => void;
  onSavePortfolio: () => void;
  onDelete: () => void;
  onClear: () => void;
  onBuyHold: () => void;
  canSavePortfolio: boolean;
}

export const PortfolioComposer = memo(function PortfolioComposer({
  draft,
  onMembersChange,
  onConfigChange,
  onLoad,
  onSave,
  onSavePortfolio,
  onDelete,
  onClear,
  onBuyHold,
  canSavePortfolio,
}: PortfolioComposerProps) {
  return (
    <div className="pf-composer-container">
      <PortfolioComposition
        members={draft.members}
        onChange={onMembersChange}
        onLoad={onLoad}
        onSave={onSave}
        onSavePortfolio={onSavePortfolio}
        onDelete={onDelete}
        onClear={onClear}
        onBuyHold={onBuyHold}
        canSavePortfolio={canSavePortfolio}
      />
      <PortfolioConfiguration
        config={draft.config}
        members={draft.members}
        onChange={onConfigChange}
      />
    </div>
  );
});
