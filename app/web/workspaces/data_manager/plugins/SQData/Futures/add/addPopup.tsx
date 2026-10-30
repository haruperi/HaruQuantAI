import { SQDataAddView } from '../../Equity/add/addPopup';
import type { SQAddCallbacks } from '../../Equity/add/SQEquityDataAddCtrl';
import { useSQFuturesDataAdd } from './SQFuturesDataAddCtrl';
import { FuturesDataUsageConditions } from './dataUsageConditionsPopup';
import '../styles.css';
export function SQFuturesAddPopup(props: SQAddCallbacks) { return <SQDataAddView controller={useSQFuturesDataAdd(props)} Conditions={FuturesDataUsageConditions}/>; }
