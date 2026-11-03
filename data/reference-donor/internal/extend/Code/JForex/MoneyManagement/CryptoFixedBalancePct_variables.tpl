
	// Money Management - Crypto fixed % of balance
	@Configurable(value = "--------- Money Management ---------", readOnly = true)
	public String mmType = "Crypto fixed % of balance";
	@Configurable("Use Money Management")
	public boolean UseMoneyManagement = true;
	@Configurable(value = "Risk in %", stepSize = 0.1)
	public double mmRiskPercent = <@printMMVariableNumber "#Risk#" />;
	@Configurable(value = "Size if no MM", stepSize = 0.1)
	public double mmLotsIfNoMM = 1;
	@Configurable(value = "Size Decimals", stepSize = 1)
	public int mmDecimals = <@printMMVariableNumber "#Decimals#" />;