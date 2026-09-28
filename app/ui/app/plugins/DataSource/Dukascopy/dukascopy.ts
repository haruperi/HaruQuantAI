import { rawDukascopyCatalogue as rawCatalogue } from '../../../host/catalogs';

export interface DukasSymbol {
  symbol: string; name: string; category: string; subcategory: string;
  fullCategory: string; dateFrom: string; dateFromM1: string;
  decimals: number; tickValue: number; defaultSpread: number;
  tickSize: number; tickStep: number; instrumentType: number;
}
export interface BrokerProfile { id:string;name:string;postfix:string;timezone:string;mtUse:boolean;instruments:string[] }
export interface AddDukasRequest {
  symbols: string[]; dataType: 'TICK' | 'M1'; broker: string;
  postfix: string; instruments: string[];
}
function date(value: string): string {
  const match = /^(\d{1,2})\.(\d{1,2})\.(\d{4})$/.exec(value);
  if (!match) throw new Error('Invalid catalogue date');
  const [, day, month, year] = match;
  const iso = `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`;
  if (new Date(iso).toISOString().slice(0, 10) !== iso) throw new Error('Invalid catalogue date');
  return iso;
}
/** Parse the donor's twelve-column catalogue without modifying its order. */
export function parseCatalogue(raw: string): DukasSymbol[] {
  const seen = new Set<string>();
  return raw.split(/\r?\n/).filter(line => line.trim()).map(line => {
    const fields = line.split(';').map(value => value.trim());
    if (fields.length !== 12) throw new Error('Invalid catalogue row');
    const [symbol, name, category, subcategory, tick, minute] = fields;
    if (!symbol || seen.has(symbol)) throw new Error('Invalid catalogue symbol');
    seen.add(symbol);
    const numbers = fields.slice(6).map(Number);
    if (numbers.some(value => !Number.isFinite(value))) throw new Error('Invalid catalogue metadata');
    const [decimals, tickValue, defaultSpread, tickSize, tickStep, instrumentType] = numbers;
    return { symbol, name, category, subcategory, fullCategory: `${category} - ${subcategory}`,
      dateFrom: date(tick), dateFromM1: date(minute), decimals, tickValue, defaultSpread, tickSize, tickStep, instrumentType };
  });
}
export const catalogue = parseCatalogue(rawCatalogue);
export const categories = [{ value: '', name: 'All' }];
for (const item of catalogue) {
  if (!categories.some(option => option.value === item.category)) categories.push({ value: item.category, name: `${item.category} - All` });
  if (!categories.some(option => option.value === item.fullCategory)) categories.push({ value: item.fullCategory, name: item.fullCategory });
}
export function filterCatalogue(text: string, category: string): DukasSymbol[] {
  const search = text.toLowerCase();
  return catalogue.filter(item => (item.symbol.toLowerCase().includes(search) || item.name.toLowerCase().includes(search))
    && (!category || item.fullCategory.includes(category)));
}
