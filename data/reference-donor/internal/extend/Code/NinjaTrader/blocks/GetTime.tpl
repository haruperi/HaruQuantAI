<#-- GetTime -> Hour*100 + Minute + 0.01*Second (HHMM.SS, comparable with BarTime/CurrentTime HHMM).
     Mirrors GetTime.java (SQTime.getHms = 100*H + M + 0.01*S). -->
(<@printParam block "#Hour#" /> * 100 + <@printParam block "#Minute#" /> + 0.01 * <@printParam block "#Second#" />)
