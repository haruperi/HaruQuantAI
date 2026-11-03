<#-- SendEmail -> mail via the configured NT8 Mail share service. MT parity: only in live trading
     (the MT tester ignores SendMail too); requires the Mail share account. -->
sqSendEmail("<@printParam block "#EmailSubject#" />", "<@printParam block "#Message#" />");
