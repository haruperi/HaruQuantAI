<#-- UseInitialSLPT: the branch itself is emitted elsewhere, because it needs the
     entry action's SL/PT expressions - `if (UseInitialSLPT)` around the entry calls comes from
     printEntrySLPT (Parameters.inc), the deferred `!UseInitialSLPT` block from printDeferredSLPTManage
     (ExitMethods.inc). This template only labels the section in the generated source. -->
<#-- UseInitialSLPT: true -> SL/PT are set before the entry (fixed at the fill);
     false -> they are set on the bar AFTER the fill (blocks below). -->
			// UseInitialSLPT: SL/PT set before the entry when true, on the bar after the fill when false.
