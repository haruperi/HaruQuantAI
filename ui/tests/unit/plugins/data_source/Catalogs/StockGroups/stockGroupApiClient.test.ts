import { describe, expect, it, vi } from 'vitest';
import {
  deleteStockGroup,
  exportStockGroupCsv,
  exportStockGroupsXml,
  fetchStockGroups,
  fetchStockGroupsOverview,
  getStockGroup,
  importStockGroupCsv,
  importStockGroupsXml,
  saveStockGroup,
  setStockGroupApiClient,
  toRemoteBasketPayload,
  toStockGroupDefinition,
  updateStockGroupsData,
  type RemoteBasketRecord,
} from '../../../../../../app/plugins/data_source/Catalogs/StockGroups/stockGroupApiClient';
import type { StockGroupDefinition } from '../../../../../../app/plugins/data_source/Catalogs/StockGroups/stockGroups';

describe('stockGroupApiClient', () => {
  it('maps between RemoteBasketRecord and StockGroupDefinition', () => {
    const remote: RemoteBasketRecord = {
      id: 42,
      name: '[Nasdaq 100]',
      description: 'Tech leaders',
      system: false,
      items: [
        { symbol: 'AAPL', date_from: '2010-01-01', date_to: '2025-01-01' },
        { symbol: 'MSFT', date_from: null, date_to: null },
      ],
    };

    const domain = toStockGroupDefinition(remote);
    expect(domain.id).toBe('42');
    expect(domain.name).toBe('[Nasdaq 100]');
    expect(domain.members).toEqual([
      { ticker: 'AAPL', from: '2010-01-01', to: '2025-01-01' },
      { ticker: 'MSFT', from: undefined, to: undefined },
    ]);

    const payload = toRemoteBasketPayload(domain);
    expect(payload.id).toBe(42);
    expect(payload.name).toBe('[Nasdaq 100]');
    expect(payload.items[0]).toEqual({
      symbol: 'AAPL',
      weight: 1.0,
      date_from: '2010-01-01',
      date_to: '2025-01-01',
    });
  });

  it('performs REST operations through configured DomainClient', async () => {
    const mockGet = vi.fn();
    const mockPost = vi.fn();
    const mockPut = vi.fn();
    const mockDelete = vi.fn();

    const mockClient = {
      get: mockGet,
      post: mockPost,
      put: mockPut,
      delete: mockDelete,
    };
    setStockGroupApiClient(mockClient);

    // 1. fetchStockGroups
    mockGet.mockResolvedValueOnce([
      { id: 1, name: '[[Dow Jones]]', description: 'DJIA', system: true, items: [{ symbol: 'AAPL' }] },
    ]);
    const groups = await fetchStockGroups();
    expect(groups).toHaveLength(1);
    expect(mockGet).toHaveBeenCalledWith('/baskets');

    // 2. fetchStockGroupsOverview
    mockGet.mockResolvedValueOnce([
      { id: 1, name: '[[Dow Jones]]', active_count: 30, total_count: 30, is_ready: true },
    ]);
    const overview = await fetchStockGroupsOverview();
    expect(overview[0].is_ready).toBe(true);
    expect(mockGet).toHaveBeenCalledWith('/baskets/overview');

    // 3. getStockGroup
    mockGet.mockResolvedValueOnce({
      id: 2,
      name: '[Russell 2000]',
      description: 'Small caps',
      system: false,
      items: [],
    });
    const group = await getStockGroup('[Russell 2000]');
    expect(group.name).toBe('[Russell 2000]');
    expect(mockGet).toHaveBeenCalledWith('/baskets/%5BRussell%202000%5D');

    // 4. saveStockGroup
    mockPost.mockResolvedValueOnce({});
    const sampleGroup: StockGroupDefinition = {
      id: '10',
      name: '[Test]',
      description: 'Desc',
      system: false,
      members: [{ ticker: 'TSLA' }],
    };
    await saveStockGroup(sampleGroup);
    expect(mockPost).toHaveBeenCalledWith('/baskets', expect.objectContaining({ name: '[Test]' }));

    // 5. deleteStockGroup
    mockDelete.mockResolvedValueOnce({});
    await deleteStockGroup('[Test]');
    expect(mockDelete).toHaveBeenCalledWith('/baskets/%5BTest%5D');

    // 6. updateStockGroupsData
    mockPost.mockResolvedValueOnce([
      { group_id: 1, group_name: '[Test]', status: 'started', total_stocks: 1 },
    ]);
    const updateRes = await updateStockGroupsData([1]);
    expect(updateRes[0].status).toBe('started');
    expect(mockPost).toHaveBeenCalledWith('/baskets/update-data', { basket_ids: [1] });

    // 7. exportStockGroupsXml
    mockPost.mockResolvedValueOnce({ xml_content: '<Groups><Group name="[Test]"/></Groups>' });
    const xml = await exportStockGroupsXml(['[Test]']);
    expect(xml).toContain('<Groups>');
    expect(mockPost).toHaveBeenCalledWith('/baskets/export-xml', { basket_names: ['[Test]'] });

    // 8. importStockGroupsXml
    mockPost.mockResolvedValueOnce([{ id: 5, name: '[Imported]', items: 10 }]);
    const imported = await importStockGroupsXml('<Groups/>', true);
    expect(imported[0].name).toBe('[Imported]');
    expect(mockPost).toHaveBeenCalledWith('/baskets/import-xml', { xml_content: '<Groups/>', overwrite: true });

    // 9. importStockGroupCsv
    mockPost.mockResolvedValueOnce({ id: 1, name: '[Test]', items: [{ symbol: 'NVDA' }] });
    await importStockGroupCsv('[Test]', 'NVDA;01.01.2020');
    expect(mockPost).toHaveBeenCalledWith('/baskets/import-csv', {
      basket_name: '[Test]',
      csv_text: 'NVDA;01.01.2020',
    });

    // 10. exportStockGroupCsv
    mockGet.mockResolvedValueOnce({ basket_name: '[Test]', content: 'NVDA;01.01.2020' });
    const csv = await exportStockGroupCsv('[Test]');
    expect(csv).toBe('NVDA;01.01.2020');
    expect(mockGet).toHaveBeenCalledWith('/baskets/%5BTest%5D/export-csv');
  });
});
