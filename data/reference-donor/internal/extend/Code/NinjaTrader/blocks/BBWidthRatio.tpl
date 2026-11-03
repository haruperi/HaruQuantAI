<#-- Bollinger band width ratio = 2*Deviation*StdDev / SMA (relative band width); 0 when SMA <= 0.
     Native NT StdDev/SMA. Parity with BBWidthRatio.java. -->
<@compress_single_line>(<@printIndValueAt block "SMA" shift /> > 0 ? 2 * <@printParam block "#Deviation#" /> * <@printIndValueAt block "StdDev" shift /> / <@printIndValueAt block "SMA" shift /> : 0)</@compress_single_line>