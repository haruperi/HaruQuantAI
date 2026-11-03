


class CMaxTradesPerDay : public CTradingOption {
   private:
      datetime openTimeToday;
      datetime EODTime;
      bool reachedLimitToday;
      
   public:
      CMaxTradesPerDay() {
         EODTime = D'1970.01.01';
      }

      //+----------------------------------------------+

      virtual bool onBarUpdate() {
         if(MaxTradesPerDay <= 0) {
            return true;
         }
		
         datetime currentTime = TimeCurrent();

         if(currentTime > EODTime) {
            // it is new day
            initTimeForCurrentDay(currentTime);
         }		
		
		   if(reachedLimitToday) {
		      return false;
		   }
		   
         if(getNumberOfTradesToday() >= MaxTradesPerDay) {
            reachedLimitToday = true;
            return(false);
         }
		
         return true;
      }

      //------------------------------------------------------------------------

      void initTimeForCurrentDay(datetime currentTime) {
			// set end time of the current day (so that we now when new day starts)
         EODTime = SQTime.correctDayEnd(currentTime);

         openTimeToday = SQTime.correctDayStart(currentTime);
         
         reachedLimitToday = false;
      }
      
      //------------------------------------------------------------------------

		int getNumberOfTradesToday() {
			int todayTradesCount = 0;

			HistorySelect(openTimeToday, TimeCurrent());

       // only filled orders count as trades, same as in the SQX engine - pending orders
       // (waiting, cancelled or expired) must not use up the daily limit
       for(int i=HistoryDealsTotal() - 1; i>=0; i--) {
         ulong ticket = HistoryDealGetTicket(i);
         
         if(HistoryDealSelect(ticket) && 
            checkMagicNumber(HistoryDealGetInteger(ticket, DEAL_MAGIC)) &&
            HistoryDealGetInteger(ticket, DEAL_ENTRY) == DEAL_ENTRY_IN
         ){ 
            if(HistoryDealGetInteger(ticket, DEAL_TIME) >= openTimeToday){
               todayTradesCount++;
            }
         }
       }

			return todayTradesCount;
		}      
};

// create variable for class instance (required)
CMaxTradesPerDay* objMaxTradesPerDay;