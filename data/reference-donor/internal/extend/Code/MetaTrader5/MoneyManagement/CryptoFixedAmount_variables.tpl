
input string smm = "----------- Money Management - Crypto Fixed Amount -----------";
input bool UseMoneyManagement = true;
input double mmRiskedMoney = <@printMMVariableNumber "#RiskedMoney#" />;
input int mmDecimals = <@printMMVariableNumber "#Decimals#" />;
input double mmLotsIfNoMM = 1;
input double mmMultiplier = ${orderSizeMultiplier};
input double mmStep = ${orderSizeStep};
