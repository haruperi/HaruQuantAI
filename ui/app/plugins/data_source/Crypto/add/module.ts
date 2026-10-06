import type { DataSourceCommand } from '../../Common/dataSourceRibbon';
export { AddPopup } from './addPopup';

const cryptoExchanges = [
  ['binance', 'Binance spot', 'binance', 'Binance'],
  ['binance-coin-m', 'Binance Coin-M', 'coin-m', 'BinanceCoinM'],
  ['binance-usdt-m', 'Binance USDT-M', 'usdt-m', 'BinanceUsdtM'],
  ['bitfinex', 'Bitfinex', 'bitfinex', 'Bitfinex'],
  ['poloniex', 'Poloniex', 'poloniex', 'Poloniex'],
  ['coinbase-pro', 'Coinbase Pro', 'coinbase', 'Coinbase'],
] as const;

export const addCommand = {
        id: 'crypto-add',
        label: 'Add crypto symbol',
        icon: 'crypto',
        children: cryptoExchanges.map(([id, label, icon, exchange]) => ({
          id: `crypto-add-${id}`,
          label,
          icon,
          dialog: 'crypto-add' as const,
          exchange,
        })),
      } as const satisfies DataSourceCommand;
