<#-- Average Volume is rising (value[1] < value[0]). See printAvgVolumeValueAt (Parameters.inc).
     Compared at 4 decimals, as the Java reads Value.getRounded(shift, 4). -->
(sqRound(<@printAvgVolumeValueAt block "1" />, 4) < sqRound(<@printAvgVolumeValueAt block "0" />, 4))