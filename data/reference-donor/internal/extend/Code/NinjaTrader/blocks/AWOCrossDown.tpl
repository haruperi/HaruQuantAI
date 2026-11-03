<#-- AwesomeOscillator crosses below #Level# (value[1] > Level && value[0] < Level).
     Compared at 6 decimals, as the Java reads Value.getRounded(). -->
((sqRound(<@printAOValueAt block "1" />, 6) > <@printParam block "#Level#" />) && (sqRound(<@printAOValueAt block "0" />, 6) < <@printParam block "#Level#" />))
