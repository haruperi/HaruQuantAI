import { describe, expect, it } from 'vitest';
import { detectExternalFormat, emptyExternalLines, parseExternalData, parseExternalIndicatorsJson, recognizeMq4, serializeExternalIndicatorsJson, validateExternalDefinition, type ExternalIndicatorDefinition } from '../../../../../app/plugins/DataSource/Indicators/externalIndicators';

function indicator(name = 'Sentiment'): ExternalIndicatorDefinition { const values = emptyExternalLines(); values[0].name = 'Score'; return { name, type: 2, values, timeframe: '—', dateFrom: '', dateTo: '', totalDays: 0, records: [] }; }
describe('external indicator rules', () => {
  it('validates names, line identifiers, uniqueness, and required lines', () => {
    expect(() => validateExternalDefinition(indicator(), [])).not.toThrow();
    expect(() => validateExternalDefinition(indicator('sentiment'), ['Sentiment'])).toThrow('already exists');
    const missing = indicator(); missing.values[0].name = ''; expect(() => validateExternalDefinition(missing)).toThrow('At least one');
    const invalid = indicator(); invalid.values[0].name = 'Bad value'; expect(() => validateExternalDefinition(invalid)).toThrow('special characters');
    const duplicate = indicator(); duplicate.values[1].name = 'Score'; expect(() => validateExternalDefinition(duplicate)).toThrow('unique');
  });
  it('detects and parses timestamped values with deterministic duplicate handling', () => {
    const text = 'Date,Score\n2026-09-20 10:00:00,1.5\n2026-09-20 10:01:00,2\n2026-09-20 10:01:00,3';
    const format = detectExternalFormat(text, 1); const result = parseExternalData(text, format, 1, false);
    expect(format.columns).toEqual(['Date & Time', 'Value 1']); expect(result.timeframe).toBe('M1'); expect(result.records).toHaveLength(2); expect(result.records[1].values).toEqual([3]);
    expect(() => parseExternalData(text.replace('1.5', 'bad'), format, 1, false)).toThrow('Row 2');
    expect(parseExternalData(text.replace('1.5', 'bad'), format, 1, true).ignored).toBe(1);
  });
  it('recognizes bounded MQ4 output metadata without executing source', () => {
    const result = recognizeMq4('SqADX.mq4', '#property indicator_buffers 3\n#property indicator_label1 "ADX"\n#property indicator_label2 "+DI"\n#property indicator_label3 "-DI"\nSetIndexBuffer(0,ExtADXBuffer);');
    expect(result.name).toBe('SqADX'); expect(result.values.map(line => line.name)).toEqual(['ADX', 'DI', 'DI2']);
    expect(() => validateExternalDefinition(result)).not.toThrow();
    expect(() => recognizeMq4('bad.mq4', 'int start(){return(0);}')).toThrow('no output buffers');
  });
  it('round trips versioned definition JSON and excludes records', () => {
    const value = indicator('Fundamental'); value.records = [{ timestamp: Date.UTC(2026, 8, 20), values: [4] }];
    const json = serializeExternalIndicatorsJson([value]); expect(JSON.parse(json)).toMatchObject({version:1,kind:'external-indicators',indicators:[{name:'Fundamental',type:2}]}); expect(json).not.toContain('2026');expect(parseExternalIndicatorsJson(json)[0]).toMatchObject({name:'Fundamental',records:[]});
  });
});
