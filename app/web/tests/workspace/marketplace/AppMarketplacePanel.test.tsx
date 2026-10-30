import React from 'react';
import { renderToString } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import {
  MarketplaceWorkspace,
  type InstallResult,
  type InstallState,
  type ShareTreeNodeItem,
} from '../../../workspaces/marketplace/MarketplaceWorkspace';

describe('MarketplaceWorkspace Component', () => {
  it('renders marketplace workspace iframe with normalized locale query', () => {
    const html = renderToString(<MarketplaceWorkspace initialLocale="cz" />);

    expect(html).toContain('data-testid="marketplace-workspace"');
    expect(html).toContain('data-testid="marketplace-iframe"');
    expect(html).toContain('id="marketplace-iframe"');
    expect(html).toContain('lang=cs');
  });

  it('defaults missing or null locale to en in iframe query', () => {
    const html = renderToString(<MarketplaceWorkspace initialLocale={null} />);

    expect(html).toContain('lang=en');
  });

  it('renders installation progress overlay during downloading phase', () => {
    const downloadState: InstallState = {
      title: 'Awesome Indicators',
      status: 'downloading',
      progress: 65,
    };

    const html = renderToString(
      <MarketplaceWorkspace installState={downloadState} />,
    );

    expect(html).toContain('data-testid="marketplace-install-overlay"');
    expect(html).toContain('Awesome Indicators');
    expect(html).toContain('data-testid="marketplace-install-progress-bar"');
    expect(html).toContain('width:65%');
    expect(html).toContain('Downloading… 65%');
  });

  it('renders verifying and installing phases with indeterminate bar', () => {
    const verifyState: InstallState = {
      title: 'Awesome Indicators',
      status: 'verifying',
    };
    const htmlVerify = renderToString(
      <MarketplaceWorkspace installState={verifyState} />,
    );
    expect(htmlVerify).toContain('Verifying package…');
    expect(htmlVerify).toContain('indeterminate');

    const installState: InstallState = {
      title: 'Awesome Indicators',
      status: 'installing',
    };
    const htmlInstall = renderToString(
      <MarketplaceWorkspace installState={installState} />,
    );
    expect(htmlInstall).toContain('Installing files…');
    expect(htmlInstall).toContain('indeterminate');
  });

  it('renders install result modal with unpacked location, file counts, and restart alert', () => {
    const result: InstallResult = {
      title: 'Super Strategy Pack',
      installDir: 'C:/HaruQuant/user',
      installedFiles: ['strategies/StratA.java', 'strategies/StratB.java'],
      skippedFiles: [
        { name: 'indicators/Builtin.java', reason: 'already exists in Builtin' },
      ],
      restartRequired: true,
    };

    const html = renderToString(
      <MarketplaceWorkspace installResult={result} />,
    );

    expect(html).toContain('data-testid="marketplace-install-result-popup"');
    expect(html).toContain('Installation complete');
    expect(html).toContain('Super Strategy Pack');
    expect(html).toContain('was installed successfully.');
    expect(html).toContain('data-testid="marketplace-install-result-dir"');
    expect(html).toContain('C:/HaruQuant/user');
    expect(html).toContain('data-testid="marketplace-install-result-files"');
    expect(html).toContain('strategies/StratA.java');
    expect(html).toContain('data-testid="marketplace-install-result-skipped"');
    expect(html).toContain('already exists in Builtin');
    expect(html).toContain('data-testid="marketplace-install-result-restart"');
    expect(html).toContain('Restart StrategyQuant X to activate the installed plugin.');
    expect(html).toContain('data-testid="marketplace-install-result-ok"');
  });

  it('renders uninstall confirmation modal with prompt and action buttons', () => {
    const html = renderToString(
      <MarketplaceWorkspace uninstallTarget="plugin-xyz" />,
    );

    expect(html).toContain('data-testid="marketplace-uninstall-confirm-popup"');
    expect(html).toContain('Uninstall extension');
    expect(html).toContain('Are you sure you want to uninstall this extension?');
    expect(html).toContain('data-testid="marketplace-uninstall-confirm-cancel"');
    expect(html).toContain('data-testid="marketplace-uninstall-confirm-ok"');
  });

  it('renders share popup with form fields, file tree, and excluded directories notice', () => {
    const sampleTree: ShareTreeNodeItem[] = [
      {
        id: 1,
        text: 'indicators',
        isDir: true,
        item: [
          { id: 2, text: 'CustomRSI.java', isDir: false },
          { id: 3, text: 'CustomMACD.java', isDir: false },
        ],
      },
      {
        id: 4,
        text: 'notes.txt',
        isDir: false,
      },
    ];

    const html = renderToString(
      <MarketplaceWorkspace
        isShareOpen={true}
        shareTree={sampleTree}
        excludedDirs={['settings', 'logs']}
      />,
    );

    expect(html).toContain('data-testid="marketplace-share-popup"');
    expect(html).toContain('Share a product');
    expect(html).toContain('data-testid="marketplace-share-title"');
    expect(html).toContain('data-testid="marketplace-share-description"');
    expect(html).toContain('data-testid="marketplace-share-details"');
    expect(html).toContain('data-testid="marketplace-share-category"');
    expect(html).toContain('data-testid="marketplace-share-version"');
    expect(html).toContain('data-testid="marketplace-share-author"');
    expect(html).toContain('data-testid="marketplace-share-filter"');
    expect(html).toContain('data-testid="marketplace-share-tree"');
    expect(html).toContain('CustomRSI.java');
    expect(html).toContain('CustomMACD.java');
    expect(html).toContain('data-testid="marketplace-share-excluded"');
    expect(html).toContain('settings, logs');
    expect(html).toContain('data-testid="marketplace-share-cancel"');
    expect(html).toContain('data-testid="marketplace-share-submit"');
  });
});
