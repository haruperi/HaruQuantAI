import { useProjectWorkbench, type SettingsSection } from './documents';

import {retestDataDefaults} from './retesterFixtures';
export function RetesterSettings({locked,selectedId,onSelect}:{locked:boolean;selectedId:string;onSelect:(id:string)=>void}) {
const { ProjectSettings, DataTab, TradingOptionsTab, AtmTab, MoneyManagementTab, CrossChecksTab, RankingTab, NotesTab } = useProjectWorkbench();

 const base='https://strategyquant.com/doc/strategyquant/';
 const sections:SettingsSection[]=[
  {id:'data',title:'Data',help:'Configure trading engine, symbols, timeframes and data ranges.',helpUrl:base+'data/',content:<DataTab initialState={retestDataDefaults}/>},
  {id:'options',title:'Trading options',help:'Configure trading hours and execution options.',helpUrl:base+'trading-options/',content:<TradingOptionsTab/>},
  {id:'atm',title:'ATM',help:'Advanced Trading Management',helpUrl:base+'settings-atm/',content:<AtmTab/>},
  {id:'money',title:'Money management',help:'Configure position sizing and initial capital.',helpUrl:base+'money-management/',content:<MoneyManagementTab/>},
  {id:'checks',title:'Cross checks (robustness)',help:'Configure additional robustness checks.',helpUrl:base+'cross-checks-automated-strategy-robustness-tests/',content:<CrossChecksTab/>},
  {id:'ranking',title:'Ranking',help:'Configure ranking and filtering of retested strategies.',helpUrl:base+'ranking-options/',content:<RankingTab task="Retest"/>},
  {id:'notes',title:'Notes',help:'Save notes about this configuration.',helpUrl:base+'notes/',content:<NotesTab/>},
 ];
 return <ProjectSettings sections={sections} locked={locked} selectedId={selectedId} onSelect={onSelect}/>;
}
