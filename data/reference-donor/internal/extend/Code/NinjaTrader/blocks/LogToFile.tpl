<#-- LogToFile -> append a timestamped line to a file (relative names land in the NT8 user data
     dir). sqLogToFile never throws (IO problems must not kill the strategy). -->
sqLogToFile("<@printParam block "#Filename#" />", "<@printParam block "#Message#" />");
