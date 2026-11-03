<#-- Ehlers Reflex oscillator value from the installed SqReflex indicator, which computes Reflex.java's
     MetaTrader engine branch (recursive IIR). NinjaTrader has no native Reflex. -->
<#-- The caller's `shift` MUST be passed on: comparisons such as IsRising or CrossesAbove
     render the same operand at shift and shift+1, so a fixed shift makes them compare a value
     with itself. -->
<@compress_single_line><@printReflexValueAt block shift /></@compress_single_line>