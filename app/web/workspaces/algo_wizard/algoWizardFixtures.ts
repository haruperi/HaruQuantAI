import { block, makeDraft, makeRule, type Draft } from "./algoWizardModel";
export const examples = [
  {
    name: "EMA Cross",
    file: "EMACross",
    description:
      "Simple, but popular strategy of entering the market when faster EMA crosses above slower EMA.",
    rules:
      "Enter Long when faster EMA crosses above slower EMA\nEnter Short when faster EMA crosses below slower EMA",
  },
  {
    name: "Inside Bar Breakout",
    file: "InsideBarBreakout",
    description:
      "Strategy powerful on higher timeframes - entering at the break of inside bar.",
    rules:
      "When there is an inside bar then place two stop orders:\nLong Stop above the inside bar high\nShort Stop below the inside bar low\nStop Loss is the opposite boundary of inside bar",
  },
  {
    name: "Grid Example 1",
    file: "GridExample1",
    description:
      "Example 3-level Martingale strategy. Position size increases after a losing trade.",
    rules: "",
  },
  {
    name: "Range Breakout",
    file: "RangeBreakout",
    description: "Enter the market when price breaks a predefined range.",
    rules:
      "Define range from past bars\nEnter Long above the range\nEnter Short below the range\nUse the opposite boundary as Stop Loss",
  },
  {
    name: "Bearish Divergence",
    file: "BearishDivergence",
    description:
      "Example of trading on bearish divergence between price and MACD.",
    rules: "",
  },
  {
    name: "Trail Stop by EA",
    file: "TrailingStopByEA",
    description:
      "An example of handling a custom trailing stop using AlgoWizard. Opens an order and trails its stop loss through strategy rules.",
    rules: "",
  },
  {
    name: "Trail Stop by Lowest",
    file: "TrailingStopByLowest",
    description:
      "Move the Stop Loss to the lowest price of the previous five candles.",
    rules: "",
  },
  {
    name: "Buy dips",
    file: "buy_dips",
    description: "Enter stocks during a temporary market drop.",
    rules: "",
    cloud: true,
  },
  {
    name: "Mean reversion",
    file: "mean_reversion",
    description: "Stockpicker example using a return toward average prices.",
    rules: "",
    cloud: true,
  },
  {
    name: "Breakout",
    file: "breakout",
    description: "Stockpicker example entering stocks above a previous high.",
    rules: "",
    cloud: true,
  },
];
/** Illustrative drafts, not parsed donor archives or executable strategies. */
export function exampleDraft(index: number): Draft {
  const e = examples[index];
  const d = makeDraft(e.file, e.cloud ? "Stockpicker" : "Full", true);
  const expressions = [
    [
      "EMA(FastEMA)[1] crosses above EMA(SlowEMA)[1]",
      "EMA(FastEMA)[1] crosses below EMA(SlowEMA)[1]",
    ],
    [
      "High[1] < High[2] AND Low[1] > Low[2]",
      "High[1] < High[2] AND Low[1] > Low[2]",
    ],
    ["Last trade profit < 0", "Open positions < 3"],
    ["Close[1] > Highest(20)[2]", "Close[1] < Lowest(20)[2]"],
    [
      "High[1] > High[5] AND MACD(12,26,9)[1] < MACD(12,26,9)[5]",
      "Bearish divergence",
    ],
  ][index] ?? ["Close[1] > SMA(20)[1]", "Close[1] < SMA(20)[1]"];
  d.rules[0].signals.forEach((s, i) => {
    s.conditions = [block(expressions[i])];
  });
  d.rules[1].conditions = [block("LongEntrySignal")];
  d.rules[2].conditions = [block("ShortEntrySignal")];
  d.rules[1].actions = [
    block(
      index === 1
        ? "Enter at Stop (Long, High[1], 0.1 lots)"
        : "Enter at Market (Long, 0.1 lots)",
    ),
  ];
  d.rules[2].actions = [
    block(
      index === 1
        ? "Enter at Stop (Short, Low[1], 0.1 lots)"
        : "Enter at Market (Short, 0.1 lots)",
    ),
  ];
  if (index === 0)
    d.variables.push(
      { name: "FastEMA", value: "10", type: "Integer", configurable: false },
      { name: "SlowEMA", value: "20", type: "Integer", configurable: false },
      {
        name: "MagicNumber",
        value: "11111",
        type: "Integer",
        configurable: false,
      },
    );
  if (index === 5 || index === 6) {
    const r = makeRule("Trailing stop", "Action only");
    r.actions = [
      block(
        index === 6
          ? "Move Stop Loss to Lowest(5)[1]"
          : "Move Stop Loss to Close[1] - 20 pips",
      ),
    ];
    d.rules.push(r);
  }
  return d;
}
export const blockGroups: Record<string, string[]> = {
  Comparisons: [
    "Is greater (>)",
    "Is lower (<)",
    "Equals (=)",
    "Crosses above",
    "Crosses below",
    "Is rising",
    "Is falling",
  ],
  Indicators: [
    "EMA",
    "SMA",
    "RSI",
    "MACD",
    "ATR",
    "Bollinger Bands",
    "Highest",
    "Lowest",
    "ADX",
    "Stochastic",
  ],
  Prices: ["Open", "High", "Low", "Close", "Bid", "Ask", "Volume"],
  Signals: [
    "LongEntrySignal",
    "ShortEntrySignal",
    "LongExitSignal",
    "ShortExitSignal",
    "Inside Bar",
    "Bullish engulfing",
    "Bearish divergence",
  ],
  "Order actions": [
    "Enter at Market",
    "Enter at Stop",
    "Enter at Limit",
    "Close position",
    "Close all positions",
    "Cancel pending orders",
  ],
  "Other actions": [
    "Set Stop Loss",
    "Set Profit Target",
    "Move Stop Loss",
    "Assign variable",
    "Log to journal",
  ],
  "Random blocks": [
    "Random condition",
    "Random indicator",
    "Random value",
    "Random action",
  ],
};
