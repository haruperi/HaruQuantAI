<#-- GEN-34 (plán 094): Crypto fixed amount MM (JForex). ⚠️ PARITA NEOVERENÁ (compile-only) - formula
     zrkadlí autoritatívne NT SQ.inc:175 sqMMFixedAmountByPrice (= RiskedMoney / price), štruktúra
     zrkadlí JForex CryptoSizeByPrice_class.tpl (JForex API). Behaviorálnu paritu treba overiť na platforme. -->


double sqMMCryptoFixedAmount(String symbol, OrderCommand orderType, double price, double RiskedMoney, int mmDecimals) throws JFException {
   print("Computing Money Management for order - Crypto fixed amount");

   if(UseMoneyManagement == false) {
      print("Use Money Management = false, MM not used");
      return mmLotsIfNoMM;
   }

   symbol = correctSymbol(symbol);

   double openPrice = price > 0 ? price : (orderType.isLong() ? sqGetAsk(symbol) : sqGetBid(symbol));

   print("Price: ", openPrice, ", RiskedMoney: ", RiskedMoney);

   if(RiskedMoney <= 0 || openPrice <= 0) {
      print("Computing Money Management - Incorrect RiskedMoney or price value");
      return(0);
   }

   //Crypto sizing by price (NT SQ.inc sqMMFixedAmountByPrice): units = RiskedMoney / price
   double LotSize = RiskedMoney / openPrice;

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
