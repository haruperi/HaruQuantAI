<#-- Three consecutive bear bars covering >= #MinimumMove# (deci-pips). The installed SqVPSignal indicator computes the Java _evaluateSignal.      IGNORES #SessionType#: VPOpenDriveShort.java's own evaluate() reads only #MinimumMove# and bar OHLC.
     IGNORES #SessionStartHours#: the block's own evaluate() never reads it.
     IGNORES #SessionStartMinutes#: the block's own evaluate() never reads it.
     IGNORES #ProfileRows#: the block's own evaluate() never reads it.
     IGNORES #ValueAreaPct#: the block's own evaluate() never reads it.
-->
<#global sqUsesIndicatorPackage = true>((<@printSeriesAt block "0">SqVPSignal(<@printInput block />, 9, -1, 1, 150, 70, <@printParam block "#MinimumMove#" />, 0, 0, SqPip).Values[0]</@printSeriesAt> > 0.5))
