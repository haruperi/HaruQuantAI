# `AutomaticPortfolioBuilder` task

Searches strategy combinations to build portfolios (the Portfolio Master app project's task).
Sections: `AutomaticPortfolioBuilder`, `Databanks`. Parser:
`PortfolioMasterSettings.loadFromXml` (`SQAppLib/…/portfolioMaster/PortfolioMasterSettings.java`).

Default template: `internal/plugins/TaskAutomaticPortfolioBuilder/task.xml`. Small complete real
example: `tests/backend/cli/AutomaticPortfolioBuilder.cfx`.

```xml
<AutomaticPortfolioBuilder>
  <SearchType>bruteforce|genetic</SearchType>
  <GenPopulationSize>100</GenPopulationSize>
  <GenGenerations>700</GenGenerations>
  <GenRunContinually>false</GenRunContinually>
  <GenRestartAfterStagnation>true</GenRestartAfterStagnation>
  <GenGenerationLimit>500</GenGenerationLimit>
  <MinStrategies>2</MinStrategies>
  <MaxStrategies>8</MaxStrategies>
  <MaxStrategiesDatabank>100</MaxStrategiesDatabank>
  <MaxStrategiesSector>3</MaxStrategiesSector>
  <DateRange>full|limited</DateRange>
  <DateRangeFrom>…</DateRangeFrom><DateRangeTo>…</DateRangeTo>
  <DateRangeIsPct>70</DateRangeIsPct><DateRangeReverse>false</DateRangeReverse>
  <FitnessType>NetProfitIS</FitnessType>   <!-- base + IS|Full suffix; classes in SQ/PortfolioMasterFitness/:
                                                NetProfit, PctStagnation, ReturnDD -->
  <CorrMax>0.3</CorrMax><CorrType>ProfitLoss</CorrType><CorrSampleType>10</CorrSampleType>
  <CorrPeriod>10</CorrPeriod><CorrAllowNegative>true</CorrAllowNegative>
  <CorrAddEmptyPeriods>false</CorrAddEmptyPeriods>
  <FilterOverlappingTrades>…</FilterOverlappingTrades>
  <MMMethodOptional>…</MMMethodOptional>
  <Conditions>…acceptance…</Conditions>
  <MoneyManagement>…same schema as shared RiskMoneyManagement/MoneyManagement…</MoneyManagement>
</AutomaticPortfolioBuilder>
```

Databank wiring: Input = `Simple strategies`, Output = `Results` (see
[shared-sections.md](shared-sections.md)); `<SelectedStrategies>` supported via
`retestSelected="true"`.
