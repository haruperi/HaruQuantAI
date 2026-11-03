<#-- Money Management - Crypto fixed amount. -->
<#-- Crypto sizing divides money by the price, so on a futures instrument the size can come out below one contract:
     StrategyQuant then opens no trade, the export trades one contract (its minimum). Meant for crypto instruments. -->
		// Money Management - Crypto fixed amount (crypto instruments; below one contract StrategyQuant opens no trade, this strategy one)
		private double mmRiskedMoney = <@printMMSize "#RiskedMoney#" />;
		private int mmDecimals = <@printMMSize "#Decimals#" />;
