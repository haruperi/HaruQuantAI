<#-- Bollinger Bands (multi-output) -> native NinjaScript Bollinger(input, numStdDev, period);
     #Line# selects Upper (.Upper) or Lower (.Lower). BollingerBands.java declares exactly those two
     @Output series and no middle band, so #Line# is only ever 0 or 1.
     Mapping in printBollingerLine (Parameters.inc).
     Docs: https://ninjatrader.com/support/helpGuides/nt8/bollinger_bands.htm -->
<@printBollingerLine block shift />