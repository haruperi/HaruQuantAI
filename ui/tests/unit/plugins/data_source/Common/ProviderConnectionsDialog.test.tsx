import { renderToString } from 'react-dom/server';
import { expect, it } from 'vitest';
import { ProviderConnectionsDialog } from '../../../../../app/plugins/data_source/Common/ProviderConnectionsDialog';

it('offers a single provider connection editor without rendering saved secrets',()=>{
  const html=renderToString(<ProviderConnectionsDialog provider="yahoo" onClose={()=>{}} onSaved={()=>{}}/>);
  expect(html).toContain('Saved connection');expect(html).toContain('Test access');expect(html).toContain('Save connection');
  expect(html.match(/type="password"/g)).toHaveLength(3);
  expect(html).toContain('saved secrets are never displayed');
});
