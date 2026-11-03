<#-- UseInitialSLPT: keep the initial SL/PT. NT Managed already fixes SL/PT at entry (native behavior).

     Emitted as a CONSTANT true, not as the strategy's setting, because StrategyQuant's own backtest
     has no other behaviour: UseInitialSLPT.isUsedInTrading() returns false, so the engine always
     fixes SL/PT at the fill whatever the option says. An export that deferred them would therefore
     disagree with the backtest it was exported from: a deferred stop misses its bar, the position is
     held one bar longer and the next entry may never happen, so the trade sequences diverge for good. -->
		private bool UseInitialSLPT = true;   // StrategyQuant's backtest always fixes SL/PT at entry
