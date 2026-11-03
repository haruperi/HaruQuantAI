<#-- Keltner Channel (multi-output) value -> native NinjaScript KeltnerChannel(input, offsetMultiplier, period).
     #Line# selects .Upper (0) / .Lower (1) / Midline (2, NT default). NT order offsetMultiplier=#Deviation#,
     period=#Period#. Mapping in printKCLine (Parameters.inc).
     Docs: https://ninjatrader.com/support/helpguides/nt8/keltner_channel.htm -->
<@printKCLine block shift />