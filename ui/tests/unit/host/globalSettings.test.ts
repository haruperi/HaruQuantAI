import { describe, expect, it } from 'vitest';

import {
  applicationLanguages,
  applicationSkins,
  clampZoom,
  configurationTabs,
  createDefaultConfiguration,
  credentialsTabs,
  globalMenuGroups,
  globalMenuLabels,
  isEmail,
  mergeAppSettings,
  safeMcpSettings,
  safeRemoteSettings,
  safeSmtpSettings,
  safeTelegramSettings,
  validateConfiguration,
} from '../../../app/host/globalSettings';

describe('global settings contracts', () => {
  it('matches the audited HaruQuantAI menu groups and configuration tabs', () => {
    expect(globalMenuGroups.flat().map(id => globalMenuLabels[id])).toEqual([
      'Configuration...', 'Credentials...', 'Benchmark...', 'Remote access...', 'MCP Server...', 'Notifications...',
      'Skin', 'Zoom', 'Reload UI', 'Exit',
    ]);
    expect(configurationTabs).toEqual([
      'Global', 'CPU', 'Performance', 'Memory', 'Databanks', 'Optimizations', 'Troubleshooting',
      'Directories', 'Backtest Engine',
    ]);
    expect(credentialsTabs).toEqual([
      'MetaTrader 5', 'cTrader', 'AI Agents',
    ]);
  });

  it('keeps the active languages and skins explicit', () => {
    expect(applicationLanguages).toHaveLength(12);
    expect(applicationLanguages[0]).toBe('English');
    expect(applicationSkins).toEqual(['Dark skin', 'Light skin']);
  });

  it('merges old persisted settings with complete nested defaults', () => {
    const settings = mergeAppSettings({ theme: 'light', workers: 3 } as never);
    expect(settings.theme).toBe('light');
    expect(settings.workers).toBe(3);
    expect(settings.configuration.coreUsage).toBe('reserve-one');
    expect(settings.remoteAccess.allow).toBe(false);
    expect(settings.smtp.port).toBe('587');
  });

  it('drops the legacy persisted collapsed navigation preference', () => {
    const settings = mergeAppSettings({ navigationCollapsed: true });
    expect('navigationCollapsed' in settings).toBe(false);
  });

  it('validates bounded cores, memory, and custom window text', () => {
    const value = createDefaultConfiguration();
    expect(validateConfiguration(value)).toBeNull();
    expect(validateConfiguration({ ...value, customCores: 0 })).toContain('Custom cores');
    expect(validateConfiguration({ ...value, memoryGb: 1 })).toContain('Maximum memory');
    expect(validateConfiguration({ ...value, headerCustomText: 'x'.repeat(31) })).toContain('30');
  });

  it('clamps HaruQuantAI zoom and strips secret drafts', () => {
    expect(clampZoom(0.1)).toBe(0.7);
    expect(clampZoom(1.26)).toBe(1.3);
    expect(clampZoom(2.4)).toBe(1.8);
    expect(safeRemoteSettings({ allow: true, requirePassword: true, password: 'secret' })).toEqual({ allow: true, requirePassword: true }); // pragma: allowlist secret
    expect(safeSmtpSettings({ enabled: true, server: ' smtp.test ', port: ' 587 ', ssl: true, username: ' me ', emailFrom: ' from@test.dev ', password: 'secret' })).toEqual({ enabled: true, server: 'smtp.test', port: '587', ssl: true, username: 'me', emailFrom: 'from@test.dev' }); // pragma: allowlist secret
    expect(safeTelegramSettings({ enabled: true, chatId: ' 12345 ', parseMode: 'HTML', disableNotification: false, botToken: 'secret' })).toEqual({ enabled: true, chatId: '12345', parseMode: 'HTML', disableNotification: false }); // pragma: allowlist secret
    expect(safeMcpSettings({ enabled: true, host: ' 127.0.0.1 ', port: 5055, transport: 'sse', allowedTools: ['backtest'], maxContextItems: 50, authToken: 'secret' })).toEqual({ enabled: true, host: '127.0.0.1', port: 5055, transport: 'sse', allowedTools: ['backtest'], maxContextItems: 50 }); // pragma: allowlist secret
  });

  it('uses a bounded practical email check for the mock SMTP test', () => {
    expect(isEmail('owner@example.test')).toBe(true);
    expect(isEmail('owner')).toBe(false);
  });
});
