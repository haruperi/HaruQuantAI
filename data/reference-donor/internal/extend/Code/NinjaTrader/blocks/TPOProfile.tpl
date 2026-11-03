<#-- IGNORES #TickSize#: both sides resolve the tick size from the instrument, so the parameter
     carries nothing the export could use. On this side SqTPOProfile bins with NinjaScript's own
     TickSize (binSize = ticksPerBin * TickSize); on the StrategyQuant side TPOProfileIndicatorChart
     reads cfgChart().getInstrumentInfo().tickStep directly and never looks at the parameter - the
     block only fills it in at init so a template that WANTED the value would have one to export.
     TPO / Market Profile (multi-output) from the installed SqTPOProfile indicator;
     #Line# = the Java output order 0..22. Mapping in printTPOProfileLine (Parameters.inc).
     #UseCustomHours# + #StartHour#/#StartMinute#/#EndHour#/#EndMinute# are passed through to the
     indicator's custom window. All 23 outputs, all 8 session types and the custom RTH window.
     IGNORES #ShowCandlesticks#: chart drawing only (return ShowX; in the Java) - no meaning in generated code.
     IGNORES #ShowShapeLabel#: chart drawing only (return ShowX; in the Java) - no meaning in generated code.
     IGNORES #UseBlockMode#: chart drawing only (return ShowX; in the Java) - no meaning in generated code.
-->
<@printTPOProfileLine block shift />
