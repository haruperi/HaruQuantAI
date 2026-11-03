<#-- MACD main line crosses below #Level#. -->
(<@printMACDValueAt block "MAIN" "1" /> > <@printParam block "#Level#" /> && <@printMACDValueAt block "MAIN" "0" /> < <@printParam block "#Level#" />)