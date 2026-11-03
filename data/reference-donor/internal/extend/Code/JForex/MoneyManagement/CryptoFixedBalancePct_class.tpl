<#-- GEN-34 (plán 094): Crypto fixed % of balance MM (JForex). ⚠️ PARITA NEOVERENÁ (compile-only) -
     formula zrkadlí autoritatívne NT SQ.inc:184 sqMMBalancePctByPrice (= balance * min(risk,100)/100 / price),
     štruktúra zrkadlí JForex CryptoSizeByPrice_class.tpl. Behaviorálnu paritu treba overiť na platforme. -->


double sqMMCryptoFixedBalancePct(String symbol, OrderCommand orderType, double price, double riskPct, int mmDecimals) throws JFException {
   print("Computing Money Management for order - Crypto fixed % of balance");

   if(UseMoneyManagement == false) {
      print("Use Money Management = false, MM not used");
      return mmLotsIfNoMM;
   }

   symbol = correctSymbol(symbol);

   double openPrice = price > 0 ? price : (orderType.isLong() ? sqGetAsk(symbol) : sqGetBid(symbol));

   print("Price: ", openPrice, ", riskPct: ", riskPct);

   if(openPrice <= 0) {
      return(0);
   }

   //Crypto sizing by price (NT SQ.inc sqMMBalancePctByPrice): units = (balance * min(risk,100)/100) / price
   double moneyToRisk = context.getAccount().getBalance() * (Math.min(riskPct, 100.0) / 100.0);
   double LotSize = moneyToRisk / openPrice;

   // round computed trade size
   LotSize = roundDown(LotSize, mmDecimals);

   double Smallest_Lot = instrument.getMinTradeAmount() / 100000;
   double Largest_Lot = instrument.getMaxTradeAmount()  / 100000;
   double LotStep = instrument.getTradeAmountIncrement()  / 100000;

   //--- MAXLOT and MINLOT management

   print("Computing Money Management - Smallest_Lot: ", Smallest_Lot, ", Largest_Lot: ", Largest_Lot,", Computed LotSize: ", LotSize);

   if(LotSize <= 0) {
      return(0);
   }

   if (LotSize < Smallest_Lot) {
      print("LotSize is too small. Minimal allowed lot size: ", Smallest_Lot);
      LotSize = 0;
   }
   else if (LotSize > Largest_Lot) {
      print("LotSize is too big. LotSize set to maximal allowed market value: ", Largest_Lot);
      LotSize = Largest_Lot;
   }

   return (LotSize);
}
