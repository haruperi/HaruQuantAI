//+------------------------------------------------------------------+
//| COT (Commitments of Traders) data runtime - MQL5                 |
//|                                                                  |
//| Downloads weekly COT data from the StrategyQuant license server  |
//| (license verified) into in-memory arrays and serves values to    |
//| the strategy via sqCOTData(). Downloaded data is mirrored into   |
//| CSV cache files in the common Files folder (FILE_COMMON) so the  |
//| Strategy Tester, where WebRequest is not allowed, can read them. |
//|                                                                  |
//| Live chart:  data is downloaded on the first tick and refreshed  |
//|              automatically when a new weekly record is expected. |
//| Backtest:    data is loaded from the CSV cache written by a      |
//|              previous live run of a COT strategy.                 |
//|                                                                  |
//| Keep the logic in sync with MetaTrader4/COT.mqh.                 |
//+------------------------------------------------------------------+

#define SQ_COT_STATE_UNINITIALIZED 0
#define SQ_COT_STATE_OK            1
#define SQ_COT_STATE_LOADING       2
#define SQ_COT_STATE_ERR_DOWNLOAD  3
#define SQ_COT_STATE_ERR_LICENSE   4
#define SQ_COT_STATE_ERR_CONFIG    5

#define SQ_COT_OUTPUTS             5
#define SQ_COT_REFRESH_AGE         691200 // 8 days - expect a new weekly record this long after the last one
#define SQ_COT_REFRESH_CHECK_DELAY 21600  // 6 hours between refresh checks
#define SQ_COT_BACKGROUND_RETRY    900    // 15 minutes between retries after the retry limit was reached

class CCOTSeries {
public:
   string   id;
   datetime times[];
   double   values[];   // flat array, count * SQ_COT_OUTPUTS, values[record * SQ_COT_OUTPUTS + output]
   int      count;

   CCOTSeries() { count = 0; }
};

CCOTSeries *g_cotSeries[];
int      g_cotState = SQ_COT_STATE_UNINITIALIZED;
int      g_cotRetryCount = 0;
datetime g_cotNextAttemptTime = 0;
datetime g_cotLastRefreshCheck = 0;
bool     g_cotAlertShown = false;

//+------------------------------------------------------------------+

bool sqCOTIsTester() {
   return MQLInfoInteger(MQL_TESTER) != 0 || MQLInfoInteger(MQL_OPTIMIZATION) != 0;
}

//+------------------------------------------------------------------+

void sqCOTRegister(string identifier) {
   if(sqCOTFindSeries(identifier) >= 0) {
      return;
   }

   int count = ArraySize(g_cotSeries);
   ArrayResize(g_cotSeries, count + 1);
   g_cotSeries[count] = new CCOTSeries();
   g_cotSeries[count].id = identifier;
}

//+------------------------------------------------------------------+

void sqCOTDeinit() {
   for(int i = 0; i < ArraySize(g_cotSeries); i++) {
      if(CheckPointer(g_cotSeries[i]) == POINTER_DYNAMIC) {
         delete g_cotSeries[i];
      }
   }
   ArrayResize(g_cotSeries, 0);
}

//+------------------------------------------------------------------+

int sqCOTFindSeries(string identifier) {
   for(int i = 0; i < ArraySize(g_cotSeries); i++) {
      if(g_cotSeries[i].id == identifier) {
         return i;
      }
   }
   return -1;
}

//+------------------------------------------------------------------+
//| Called from OnInit after all identifiers are registered.         |
//| Loads the CSV cache; on a live chart missing data is downloaded  |
//| later from OnTick (WebRequest is unreliable inside OnInit).      |
//+------------------------------------------------------------------+
void sqCOTInitialLoad() {
   if(ArraySize(g_cotSeries) == 0) {
      g_cotState = SQ_COT_STATE_OK;
      return;
   }

   bool allLoaded = true;
   for(int i = 0; i < ArraySize(g_cotSeries); i++) {
      if(!sqCOTReadCacheFile(i)) {
         allLoaded = false;
      }
   }

   if(sqCOTIsTester()) {
      if(allLoaded) {
         g_cotState = SQ_COT_STATE_OK;
      } else {
         g_cotState = SQ_COT_STATE_ERR_CONFIG;
         sqCOTAlertOnce("COT data cache was not found in the common Files folder. Run this EA once on a live/demo chart to download COT data, then run the backtest again. The strategy will not trade.");
      }
      return;
   }

   if(COTLicenseCode == "") {
      g_cotState = SQ_COT_STATE_ERR_CONFIG;
      sqCOTAlertOnce("COT license code is not set. Fill the COTLicenseCode input parameter. The strategy will not trade.");
      return;
   }

   if(allLoaded) {
      // cached data is used immediately, the weekly refresh check downloads new records when due
      g_cotState = SQ_COT_STATE_OK;
   } else {
      g_cotState = SQ_COT_STATE_LOADING;
      g_cotNextAttemptTime = 0;
   }
}

//+------------------------------------------------------------------+
//| OnTick gate - returns true when COT data is ready for trading.   |
//| Also drives the initial download, retries and weekly refresh.    |
//+------------------------------------------------------------------+
bool sqCOTReady() {
   if(ArraySize(g_cotSeries) == 0) {
      return true;
   }

   if(g_cotState == SQ_COT_STATE_OK) {
      sqCOTCheckWeeklyRefresh();
      return true;
   }

   if(g_cotState == SQ_COT_STATE_LOADING) {
      if(TimeLocal() >= g_cotNextAttemptTime) {
         string error = "";
         if(sqCOTDownloadAll(error)) {
            g_cotState = SQ_COT_STATE_OK;
            g_cotRetryCount = 0;
            Print("COT: data downloaded, the strategy is ready.");
            return true;
         }

         if(g_cotState != SQ_COT_STATE_LOADING) {
            // download switched to a terminal error state (license/config)
            return false;
         }

         g_cotRetryCount++;
         g_cotNextAttemptTime = TimeLocal() + COTRetryDelaySeconds;

         if(g_cotRetryCount >= COTMaxRetries) {
            g_cotState = SQ_COT_STATE_ERR_DOWNLOAD;
            g_cotNextAttemptTime = TimeLocal() + SQ_COT_BACKGROUND_RETRY;
            sqCOTAlertOnce("Cannot download COT data: " + error + ". The strategy will not open new trades until COT data is available.");
         }
      }
      return false;
   }

   if(g_cotState == SQ_COT_STATE_ERR_DOWNLOAD) {
      if(TimeLocal() >= g_cotNextAttemptTime) {
         string error = "";
         if(sqCOTDownloadAll(error)) {
            g_cotState = SQ_COT_STATE_OK;
            g_cotRetryCount = 0;
            Print("COT: data downloaded, the strategy resumes trading.");
            return true;
         }
         g_cotNextAttemptTime = TimeLocal() + SQ_COT_BACKGROUND_RETRY;
      }
      return false;
   }

   // SQ_COT_STATE_ERR_LICENSE, SQ_COT_STATE_ERR_CONFIG, SQ_COT_STATE_UNINITIALIZED
   return false;
}

//+------------------------------------------------------------------+
//| Returns the COT value valid at the bar time, mirroring the SQX   |
//| backtest engine: the nearest earlier record is carried forward,  |
//| bars before the first record return 0.                           |
//+------------------------------------------------------------------+
double sqCOTData(string identifier, int output, int shift) {
   int idx = sqCOTFindSeries(identifier);
   if(idx < 0 || g_cotSeries[idx].count == 0) {
      return 0;
   }
   if(output < 0 || output >= SQ_COT_OUTPUTS) {
      return 0;
   }
   if(shift < 0 || shift >= Bars(_Symbol, _Period)) {
      return 0;
   }

   return sqCOTValueAt(idx, output, iTime(_Symbol, _Period, shift));
}

//+------------------------------------------------------------------+

double sqCOTValueAt(int idx, int output, datetime barTime) {
   int lo = 0;
   int hi = g_cotSeries[idx].count - 1;
   int pos = -1;

   while(lo <= hi) {
      int mid = (lo + hi) / 2;
      if(g_cotSeries[idx].times[mid] <= barTime) {
         pos = mid;
         lo = mid + 1;
      } else {
         hi = mid - 1;
      }
   }

   if(pos < 0) {
      return 0;
   }

   return g_cotSeries[idx].values[pos * SQ_COT_OUTPUTS + output];
}

//+------------------------------------------------------------------+
//| COT data is weekly - when the last record is older than 8 days   |
//| and the last check was more than 6 hours ago, download new data. |
//| A failed refresh keeps the strategy trading on carry-forward     |
//| data, the same way an SQX backtest runs on a static snapshot.    |
//+------------------------------------------------------------------+
void sqCOTCheckWeeklyRefresh() {
   if(sqCOTIsTester()) {
      return;
   }
   if(TimeLocal() - g_cotLastRefreshCheck < SQ_COT_REFRESH_CHECK_DELAY) {
      return;
   }
   g_cotLastRefreshCheck = TimeLocal();

   datetime oldestLastRecord = 0;
   for(int i = 0; i < ArraySize(g_cotSeries); i++) {
      if(g_cotSeries[i].count == 0) {
         continue;
      }
      datetime lastRecord = g_cotSeries[i].times[g_cotSeries[i].count - 1];
      if(oldestLastRecord == 0 || lastRecord < oldestLastRecord) {
         oldestLastRecord = lastRecord;
      }
   }

   if(oldestLastRecord > 0 && TimeCurrent() < oldestLastRecord + SQ_COT_REFRESH_AGE) {
      return;
   }

   string error = "";
   if(!sqCOTDownloadAll(error)) {
      Print("COT: weekly refresh failed: ", error, ". The strategy continues trading on the last downloaded data.");
   }
}

//+------------------------------------------------------------------+
//| One POST request for all registered identifiers. On success the  |
//| series arrays are replaced and the CSV cache files rewritten.    |
//+------------------------------------------------------------------+
bool sqCOTDownloadAll(string &errorMessage) {
   string identifiers = "";
   for(int i = 0; i < ArraySize(g_cotSeries); i++) {
      if(i > 0) {
         identifiers = identifiers + ",";
      }
      identifiers = identifiers + g_cotSeries[i].id;
   }

   string body = "license=" + COTLicenseCode + "&id=" + identifiers + "&p=mt5&acc=" + IntegerToString(AccountInfoInteger(ACCOUNT_LOGIN)) + "&v=1";
   string headers = "Content-Type: application/x-www-form-urlencoded\r\n";

   char post[];
   char result[];
   string resultHeaders;

   StringToCharArray(body, post, 0, StringLen(body));

   ResetLastError();
   int status = WebRequest("POST", COTServerUrl, headers, 10000, post, result, resultHeaders);

   if(status == -1) {
      int err = GetLastError();
      if(err == 4014 || err == 4060) {
         // URL not whitelisted in the terminal options
         g_cotState = SQ_COT_STATE_ERR_CONFIG;
         sqCOTAlertOnce("WebRequest to " + COTServerUrl + " is not allowed. Add the URL to Tools -> Options -> Expert Advisors -> 'Allow WebRequest for listed URL' and restart the EA. The strategy will not trade.");
         errorMessage = "WebRequest not allowed";
         return false;
      }
      errorMessage = "network error " + IntegerToString(err);
      return false;
   }

   string response = CharArrayToString(result, 0, WHOLE_ARRAY, CP_UTF8);

   if(status != 200) {
      if(StringFind(response, "ERROR;LICENSE;") == 0) {
         g_cotState = SQ_COT_STATE_ERR_LICENSE;
         sqCOTAlertOnce("COT license error: " + StringSubstr(response, 14) + " The strategy will not trade.");
         errorMessage = "license rejected";
         return false;
      }
      errorMessage = "server returned status " + IntegerToString(status);
      return false;
   }

   if(!sqCOTParseCsv(response)) {
      errorMessage = "cannot parse COT data response";
      return false;
   }

   // an identifier unknown to the server yields an empty series - trading on permanent zeros would be wrong
   for(int i = 0; i < ArraySize(g_cotSeries); i++) {
      if(g_cotSeries[i].count == 0) {
         g_cotState = SQ_COT_STATE_ERR_CONFIG;
         sqCOTAlertOnce("COT data for identifier '" + g_cotSeries[i].id + "' are not available on the server. The strategy will not trade.");
         errorMessage = "unknown COT identifier " + g_cotSeries[i].id;
         return false;
      }
   }

   sqCOTWriteCacheFiles();

   return true;
}

//+------------------------------------------------------------------+
//| Response format: header line, then                               |
//| identifier;yyyy-MM-dd;cpihedg;ctihedg;cpispec;ctispec;cpismall   |
//| Rows are grouped by identifier and sorted ascending by date.     |
//+------------------------------------------------------------------+
bool sqCOTParseCsv(string csv) {
   string lines[];
   int lineCount = StringSplit(csv, '\n', lines);

   if(lineCount < 1 || StringFind(lines[0], "identifier;date;") != 0) {
      return false;
   }

   for(int i = 0; i < ArraySize(g_cotSeries); i++) {
      g_cotSeries[i].count = 0;
      ArrayResize(g_cotSeries[i].times, 0);
      ArrayResize(g_cotSeries[i].values, 0);
   }

   int totalRecords = 0;
   for(int l = 1; l < lineCount; l++) {
      if(sqCOTAppendCsvLine(lines[l])) {
         totalRecords++;
      }
   }

   return totalRecords > 0;
}

//+------------------------------------------------------------------+

bool sqCOTAppendCsvLine(string line) {
   StringTrimRight(line);
   if(line == "") {
      return false;
   }

   string parts[];
   if(StringSplit(line, ';', parts) != 2 + SQ_COT_OUTPUTS) {
      return false;
   }

   int idx = sqCOTFindSeries(parts[0]);
   if(idx < 0) {
      return false;
   }

   datetime time = sqCOTParseDate(parts[1]);
   if(time <= 0) {
      return false;
   }

   int count = g_cotSeries[idx].count;
   ArrayResize(g_cotSeries[idx].times, count + 1, 1024);
   ArrayResize(g_cotSeries[idx].values, (count + 1) * SQ_COT_OUTPUTS, 1024 * SQ_COT_OUTPUTS);

   g_cotSeries[idx].times[count] = time;
   for(int v = 0; v < SQ_COT_OUTPUTS; v++) {
      g_cotSeries[idx].values[count * SQ_COT_OUTPUTS + v] = StringToDouble(parts[2 + v]);
   }
   g_cotSeries[idx].count = count + 1;

   return true;
}

//+------------------------------------------------------------------+

datetime sqCOTParseDate(string date) {
   // yyyy-MM-dd -> yyyy.MM.dd for StringToTime
   StringReplace(date, "-", ".");
   return StringToTime(date);
}

//+------------------------------------------------------------------+
//| Cache file (one per identifier, in the common Files folder):     |
//|   SQCOT;1;identifier;downloadUnixTime                            |
//|   followed by the server CSV rows of this identifier             |
//+------------------------------------------------------------------+
string sqCOTCacheFileName(string identifier) {
   return "SQ_COT_" + identifier + ".csv";
}

//+------------------------------------------------------------------+

bool sqCOTReadCacheFile(int idx) {
   string fileName = sqCOTCacheFileName(g_cotSeries[idx].id);

   int handle = FileOpen(fileName, FILE_READ|FILE_TXT|FILE_ANSI|FILE_COMMON|FILE_SHARE_READ|FILE_SHARE_WRITE);
   if(handle == INVALID_HANDLE) {
      return false;
   }

   g_cotSeries[idx].count = 0;
   ArrayResize(g_cotSeries[idx].times, 0);
   ArrayResize(g_cotSeries[idx].values, 0);

   bool headerOk = false;
   if(!FileIsEnding(handle)) {
      string header = FileReadString(handle);
      headerOk = (StringFind(header, "SQCOT;1;" + g_cotSeries[idx].id + ";") == 0);
   }

   if(headerOk) {
      while(!FileIsEnding(handle)) {
         sqCOTAppendCsvLine(FileReadString(handle));
      }
   }

   FileClose(handle);

   if(!headerOk || g_cotSeries[idx].count == 0) {
      // corrupted or foreign cache file - treat as missing
      g_cotSeries[idx].count = 0;
      return false;
   }

   return true;
}

//+------------------------------------------------------------------+

void sqCOTWriteCacheFiles() {
   for(int i = 0; i < ArraySize(g_cotSeries); i++) {
      if(g_cotSeries[i].count == 0) {
         continue;
      }

      string fileName = sqCOTCacheFileName(g_cotSeries[i].id);

      int handle = FileOpen(fileName, FILE_WRITE|FILE_TXT|FILE_ANSI|FILE_COMMON);
      if(handle == INVALID_HANDLE) {
         Print("COT: cannot write cache file ", fileName, ", error ", GetLastError());
         continue;
      }

      FileWriteString(handle, "SQCOT;1;" + g_cotSeries[i].id + ";" + IntegerToString((int) TimeLocal()) + "\n");

      for(int r = 0; r < g_cotSeries[i].count; r++) {
         string date = TimeToString(g_cotSeries[i].times[r], TIME_DATE);
         StringReplace(date, ".", "-");

         string line = g_cotSeries[i].id + ";" + date;
         for(int v = 0; v < SQ_COT_OUTPUTS; v++) {
            line = line + ";" + sqCOTFormatValue(g_cotSeries[i].values[r * SQ_COT_OUTPUTS + v]);
         }

         FileWriteString(handle, line + "\n");
      }

      FileClose(handle);
   }
}

//+------------------------------------------------------------------+

string sqCOTFormatValue(double value) {
   string formatted = DoubleToString(value, 8);

   // trim trailing zeros and a trailing decimal point
   int len = StringLen(formatted);
   while(len > 1 && StringSubstr(formatted, len - 1, 1) == "0") {
      len--;
   }
   if(len > 1 && StringSubstr(formatted, len - 1, 1) == ".") {
      len--;
   }

   return StringSubstr(formatted, 0, len);
}

//+------------------------------------------------------------------+

void sqCOTAlertOnce(string message) {
   Print("COT: ", message);

   if(!g_cotAlertShown && !sqCOTIsTester()) {
      Alert("COT: " + message);
   }
   g_cotAlertShown = true;
}
