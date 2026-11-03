<#-- GEN-34 (plán 094): ATR risk-based sizing MM (JForex). ⚠️ PARITA NEOVERENÁ (compile-only) - formula
     zrkadlí autoritatívne NT SQ.inc:194 sqMMAtrRisk (slInMoney = ATR·mult·PointValue; size =
     equity·min(risk,100)/100 / slInMoney; if <=0 -> lotsIfNoMM; min(size,maxLots)), štruktúra zrkadlí
     JForex RiskFixedPctOfAccount_class.tpl. sqATR shift=1 = NT ATR[1]. Paritu treba overiť na platforme. -->


private double sqMMATRRiskBasedSizing(String symbol, OrderCommand orderType, double price, double RiskInPercent, int atrPeriod, double atrMult, int Decimals, double LotsIfNoMM, double MaximumLots) throws JFException {
   print("Computing Money Management for order - ATR risk-based sizing");

   if(UseMoneyManagement == false) {
      print("Use Money Management = false, MM not used");
      return mmLotsIfNoMM;
   }

   symbol = correctSymbol(symbol);
   instrument = getInstrument(symbol);

   double openPrice = price > 0 ? price : (orderType.isLong() ? sqGetAsk(symbol) : sqGetBid(symbol));
   double LotSize = 0;

   if(RiskInPercent < 0) {
      print("Computing Money Management - Incorrect RiskInPercent size, it must be above 0");
      return 0;
   }

   double PointValue = getPointValue(instrument);
   double Smallest_Lot = instrument.getMinTradeAmount() / 100000;
   double Largest_Lot = instrument.getMaxTradeAmount()  / 100000;
   double LotStep = instrument.getTradeAmountIncrement()  / 100000;

   // ATR-based stop distance in money (NT SQ.inc sqMMAtrRisk): ATR[1] * mult * PointValue
   double atrValue = sqATR("Current", 0, atrPeriod, 1);
   double slInMoney = atrValue * atrMult * PointValue;

   //Maximum amount of money to risk
   double moneyToRisk = context.getAccount().getEquity() * (Math.min(RiskInPercent, 100.0) / 100.0);

   if(slInMoney > 0) {
      LotSize = roundDown(moneyToRisk / slInMoney, Decimals);
   }
   else {
      LotSize = 0;
   }

   //--- MAXLOT and MINLOT management

   print("Computing Money Management - Smallest_Lot: ", Smallest_Lot, ", Largest_Lot: ", Largest_Lot,", Computed LotSize: ", LotSize);
   print("Max money to risk: ", moneyToRisk, ", ATR value: ", atrValue, ", SL in money: ", slInMoney, ", Point value: ", PointValue);

   if(LotSize <= 0) {
      print("Calculated LotSize is <= 0. Using LotsIfNoMM value: ", LotsIfNoMM);
      LotSize = LotsIfNoMM;
   }

   if(LotSize > MaximumLots) {
      print("LotSize is too big. LotSize set to maximal allowed value (MaximumLots): ", MaximumLots);
      LotSize = MaximumLots;
   }

   //--------------------------------------------

   if (LotSize < Smallest_Lot) {
      print("Calculated LotSize is too small. Minimal allowed lot size from the broker is: ", Smallest_Lot, ". Please, increase your risk or set fixed LotSize.");
      LotSize = 0;
   }
   else if (LotSize > Largest_Lot) {
      print("LotSize is too big. LotSize set to maximal allowed market value: ", Largest_Lot);
      LotSize = Largest_Lot;
   }

   return LotSize;
}
