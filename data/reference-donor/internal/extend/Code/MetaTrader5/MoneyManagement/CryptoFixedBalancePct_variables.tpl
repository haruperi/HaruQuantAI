
input string smm = "----------- Money Management - Crypto Fixed % Of Balance -----------";
input bool UseMoneyManagement = true;
input double mmRiskPercent = <@printMMVariableNumber "#Risk#" />;
input int mmDecimals = <@printMMVariableNumber "#Decimals#" />;
input double mmLotsIfNoMM = 1;
input double mmMultiplier = ${orderSizeMultiplier};
input double mmStep = ${orderSizeStep};
