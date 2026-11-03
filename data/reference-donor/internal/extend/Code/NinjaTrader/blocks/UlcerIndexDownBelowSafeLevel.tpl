<#-- Ulcer Index (Down) below safe level. #Mode#=2. Parity with UlcerIndexDownBelowSafeLevel.java (UI < SafeLevel).
     Compared at 6 decimals, as the Java reads getRounded(). -->
<@compress_single_line>(sqRound(<@printUlcerIndexValueAt block "0" />, 6) < <@printParam block "#SafeLevel#" />)</@compress_single_line>