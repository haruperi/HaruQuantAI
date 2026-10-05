/**
 * Dukascopy & StrategyQuant CDN Data Legal Disclaimers.
 *
 * 1:1 Parity with SQX Build 144:
 * C:\SQX\internal\plugins\DataSourceDukascopy\disclaimer (disclaimerPopup.html, cdnDisclaimerPopup.html).
 */
import { useEffect, useRef, useState } from 'react';
import { Button } from '../../../components/ui';

export function DukascopyDisclaimerDialog({
  open = true,
  onClose,
}: {
  open?: boolean;
  onClose: () => void;
}) {
  const [activeTab, setActiveTab] = useState<'dukascopy' | 'cdn'>('dukascopy');
  const root = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const previous = document.activeElement as HTMLElement | null;
    root.current?.querySelector<HTMLButtonElement>('button')?.focus();
    return () => previous?.focus();
  }, [open]);

  if (!open) return null;

  return (
    <div className="modal-backdrop dukas-download-overlay">
      <div
        ref={root}
        className="modal dukas-download-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="dukas-disclaimer-title"
        style={{ maxWidth: '640px', width: '90%' }}
        onKeyDown={(event) => {
          if (event.key === 'Escape') {
            event.stopPropagation();
            onClose();
          }
        }}
      >
        <div className="modal-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border-color, #333)', paddingBottom: '12px', marginBottom: '16px' }}>
          <h3 id="dukas-disclaimer-title" style={{ margin: 0, fontSize: '1.15rem', fontWeight: 600 }}>
            {activeTab === 'dukascopy' ? 'Dukascopy Data Disclaimer' : 'StrategyQuant CDN Data Disclaimer'}
          </h3>
          <button
            type="button"
            className="close-button"
            onClick={onClose}
            aria-label="Close"
            style={{ background: 'none', border: 'none', color: 'inherit', fontSize: '1.25rem', cursor: 'pointer' }}
          >
            &times;
          </button>
        </div>

        <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
          <Button
            className={activeTab === 'dukascopy' ? 'primary' : 'secondary'}
            onClick={() => setActiveTab('dukascopy')}
          >
            Dukascopy Bank SA
          </Button>
          <Button
            className={activeTab === 'cdn' ? 'primary' : 'secondary'}
            onClick={() => setActiveTab('cdn')}
          >
            StrategyQuant CDN
          </Button>
        </div>

        <div className="modal-body" style={{ maxHeight: '380px', overflowY: 'auto', lineHeight: '1.5', fontSize: '0.9rem', color: 'var(--text-secondary, #ccc)' }}>
          {activeTab === 'dukascopy' ? (
            <div className="disclaimer-content">
              <h4 style={{ color: 'var(--text-primary, #fff)', marginTop: 0 }}>Disclaimer</h4>
              <p>
                The Dukascopy Trading Tools include different financial information. Such data are a result
                of original and unique methods and technology of information gathering, compilation,
                analysis and statistical evaluation developed by Dukascopy Bank SA. Therefore, such data
                reflect the current fair value of the respective financial instruments as independently
                assessed by Dukascopy Bank SA and NOT the actual values at a given point in time. If you are
                looking to obtain actual quotes please contact the respective entities that provide this
                information.
              </p>
              <p>
                The Dukascopy Trading Tools data and/or any other data available as free product from
                Dukascopy Bank's website shall not constitute a forecast of the market value of any
                instruments at any future point either, and is not an investment advice or recommendation in
                any form.
              </p>
              <p>
                Anyone using and/or putting free web products including all or parts of the information taken
                from the Dukascopy Trading Tools and/or any other data available as free product from
                Dukascopy Bank's website shall put a clear note to the public that such data are not meant
                to indicate the actual value at any given point in time but represent a discretionary
                assessment by Dukascopy Bank SA only.
              </p>
              <p>
                The market data assessment system is in constant development and is provided &quot;AS IS&quot;, &quot;AS
                AVAILABLE&quot;, &quot;WITH ALL ITS FAULTS&quot; and is offered without any covenants or any express,
                implied or statutory warranties including (without limitation and qualification) any
                warranties as to accuracy, functionality, performance, merchantability, quiet enjoyment,
                system integration, data accuracy or fitness for any particular purpose and any warranties
                arising from trade usage, course of dealing or course of performance.
              </p>
            </div>
          ) : (
            <div className="disclaimer-content">
              <h4 style={{ color: 'var(--text-primary, #fff)', marginTop: 0 }}>StrategyQuant CDN Data Disclaimer</h4>
              <p>
                In order to provide faster downloads for its clients StrategyQuant offers pre-packaged
                Dukascopy data for some of the symbols on its own CDN servers.
              </p>
              <p>
                The data available on SQ CDN were created from original Dukascopy data obtained from
                Dukascopy website. StrategyQuant does not guarantee that the data prepared on its CDN servers
                exactly match Dukascopy data.
              </p>
              <p>
                The data are provided &quot;AS IS&quot;, &quot;AS AVAILABLE&quot;, &quot;WITH ALL ITS FAULTS&quot; and is offered
                without any covenants or any express, implied or statutory warranties including (without
                limitation and qualification) any warranties as to accuracy, functionality, performance,
                merchantability, quiet enjoyment, system integration, data accuracy or fitness for any
                particular purpose and any warranties arising from trade usage, course of dealing or course
                of performance.
              </p>
            </div>
          )}
        </div>

        <div className="modal-footer" style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '20px', paddingTop: '12px', borderTop: '1px solid var(--border-color, #333)' }}>
          <Button className="primary" onClick={onClose}>
            Close
          </Button>
        </div>
      </div>
    </div>
  );
}

export default DukascopyDisclaimerDialog;
