<#-- GetDate -> (Year-1900)*10000 + Month*100 + Day (YYYMMDD, comparable with BarDate/CurrentDate).
     Mirrors GetDate.java (SQTime.getYmd with year-1900 offset). -->
((<@printParam block "#Year#" /> - 1900) * 10000 + <@printParam block "#Month#" /> * 100 + <@printParam block "#Day#" />)
