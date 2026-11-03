
	// Money Management - Crypto fixed amount
	@Configurable(value = "--------- Money Management ---------", readOnly = true)
	public String mmType = "Crypto fixed amount";
	@Configurable("Use Money Management")
	public boolean UseMoneyManagement = true;
	@Configurable(value = "Risked money", stepSize = 0.1)
	public double mmRiskedMoney = <@printMMVariableNumber "#RiskedMoney#" />;
	@Configurable(value = "Size if no MM", stepSize = 0.1)
	public double mmLotsIfNoMM = 1;
	@Configurable(value = "Size Decimals", stepSize = 1)
	public int mmDecimals = <@printMMVariableNumber "#Decimals#" />;