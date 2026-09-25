import { useMemo, useState } from 'react';
import { blocksSections, buildingBlocksCatalog, type BlockEntry } from './settingsFixtures';

/**
 * "Building blocks" tab (donor evidence SQX144-EV-000042): the accordion of
 * counted, filterable catalog sections. Catalog entries derive from the
 * donor Build template; Signals / Stop & Limit / Custom data carry labelled
 * demo lists (engine-fed in the donor).
 */
export function BuildingBlocksTab() {
  const [blocks, setBlocks] = useState<BlockEntry[]>(buildingBlocksCatalog);
  const [openSection, setOpenSection] = useState<string>('signals');
  const [filter, setFilter] = useState<{ section: string; key: string }>({ section: '', key: 'None' });

  const toggle = (key: string) =>
    setBlocks(current => current.map(b => (b.key === key ? { ...b, use: !b.use } : b)));

  const selectedCount = (category: BlockEntry['category']) =>
    blocks.filter(b => b.category === category && b.use).length;

  return (
    <div className="settings-blocks sqd-tab-content">
      <div className="sqd-blocks-grids">
        {blocksSections.map(section => {
          const opened = openSection === section.id;
          const entries = blocks.filter(b => b.category === section.category);
          const visible = useMemo(() => {
            if (filter.section === section.id) {
              if (filter.key === 'Checked') return entries.filter(b => b.use);
              if (filter.key === 'Unchecked') return entries.filter(b => !b.use);
            }
            return entries;
          }, [entries, filter, section.id]);
          return (
            <div className={`sqd-blocks-col${section.id === 'signals' || section.id === 'indicators' ? ' left' : ''}`} key={section.id}>
              <button
                type="button"
                className={`sqd-blocks-legend${opened ? ' opened' : ' closed'}`}
                onClick={() => setOpenSection(opened ? '' : section.id)}
                aria-expanded={opened}
              >
                <span className="sqd-blocks-title">{section.title}</span>
                <label className="sqd-blocks-count" onClick={e => e.stopPropagation()}>
                  <span>{selectedCount(section.category)}</span> {section.countLabel}
                </label>
                <div className="sqd-blocks-help">{section.help}</div>
              </button>
              {opened && (
                <>
                  <div className="sqd-blocks-filter">
                    <label>Filter:</label>
                    <button type="button" className="sqd-link-button" onClick={() => setFilter({ section: section.id, key: 'None' })}>Reset</button>
                    <div className="sqd-btn-group">
                      <button
                        type="button"
                        className={`sqd-filter-checked${filter.section === section.id && filter.key === 'Checked' ? ' active' : ''}`}
                        aria-label="Show checked only"
                        onClick={() => setFilter({ section: section.id, key: 'Checked' })}
                      >
                        <input type="checkbox" checked readOnly aria-hidden="true" />
                      </button>
                      {['Checked', 'Unchecked'].map(key => (
                        <button
                          type="button"
                          key={key}
                          className={filter.section === section.id && filter.key === key ? 'active' : ''}
                          onClick={() => setFilter({ section: section.id, key })}
                        >
                          {key}
                        </button>
                      ))}
                    </div>
                  </div>
                  <div className="sqd-blocks-grid" role="list">
                    {visible.map(block => (
                      <label className="sqd-blocks-row" role="listitem" key={block.key}>
                        <input type="checkbox" checked={block.use} onChange={() => toggle(block.key)} />
                        <span className="sqd-blocks-key">{block.key}</span>
                        <span className="sqd-blocks-weight" title="Block weight">{block.weight}</span>
                      </label>
                    ))}
                    {visible.length === 0 && <div className="sqd-blocks-empty">No blocks match the filter</div>}
                  </div>
                </>
              )}
              {section.id !== blocksSections[blocksSections.length - 1].id && <div className="sqd-blocks-sepaline" />}
            </div>
          );
        })}
      </div>
    </div>
  );
}
