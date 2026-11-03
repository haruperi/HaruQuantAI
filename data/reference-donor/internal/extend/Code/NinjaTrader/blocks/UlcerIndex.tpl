<#-- Ulcer Index value via the installed SqUlcerIndex indicator. #Mode#: 1=UP (from highest), 2=Down (from lowest).
     NinjaTrader has no native Ulcer Index. -->
<#-- The caller's `shift` MUST be passed on: comparisons such as IsRising or CrossesAbove
     render the same operand at shift and shift+1, so a fixed shift makes them compare a value
     with itself. -->
<@compress_single_line><@printUlcerIndexValueAt block shift /></@compress_single_line>