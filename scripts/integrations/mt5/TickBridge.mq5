#property copyright "HaruQuantAI"
#property version   "2.01"
#property strict

input string InpServerHost       = "127.0.0.1";
input uint   InpServerPort       = 9001;
input uint   InpConnectTimeoutMs = 1000;
input int    InpIntervalSeconds  = 1;
input string InpSourceId         = "mt5-terminal-1";
input string InpAuthToken        = "";
input string InpSymbols          = "EURUSD,GBPUSD,USDJPY,XAUUSD";
input bool   InpLogSnapshots     = false;

#define BOOK_MAX_LEVELS 50

int    g_socket = INVALID_HANDLE;
ulong  g_sequence = 0;
ulong  g_book_sequence = 0;
ulong  g_revision = 0;
string g_symbols[];
bool   g_book_subscribed[];
string g_receive_buffer = "";
ulong  g_last_heartbeat_ms = 0;

//+------------------------------------------------------------------+
//| Expert initialization                                             |
//+------------------------------------------------------------------+
int OnInit()
  {
   if(InpIntervalSeconds < 1)
     {
      Print("InpIntervalSeconds must be at least 1");
      return INIT_PARAMETERS_INCORRECT;
     }
   if(StringLen(InpServerHost) == 0 || StringLen(InpSourceId) == 0 ||
      StringLen(InpAuthToken) == 0)
     {
      Print("Server host, source ID, and authentication token are required");
      return INIT_PARAMETERS_INCORRECT;
     }
   if(!ParseSymbols())
      return INIT_PARAMETERS_INCORRECT;
   if(!EventSetTimer(InpIntervalSeconds))
     {
      PrintFormat("EventSetTimer failed. Error %d", GetLastError());
      return INIT_FAILED;
     }

   // A failed initial connection is not fatal. OnTimer retries every second.
   EnsureConnected();
   return INIT_SUCCEEDED;
  }

//+------------------------------------------------------------------+
//| Expert deinitialization                                           |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
  {
   EventKillTimer();
   ReleaseAllBooks();
   CloseSocket();
  }

//+------------------------------------------------------------------+
//| Release every currently held Depth-of-Market subscription         |
//+------------------------------------------------------------------+
void ReleaseAllBooks()
  {
   for(int index = 0; index < ArraySize(g_symbols); index++)
      if(g_book_subscribed[index])
         MarketBookRelease(g_symbols[index]);
  }

//+------------------------------------------------------------------+
//| One latest multi-symbol snapshot per configured timer interval    |
//+------------------------------------------------------------------+
void OnTimer()
  {
   if(!EnsureConnected())
      return;

   if(!ProcessCommands())
     {
      CloseSocket();
      return;
     }
   if(g_revision == 0)
      return;
   if(ArraySize(g_symbols) == 0)
     {
      const ulong now_ms = GetTickCount64();
      if(now_ms - g_last_heartbeat_ms >= 3000)
        {
         if(!SendLine(BuildHeartbeatJson()))
           {
            PrintFormat("Idle heartbeat send failed. Error %d", GetLastError());
            CloseSocket();
            return;
           }
         g_last_heartbeat_ms = now_ms;
        }
      return;
     }

   const ulong next_sequence = g_sequence + 1;
   const string message = BuildSnapshotJson(next_sequence);
   if(!SendLine(message))
     {
      PrintFormat("Snapshot send failed. Error %d", GetLastError());
      CloseSocket();
      return;
     }
   g_sequence = next_sequence;
   if(InpLogSnapshots)
      PrintFormat("Sent MT5 snapshot %I64u for %d symbols",
                  g_sequence, ArraySize(g_symbols));

   const ulong next_book_sequence = g_book_sequence + 1;
   const string book_message = BuildBookJson(next_book_sequence);
   if(!SendLine(book_message))
     {
      PrintFormat("Book send failed. Error %d", GetLastError());
      CloseSocket();
      return;
     }
   g_book_sequence = next_book_sequence;
  }

//+------------------------------------------------------------------+
//| Parse and select exact broker-native symbol names                 |
//+------------------------------------------------------------------+
bool ParseSymbols()
  {
   string raw[];
   const ushort separator = StringGetCharacter(",", 0);
   const int count = StringSplit(InpSymbols, separator, raw);
   if(count <= 0)
     {
      Print("InpSymbols must contain at least one symbol");
      return false;
     }

   ArrayResize(g_symbols, 0);
   for(int index = 0; index < count; index++)
     {
      string symbol = raw[index];
      StringTrimLeft(symbol);
      StringTrimRight(symbol);
      if(StringLen(symbol) == 0)
         continue;
      if(ContainsSymbol(symbol))
        {
         PrintFormat("Duplicate configured symbol: %s", symbol);
         return false;
        }
      if(!SymbolSelect(symbol, true))
        {
         PrintFormat("SymbolSelect failed for %s. Error %d",
                     symbol, GetLastError());
         return false;
        }
      const int size = ArraySize(g_symbols);
      ArrayResize(g_symbols, size + 1);
      ArrayResize(g_book_subscribed, size + 1);
      g_symbols[size] = symbol;
      // A failed MarketBookAdd means this broker/symbol publishes no book;
      // BuildBookJson reports it as an explicit per-symbol error, never a
      // synthesized empty book.
      g_book_subscribed[size] = MarketBookAdd(symbol);
      if(!g_book_subscribed[size])
         PrintFormat("MarketBookAdd unavailable for %s. Error %d",
                     symbol, GetLastError());
     }

   if(ArraySize(g_symbols) == 0)
     {
      Print("InpSymbols did not contain a usable symbol");
      return false;
     }
   return true;
  }

//+------------------------------------------------------------------+
//| Check whether the configured list already contains a symbol       |
//+------------------------------------------------------------------+
bool ContainsSymbol(const string symbol)
  {
   for(int index = 0; index < ArraySize(g_symbols); index++)
      if(g_symbols[index] == symbol)
         return true;
   return false;
  }

//+------------------------------------------------------------------+
//| Establish/re-establish one persistent TCP connection              |
//+------------------------------------------------------------------+
bool EnsureConnected()
  {
   if(g_socket != INVALID_HANDLE && SocketIsConnected(g_socket))
      return true;

   CloseSocket();
   ResetLastError();
   g_socket = SocketCreate(SOCKET_DEFAULT);
   if(g_socket == INVALID_HANDLE)
     {
      PrintFormat("SocketCreate failed. Error %d", GetLastError());
      return false;
     }
   if(!SocketConnect(g_socket, InpServerHost, InpServerPort,
                     InpConnectTimeoutMs))
     {
      PrintFormat("SocketConnect to %s:%u failed. Error %d",
                  InpServerHost, InpServerPort, GetLastError());
      CloseSocket();
      return false;
     }
   g_revision = 0;
   g_receive_buffer = "";
   if(!SendLine(BuildHelloJson()))
     {
      PrintFormat("MT5 bridge hello send failed. Error %d", GetLastError());
      CloseSocket();
      return false;
     }
   PrintFormat("Connected MT5 snapshot bridge to %s:%u",
               InpServerHost, InpServerPort);
   return true;
  }

//+------------------------------------------------------------------+
//| Release the current socket handle                                 |
//+------------------------------------------------------------------+
void CloseSocket()
  {
   if(g_socket != INVALID_HANDLE)
     {
      SocketClose(g_socket);
      g_socket = INVALID_HANDLE;
     }
  }

//+------------------------------------------------------------------+
//| Send one UTF-8 newline-delimited JSON message                     |
//+------------------------------------------------------------------+
bool SendLine(const string payload)
  {
   if(g_socket == INVALID_HANDLE || !SocketIsConnected(g_socket))
      return false;

   uchar bytes[];
   const int copied = StringToCharArray(payload + "\n", bytes, 0,
                                        WHOLE_ARRAY, CP_UTF8);
   if(copied <= 1)
      return false;

   // StringToCharArray with WHOLE_ARRAY also copies terminal zero.
   const int payload_length = copied - 1;
   int offset = 0;
   while(offset < payload_length)
     {
      const int remaining = payload_length - offset;
      uchar chunk[];
      ArrayResize(chunk, remaining);
      ArrayCopy(chunk, bytes, 0, offset, remaining);
      const int sent = SocketSend(g_socket, chunk, (uint)remaining);
      if(sent <= 0)
         return false;
      offset += sent;
     }
   return true;
  }

//+------------------------------------------------------------------+
//| Build the authenticated first message                             |
//+------------------------------------------------------------------+
string BuildHelloJson()
  {
   return "{\"type\":\"hello\","
          "\"protocol\":\"haruquant.mt5.snapshot.v2\","
          "\"source_id\":\"" + JsonEscape(InpSourceId) + "\","
          "\"token\":\"" + JsonEscape(InpAuthToken) + "\","
          "\"interval_seconds\":" + IntegerToString(InpIntervalSeconds) + ","
          "\"symbols\":" + BuildSymbolsJson() + "}";
  }

//+------------------------------------------------------------------+
//| Broker-to-UTC millisecond offset for time_msc normalization      |
//| MT5 reports tick time in the broker/server timezone coordinate   |
//| rather than as a pure Unix UTC epoch. TimeGMT() is real UTC; the |
//| difference (TimeCurrent - TimeGMT) is the offset we must remove  |
//| so the Python gateway can compute ages against its UTC clock.    |
//+------------------------------------------------------------------+
long UtcOffsetMs()
  {
   return (long)(TimeCurrent() - TimeGMT()) * 1000;
  }

//+------------------------------------------------------------------+
//| Build one latest quote per symbol                                 |
//+------------------------------------------------------------------+
string BuildSnapshotJson(const ulong sequence)
  {
   const long utc_offset_ms = UtcOffsetMs();
   string quotes = "[";
   string errors = "[";
   bool first_quote = true;
   bool first_error = true;

   for(int index = 0; index < ArraySize(g_symbols); index++)
     {
      const string symbol = g_symbols[index];
      MqlTick tick = {};
      ResetLastError();
      const bool read_ok = SymbolInfoTick(symbol, tick);
      if(!read_ok || tick.time_msc <= 0 || tick.bid <= 0.0 || tick.ask <= 0.0)
        {
         if(!first_error)
            errors += ",";
         errors += "{\"symbol\":\"" + JsonEscape(symbol) +
                   "\",\"code\":" + IntegerToString(GetLastError()) + "}";
         first_error = false;
         continue;
        }

      const int digits = (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS);
      if(!first_quote)
         quotes += ",";
      quotes += "{\"symbol\":\"" + JsonEscape(symbol) + "\","
                "\"bid\":" + DoubleToString(tick.bid, digits) + ","
                "\"ask\":" + DoubleToString(tick.ask, digits) + ","
                "\"last\":" + DoubleToString(tick.last, digits) + ","
                "\"volume\":" + IntegerToString((long)tick.volume) + ","
                "\"volume_real\":" + DoubleToString(tick.volume_real, 8) + ","
                "\"time_msc\":" + IntegerToString((long)(tick.time_msc - utc_offset_ms)) + ","
                "\"flags\":" + IntegerToString((int)tick.flags) + ","
                "\"digits\":" + IntegerToString(digits) + "}";
      first_quote = false;
     }

   quotes += "]";
   errors += "]";
   return "{\"type\":\"snapshot\","
          "\"protocol\":\"haruquant.mt5.snapshot.v2\","
          "\"sequence\":" + StringFormat("%I64u", sequence) + ","
          "\"revision\":" + StringFormat("%I64u", g_revision) + ","
          "\"quotes\":" + quotes + ","
          "\"errors\":" + errors + "}";
  }

//+------------------------------------------------------------------+
//| Build one Depth-of-Market read per subscribed symbol              |
//| A symbol whose MarketBookAdd failed (unsupported by this broker)  |
//| is reported as an explicit error, never a synthesized empty book. |
//| A subscribed symbol with zero current resting levels is a genuine |
//| empty book, reported as empty bids/asks, not an error.            |
//+------------------------------------------------------------------+
string BuildBookJson(const ulong sequence)
  {
   string books = "[";
   string errors = "[";
   bool first_book = true;
   bool first_error = true;

   for(int index = 0; index < ArraySize(g_symbols); index++)
     {
      const string symbol = g_symbols[index];
      if(!g_book_subscribed[index])
        {
         if(!first_error)
            errors += ",";
         errors += "{\"symbol\":\"" + JsonEscape(symbol) + "\",\"code\":0}";
         first_error = false;
         continue;
        }

      MqlBookInfo book[];
      ResetLastError();
      if(!MarketBookGet(symbol, book))
        {
         if(!first_error)
            errors += ",";
         errors += "{\"symbol\":\"" + JsonEscape(symbol) +
                   "\",\"code\":" + IntegerToString(GetLastError()) + "}";
         first_error = false;
         continue;
        }

      const int digits = (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS);
      const int book_depth = (int)SymbolInfoInteger(symbol, SYMBOL_TICKS_BOOKDEPTH);
      string bids = "[";
      string asks = "[";
      bool first_bid = true;
      bool first_ask = true;
      int bid_count = 0;
      int ask_count = 0;
      for(int level = 0; level < ArraySize(book); level++)
        {
         const double volume = book[level].volume_real > 0.0
            ? book[level].volume_real
            : (double)book[level].volume;
         if(book[level].type == BOOK_TYPE_BUY && bid_count < BOOK_MAX_LEVELS)
           {
            if(!first_bid)
               bids += ",";
            bids += "{\"price\":" + DoubleToString(book[level].price, digits) +
                    ",\"volume\":" + DoubleToString(volume, 8) + "}";
            first_bid = false;
            bid_count++;
           }
         else if(book[level].type == BOOK_TYPE_SELL && ask_count < BOOK_MAX_LEVELS)
           {
            if(!first_ask)
               asks += ",";
            asks += "{\"price\":" + DoubleToString(book[level].price, digits) +
                    ",\"volume\":" + DoubleToString(volume, 8) + "}";
            first_ask = false;
            ask_count++;
           }
        }
      bids += "]";
      asks += "]";

      if(!first_book)
         books += ",";
      books += "{\"symbol\":\"" + JsonEscape(symbol) + "\","
               "\"book_depth\":" + IntegerToString(book_depth) + ","
               "\"bids\":" + bids + ","
               "\"asks\":" + asks + "}";
      first_book = false;
     }

   books += "]";
   errors += "]";
   return "{\"type\":\"book\","
          "\"protocol\":\"haruquant.mt5.snapshot.v2\","
          "\"sequence\":" + StringFormat("%I64u", sequence) + ","
          "\"revision\":" + StringFormat("%I64u", g_revision) + ","
          "\"books\":" + books + ","
          "\"errors\":" + errors + "}";
  }

//+------------------------------------------------------------------+
//| Drain and apply complete newline-delimited subscription commands  |
//+------------------------------------------------------------------+
bool ProcessCommands()
  {
   while(SocketIsReadable(g_socket) > 0)
     {
      const uint available = SocketIsReadable(g_socket);
      uchar bytes[];
      const int received = SocketRead(g_socket, bytes, available, 10);
      if(received <= 0)
         return false;
      g_receive_buffer += CharArrayToString(bytes, 0, received, CP_UTF8);
      if(StringLen(g_receive_buffer) > 1048576)
         return false;
     }

   int newline = StringFind(g_receive_buffer, "\n");
   while(newline >= 0)
     {
      string line = StringSubstr(g_receive_buffer, 0, newline);
      g_receive_buffer = StringSubstr(g_receive_buffer, newline + 1);
      if(StringLen(line) > 0 && StringSubstr(line, StringLen(line) - 1) == "\r")
         line = StringSubstr(line, 0, StringLen(line) - 1);
      if(StringLen(line) > 0 && !ApplySetSymbols(line))
         return false;
      newline = StringFind(g_receive_buffer, "\n");
     }
   return true;
  }

//+------------------------------------------------------------------+
//| Apply one strict complete-set command and acknowledge its result  |
//+------------------------------------------------------------------+
bool ApplySetSymbols(const string message)
  {
   if(StringFind(message, "\"type\":\"set_symbols\"") < 0 ||
      StringFind(message, "\"protocol\":\"haruquant.mt5.snapshot.v2\"") < 0)
      return false;
   const string revision_marker = "\"revision\":";
   const string symbols_marker = "\"symbols\":[";
   const int revision_start = StringFind(message, revision_marker);
   const int symbols_start = StringFind(message, symbols_marker);
   if(revision_start < 0 || symbols_start < 0)
      return false;
   const int value_start = revision_start + StringLen(revision_marker);
   const int value_end = StringFind(message, ",", value_start);
   if(value_end < 0)
      return false;
   const ulong revision = (ulong)StringToInteger(
      StringSubstr(message, value_start, value_end - value_start));
   if(revision == 0)
      return false;
   if(revision < g_revision)
      return true;

   const int array_start = symbols_start + StringLen(symbols_marker);
   const int array_end = StringFind(message, "]", array_start);
   if(array_end < 0)
      return false;
   string requested[];
   const string body = StringSubstr(message, array_start, array_end - array_start);
   if(StringLen(body) > 0)
     {
      string raw[];
      const ushort comma = StringGetCharacter(",", 0);
      const int count = StringSplit(body, comma, raw);
      ArrayResize(requested, count);
      for(int index = 0; index < count; index++)
        {
         string item = raw[index];
         StringTrimLeft(item);
         StringTrimRight(item);
         if(StringLen(item) < 2 || StringSubstr(item, 0, 1) != "\"" ||
            StringSubstr(item, StringLen(item) - 1) != "\"")
            return false;
         requested[index] = StringSubstr(item, 1, StringLen(item) - 2);
        }
     }

   string applied[];
   bool   applied_book[];
   string rejected_symbols[];
   int rejected_codes[];
   for(int index = 0; index < ArraySize(requested); index++)
     {
      ResetLastError();
      if(SymbolSelect(requested[index], true))
        {
         const int size = ArraySize(applied);
         ArrayResize(applied, size + 1);
         ArrayResize(applied_book, size + 1);
         applied[size] = requested[index];
         applied_book[size] = MarketBookAdd(requested[index]);
         if(!applied_book[size])
            PrintFormat("MarketBookAdd unavailable for %s. Error %d",
                        requested[index], GetLastError());
        }
      else
        {
         const int size = ArraySize(rejected_symbols);
         ArrayResize(rejected_symbols, size + 1);
         ArrayResize(rejected_codes, size + 1);
         rejected_symbols[size] = requested[index];
         rejected_codes[size] = GetLastError();
        }
     }
   for(int index = 0; index < ArraySize(g_symbols); index++)
     {
      bool retained = false;
      for(int requested_index = 0; requested_index < ArraySize(applied); requested_index++)
         if(g_symbols[index] == applied[requested_index])
            retained = true;
      if(!retained)
        {
         if(g_book_subscribed[index])
            MarketBookRelease(g_symbols[index]);
         SymbolSelect(g_symbols[index], false);
        }
     }
   ArrayResize(g_symbols, ArraySize(applied));
   ArrayCopy(g_symbols, applied);
   ArrayResize(g_book_subscribed, ArraySize(applied_book));
   ArrayCopy(g_book_subscribed, applied_book);
   g_revision = revision;
   return SendLine(BuildSymbolsAppliedJson(rejected_symbols, rejected_codes));
  }

//+------------------------------------------------------------------+
//| Build one acknowledgment for the currently applied revision      |
//+------------------------------------------------------------------+
string BuildSymbolsAppliedJson(string &rejected_symbols[], int &rejected_codes[])
  {
   string errors = "[";
   for(int index = 0; index < ArraySize(rejected_symbols); index++)
     {
      if(index > 0)
         errors += ",";
      errors += "{\"symbol\":\"" + JsonEscape(rejected_symbols[index]) +
                "\",\"code\":" + IntegerToString(rejected_codes[index]) + "}";
     }
   errors += "]";
   return "{\"type\":\"symbols_applied\","
          "\"protocol\":\"haruquant.mt5.snapshot.v2\","
          "\"revision\":" + StringFormat("%I64u", g_revision) + ","
          "\"symbols\":" + BuildSymbolsJson() + ","
          "\"errors\":" + errors + "}";
  }

//+------------------------------------------------------------------+
//| Keep the paused control connection healthy without reading ticks |
//+------------------------------------------------------------------+
string BuildHeartbeatJson()
  {
   return "{\"type\":\"heartbeat\","
          "\"protocol\":\"haruquant.mt5.snapshot.v2\","
          "\"revision\":" + StringFormat("%I64u", g_revision) + "}";
  }

//+------------------------------------------------------------------+
//| Encode configured symbols as a JSON array                         |
//+------------------------------------------------------------------+
string BuildSymbolsJson()
  {
   string result = "[";
   for(int index = 0; index < ArraySize(g_symbols); index++)
     {
      if(index > 0)
         result += ",";
      result += "\"" + JsonEscape(g_symbols[index]) + "\"";
     }
   return result + "]";
  }

//+------------------------------------------------------------------+
//| Minimal JSON string escaping                                      |
//+------------------------------------------------------------------+
string JsonEscape(const string value)
  {
   string result = "";
   for(int index = 0; index < StringLen(value); index++)
     {
      const ushort character = StringGetCharacter(value, index);
      if(character == 34)
         result += "\\\"";
      else if(character == 92)
         result += "\\\\";
      else if(character == 8)
         result += "\\b";
      else if(character == 9)
         result += "\\t";
      else if(character == 10)
         result += "\\n";
      else if(character == 12)
         result += "\\f";
      else if(character == 13)
         result += "\\r";
      else if(character < 32)
         result += StringFormat("\\u%04X", (int)character);
      else
         result += StringSubstr(value, index, 1);
     }
   return result;
  }
