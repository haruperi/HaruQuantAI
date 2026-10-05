/** Owner-local presentation/resource documents; no backend execution authority. */
export interface RuleNode {
  id: string;
  depth: number;
  kind: 'event' | 'if' | 'then' | 'condition' | 'action';
  label: string;
  parentId?: string;
  operator?: 'AND' | 'OR';
  leftExpr?: string;
  compOp?: '>' | '<' | '>=' | '<=' | '==' | '!=' | 'crosses above' | 'crosses below' | 'is rising' | 'is falling';
  rightExpr?: string;
  actionType?: 'Enter at Market' | 'Place Stop Order' | 'Place Limit Order' | 'Set Stop Loss' | 'Set Profit Target' | 'Trailing Stop' | 'Move SL to BE' | 'Exit Market';
  actionParams?: Record<string, number | string>;
  signalGroup?: 'Long Entry' | 'Short Entry' | 'Long Exit' | 'Short Exit';
}
