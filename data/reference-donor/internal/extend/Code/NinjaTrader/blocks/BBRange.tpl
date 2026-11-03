<#-- Bollinger band range = 2 * Deviation * StdDev(input, Period) = upper - lower. Native NT StdDev.
     Parity with BBRange.java (2 * Deviation * stdDev). -->
<@compress_single_line>(2 * <@printParam block "#Deviation#" /> * <@printIndValueAt block "StdDev" shift />)</@compress_single_line>