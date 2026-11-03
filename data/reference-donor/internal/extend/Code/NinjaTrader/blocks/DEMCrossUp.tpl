<#-- DeMarker crosses above #Level# (value[1] < Level && value[0] > Level). -->
((sqRound(<@printDeMarkerValueAt block "1" />, 6) < <@printParam block "#Level#" />) && (sqRound(<@printDeMarkerValueAt block "0" />, 6) > <@printParam block "#Level#" />))
