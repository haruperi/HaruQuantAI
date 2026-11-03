<#-- Ulcer Index (Down) rising: current value greater than 1 bar ago. #Mode#=2. Parity with UlcerIndexDownRising.java.
     Compared at 6 decimals, as the Java reads getRounded(). -->
<@compress_single_line>(sqRound(<@printUlcerIndexValueAt block "1" />, 6) < sqRound(<@printUlcerIndexValueAt block "0" />, 6))</@compress_single_line>