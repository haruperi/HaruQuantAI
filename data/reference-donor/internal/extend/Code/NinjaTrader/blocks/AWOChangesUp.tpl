<#-- AwesomeOscillator changes direction up = local minimum (value[2] > value[1] && value[1] < value[0]).
     Compared at 6 decimals, as the Java reads Value.getRounded(). -->
((sqRound(<@printAOValueAt block "2" />, 6) > sqRound(<@printAOValueAt block "1" />, 6)) && (sqRound(<@printAOValueAt block "1" />, 6) < sqRound(<@printAOValueAt block "0" />, 6)))
