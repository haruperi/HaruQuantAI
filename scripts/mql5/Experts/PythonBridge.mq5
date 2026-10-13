//+------------------------------------------------------------------+
//| PythonBridge.mq5                                                 |
//| Native MQL5 Standard Library Trade Classes <-> Python bridge     |
//+------------------------------------------------------------------+
#property strict
#property version   "1.00"
#property description "Connects as a TCP client to the loopback Python bridge."
#property description "Add 127.0.0.1 to Tools > Options > Expert Advisors > allowed URLs/addresses if required by your terminal build."

#include <Trade/Trade.mqh>
#include <Trade/AccountInfo.mqh>
#include <Trade/SymbolInfo.mqh>
#include <Trade/OrderInfo.mqh>
#include <Trade/HistoryOrderInfo.mqh>
#include <Trade/PositionInfo.mqh>
#include <Trade/DealInfo.mqh>
#include <Trade/TerminalInfo.mqh>

input string InpBridgeHost       = "127.0.0.1";
input uint   InpBridgePort       = 8765;
input string InpAuthToken        = "P8H5yPraTVSz4vkuaMVgWN8qcfeXUswuxIV70QES0Co";
input uint   InpConnectTimeoutMs = 2000;
input uint   InpReconnectMs      = 1000;
input bool   InpVerboseReconnectLogs = false;
input uint   InpPollMs           = 20;
input bool   InpForceLockRecovery= false;

int    g_socket = INVALID_HANDLE;
string g_rx = "";
ulong  g_last_connect_try = 0;
int    g_last_connect_error = -1;
bool   g_authenticated = false;
string g_lock_name = "";
double g_lock_owner = 0.0;
bool   g_lock_owned = false;

class CBridgeTrade : public CTrade
  {
public:
   void SetCheckResult(const MqlTradeCheckResult &res) { m_check_result=res; }
   ulong GetDeviation() const { return m_deviation; }
   ENUM_ORDER_TYPE_FILLING GetTypeFilling() const { return m_type_filling; }
   ulong GetMagic() const { return m_magic; }
  };

// Per-proxy native objects. Each Python proxy ID gets its own C* instance.
string g_trade_ids[];        CBridgeTrade *g_trade_objs[];
string g_account_ids[];      CAccountInfo *g_account_objs[];
string g_symbol_ids[];       CSymbolInfo *g_symbol_objs[];
string g_order_ids[];        COrderInfo *g_order_objs[];
string g_history_ids[];      CHistoryOrderInfo *g_history_objs[];
string g_position_ids[];     CPositionInfo *g_position_objs[];
string g_deal_ids[];         CDealInfo *g_deal_objs[];
string g_terminal_ids[];     CTerminalInfo *g_terminal_objs[];

// request_id -> Python command_id correlation for OnTradeTransaction.
ulong  g_request_ids[];
string g_request_commands[];

//--------------------------- JSON / wire helpers -----------------------------
string JsonDecodeString(string raw);
string JsonEscape(const string value)
  {
   string out="";
   int n=StringLen(value);
   for(int i=0;i<n;i++)
     {
      ushort c=StringGetCharacter(value,i);
      if(c=='\\') out+="\\\\";
      else if(c=='"') out+="\\\"";
      else if(c=='\n') out+="\\n";
      else if(c=='\r') out+="\\r";
      else if(c=='\t') out+="\\t";
      else out+=ShortToString(c);
     }
   return out;
  }

string JsonQuote(const string value)
  {
   string safe=value;
   if(StringFind(safe,"@")==0) safe="@"+safe;
   return "\""+JsonEscape(safe)+"\"";
  }

bool WildcardMatch(const string text, const string pattern)
  {
   int s=0, p=0, s_len=StringLen(text), p_len=StringLen(pattern);
   int star_idx=-1, match=0;
   while(s < s_len)
     {
      if(p < p_len && (StringGetCharacter(pattern,p)=='?' || StringGetCharacter(pattern,p)==StringGetCharacter(text,s)))
        {
         s++; p++;
        }
      else if(p < p_len && StringGetCharacter(pattern,p)=='*')
        {
         star_idx = p;
         match = s;
         p++;
        }
      else if(star_idx != -1)
        {
         p = star_idx + 1;
         match++;
         s = match;
        }
      else return false;
     }
   while(p < p_len && StringGetCharacter(pattern,p)=='*') p++;
   return p == p_len;
  }

bool MatchSymbolGroup(const string name, const string group)
  {
   if(StringLen(group)==0 || group=="*") return true;
   string patterns[];
   int count=StringSplit(group,',',patterns);
   if(count<=0) return true;

   bool has_includes=false;
   bool matched_include=false;

   for(int i=0; i<count; i++)
     {
      string pat=Trim(patterns[i]);
      if(StringLen(pat)==0) continue;
      if(StringFind(pat,"!")==0)
        {
         string excl=StringSubstr(pat,1);
         if(WildcardMatch(name,excl)) return false;
        }
      else
        {
         has_includes=true;
         if(!matched_include && WildcardMatch(name,pat)) matched_include=true;
        }
     }
   if(has_includes && !matched_include) return false;
   return true;
  }

string ULongToStringExact(ulong value)
  {
   if(value==0) return "0";
   string out="";
   while(value>0)
     {
      uint digit=(uint)(value%10);
      out=IntegerToString((int)digit)+out;
      value/=10;
     }
   return out;
  }

ulong ParseULongExact(string value)
  {
   value=JsonDecodeString(value);
   if(StringFind(value,"@i64:")==0 || StringFind(value,"@u64:")==0)
      value=StringSubstr(value,5);
   ulong result=0;
   int n=StringLen(value);
   for(int i=0;i<n;i++)
     {
      ushort c=StringGetCharacter(value,i);
      if(c<'0' || c>'9') continue;
      result=result*10+(ulong)(c-'0');
     }
   return result;
  }

string JsonULong(const ulong value) { return "\"@u64:"+ULongToStringExact(value)+"\""; }
string JsonLong(const long value) { return "\"@i64:"+IntegerToString(value)+"\""; }
string JsonDouble(const double value) { return DoubleToString(value,16); }
string JsonBool(const bool value) { return value ? "true" : "false"; }

bool IsSpace(ushort c) { return c==' ' || c=='\t' || c=='\r' || c=='\n'; }

string Trim(string value)
  {
   StringTrimLeft(value);
   StringTrimRight(value);
   return value;
  }

int SkipSpaces(const string s,int p)
  {
   int n=StringLen(s);
   while(p<n && IsSpace(StringGetCharacter(s,p))) p++;
   return p;
  }

int FindStringEnd(const string s,int start)
  {
   bool esc=false;
   int n=StringLen(s);
   for(int i=start+1;i<n;i++)
     {
      ushort c=StringGetCharacter(s,i);
      if(esc) { esc=false; continue; }
      if(c=='\\') { esc=true; continue; }
      if(c=='"') return i;
     }
   return -1;
  }

string JsonDecodeString(string raw)
  {
   raw=Trim(raw);
   if(StringLen(raw)>=2 && StringGetCharacter(raw,0)=='"' && StringGetCharacter(raw,StringLen(raw)-1)=='"')
      raw=StringSubstr(raw,1,StringLen(raw)-2);
   string out="";
   bool esc=false;
   int n=StringLen(raw);
   for(int i=0;i<n;i++)
     {
      ushort c=StringGetCharacter(raw,i);
      if(!esc && c=='\\') { esc=true; continue; }
      if(esc)
        {
         if(c=='n') out+="\n";
         else if(c=='r') out+="\r";
         else if(c=='t') out+="\t";
         else out+=ShortToString(c);
         esc=false;
        }
      else out+=ShortToString(c);
     }
   // Python escapes application strings beginning with @ by doubling it.
   if(StringFind(out,"@@")==0) out=StringSubstr(out,1);
   return out;
  }

bool JsonExtractRaw(const string json,const string key,string &out)
  {
   string needle="\""+key+"\"";
   int p=StringFind(json,needle);
   if(p<0) return false;
   p=StringFind(json,":",p+StringLen(needle));
   if(p<0) return false;
   p=SkipSpaces(json,p+1);
   int n=StringLen(json);
   if(p>=n) return false;
   ushort first=StringGetCharacter(json,p);
   if(first=='"')
     {
      int e=FindStringEnd(json,p);
      if(e<0) return false;
      out=StringSubstr(json,p,e-p+1);
      return true;
     }
   if(first=='[' || first=='{')
     {
      ushort open=first;
      ushort close=(first=='[' ? ']' : '}');
      int depth=0; bool in_string=false; bool esc=false;
      for(int i=p;i<n;i++)
        {
         ushort c=StringGetCharacter(json,i);
         if(in_string)
           {
            if(esc) { esc=false; continue; }
            if(c=='\\') { esc=true; continue; }
            if(c=='"') in_string=false;
            continue;
           }
         if(c=='"') { in_string=true; continue; }
         if(c==open) depth++;
         if(c==close)
           {
            depth--;
            if(depth==0)
              {
               out=StringSubstr(json,p,i-p+1);
               return true;
              }
           }
        }
      return false;
     }
   int e=p;
   while(e<n)
     {
      ushort c=StringGetCharacter(json,e);
      if(c==',' || c=='}') break;
      e++;
     }
   out=Trim(StringSubstr(json,p,e-p));
   return true;
  }

bool JsonGetString(const string json,const string key,string &out)
  {
   string raw;
   if(!JsonExtractRaw(json,key,raw)) return false;
   out=JsonDecodeString(raw);
   return true;
  }

long JsonGetInt(const string json,const string key,const long def=0)
  {
   string raw;
   if(!JsonExtractRaw(json,key,raw)) return def;
   raw=JsonDecodeString(raw);
   if(StringFind(raw,"@i64:")==0 || StringFind(raw,"@u64:")==0) raw=StringSubstr(raw,5);
   return (long)StringToInteger(raw);
  }

ulong JsonGetULong(const string json,const string key,const ulong def=0)
  {
   string raw;
   if(!JsonExtractRaw(json,key,raw)) return def;
   return ParseULongExact(raw);
  }

double JsonGetDouble(const string json,const string key,const double def=0.0)
  {
   string raw;
   if(!JsonExtractRaw(json,key,raw)) return def;
   raw=JsonDecodeString(raw);
   if(StringFind(raw,"@i64:")==0 || StringFind(raw,"@u64:")==0) raw=StringSubstr(raw,5);
   return StringToDouble(raw);
  }

bool JsonArrayTokens(const string raw,string &tokens[])
  {
   ArrayResize(tokens,0);
   string s=Trim(raw);
   if(StringLen(s)<2 || StringGetCharacter(s,0)!='[') return false;
   int end=StringLen(s)-1;
   int start=1; bool in_string=false; bool esc=false; int depth=0;
   for(int i=1;i<end;i++)
     {
      ushort c=StringGetCharacter(s,i);
      if(in_string)
        {
         if(esc) { esc=false; continue; }
         if(c=='\\') { esc=true; continue; }
         if(c=='"') in_string=false;
         continue;
        }
      if(c=='"') { in_string=true; continue; }
      if(c=='[' || c=='{') depth++;
      else if(c==']' || c=='}') depth--;
      else if(c==',' && depth==0)
        {
         int n=ArraySize(tokens); ArrayResize(tokens,n+1);
         tokens[n]=Trim(StringSubstr(s,start,i-start));
         start=i+1;
        }
     }
   string tail=Trim(StringSubstr(s,start,end-start));
   if(StringLen(tail)>0)
     {
      int n=ArraySize(tokens); ArrayResize(tokens,n+1); tokens[n]=tail;
     }
   return true;
  }

string ArgString(string &args[],int index,const string def="")
  {
   if(index<0 || index>=ArraySize(args)) return def;
   string raw=Trim(args[index]);
   if(raw=="null") return def;
   return JsonDecodeString(raw);
  }

long ArgLong(string &args[],int index,const long def=0)
  {
   if(index<0 || index>=ArraySize(args)) return def;
   string s=ArgString(args,index,"");
   if(StringFind(s,"@i64:")==0 || StringFind(s,"@u64:")==0) s=StringSubstr(s,5);
   if(StringLen(s)==0) return def;
   return StringToInteger(s);
  }

ulong ArgULong(string &args[],int index,const ulong def=0)
  {
   if(index<0 || index>=ArraySize(args)) return def;
   string s=ArgString(args,index,"");
   if(StringLen(s)==0) return def;
   return ParseULongExact(s);
  }

double ArgDouble(string &args[],int index,const double def=0.0)
  {
   if(index<0 || index>=ArraySize(args)) return def;
   string s=ArgString(args,index,"");
   if(StringLen(s)==0 || s=="null") return def;
   if(StringFind(s,"@i64:")==0 || StringFind(s,"@u64:")==0) s=StringSubstr(s,5);
   return StringToDouble(s);
  }

bool ArgBool(string &args[],int index,const bool def=false)
  {
   if(index<0 || index>=ArraySize(args)) return def;
   string s=ArgString(args,index,"");
   StringToLower(s);
   if(s=="true" || s=="1") return true;
   if(s=="false" || s=="0") return false;
   return def;
  }

bool ArgLooksInteger(string &args[],int index)
  {
   if(index<0 || index>=ArraySize(args)) return false;
   string raw=Trim(args[index]);
   string s=JsonDecodeString(raw);
   if(StringFind(s,"@i64:")==0 || StringFind(s,"@u64:")==0) return true;
   if(StringLen(raw)>0 && StringGetCharacter(raw,0)!='"')
     {
      ushort c=StringGetCharacter(raw,0);
      return (c>='0' && c<='9') || c=='-';
     }
   return false;
  }

ENUM_ORDER_TYPE ParseOrderType(string &args[],int index,const ENUM_ORDER_TYPE def=ORDER_TYPE_BUY)
  {
   string s=ArgString(args,index,"");
   if(StringFind(s,"@i64:")==0) return (ENUM_ORDER_TYPE)StringToInteger(StringSubstr(s,5));
   if(s=="ORDER_TYPE_BUY") return ORDER_TYPE_BUY;
   if(s=="ORDER_TYPE_SELL") return ORDER_TYPE_SELL;
   if(s=="ORDER_TYPE_BUY_LIMIT") return ORDER_TYPE_BUY_LIMIT;
   if(s=="ORDER_TYPE_SELL_LIMIT") return ORDER_TYPE_SELL_LIMIT;
   if(s=="ORDER_TYPE_BUY_STOP") return ORDER_TYPE_BUY_STOP;
   if(s=="ORDER_TYPE_SELL_STOP") return ORDER_TYPE_SELL_STOP;
   if(s=="ORDER_TYPE_BUY_STOP_LIMIT") return ORDER_TYPE_BUY_STOP_LIMIT;
   if(s=="ORDER_TYPE_SELL_STOP_LIMIT") return ORDER_TYPE_SELL_STOP_LIMIT;
   if(StringLen(s)>0) return (ENUM_ORDER_TYPE)StringToInteger(s);
   return def;
  }

ENUM_ORDER_TYPE_FILLING ParseFilling(string &args[],int index,const ENUM_ORDER_TYPE_FILLING def=ORDER_FILLING_FOK)
  {
   string s=ArgString(args,index,"");
   if(StringFind(s,"@i64:")==0) return (ENUM_ORDER_TYPE_FILLING)StringToInteger(StringSubstr(s,5));
   if(s=="ORDER_FILLING_FOK") return ORDER_FILLING_FOK;
   if(s=="ORDER_FILLING_IOC") return ORDER_FILLING_IOC;
   if(s=="ORDER_FILLING_RETURN") return ORDER_FILLING_RETURN;
   if(s=="ORDER_FILLING_BOC") return ORDER_FILLING_BOC;
   if(StringLen(s)>0) return (ENUM_ORDER_TYPE_FILLING)StringToInteger(s);
   return def;
  }

ENUM_ORDER_TYPE_TIME ParseOrderTime(string &args[],int index,const ENUM_ORDER_TYPE_TIME def=ORDER_TIME_GTC)
  {
   string s=ArgString(args,index,"");
   if(StringFind(s,"@i64:")==0) return (ENUM_ORDER_TYPE_TIME)StringToInteger(StringSubstr(s,5));
   if(s=="ORDER_TIME_GTC") return ORDER_TIME_GTC;
   if(s=="ORDER_TIME_DAY") return ORDER_TIME_DAY;
   if(s=="ORDER_TIME_SPECIFIED") return ORDER_TIME_SPECIFIED;
   if(s=="ORDER_TIME_SPECIFIED_DAY") return ORDER_TIME_SPECIFIED_DAY;
   if(StringLen(s)>0) return (ENUM_ORDER_TYPE_TIME)StringToInteger(s);
   return def;
  }

ENUM_LOG_LEVELS ParseLogLevel(string &args[],int index)
  {
   string s=ArgString(args,index,"");
   if(s=="LOG_LEVEL_NO") return LOG_LEVEL_NO;
   if(s=="LOG_LEVEL_ERRORS") return LOG_LEVEL_ERRORS;
   if(s=="LOG_LEVEL_ALL") return LOG_LEVEL_ALL;
   if(StringFind(s,"@i64:")==0) s=StringSubstr(s,5);
   return (ENUM_LOG_LEVELS)StringToInteger(s);
  }

// Generic property enum strings. Integer IDs remain accepted for every enum.
// The common symbolic IDs are mapped here; extend this table as the bridge grows.
long ParseEnumCode(string &args[],int index)
  {
   string s=ArgString(args,index,"");
   if(StringFind(s,"@i64:")==0 || StringFind(s,"@u64:")==0)
      return (long)StringToInteger(StringSubstr(s,5));
   if(StringLen(s)==0) return 0;

   // Account properties
   if(s=="ACCOUNT_LOGIN") return ACCOUNT_LOGIN;
   if(s=="ACCOUNT_TRADE_MODE") return ACCOUNT_TRADE_MODE;
   if(s=="ACCOUNT_LEVERAGE") return ACCOUNT_LEVERAGE;
   if(s=="ACCOUNT_LIMIT_ORDERS") return ACCOUNT_LIMIT_ORDERS;
   if(s=="ACCOUNT_MARGIN_SO_MODE") return ACCOUNT_MARGIN_SO_MODE;
   if(s=="ACCOUNT_TRADE_ALLOWED") return ACCOUNT_TRADE_ALLOWED;
   if(s=="ACCOUNT_TRADE_EXPERT") return ACCOUNT_TRADE_EXPERT;
   if(s=="ACCOUNT_MARGIN_MODE") return ACCOUNT_MARGIN_MODE;
   if(s=="ACCOUNT_BALANCE") return ACCOUNT_BALANCE;
   if(s=="ACCOUNT_CREDIT") return ACCOUNT_CREDIT;
   if(s=="ACCOUNT_PROFIT") return ACCOUNT_PROFIT;
   if(s=="ACCOUNT_EQUITY") return ACCOUNT_EQUITY;
   if(s=="ACCOUNT_MARGIN") return ACCOUNT_MARGIN;
   if(s=="ACCOUNT_MARGIN_FREE") return ACCOUNT_MARGIN_FREE;
   if(s=="ACCOUNT_MARGIN_LEVEL") return ACCOUNT_MARGIN_LEVEL;
   if(s=="ACCOUNT_MARGIN_SO_CALL") return ACCOUNT_MARGIN_SO_CALL;
   if(s=="ACCOUNT_MARGIN_SO_SO") return ACCOUNT_MARGIN_SO_SO;
   if(s=="ACCOUNT_NAME") return ACCOUNT_NAME;
   if(s=="ACCOUNT_SERVER") return ACCOUNT_SERVER;
   if(s=="ACCOUNT_CURRENCY") return ACCOUNT_CURRENCY;
   if(s=="ACCOUNT_COMPANY") return ACCOUNT_COMPANY;
   if(s=="ACCOUNT_CURRENCY_DIGITS") return ACCOUNT_CURRENCY_DIGITS;
   if(s=="ACCOUNT_FIFO_CLOSE") return ACCOUNT_FIFO_CLOSE;
   if(s=="ACCOUNT_MARGIN_INITIAL") return ACCOUNT_MARGIN_INITIAL;
   if(s=="ACCOUNT_MARGIN_MAINTENANCE") return ACCOUNT_MARGIN_MAINTENANCE;
   if(s=="ACCOUNT_ASSETS") return ACCOUNT_ASSETS;
   if(s=="ACCOUNT_LIABILITIES") return ACCOUNT_LIABILITIES;
   if(s=="ACCOUNT_COMMISSION_BLOCKED") return ACCOUNT_COMMISSION_BLOCKED;

   // Common order / position / deal properties
   if(s=="ORDER_TICKET") return ORDER_TICKET;
   if(s=="ORDER_TIME_SETUP") return ORDER_TIME_SETUP;
   if(s=="ORDER_TIME_SETUP_MSC") return ORDER_TIME_SETUP_MSC;
   if(s=="ORDER_TYPE") return ORDER_TYPE;
   if(s=="ORDER_STATE") return ORDER_STATE;
   if(s=="ORDER_TIME_EXPIRATION") return ORDER_TIME_EXPIRATION;
   if(s=="ORDER_TIME_DONE") return ORDER_TIME_DONE;
   if(s=="ORDER_TIME_DONE_MSC") return ORDER_TIME_DONE_MSC;
   if(s=="ORDER_TYPE_FILLING") return ORDER_TYPE_FILLING;
   if(s=="ORDER_TYPE_TIME") return ORDER_TYPE_TIME;
   if(s=="ORDER_MAGIC") return ORDER_MAGIC;
   if(s=="ORDER_POSITION_ID") return ORDER_POSITION_ID;
   if(s=="ORDER_VOLUME_INITIAL") return ORDER_VOLUME_INITIAL;
   if(s=="ORDER_VOLUME_CURRENT") return ORDER_VOLUME_CURRENT;
   if(s=="ORDER_PRICE_OPEN") return ORDER_PRICE_OPEN;
   if(s=="ORDER_SL") return ORDER_SL;
   if(s=="ORDER_TP") return ORDER_TP;
   if(s=="ORDER_PRICE_CURRENT") return ORDER_PRICE_CURRENT;
   if(s=="ORDER_PRICE_STOPLIMIT") return ORDER_PRICE_STOPLIMIT;
   if(s=="ORDER_SYMBOL") return ORDER_SYMBOL;
   if(s=="ORDER_COMMENT") return ORDER_COMMENT;

   if(s=="POSITION_TIME") return POSITION_TIME;
   if(s=="POSITION_TIME_MSC") return POSITION_TIME_MSC;
   if(s=="POSITION_TIME_UPDATE") return POSITION_TIME_UPDATE;
   if(s=="POSITION_TIME_UPDATE_MSC") return POSITION_TIME_UPDATE_MSC;
   if(s=="POSITION_TYPE") return POSITION_TYPE;
   if(s=="POSITION_MAGIC") return POSITION_MAGIC;
   if(s=="POSITION_IDENTIFIER") return POSITION_IDENTIFIER;
   if(s=="POSITION_VOLUME") return POSITION_VOLUME;
   if(s=="POSITION_PRICE_OPEN") return POSITION_PRICE_OPEN;
   if(s=="POSITION_SL") return POSITION_SL;
   if(s=="POSITION_TP") return POSITION_TP;
   if(s=="POSITION_PRICE_CURRENT") return POSITION_PRICE_CURRENT;
   if(s=="POSITION_SWAP") return POSITION_SWAP;
   if(s=="POSITION_PROFIT") return POSITION_PROFIT;
   if(s=="POSITION_SYMBOL") return POSITION_SYMBOL;
   if(s=="POSITION_COMMENT") return POSITION_COMMENT;

   if(s=="DEAL_TICKET") return DEAL_TICKET;
   if(s=="DEAL_ORDER") return DEAL_ORDER;
   if(s=="DEAL_TIME") return DEAL_TIME;
   if(s=="DEAL_TIME_MSC") return DEAL_TIME_MSC;
   if(s=="DEAL_TYPE") return DEAL_TYPE;
   if(s=="DEAL_ENTRY") return DEAL_ENTRY;
   if(s=="DEAL_MAGIC") return DEAL_MAGIC;
   if(s=="DEAL_POSITION_ID") return DEAL_POSITION_ID;
   if(s=="DEAL_VOLUME") return DEAL_VOLUME;
   if(s=="DEAL_PRICE") return DEAL_PRICE;
   if(s=="DEAL_COMMISSION") return DEAL_COMMISSION;
   if(s=="DEAL_SWAP") return DEAL_SWAP;
   if(s=="DEAL_PROFIT") return DEAL_PROFIT;
   if(s=="DEAL_SYMBOL") return DEAL_SYMBOL;
   if(s=="DEAL_COMMENT") return DEAL_COMMENT;

   // Common symbol properties
   if(s=="SYMBOL_SELECT") return SYMBOL_SELECT;
   if(s=="SYMBOL_VISIBLE") return SYMBOL_VISIBLE;
   if(s=="SYMBOL_SESSION_DEALS") return SYMBOL_SESSION_DEALS;
   if(s=="SYMBOL_SESSION_BUY_ORDERS") return SYMBOL_SESSION_BUY_ORDERS;
   if(s=="SYMBOL_SESSION_SELL_ORDERS") return SYMBOL_SESSION_SELL_ORDERS;
   if(s=="SYMBOL_VOLUME") return SYMBOL_VOLUME;
   if(s=="SYMBOL_VOLUMEHIGH") return SYMBOL_VOLUMEHIGH;
   if(s=="SYMBOL_VOLUMELOW") return SYMBOL_VOLUMELOW;
   if(s=="SYMBOL_TIME") return SYMBOL_TIME;
   if(s=="SYMBOL_DIGITS") return SYMBOL_DIGITS;
   if(s=="SYMBOL_SPREAD") return SYMBOL_SPREAD;
   if(s=="SYMBOL_SPREAD_FLOAT") return SYMBOL_SPREAD_FLOAT;
   if(s=="SYMBOL_TICKS_BOOKDEPTH") return SYMBOL_TICKS_BOOKDEPTH;
   if(s=="SYMBOL_TRADE_STOPS_LEVEL") return SYMBOL_TRADE_STOPS_LEVEL;
   if(s=="SYMBOL_TRADE_FREEZE_LEVEL") return SYMBOL_TRADE_FREEZE_LEVEL;
   if(s=="SYMBOL_BID") return SYMBOL_BID;
   if(s=="SYMBOL_ASK") return SYMBOL_ASK;
   if(s=="SYMBOL_LAST") return SYMBOL_LAST;
   if(s=="SYMBOL_POINT") return SYMBOL_POINT;
   if(s=="SYMBOL_TRADE_TICK_VALUE") return SYMBOL_TRADE_TICK_VALUE;
   if(s=="SYMBOL_TRADE_TICK_SIZE") return SYMBOL_TRADE_TICK_SIZE;
   if(s=="SYMBOL_TRADE_CONTRACT_SIZE") return SYMBOL_TRADE_CONTRACT_SIZE;
   if(s=="SYMBOL_VOLUME_MIN") return SYMBOL_VOLUME_MIN;
   if(s=="SYMBOL_VOLUME_MAX") return SYMBOL_VOLUME_MAX;
   if(s=="SYMBOL_VOLUME_STEP") return SYMBOL_VOLUME_STEP;
   if(s=="SYMBOL_VOLUME_LIMIT") return SYMBOL_VOLUME_LIMIT;
   if(s=="SYMBOL_SWAP_LONG") return SYMBOL_SWAP_LONG;
   if(s=="SYMBOL_SWAP_SHORT") return SYMBOL_SWAP_SHORT;
   if(s=="SYMBOL_CURRENCY_BASE") return SYMBOL_CURRENCY_BASE;
   if(s=="SYMBOL_CURRENCY_PROFIT") return SYMBOL_CURRENCY_PROFIT;
   if(s=="SYMBOL_CURRENCY_MARGIN") return SYMBOL_CURRENCY_MARGIN;
   if(s=="SYMBOL_DESCRIPTION") return SYMBOL_DESCRIPTION;
   if(s=="SYMBOL_PATH") return SYMBOL_PATH;
   if(s=="SYMBOL_CUSTOM") return SYMBOL_CUSTOM;
   if(s=="SYMBOL_CHART_MODE") return SYMBOL_CHART_MODE;
   if(s=="SYMBOL_START_TIME") return SYMBOL_START_TIME;
   if(s=="SYMBOL_EXPIRATION_TIME") return SYMBOL_EXPIRATION_TIME;
   if(s=="SYMBOL_TRADE_CALC_MODE") return SYMBOL_TRADE_CALC_MODE;
   if(s=="SYMBOL_TRADE_MODE") return SYMBOL_TRADE_MODE;
   if(s=="SYMBOL_TRADE_EXEMODE") return SYMBOL_TRADE_EXEMODE;
   if(s=="SYMBOL_SWAP_MODE") return SYMBOL_SWAP_MODE;
   if(s=="SYMBOL_SWAP_ROLLOVER3DAYS") return SYMBOL_SWAP_ROLLOVER3DAYS;
   if(s=="SYMBOL_MARGIN_HEDGED_USE_LEG") return SYMBOL_MARGIN_HEDGED_USE_LEG;
   if(s=="SYMBOL_EXPIRATION_MODE") return SYMBOL_EXPIRATION_MODE;
   if(s=="SYMBOL_FILLING_MODE") return SYMBOL_FILLING_MODE;
   if(s=="SYMBOL_ORDER_MODE") return SYMBOL_ORDER_MODE;
   if(s=="SYMBOL_ORDER_GTC_MODE") return SYMBOL_ORDER_GTC_MODE;
   if(s=="SYMBOL_OPTION_MODE") return SYMBOL_OPTION_MODE;
   if(s=="SYMBOL_OPTION_RIGHT") return SYMBOL_OPTION_RIGHT;
   if(s=="SYMBOL_BIDHIGH") return SYMBOL_BIDHIGH;
   if(s=="SYMBOL_BIDLOW") return SYMBOL_BIDLOW;
   if(s=="SYMBOL_ASKHIGH") return SYMBOL_ASKHIGH;
   if(s=="SYMBOL_ASKLOW") return SYMBOL_ASKLOW;
   if(s=="SYMBOL_LASTHIGH") return SYMBOL_LASTHIGH;
   if(s=="SYMBOL_LASTLOW") return SYMBOL_LASTLOW;
   if(s=="SYMBOL_VOLUME_REAL") return SYMBOL_VOLUME_REAL;
   if(s=="SYMBOL_VOLUMEHIGH_REAL") return SYMBOL_VOLUMEHIGH_REAL;
   if(s=="SYMBOL_VOLUMELOW_REAL") return SYMBOL_VOLUMELOW_REAL;
   if(s=="SYMBOL_OPTION_STRIKE") return SYMBOL_OPTION_STRIKE;
   if(s=="SYMBOL_TRADE_TICK_VALUE_PROFIT") return SYMBOL_TRADE_TICK_VALUE_PROFIT;
   if(s=="SYMBOL_TRADE_TICK_VALUE_LOSS") return SYMBOL_TRADE_TICK_VALUE_LOSS;
   if(s=="SYMBOL_TRADE_ACCRUED_INTEREST") return SYMBOL_TRADE_ACCRUED_INTEREST;
   if(s=="SYMBOL_TRADE_FACE_VALUE") return SYMBOL_TRADE_FACE_VALUE;
   if(s=="SYMBOL_TRADE_LIQUIDITY_RATE") return SYMBOL_TRADE_LIQUIDITY_RATE;
   if(s=="SYMBOL_MARGIN_INITIAL") return SYMBOL_MARGIN_INITIAL;
   if(s=="SYMBOL_MARGIN_MAINTENANCE") return SYMBOL_MARGIN_MAINTENANCE;
   if(s=="SYMBOL_SESSION_VOLUME") return SYMBOL_SESSION_VOLUME;
   if(s=="SYMBOL_SESSION_TURNOVER") return SYMBOL_SESSION_TURNOVER;
   if(s=="SYMBOL_SESSION_INTEREST") return SYMBOL_SESSION_INTEREST;
   if(s=="SYMBOL_SESSION_BUY_ORDERS_VOLUME") return SYMBOL_SESSION_BUY_ORDERS_VOLUME;
   if(s=="SYMBOL_SESSION_SELL_ORDERS_VOLUME") return SYMBOL_SESSION_SELL_ORDERS_VOLUME;
   if(s=="SYMBOL_SESSION_OPEN") return SYMBOL_SESSION_OPEN;
   if(s=="SYMBOL_SESSION_CLOSE") return SYMBOL_SESSION_CLOSE;
   if(s=="SYMBOL_SESSION_AW") return SYMBOL_SESSION_AW;
   if(s=="SYMBOL_SESSION_PRICE_SETTLEMENT") return SYMBOL_SESSION_PRICE_SETTLEMENT;
   if(s=="SYMBOL_SESSION_PRICE_LIMIT_MIN") return SYMBOL_SESSION_PRICE_LIMIT_MIN;
   if(s=="SYMBOL_SESSION_PRICE_LIMIT_MAX") return SYMBOL_SESSION_PRICE_LIMIT_MAX;
   if(s=="SYMBOL_MARGIN_HEDGED") return SYMBOL_MARGIN_HEDGED;
   if(s=="SYMBOL_PRICE_CHANGE") return SYMBOL_PRICE_CHANGE;
   if(s=="SYMBOL_PRICE_VOLATILITY") return SYMBOL_PRICE_VOLATILITY;
   if(s=="SYMBOL_PRICE_THEORETICAL") return SYMBOL_PRICE_THEORETICAL;
   if(s=="SYMBOL_PRICE_GREEKS_DELTA" || s=="SYMBOL_PRICE_DELTA") return SYMBOL_PRICE_DELTA;
   if(s=="SYMBOL_PRICE_GREEKS_THETA" || s=="SYMBOL_PRICE_THETA") return SYMBOL_PRICE_THETA;
   if(s=="SYMBOL_PRICE_GREEKS_GAMMA" || s=="SYMBOL_PRICE_GAMMA") return SYMBOL_PRICE_GAMMA;
   if(s=="SYMBOL_PRICE_GREEKS_VEGA" || s=="SYMBOL_PRICE_VEGA") return SYMBOL_PRICE_VEGA;
   if(s=="SYMBOL_PRICE_GREEKS_RHO" || s=="SYMBOL_PRICE_RHO") return SYMBOL_PRICE_RHO;
   if(s=="SYMBOL_PRICE_GREEKS_OMEGA" || s=="SYMBOL_PRICE_OMEGA") return SYMBOL_PRICE_OMEGA;
   if(s=="SYMBOL_PRICE_SENSITIVITY") return SYMBOL_PRICE_SENSITIVITY;
   if(s=="SYMBOL_BASIS") return SYMBOL_BASIS;
   if(s=="SYMBOL_CATEGORY") return SYMBOL_CATEGORY;
   if(s=="SYMBOL_EXCHANGE") return SYMBOL_EXCHANGE;
   if(s=="SYMBOL_FORMULA") return SYMBOL_FORMULA;
   if(s=="SYMBOL_ISIN") return SYMBOL_ISIN;
   if(s=="SYMBOL_PAGE") return SYMBOL_PAGE;

   // Terminal
   if(s=="TERMINAL_BUILD") return TERMINAL_BUILD;
   if(s=="TERMINAL_CONNECTED") return TERMINAL_CONNECTED;
   if(s=="TERMINAL_TRADE_ALLOWED") return TERMINAL_TRADE_ALLOWED;
   if(s=="TERMINAL_DLLS_ALLOWED") return TERMINAL_DLLS_ALLOWED;
   if(s=="TERMINAL_EMAIL_ENABLED") return TERMINAL_EMAIL_ENABLED;
   if(s=="TERMINAL_FTP_ENABLED") return TERMINAL_FTP_ENABLED;
   if(s=="TERMINAL_MAXBARS") return TERMINAL_MAXBARS;
   if(s=="TERMINAL_CODEPAGE") return TERMINAL_CODEPAGE;
   if(s=="TERMINAL_CPU_CORES") return TERMINAL_CPU_CORES;
   if(s=="TERMINAL_MEMORY_PHYSICAL") return TERMINAL_MEMORY_PHYSICAL;
   if(s=="TERMINAL_MEMORY_TOTAL") return TERMINAL_MEMORY_TOTAL;
   if(s=="TERMINAL_MEMORY_AVAILABLE") return TERMINAL_MEMORY_AVAILABLE;
   if(s=="TERMINAL_MEMORY_USED") return TERMINAL_MEMORY_USED;
   if(s=="TERMINAL_X64") return TERMINAL_X64;
   if(s=="TERMINAL_OPENCL_SUPPORT") return TERMINAL_OPENCL_SUPPORT;
   if(s=="TERMINAL_DISK_SPACE") return TERMINAL_DISK_SPACE;
   if(s=="TERMINAL_LANGUAGE") return TERMINAL_LANGUAGE;
   if(s=="TERMINAL_NAME") return TERMINAL_NAME;
   if(s=="TERMINAL_COMPANY") return TERMINAL_COMPANY;
   if(s=="TERMINAL_PATH") return TERMINAL_PATH;
   if(s=="TERMINAL_DATA_PATH") return TERMINAL_DATA_PATH;
   if(s=="TERMINAL_COMMONDATA_PATH") return TERMINAL_COMMONDATA_PATH;
   if(s=="TERMINAL_COMMUNITY_ACCOUNT") return TERMINAL_COMMUNITY_ACCOUNT;
   if(s=="TERMINAL_COMMUNITY_CONNECTION") return TERMINAL_COMMUNITY_CONNECTION;
   if(s=="TERMINAL_NOTIFICATIONS_ENABLED") return TERMINAL_NOTIFICATIONS_ENABLED;
   if(s=="TERMINAL_MQID") return TERMINAL_MQID;
   if(s=="TERMINAL_PING_LAST") return TERMINAL_PING_LAST;

   return StringToInteger(s);
  }

//----------------------------- socket helpers --------------------------------
bool SocketSendText(const string text)
  {
   if(g_socket==INVALID_HANDLE || !SocketIsConnected(g_socket)) return false;
   uchar bytes[];
   int count=StringToCharArray(text,bytes,0,WHOLE_ARRAY,CP_UTF8);
   if(count<=1) return false;
   int total=count-1;
   int sent_total=0;
   while(sent_total<total)
     {
      uchar chunk[];
      int remaining=total-sent_total;
      ArrayCopy(chunk,bytes,0,sent_total,remaining);
      int sent=SocketSend(g_socket,chunk,(uint)remaining);
      if(sent<=0) return false;
      sent_total+=sent;
     }
   return true;
  }

bool SendJson(const string json)
  {
   return SocketSendText(json+"\n");
  }

void RespondRaw(const string command_id,const bool ok,const string value_json,const string meta_json="{}",const string error_json="null")
  {
   string msg="{\"v\":\"@i64:1\",\"kind\":\"response\",\"command_id\":"+JsonQuote(command_id)+
              ",\"ok\":"+JsonBool(ok)+",\"value\":"+value_json+
              ",\"meta\":"+meta_json+",\"error\":"+error_json+"}";
   SendJson(msg);
  }

void RespondError(const string command_id,const string code,const string message,const bool uncertain=false)
  {
   string err="{\"code\":"+JsonQuote(code)+",\"message\":"+JsonQuote(message)+"}";
   string meta="{\"uncertain\":"+JsonBool(uncertain)+"}";
   RespondRaw(command_id,false,"null",meta,err);
  }

void RespondBool(const string id,const bool ok,const bool value) { RespondRaw(id,ok,JsonBool(value)); }
void RespondLong(const string id,const bool ok,const long value) { RespondRaw(id,ok,JsonLong(value)); }
void RespondULong(const string id,const bool ok,const ulong value) { RespondRaw(id,ok,JsonULong(value)); }
void RespondDouble(const string id,const bool ok,const double value) { RespondRaw(id,ok,JsonDouble(value)); }
void RespondString(const string id,const bool ok,const string value) { RespondRaw(id,ok,JsonQuote(value)); }

string PropertyLongJson(const bool ok,const long value,const string error="")
  {
   return "{\"ok\":"+JsonBool(ok)+",\"value\":"+JsonLong(value)+",\"error\":"+(ok ? "null" : JsonQuote(error))+"}";
  }
string PropertyDoubleJson(const bool ok,const double value,const string error="")
  {
   return "{\"ok\":"+JsonBool(ok)+",\"value\":"+JsonDouble(value)+",\"error\":"+(ok ? "null" : JsonQuote(error))+"}";
  }
string PropertyStringJson(const bool ok,const string value,const string error="")
  {
   return "{\"ok\":"+JsonBool(ok)+",\"value\":"+JsonQuote(value)+",\"error\":"+(ok ? "null" : JsonQuote(error))+"}";
  }

//----------------------------- object registry -------------------------------
CBridgeTrade* GetTrade(const string id)
  {
   for(int i=0;i<ArraySize(g_trade_ids);i++) if(g_trade_ids[i]==id) return g_trade_objs[i];
   int n=ArraySize(g_trade_ids); ArrayResize(g_trade_ids,n+1); ArrayResize(g_trade_objs,n+1);
   g_trade_ids[n]=id; g_trade_objs[n]=new CBridgeTrade; return g_trade_objs[n];
  }
CAccountInfo* GetAccount(const string id)
  {
   for(int i=0;i<ArraySize(g_account_ids);i++) if(g_account_ids[i]==id) return g_account_objs[i];
   int n=ArraySize(g_account_ids); ArrayResize(g_account_ids,n+1); ArrayResize(g_account_objs,n+1);
   g_account_ids[n]=id; g_account_objs[n]=new CAccountInfo; return g_account_objs[n];
  }
CSymbolInfo* GetSymbol(const string id)
  {
   for(int i=0;i<ArraySize(g_symbol_ids);i++) if(g_symbol_ids[i]==id) return g_symbol_objs[i];
   int n=ArraySize(g_symbol_ids); ArrayResize(g_symbol_ids,n+1); ArrayResize(g_symbol_objs,n+1);
   g_symbol_ids[n]=id; g_symbol_objs[n]=new CSymbolInfo; return g_symbol_objs[n];
  }
COrderInfo* GetOrder(const string id)
  {
   for(int i=0;i<ArraySize(g_order_ids);i++) if(g_order_ids[i]==id) return g_order_objs[i];
   int n=ArraySize(g_order_ids); ArrayResize(g_order_ids,n+1); ArrayResize(g_order_objs,n+1);
   g_order_ids[n]=id; g_order_objs[n]=new COrderInfo; return g_order_objs[n];
  }
CHistoryOrderInfo* GetHistory(const string id)
  {
   for(int i=0;i<ArraySize(g_history_ids);i++) if(g_history_ids[i]==id) return g_history_objs[i];
   int n=ArraySize(g_history_ids); ArrayResize(g_history_ids,n+1); ArrayResize(g_history_objs,n+1);
   g_history_ids[n]=id; g_history_objs[n]=new CHistoryOrderInfo; return g_history_objs[n];
  }
CPositionInfo* GetPosition(const string id)
  {
   for(int i=0;i<ArraySize(g_position_ids);i++) if(g_position_ids[i]==id) return g_position_objs[i];
   int n=ArraySize(g_position_ids); ArrayResize(g_position_ids,n+1); ArrayResize(g_position_objs,n+1);
   g_position_ids[n]=id; g_position_objs[n]=new CPositionInfo; return g_position_objs[n];
  }
CDealInfo* GetDeal(const string id)
  {
   for(int i=0;i<ArraySize(g_deal_ids);i++) if(g_deal_ids[i]==id) return g_deal_objs[i];
   int n=ArraySize(g_deal_ids); ArrayResize(g_deal_ids,n+1); ArrayResize(g_deal_objs,n+1);
   g_deal_ids[n]=id; g_deal_objs[n]=new CDealInfo; return g_deal_objs[n];
  }
CTerminalInfo* GetTerminal(const string id)
  {
   for(int i=0;i<ArraySize(g_terminal_ids);i++) if(g_terminal_ids[i]==id) return g_terminal_objs[i];
   int n=ArraySize(g_terminal_ids); ArrayResize(g_terminal_ids,n+1); ArrayResize(g_terminal_objs,n+1);
   g_terminal_ids[n]=id; g_terminal_objs[n]=new CTerminalInfo; return g_terminal_objs[n];
  }

void TrackRequest(const ulong request_id,const string command_id)
  {
   if(request_id==0) return;
   for(int i=0;i<ArraySize(g_request_ids);i++)
      if(g_request_ids[i]==request_id) { g_request_commands[i]=command_id; return; }
   int n=ArraySize(g_request_ids); ArrayResize(g_request_ids,n+1); ArrayResize(g_request_commands,n+1);
   g_request_ids[n]=request_id; g_request_commands[n]=command_id;
  }

string CommandForRequest(const ulong request_id)
  {
   for(int i=0;i<ArraySize(g_request_ids);i++) if(g_request_ids[i]==request_id) return g_request_commands[i];
   return "";
  }

//------------------------- trade structure serialization ---------------------
string RequestJson(const MqlTradeRequest &r)
  {
   return "{"
      "\"action\":"+JsonLong((long)r.action)+
      ",\"magic\":"+JsonULong(r.magic)+
      ",\"order\":"+JsonULong(r.order)+
      ",\"symbol\":"+JsonQuote(r.symbol)+
      ",\"volume\":"+JsonDouble(r.volume)+
      ",\"price\":"+JsonDouble(r.price)+
      ",\"stoplimit\":"+JsonDouble(r.stoplimit)+
      ",\"sl\":"+JsonDouble(r.sl)+
      ",\"tp\":"+JsonDouble(r.tp)+
      ",\"deviation\":"+JsonULong(r.deviation)+
      ",\"type\":"+JsonLong((long)r.type)+
      ",\"type_filling\":"+JsonLong((long)r.type_filling)+
      ",\"type_time\":"+JsonLong((long)r.type_time)+
      ",\"expiration\":"+JsonLong((long)r.expiration)+
      ",\"comment\":"+JsonQuote(r.comment)+
      ",\"position\":"+JsonULong(r.position)+
      ",\"position_by\":"+JsonULong(r.position_by)+
      "}";
  }

string ResultJson(const MqlTradeResult &r)
  {
   return "{"
      "\"retcode\":"+JsonULong(r.retcode)+
      ",\"deal\":"+JsonULong(r.deal)+
      ",\"order\":"+JsonULong(r.order)+
      ",\"volume\":"+JsonDouble(r.volume)+
      ",\"price\":"+JsonDouble(r.price)+
      ",\"bid\":"+JsonDouble(r.bid)+
      ",\"ask\":"+JsonDouble(r.ask)+
      ",\"comment\":"+JsonQuote(r.comment)+
      ",\"request_id\":"+JsonULong(r.request_id)+
      ",\"retcode_external\":"+JsonLong((long)r.retcode_external)+
      "}";
  }

string CheckResultJson(const MqlTradeCheckResult &r)
  {
   return "{"
      "\"retcode\":"+JsonULong(r.retcode)+
      ",\"balance\":"+JsonDouble(r.balance)+
      ",\"equity\":"+JsonDouble(r.equity)+
      ",\"profit\":"+JsonDouble(r.profit)+
      ",\"margin\":"+JsonDouble(r.margin)+
      ",\"margin_free\":"+JsonDouble(r.margin_free)+
      ",\"margin_level\":"+JsonDouble(r.margin_level)+
      ",\"comment\":"+JsonQuote(r.comment)+
      "}";
  }

string AccountInfoJson(CAccountInfo *obj)
  {
   return "{"
      "\"login\":"+JsonULong((ulong)obj.Login())+
      ",\"trade_mode\":"+JsonLong((long)obj.TradeMode())+
      ",\"trade_mode_description\":"+JsonQuote(obj.TradeModeDescription())+
      ",\"leverage\":"+JsonULong((ulong)obj.Leverage())+
      ",\"stopout_mode\":"+JsonLong((long)obj.StopoutMode())+
      ",\"stopout_mode_description\":"+JsonQuote(obj.StopoutModeDescription())+
      ",\"margin_mode\":"+JsonLong((long)obj.MarginMode())+
      ",\"margin_mode_description\":"+JsonQuote(obj.MarginModeDescription())+
      ",\"trade_allowed\":"+JsonBool(obj.TradeAllowed())+
      ",\"trade_expert\":"+JsonBool(obj.TradeExpert())+
      ",\"limit_orders\":"+JsonLong((long)obj.LimitOrders())+
      ",\"balance\":"+JsonDouble((double)obj.Balance())+
      ",\"credit\":"+JsonDouble((double)obj.Credit())+
      ",\"profit\":"+JsonDouble((double)obj.Profit())+
      ",\"equity\":"+JsonDouble((double)obj.Equity())+
      ",\"margin\":"+JsonDouble((double)obj.Margin())+
      ",\"free_margin\":"+JsonDouble((double)obj.FreeMargin())+
      ",\"margin_level\":"+JsonDouble((double)obj.MarginLevel())+
      ",\"margin_call\":"+JsonDouble((double)obj.MarginCall())+
      ",\"margin_stop_out\":"+JsonDouble((double)obj.MarginStopOut())+
      ",\"name\":"+JsonQuote(obj.Name())+
      ",\"server\":"+JsonQuote(obj.Server())+
      ",\"currency\":"+JsonQuote(obj.Currency())+
      ",\"company\":"+JsonQuote(obj.Company())+
      ",\"currency_digits\":"+JsonLong((long)AccountInfoInteger(ACCOUNT_CURRENCY_DIGITS))+
      ",\"fifo_close\":"+JsonBool((bool)AccountInfoInteger(ACCOUNT_FIFO_CLOSE))+
      ",\"margin_initial\":"+JsonDouble(AccountInfoDouble(ACCOUNT_MARGIN_INITIAL))+
      ",\"margin_maintenance\":"+JsonDouble(AccountInfoDouble(ACCOUNT_MARGIN_MAINTENANCE))+
      ",\"assets\":"+JsonDouble(AccountInfoDouble(ACCOUNT_ASSETS))+
      ",\"liabilities\":"+JsonDouble(AccountInfoDouble(ACCOUNT_LIABILITIES))+
      ",\"commission_blocked\":"+JsonDouble(AccountInfoDouble(ACCOUNT_COMMISSION_BLOCKED))+
      "}";
  }

string TerminalInfoJson(CTerminalInfo *obj)
  {
   return "{"
      "\"build\":"+JsonLong((long)obj.Build())+
      ",\"connected\":"+JsonBool(obj.IsConnected())+
      ",\"dlls_allowed\":"+JsonBool(obj.IsDLLsAllowed())+
      ",\"trade_allowed\":"+JsonBool(obj.IsTradeAllowed())+
      ",\"email_enabled\":"+JsonBool(obj.IsEmailEnabled())+
      ",\"ftp_enabled\":"+JsonBool(obj.IsFtpEnabled())+
      ",\"max_bars\":"+JsonLong((long)obj.MaxBars())+
      ",\"code_page\":"+JsonLong((long)obj.CodePage())+
      ",\"cpu_cores\":"+JsonLong((long)obj.CPUCores())+
      ",\"memory_physical\":"+JsonLong((long)obj.MemoryPhysical())+
      ",\"memory_total\":"+JsonLong((long)obj.MemoryTotal())+
      ",\"memory_available\":"+JsonLong((long)obj.MemoryAvailable())+
      ",\"memory_used\":"+JsonLong((long)obj.MemoryUsed())+
      ",\"is_x64\":"+JsonBool(obj.IsX64())+
      ",\"opencl_support\":"+JsonLong((long)obj.OpenCLSupport())+
      ",\"disk_space\":"+JsonLong((long)obj.DiskSpace())+
      ",\"language\":"+JsonQuote(obj.Language())+
      ",\"name\":"+JsonQuote(obj.Name())+
      ",\"company\":"+JsonQuote(obj.Company())+
      ",\"path\":"+JsonQuote(obj.Path())+
      ",\"data_path\":"+JsonQuote(obj.DataPath())+
      ",\"common_data_path\":"+JsonQuote(obj.CommonDataPath())+
      ",\"community_account\":"+JsonBool((bool)TerminalInfoInteger(TERMINAL_COMMUNITY_ACCOUNT))+
      ",\"community_connection\":"+JsonBool((bool)TerminalInfoInteger(TERMINAL_COMMUNITY_CONNECTION))+
      ",\"tradeapi_disabled\":"+JsonBool(false)+
      ",\"notifications_enabled\":"+JsonBool((bool)TerminalInfoInteger(TERMINAL_NOTIFICATIONS_ENABLED))+
      ",\"mqid\":"+JsonBool((bool)TerminalInfoInteger(TERMINAL_MQID))+
      ",\"ping_last\":"+JsonLong((long)TerminalInfoInteger(TERMINAL_PING_LAST))+
      ",\"community_balance\":"+JsonDouble(TerminalInfoDouble(TERMINAL_COMMUNITY_BALANCE))+
      ",\"retransmission\":"+JsonDouble(TerminalInfoDouble(TERMINAL_RETRANSMISSION))+
      "}";
  }

string TradeMeta(CTrade &obj)
  {
   MqlTradeResult r; ZeroMemory(r); obj.Result(r);
   bool uncertain=(r.retcode==10012 || r.retcode==10031);
   return "{\"retcode\":"+JsonULong(r.retcode)+
          ",\"request_id\":"+JsonULong(r.request_id)+
          ",\"uncertain\":"+JsonBool(uncertain)+
          ",\"result\":"+ResultJson(r)+"}";
  }

void RespondTradeBool(const string command_id,CTrade &obj,const bool value)
  {
   MqlTradeResult r; ZeroMemory(r); obj.Result(r); TrackRequest(r.request_id,command_id);
   RespondRaw(command_id,true,JsonBool(value),TradeMeta(obj));
  }

//------------------------------ dispatchers ----------------------------------
void DispatchTrade(const string command_id,const string object_id,const string method,string &args[])
  {
   CBridgeTrade *p=GetTrade(object_id);
   if(CheckPointer(p)==POINTER_INVALID) { RespondError(command_id,"OBJECT_CREATE_FAILED","CTrade allocation failed"); return; }
   CBridgeTrade *obj=p;

   if(method=="ReloadEA") { ChartSetSymbolPeriod(0,_Symbol,_Period); RespondBool(command_id,true,true); return; }
   if(method=="LogLevel") { obj.LogLevel(ParseLogLevel(args,0)); RespondBool(command_id,true,true); return; }
   if(method=="SetExpertMagicNumber") { obj.SetExpertMagicNumber(ArgULong(args,0)); RespondBool(command_id,true,true); return; }
   if(method=="SetDeviationInPoints") { obj.SetDeviationInPoints(ArgULong(args,0)); RespondBool(command_id,true,true); return; }
   if(method=="SetTypeFilling") { obj.SetTypeFilling(ParseFilling(args,0)); RespondBool(command_id,true,true); return; }
   if(method=="SetTypeFillingBySymbol") { RespondBool(command_id,true,obj.SetTypeFillingBySymbol(ArgString(args,0))); return; }
   if(method=="SetAsyncMode") { obj.SetAsyncMode(ArgBool(args,0)); RespondBool(command_id,true,true); return; }
   if(method=="SetMarginMode") { obj.SetMarginMode(); RespondBool(command_id,true,true); return; }

   if(method=="OrderOpen")
     {
      bool ok=obj.OrderOpen(ArgString(args,0),ParseOrderType(args,1),ArgDouble(args,2),ArgDouble(args,3),
                            ArgDouble(args,4),ArgDouble(args,5),ArgDouble(args,6),ParseOrderTime(args,7),
                            (datetime)ArgLong(args,8),ArgString(args,9,""));
      RespondTradeBool(command_id,p,ok); return;
     }
   if(method=="OrderCheck")
     {
      MqlTradeRequest chk_req;
      MqlTradeCheckResult chk_res;
      ZeroMemory(chk_req);
      ZeroMemory(chk_res);
      chk_req.action=TRADE_ACTION_DEAL;
      chk_req.type=ORDER_TYPE_BUY;
      chk_req.magic=obj.GetMagic();
      chk_req.deviation=obj.GetDeviation();
      chk_req.type_filling=obj.GetTypeFilling();
      if(ArraySize(args)>0)
        {
         if(StringFind(args[0],"{")>=0)
           {
            string val;
            if(JsonGetString(args[0],"symbol",val)) chk_req.symbol=val;
            chk_req.action=(ENUM_TRADE_REQUEST_ACTIONS)JsonGetInt(args[0],"action",chk_req.action);
            string ot_key=(StringFind(args[0],"\"order_type\"")>=0 ? "order_type" : "type");
            chk_req.type=(ENUM_ORDER_TYPE)JsonGetInt(args[0],ot_key,chk_req.type);
            chk_req.volume=JsonGetDouble(args[0],"volume",chk_req.volume);
            chk_req.price=JsonGetDouble(args[0],"price",chk_req.price);
            chk_req.sl=JsonGetDouble(args[0],"sl",chk_req.sl);
            chk_req.tp=JsonGetDouble(args[0],"tp",chk_req.tp);
            chk_req.deviation=JsonGetULong(args[0],"deviation",chk_req.deviation);
            chk_req.magic=JsonGetULong(args[0],"magic",chk_req.magic);
            if(JsonExtractRaw(args[0],"type_filling",val))
               chk_req.type_filling=(ENUM_ORDER_TYPE_FILLING)JsonGetInt(args[0],"type_filling",chk_req.type_filling);
           }
         else if(ArraySize(args)>=3)
           {
            chk_req.action=TRADE_ACTION_DEAL;
            chk_req.symbol=ArgString(args,0);
            chk_req.type=ParseOrderType(args,1);
            chk_req.volume=ArgDouble(args,2);
            if(ArraySize(args)>3) chk_req.price=ArgDouble(args,3);
            if(ArraySize(args)>4) chk_req.sl=ArgDouble(args,4);
            if(ArraySize(args)>5) chk_req.tp=ArgDouble(args,5);
            if(ArraySize(args)>6) chk_req.deviation=ArgULong(args,6,10);
           }
        }
      if(chk_req.type_filling==0)
        {
         uint filling=(uint)SymbolInfoInteger(chk_req.symbol,SYMBOL_FILLING_MODE);
         if((filling&SYMBOL_FILLING_FOK)==SYMBOL_FILLING_FOK) chk_req.type_filling=ORDER_FILLING_FOK;
         else if((filling&SYMBOL_FILLING_IOC)==SYMBOL_FILLING_IOC) chk_req.type_filling=ORDER_FILLING_IOC;
         else chk_req.type_filling=ORDER_FILLING_RETURN;
        }
      if(chk_req.price<=0.0)
        {
         chk_req.price=SymbolInfoDouble(chk_req.symbol,chk_req.type==ORDER_TYPE_SELL ? SYMBOL_BID : SYMBOL_ASK);
        }
      ResetLastError();
      bool ok=obj.OrderCheck(chk_req,chk_res);
      int err=GetLastError();
      if(!ok && chk_res.retcode==0)
        {
         chk_res.retcode=(err!=0 ? err : 10013);
        }
      if(chk_res.comment=="")
        {
         chk_res.comment=StringFormat("ok=%d ret=%d err=%d price=%.5f vol=%.2f fill=%d act=%d type=%d",
                                      ok, chk_res.retcode, err, chk_req.price, chk_req.volume,
                                      chk_req.type_filling, chk_req.action, chk_req.type);
        }
      PrintFormat("PythonBridge OrderCheck: action=%d sym=%s type=%d vol=%.2f price=%.5f filling=%d -> ok=%s retcode=%d comment=%s margin=%.2f",
                  chk_req.action, chk_req.symbol, chk_req.type, chk_req.volume, chk_req.price, chk_req.type_filling,
                  ok ? "true" : "false", chk_res.retcode, chk_res.comment, chk_res.margin);
      obj.SetCheckResult(chk_res);
      RespondBool(command_id,true,ok);
      return;
     }
   if(method=="OrderModify")
     {
      bool ok=obj.OrderModify(ArgULong(args,0),ArgDouble(args,1),ArgDouble(args,2),ArgDouble(args,3),
                              ParseOrderTime(args,4),(datetime)ArgLong(args,5),ArgDouble(args,6));
      RespondTradeBool(command_id,p,ok); return;
     }
   if(method=="OrderDelete") { RespondTradeBool(command_id,p,obj.OrderDelete(ArgULong(args,0))); return; }
   if(method=="PositionOpen")
     {
      bool ok=obj.PositionOpen(ArgString(args,0),ParseOrderType(args,1),ArgDouble(args,2),ArgDouble(args,3),
                               ArgDouble(args,4),ArgDouble(args,5),ArgString(args,6,""));
      RespondTradeBool(command_id,p,ok); return;
     }
   if(method=="PositionModify")
     {
      bool ok=ArgLooksInteger(args,0)
         ? obj.PositionModify(ArgULong(args,0),ArgDouble(args,1),ArgDouble(args,2))
         : obj.PositionModify(ArgString(args,0),ArgDouble(args,1),ArgDouble(args,2));
      RespondTradeBool(command_id,p,ok); return;
     }
   if(method=="PositionClose")
     {
      ulong deviation=(ArraySize(args)>1 ? ArgULong(args,1,ULONG_MAX) : ULONG_MAX);
      bool ok=ArgLooksInteger(args,0) ? obj.PositionClose(ArgULong(args,0),deviation) : obj.PositionClose(ArgString(args,0),deviation);
      RespondTradeBool(command_id,p,ok); return;
     }
   if(method=="PositionClosePartial")
     {
      ulong deviation=(ArraySize(args)>2 ? ArgULong(args,2,ULONG_MAX) : ULONG_MAX);
      bool ok=ArgLooksInteger(args,0)
         ? obj.PositionClosePartial(ArgULong(args,0),ArgDouble(args,1),deviation)
         : obj.PositionClosePartial(ArgString(args,0),ArgDouble(args,1),deviation);
      RespondTradeBool(command_id,p,ok); return;
     }
   if(method=="PositionCloseBy") { RespondTradeBool(command_id,p,obj.PositionCloseBy(ArgULong(args,0),ArgULong(args,1))); return; }

   if(method=="Buy")
     { RespondTradeBool(command_id,p,obj.Buy(ArgDouble(args,0),ArgString(args,1,_Symbol),ArgDouble(args,2),ArgDouble(args,3),ArgDouble(args,4),ArgString(args,5,""))); return; }
   if(method=="Sell")
     { RespondTradeBool(command_id,p,obj.Sell(ArgDouble(args,0),ArgString(args,1,_Symbol),ArgDouble(args,2),ArgDouble(args,3),ArgDouble(args,4),ArgString(args,5,""))); return; }
   if(method=="BuyLimit")
     { RespondTradeBool(command_id,p,obj.BuyLimit(ArgDouble(args,0),ArgDouble(args,1),ArgString(args,2,_Symbol),ArgDouble(args,3),ArgDouble(args,4),ParseOrderTime(args,5),(datetime)ArgLong(args,6),ArgString(args,7,""))); return; }
   if(method=="BuyStop")
     { RespondTradeBool(command_id,p,obj.BuyStop(ArgDouble(args,0),ArgDouble(args,1),ArgString(args,2,_Symbol),ArgDouble(args,3),ArgDouble(args,4),ParseOrderTime(args,5),(datetime)ArgLong(args,6),ArgString(args,7,""))); return; }
   if(method=="SellLimit")
     { RespondTradeBool(command_id,p,obj.SellLimit(ArgDouble(args,0),ArgDouble(args,1),ArgString(args,2,_Symbol),ArgDouble(args,3),ArgDouble(args,4),ParseOrderTime(args,5),(datetime)ArgLong(args,6),ArgString(args,7,""))); return; }
   if(method=="SellStop")
     { RespondTradeBool(command_id,p,obj.SellStop(ArgDouble(args,0),ArgDouble(args,1),ArgString(args,2,_Symbol),ArgDouble(args,3),ArgDouble(args,4),ParseOrderTime(args,5),(datetime)ArgLong(args,6),ArgString(args,7,""))); return; }

   MqlTradeRequest req; MqlTradeResult res; MqlTradeCheckResult chk;
   ZeroMemory(req); ZeroMemory(res); ZeroMemory(chk);
   if(method=="Request") { obj.Request(req); RespondRaw(command_id,true,RequestJson(req)); return; }
   if(method=="Result") { obj.Result(res); RespondRaw(command_id,true,ResultJson(res)); return; }
   if(method=="CheckResult") { obj.CheckResult(chk); RespondRaw(command_id,true,CheckResultJson(chk)); return; }

   if(method=="RequestAction") { RespondLong(command_id,true,(long)obj.RequestAction()); return; }
   if(method=="RequestActionDescription") { RespondString(command_id,true,obj.RequestActionDescription()); return; }
   if(method=="RequestMagic") { RespondULong(command_id,true,obj.RequestMagic()); return; }
   if(method=="RequestOrder") { RespondULong(command_id,true,obj.RequestOrder()); return; }
   if(method=="RequestSymbol") { RespondString(command_id,true,obj.RequestSymbol()); return; }
   if(method=="RequestVolume") { RespondDouble(command_id,true,obj.RequestVolume()); return; }
   if(method=="RequestPrice") { RespondDouble(command_id,true,obj.RequestPrice()); return; }
   if(method=="RequestStopLimit") { RespondDouble(command_id,true,obj.RequestStopLimit()); return; }
   if(method=="RequestSL") { RespondDouble(command_id,true,obj.RequestSL()); return; }
   if(method=="RequestTP") { RespondDouble(command_id,true,obj.RequestTP()); return; }
   if(method=="RequestDeviation") { RespondULong(command_id,true,obj.RequestDeviation()); return; }
   if(method=="RequestType") { RespondLong(command_id,true,(long)obj.RequestType()); return; }
   if(method=="RequestTypeDescription") { RespondString(command_id,true,obj.RequestTypeDescription()); return; }
   if(method=="RequestTypeFilling") { RespondLong(command_id,true,(long)obj.RequestTypeFilling()); return; }
   if(method=="RequestTypeFillingDescription") { RespondString(command_id,true,obj.RequestTypeFillingDescription()); return; }
   if(method=="RequestTypeTime") { RespondLong(command_id,true,(long)obj.RequestTypeTime()); return; }
   if(method=="RequestTypeTimeDescription") { RespondString(command_id,true,obj.RequestTypeTimeDescription()); return; }
   if(method=="RequestExpiration") { RespondLong(command_id,true,(long)obj.RequestExpiration()); return; }
   if(method=="RequestComment") { RespondString(command_id,true,obj.RequestComment()); return; }
   if(method=="RequestPosition") { RespondULong(command_id,true,obj.RequestPosition()); return; }
   if(method=="RequestPositionBy") { RespondULong(command_id,true,obj.RequestPositionBy()); return; }

   if(method=="ResultRetcode") { RespondULong(command_id,true,obj.ResultRetcode()); return; }
   if(method=="ResultRetcodeDescription") { RespondString(command_id,true,obj.ResultRetcodeDescription()); return; }
   if(method=="ResultDeal") { RespondULong(command_id,true,obj.ResultDeal()); return; }
   if(method=="ResultOrder") { RespondULong(command_id,true,obj.ResultOrder()); return; }
   if(method=="ResultVolume") { RespondDouble(command_id,true,obj.ResultVolume()); return; }
   if(method=="ResultPrice") { RespondDouble(command_id,true,obj.ResultPrice()); return; }
   if(method=="ResultBid") { RespondDouble(command_id,true,obj.ResultBid()); return; }
   if(method=="ResultAsk") { RespondDouble(command_id,true,obj.ResultAsk()); return; }
   if(method=="ResultComment") { RespondString(command_id,true,obj.ResultComment()); return; }

   if(method=="CheckResultRetcode") { RespondULong(command_id,true,obj.CheckResultRetcode()); return; }
   if(method=="CheckResultRetcodeDescription") { RespondString(command_id,true,obj.CheckResultRetcodeDescription()); return; }
   if(method=="CheckResultBalance") { RespondDouble(command_id,true,obj.CheckResultBalance()); return; }
   if(method=="CheckResultEquity") { RespondDouble(command_id,true,obj.CheckResultEquity()); return; }
   if(method=="CheckResultProfit") { RespondDouble(command_id,true,obj.CheckResultProfit()); return; }
   if(method=="CheckResultMargin") { RespondDouble(command_id,true,obj.CheckResultMargin()); return; }
   if(method=="CheckResultMarginFree") { RespondDouble(command_id,true,obj.CheckResultMarginFree()); return; }
   if(method=="CheckResultMarginLevel") { RespondDouble(command_id,true,obj.CheckResultMarginLevel()); return; }
   if(method=="CheckResultComment") { RespondString(command_id,true,obj.CheckResultComment()); return; }

   if(method=="PrintRequest") { obj.PrintRequest(); RespondBool(command_id,true,true); return; }
   if(method=="PrintResult") { obj.PrintResult(); RespondBool(command_id,true,true); return; }
   if(method=="FormatRequest")
     {
      obj.Request(req); string s=""; obj.FormatRequest(s,req); RespondString(command_id,true,s); return;
     }
   if(method=="FormatRequestResult")
     {
      obj.Request(req); obj.Result(res); string s=""; obj.FormatRequestResult(s,req,res); RespondString(command_id,true,s); return;
     }

   RespondError(command_id,"METHOD_NOT_IMPLEMENTED","unknown CTrade method: "+method);
  }

void DispatchAccount(const string command_id,const string object_id,const string method,string &args[])
  {
   CAccountInfo *p=GetAccount(object_id); if(CheckPointer(p)==POINTER_INVALID) { RespondError(command_id,"OBJECT_CREATE_FAILED","CAccountInfo allocation failed"); return; }
   CAccountInfo *obj=p;
   if(method=="AccountInfo") { RespondRaw(command_id, true, AccountInfoJson(obj)); return; }
   if(method=="OrderProfitCheck") { RespondDouble(command_id,true,obj.OrderProfitCheck(ArgString(args,0),ParseOrderType(args,1),ArgDouble(args,2),ArgDouble(args,3),ArgDouble(args,4))); return; }
   if(method=="MarginCheck") { RespondDouble(command_id,true,obj.MarginCheck(ArgString(args,0),ParseOrderType(args,1),ArgDouble(args,2),ArgDouble(args,3))); return; }
   if(method=="FreeMarginCheck") { RespondDouble(command_id,true,obj.FreeMarginCheck(ArgString(args,0),ParseOrderType(args,1),ArgDouble(args,2),ArgDouble(args,3))); return; }
   if(method=="MaxLotCheck") { RespondDouble(command_id,true,obj.MaxLotCheck(ArgString(args,0),ParseOrderType(args,1),ArgDouble(args,2),ArgDouble(args,3,100.0))); return; }
   RespondError(command_id,"METHOD_NOT_IMPLEMENTED","unknown CAccountInfo method: "+method);
  }

void DispatchSymbol(const string command_id,const string object_id,const string method,string &args[])
  {
   CSymbolInfo *p=GetSymbol(object_id); if(CheckPointer(p)==POINTER_INVALID) { RespondError(command_id,"OBJECT_CREATE_FAILED","CSymbolInfo allocation failed"); return; }
   CSymbolInfo *obj=p;
   if(method=="Name")
     {
      if(ArraySize(args)==0) RespondString(command_id,true,obj.Name());
      else RespondBool(command_id,true,obj.Name(ArgString(args,0)));
      return;
     }
   if(method=="Select")
     {
      if(ArraySize(args)==0) RespondBool(command_id,true,obj.Select());
      else RespondBool(command_id,true,obj.Select(ArgBool(args,0)));
      return;
     }
   if(method=="Refresh") { RespondBool(command_id, true, obj.Refresh()); return; }
   if(method=="RefreshRates") { RespondBool(command_id, true, obj.RefreshRates()); return; }
   if(method=="IsSynchronized") { RespondBool(command_id, true, obj.IsSynchronized()); return; }
   if(method=="SpreadFloat") { RespondBool(command_id, true, obj.SpreadFloat()); return; }
   if(method=="Volume") { RespondLong(command_id, true, (long)(obj.Volume())); return; }
   if(method=="VolumeHigh") { RespondLong(command_id, true, (long)(obj.VolumeHigh())); return; }
   if(method=="VolumeLow") { RespondLong(command_id, true, (long)(obj.VolumeLow())); return; }
   if(method=="Time") { RespondLong(command_id, true, (long)(obj.Time())); return; }
   if(method=="Spread") { RespondLong(command_id, true, (long)(obj.Spread())); return; }
   if(method=="TicksBookDepth") { RespondLong(command_id, true, (long)(obj.TicksBookDepth())); return; }
   if(method=="StopsLevel") { RespondLong(command_id, true, (long)(obj.StopsLevel())); return; }
   if(method=="FreezeLevel") { RespondLong(command_id, true, (long)(obj.FreezeLevel())); return; }
   if(method=="TradeCalcMode") { RespondLong(command_id, true, (long)(obj.TradeCalcMode())); return; }
   if(method=="TradeMode") { RespondLong(command_id, true, (long)(obj.TradeMode())); return; }
   if(method=="TradeExecution") { RespondLong(command_id, true, (long)(obj.TradeExecution())); return; }
   if(method=="SwapMode") { RespondLong(command_id, true, (long)(obj.SwapMode())); return; }
   if(method=="SwapRollover3days") { RespondLong(command_id, true, (long)(obj.SwapRollover3days())); return; }
   if(method=="TradeTimeFlags") { RespondLong(command_id, true, (long)(obj.TradeTimeFlags())); return; }
   if(method=="TradeFillFlags") { RespondLong(command_id, true, (long)(obj.TradeFillFlags())); return; }
   if(method=="Digits") { RespondLong(command_id, true, (long)(obj.Digits())); return; }
   if(method=="SessionDeals") { RespondLong(command_id, true, (long)(obj.SessionDeals())); return; }
   if(method=="SessionBuyOrders") { RespondLong(command_id, true, (long)(obj.SessionBuyOrders())); return; }
   if(method=="SessionSellOrders") { RespondLong(command_id, true, (long)(obj.SessionSellOrders())); return; }
   if(method=="Bid") { RespondDouble(command_id, true, (double)(obj.Bid())); return; }
   if(method=="BidHigh") { RespondDouble(command_id, true, (double)(obj.BidHigh())); return; }
   if(method=="BidLow") { RespondDouble(command_id, true, (double)(obj.BidLow())); return; }
   if(method=="Ask") { RespondDouble(command_id, true, (double)(obj.Ask())); return; }
   if(method=="AskHigh") { RespondDouble(command_id, true, (double)(obj.AskHigh())); return; }
   if(method=="AskLow") { RespondDouble(command_id, true, (double)(obj.AskLow())); return; }
   if(method=="Last") { RespondDouble(command_id, true, (double)(obj.Last())); return; }
   if(method=="LastHigh") { RespondDouble(command_id, true, (double)(obj.LastHigh())); return; }
   if(method=="LastLow") { RespondDouble(command_id, true, (double)(obj.LastLow())); return; }
   if(method=="MarginInitial") { RespondDouble(command_id, true, (double)(obj.MarginInitial())); return; }
   if(method=="MarginMaintenance") { RespondDouble(command_id, true, (double)(obj.MarginMaintenance())); return; }
   if(method=="MarginLong") { RespondDouble(command_id, true, (double)(obj.MarginLong())); return; }
   if(method=="MarginShort") { RespondDouble(command_id, true, (double)(obj.MarginShort())); return; }
   if(method=="MarginLimit") { RespondDouble(command_id, true, (double)(obj.MarginLimit())); return; }
   if(method=="MarginStop") { RespondDouble(command_id, true, (double)(obj.MarginStop())); return; }
   if(method=="MarginStopLimit") { RespondDouble(command_id, true, (double)(obj.MarginStopLimit())); return; }
   if(method=="Point") { RespondDouble(command_id, true, (double)(obj.Point())); return; }
   if(method=="TickValue") { RespondDouble(command_id, true, (double)(obj.TickValue())); return; }
   if(method=="TickValueProfit") { RespondDouble(command_id, true, (double)(obj.TickValueProfit())); return; }
   if(method=="TickValueLoss") { RespondDouble(command_id, true, (double)(obj.TickValueLoss())); return; }
   if(method=="TickSize") { RespondDouble(command_id, true, (double)(obj.TickSize())); return; }
   if(method=="ContractSize") { RespondDouble(command_id, true, (double)(obj.ContractSize())); return; }
   if(method=="LotsMin") { RespondDouble(command_id, true, (double)(obj.LotsMin())); return; }
   if(method=="LotsMax") { RespondDouble(command_id, true, (double)(obj.LotsMax())); return; }
   if(method=="LotsStep") { RespondDouble(command_id, true, (double)(obj.LotsStep())); return; }
   if(method=="LotsLimit") { RespondDouble(command_id, true, (double)(obj.LotsLimit())); return; }
   if(method=="SwapLong") { RespondDouble(command_id, true, (double)(obj.SwapLong())); return; }
   if(method=="SwapShort") { RespondDouble(command_id, true, (double)(obj.SwapShort())); return; }
   if(method=="SessionTurnover") { RespondDouble(command_id, true, (double)(obj.SessionTurnover())); return; }
   if(method=="SessionInterest") { RespondDouble(command_id, true, (double)(obj.SessionInterest())); return; }
   if(method=="SessionBuyOrdersVolume") { RespondDouble(command_id, true, (double)(obj.SessionBuyOrdersVolume())); return; }
   if(method=="SessionSellOrdersVolume") { RespondDouble(command_id, true, (double)(obj.SessionSellOrdersVolume())); return; }
   if(method=="SessionOpen") { RespondDouble(command_id, true, (double)(obj.SessionOpen())); return; }
   if(method=="SessionClose") { RespondDouble(command_id, true, (double)(obj.SessionClose())); return; }
   if(method=="SessionAW") { RespondDouble(command_id, true, (double)(obj.SessionAW())); return; }
   if(method=="SessionPriceSettlement") { RespondDouble(command_id, true, (double)(obj.SessionPriceSettlement())); return; }
   if(method=="SessionPriceLimitMin") { RespondDouble(command_id, true, (double)(obj.SessionPriceLimitMin())); return; }
   if(method=="SessionPriceLimitMax") { RespondDouble(command_id, true, (double)(obj.SessionPriceLimitMax())); return; }
   if(method=="TradeCalcModeDescription") { RespondString(command_id, true, obj.TradeCalcModeDescription()); return; }
   if(method=="TradeModeDescription") { RespondString(command_id, true, obj.TradeModeDescription()); return; }
   if(method=="TradeExecutionDescription") { RespondString(command_id, true, obj.TradeExecutionDescription()); return; }
   if(method=="SwapModeDescription") { RespondString(command_id, true, obj.SwapModeDescription()); return; }
   if(method=="SwapRollover3daysDescription") { RespondString(command_id, true, obj.SwapRollover3daysDescription()); return; }
   if(method=="CurrencyBase") { RespondString(command_id, true, obj.CurrencyBase()); return; }
   if(method=="CurrencyProfit") { RespondString(command_id, true, obj.CurrencyProfit()); return; }
   if(method=="CurrencyMargin") { RespondString(command_id, true, obj.CurrencyMargin()); return; }
   if(method=="Bank") { RespondString(command_id, true, obj.Bank()); return; }
   if(method=="Description") { RespondString(command_id, true, obj.Description()); return; }
   if(method=="Path") { RespondString(command_id, true, obj.Path()); return; }
   if(method=="InfoInteger")
     {
      long value=0; bool ok=obj.InfoInteger((ENUM_SYMBOL_INFO_INTEGER)ParseEnumCode(args,0),value);
      RespondRaw(command_id,true,PropertyLongJson(ok,value,ok ? "" : "InfoInteger failed")); return;
     }
   if(method=="InfoDouble")
     {
      double value=0; bool ok=obj.InfoDouble((ENUM_SYMBOL_INFO_DOUBLE)ParseEnumCode(args,0),value);
      RespondRaw(command_id,true,PropertyDoubleJson(ok,value,ok ? "" : "InfoDouble failed")); return;
     }
   if(method=="InfoString")
     {
      string value=""; bool ok=obj.InfoString((ENUM_SYMBOL_INFO_STRING)ParseEnumCode(args,0),value);
      RespondRaw(command_id,true,PropertyStringJson(ok,value,ok ? "" : "InfoString failed")); return;
     }
   if(method=="NormalizePrice") { RespondDouble(command_id,true,obj.NormalizePrice(ArgDouble(args,0))); return; }
   if(method=="SymbolsTotal")
     {
      bool selected = (ArraySize(args) > 0) ? ArgBool(args, 0, false) : false;
      RespondLong(command_id, true, (long)SymbolsTotal(selected));
      return;
     }
   if(method=="SymbolsGet")
     {
      string group = (ArraySize(args) > 0) ? ArgString(args, 0, "") : "";
      int total = SymbolsTotal(false);
      string json="[";
      bool first=true;
      for(int i=0; i<total; i++)
        {
         string name=SymbolName(i, false);
         if(MatchSymbolGroup(name, group))
           {
            if(!first) json+=",";
            json+=JsonQuote(name);
            first=false;
           }
        }
      json+="]";
      RespondRaw(command_id, true, json);
      return;
     }
   if(method=="SymbolInfoTick")
     {
      string sym = (ArraySize(args) > 0 && args[0] != "") ? ArgString(args, 0) : obj.Name();
      MqlTick tick;
      if(!SymbolInfoTick(sym, tick))
        {
         RespondRaw(command_id, true, "null");
         return;
        }
      string j = "{";
      j += "\"time\":" + JsonLong((long)tick.time) + ",";
      j += "\"bid\":" + JsonDouble(tick.bid) + ",";
      j += "\"ask\":" + JsonDouble(tick.ask) + ",";
      j += "\"last\":" + JsonDouble(tick.last) + ",";
      j += "\"volume\":" + JsonLong((long)tick.volume) + ",";
      j += "\"time_msc\":" + JsonLong(tick.time_msc) + ",";
      j += "\"flags\":" + JsonLong((long)tick.flags) + ",";
      j += "\"volume_real\":" + JsonDouble(tick.volume_real) + "}";
      RespondRaw(command_id, true, j);
      return;
     }
   if(method=="SymbolSelect")
     {
      string sym = obj.Name();
      bool enable = true;
      if(ArraySize(args) == 1)
        {
         if(args[0] == "true" || args[0] == "false" || args[0] == "1" || args[0] == "0")
           enable = ArgBool(args, 0);
         else
           sym = ArgString(args, 0);
        }
      else if(ArraySize(args) >= 2)
        {
         if(args[0] != "") sym = ArgString(args, 0);
         enable = ArgBool(args, 1);
        }
      RespondBool(command_id, true, SymbolSelect(sym, enable));
      return;
     }
   if(method=="MarketBookAdd")
     {
      string sym = (ArraySize(args) > 0 && args[0] != "") ? ArgString(args, 0) : obj.Name();
      RespondBool(command_id, true, MarketBookAdd(sym));
      return;
     }
   if(method=="MarketBookRelease")
     {
      string sym = (ArraySize(args) > 0 && args[0] != "") ? ArgString(args, 0) : obj.Name();
      RespondBool(command_id, true, MarketBookRelease(sym));
      return;
     }
   if(method=="MarketBookGet")
     {
      string sym = (ArraySize(args) > 0 && args[0] != "") ? ArgString(args, 0) : obj.Name();
      MqlBookInfo book[];
      if(!MarketBookGet(sym, book))
        {
         RespondRaw(command_id, true, "[]");
         return;
        }
      int size = ArraySize(book);
      string json = "[";
      for(int i = 0; i < size; i++)
        {
         if(i > 0) json += ",";
         json += "{";
         json += "\"type\":" + JsonLong((long)book[i].type) + ",";
         json += "\"price\":" + JsonDouble(book[i].price) + ",";
         json += "\"volume\":" + JsonLong((long)book[i].volume) + ",";
         json += "\"volume_real\":" + JsonDouble(book[i].volume_real);
         json += "}";
        }
      json += "]";
      RespondRaw(command_id, true, json);
      return;
     }
   if(method=="Custom") { RespondBool(command_id, true, (bool)SymbolInfoInteger(obj.Name(), SYMBOL_CUSTOM)); return; }
   if(method=="ChartMode") { RespondLong(command_id, true, (long)SymbolInfoInteger(obj.Name(), SYMBOL_CHART_MODE)); return; }
   if(method=="Visible") { RespondBool(command_id, true, (bool)SymbolInfoInteger(obj.Name(), SYMBOL_VISIBLE)); return; }
   if(method=="StartTime") { RespondLong(command_id, true, (long)SymbolInfoInteger(obj.Name(), SYMBOL_START_TIME)); return; }
   if(method=="ExpirationTime") { RespondLong(command_id, true, (long)SymbolInfoInteger(obj.Name(), SYMBOL_EXPIRATION_TIME)); return; }
   if(method=="MarginHedgedUseLeg") { RespondBool(command_id, true, (bool)SymbolInfoInteger(obj.Name(), SYMBOL_MARGIN_HEDGED_USE_LEG)); return; }
   if(method=="ExpirationMode") { RespondLong(command_id, true, (long)SymbolInfoInteger(obj.Name(), SYMBOL_EXPIRATION_MODE)); return; }
   if(method=="FillingMode") { RespondLong(command_id, true, (long)SymbolInfoInteger(obj.Name(), SYMBOL_FILLING_MODE)); return; }
   if(method=="OrderMode") { RespondLong(command_id, true, (long)SymbolInfoInteger(obj.Name(), SYMBOL_ORDER_MODE)); return; }
   if(method=="OrderGTCMode") { RespondLong(command_id, true, (long)SymbolInfoInteger(obj.Name(), SYMBOL_ORDER_GTC_MODE)); return; }
   if(method=="OptionMode") { RespondLong(command_id, true, (long)SymbolInfoInteger(obj.Name(), SYMBOL_OPTION_MODE)); return; }
   if(method=="OptionRight") { RespondLong(command_id, true, (long)SymbolInfoInteger(obj.Name(), SYMBOL_OPTION_RIGHT)); return; }
   if(method=="VolumeReal") { RespondDouble(command_id, true, SymbolInfoDouble(obj.Name(), SYMBOL_VOLUME_REAL)); return; }
   if(method=="VolumeHighReal") { RespondDouble(command_id, true, SymbolInfoDouble(obj.Name(), SYMBOL_VOLUMEHIGH_REAL)); return; }
   if(method=="VolumeLowReal") { RespondDouble(command_id, true, SymbolInfoDouble(obj.Name(), SYMBOL_VOLUMELOW_REAL)); return; }
   if(method=="OptionStrike") { RespondDouble(command_id, true, SymbolInfoDouble(obj.Name(), SYMBOL_OPTION_STRIKE)); return; }
   if(method=="TradeAccruedInterest") { RespondDouble(command_id, true, SymbolInfoDouble(obj.Name(), SYMBOL_TRADE_ACCRUED_INTEREST)); return; }
   if(method=="TradeFaceValue") { RespondDouble(command_id, true, SymbolInfoDouble(obj.Name(), SYMBOL_TRADE_FACE_VALUE)); return; }
   if(method=="TradeLiquidityRate") { RespondDouble(command_id, true, SymbolInfoDouble(obj.Name(), SYMBOL_TRADE_LIQUIDITY_RATE)); return; }
   if(method=="SessionVolume") { RespondDouble(command_id, true, SymbolInfoDouble(obj.Name(), SYMBOL_SESSION_VOLUME)); return; }
   if(method=="MarginHedged") { RespondDouble(command_id, true, SymbolInfoDouble(obj.Name(), SYMBOL_MARGIN_HEDGED)); return; }
   if(method=="PriceChange") { RespondDouble(command_id, true, SymbolInfoDouble(obj.Name(), SYMBOL_PRICE_CHANGE)); return; }
   if(method=="PriceVolatility") { RespondDouble(command_id, true, SymbolInfoDouble(obj.Name(), SYMBOL_PRICE_VOLATILITY)); return; }
   if(method=="PriceTheoretical") { RespondDouble(command_id, true, SymbolInfoDouble(obj.Name(), SYMBOL_PRICE_THEORETICAL)); return; }
   if(method=="PriceGreeksDelta") { RespondDouble(command_id, true, SymbolInfoDouble(obj.Name(), SYMBOL_PRICE_DELTA)); return; }
   if(method=="PriceGreeksTheta") { RespondDouble(command_id, true, SymbolInfoDouble(obj.Name(), SYMBOL_PRICE_THETA)); return; }
   if(method=="PriceGreeksGamma") { RespondDouble(command_id, true, SymbolInfoDouble(obj.Name(), SYMBOL_PRICE_GAMMA)); return; }
   if(method=="PriceGreeksVega") { RespondDouble(command_id, true, SymbolInfoDouble(obj.Name(), SYMBOL_PRICE_VEGA)); return; }
   if(method=="PriceGreeksRho") { RespondDouble(command_id, true, SymbolInfoDouble(obj.Name(), SYMBOL_PRICE_RHO)); return; }
   if(method=="PriceGreeksOmega") { RespondDouble(command_id, true, SymbolInfoDouble(obj.Name(), SYMBOL_PRICE_OMEGA)); return; }
   if(method=="PriceSensitivity") { RespondDouble(command_id, true, SymbolInfoDouble(obj.Name(), SYMBOL_PRICE_SENSITIVITY)); return; }
   if(method=="Basis") { RespondString(command_id, true, SymbolInfoString(obj.Name(), SYMBOL_BASIS)); return; }
   if(method=="Category") { RespondString(command_id, true, SymbolInfoString(obj.Name(), SYMBOL_CATEGORY)); return; }
   if(method=="Exchange") { RespondString(command_id, true, SymbolInfoString(obj.Name(), SYMBOL_EXCHANGE)); return; }
   if(method=="Formula") { RespondString(command_id, true, SymbolInfoString(obj.Name(), SYMBOL_FORMULA)); return; }
   if(method=="ISIN") { RespondString(command_id, true, SymbolInfoString(obj.Name(), SYMBOL_ISIN)); return; }
   if(method=="Page") { RespondString(command_id, true, SymbolInfoString(obj.Name(), SYMBOL_PAGE)); return; }
   if(method=="as_dict")
     {
      string sym = obj.Name();
      string j = "{";
      j += "\"custom\":" + JsonBool((bool)SymbolInfoInteger(sym, SYMBOL_CUSTOM)) + ",";
      j += "\"chart_mode\":" + JsonLong((long)SymbolInfoInteger(sym, SYMBOL_CHART_MODE)) + ",";
      j += "\"select\":" + JsonBool((bool)SymbolInfoInteger(sym, SYMBOL_SELECT)) + ",";
      j += "\"visible\":" + JsonBool((bool)SymbolInfoInteger(sym, SYMBOL_VISIBLE)) + ",";
      j += "\"session_deals\":" + JsonLong((long)SymbolInfoInteger(sym, SYMBOL_SESSION_DEALS)) + ",";
      j += "\"session_buy_orders\":" + JsonLong((long)SymbolInfoInteger(sym, SYMBOL_SESSION_BUY_ORDERS)) + ",";
      j += "\"session_sell_orders\":" + JsonLong((long)SymbolInfoInteger(sym, SYMBOL_SESSION_SELL_ORDERS)) + ",";
      j += "\"volume\":" + JsonLong((long)SymbolInfoInteger(sym, SYMBOL_VOLUME)) + ",";
      j += "\"volumehigh\":" + JsonLong((long)SymbolInfoInteger(sym, SYMBOL_VOLUMEHIGH)) + ",";
      j += "\"volumelow\":" + JsonLong((long)SymbolInfoInteger(sym, SYMBOL_VOLUMELOW)) + ",";
      j += "\"time\":" + JsonLong((long)SymbolInfoInteger(sym, SYMBOL_TIME)) + ",";
      j += "\"digits\":" + JsonLong((long)SymbolInfoInteger(sym, SYMBOL_DIGITS)) + ",";
      j += "\"spread\":" + JsonLong((long)SymbolInfoInteger(sym, SYMBOL_SPREAD)) + ",";
      j += "\"spread_float\":" + JsonBool((bool)SymbolInfoInteger(sym, SYMBOL_SPREAD_FLOAT)) + ",";
      j += "\"ticks_bookdepth\":" + JsonLong((long)SymbolInfoInteger(sym, SYMBOL_TICKS_BOOKDEPTH)) + ",";
      j += "\"trade_calc_mode\":" + JsonLong((long)SymbolInfoInteger(sym, SYMBOL_TRADE_CALC_MODE)) + ",";
      j += "\"trade_mode\":" + JsonLong((long)SymbolInfoInteger(sym, SYMBOL_TRADE_MODE)) + ",";
      j += "\"start_time\":" + JsonLong((long)SymbolInfoInteger(sym, SYMBOL_START_TIME)) + ",";
      j += "\"expiration_time\":" + JsonLong((long)SymbolInfoInteger(sym, SYMBOL_EXPIRATION_TIME)) + ",";
      j += "\"trade_stops_level\":" + JsonLong((long)SymbolInfoInteger(sym, SYMBOL_TRADE_STOPS_LEVEL)) + ",";
      j += "\"trade_freeze_level\":" + JsonLong((long)SymbolInfoInteger(sym, SYMBOL_TRADE_FREEZE_LEVEL)) + ",";
      j += "\"trade_exemode\":" + JsonLong((long)SymbolInfoInteger(sym, SYMBOL_TRADE_EXEMODE)) + ",";
      j += "\"swap_mode\":" + JsonLong((long)SymbolInfoInteger(sym, SYMBOL_SWAP_MODE)) + ",";
      j += "\"swap_rollover3days\":" + JsonLong((long)SymbolInfoInteger(sym, SYMBOL_SWAP_ROLLOVER3DAYS)) + ",";
      j += "\"margin_hedged_use_leg\":" + JsonBool((bool)SymbolInfoInteger(sym, SYMBOL_MARGIN_HEDGED_USE_LEG)) + ",";
      j += "\"expiration_mode\":" + JsonLong((long)SymbolInfoInteger(sym, SYMBOL_EXPIRATION_MODE)) + ",";
      j += "\"filling_mode\":" + JsonLong((long)SymbolInfoInteger(sym, SYMBOL_FILLING_MODE)) + ",";
      j += "\"order_mode\":" + JsonLong((long)SymbolInfoInteger(sym, SYMBOL_ORDER_MODE)) + ",";
      j += "\"order_gtc_mode\":" + JsonLong((long)SymbolInfoInteger(sym, SYMBOL_ORDER_GTC_MODE)) + ",";
      j += "\"option_mode\":" + JsonLong((long)SymbolInfoInteger(sym, SYMBOL_OPTION_MODE)) + ",";
      j += "\"option_right\":" + JsonLong((long)SymbolInfoInteger(sym, SYMBOL_OPTION_RIGHT)) + ",";
      j += "\"bid\":" + JsonDouble(SymbolInfoDouble(sym, SYMBOL_BID)) + ",";
      j += "\"bidhigh\":" + JsonDouble(SymbolInfoDouble(sym, SYMBOL_BIDHIGH)) + ",";
      j += "\"bidlow\":" + JsonDouble(SymbolInfoDouble(sym, SYMBOL_BIDLOW)) + ",";
      j += "\"ask\":" + JsonDouble(SymbolInfoDouble(sym, SYMBOL_ASK)) + ",";
      j += "\"askhigh\":" + JsonDouble(SymbolInfoDouble(sym, SYMBOL_ASKHIGH)) + ",";
      j += "\"asklow\":" + JsonDouble(SymbolInfoDouble(sym, SYMBOL_ASKLOW)) + ",";
      j += "\"last\":" + JsonDouble(SymbolInfoDouble(sym, SYMBOL_LAST)) + ",";
      j += "\"lasthigh\":" + JsonDouble(SymbolInfoDouble(sym, SYMBOL_LASTHIGH)) + ",";
      j += "\"lastlow\":" + JsonDouble(SymbolInfoDouble(sym, SYMBOL_LASTLOW)) + ",";
      j += "\"volume_real\":" + JsonDouble(SymbolInfoDouble(sym, SYMBOL_VOLUME_REAL)) + ",";
      j += "\"volumehigh_real\":" + JsonDouble(SymbolInfoDouble(sym, SYMBOL_VOLUMEHIGH_REAL)) + ",";
      j += "\"volumelow_real\":" + JsonDouble(SymbolInfoDouble(sym, SYMBOL_VOLUMELOW_REAL)) + ",";
      j += "\"option_strike\":" + JsonDouble(SymbolInfoDouble(sym, SYMBOL_OPTION_STRIKE)) + ",";
      j += "\"point\":" + JsonDouble(SymbolInfoDouble(sym, SYMBOL_POINT)) + ",";
      j += "\"trade_tick_value\":" + JsonDouble(SymbolInfoDouble(sym, SYMBOL_TRADE_TICK_VALUE)) + ",";
      j += "\"trade_tick_value_profit\":" + JsonDouble(SymbolInfoDouble(sym, SYMBOL_TRADE_TICK_VALUE_PROFIT)) + ",";
      j += "\"trade_tick_value_loss\":" + JsonDouble(SymbolInfoDouble(sym, SYMBOL_TRADE_TICK_VALUE_LOSS)) + ",";
      j += "\"trade_tick_size\":" + JsonDouble(SymbolInfoDouble(sym, SYMBOL_TRADE_TICK_SIZE)) + ",";
      j += "\"trade_contract_size\":" + JsonDouble(SymbolInfoDouble(sym, SYMBOL_TRADE_CONTRACT_SIZE)) + ",";
      j += "\"trade_accrued_interest\":" + JsonDouble(SymbolInfoDouble(sym, SYMBOL_TRADE_ACCRUED_INTEREST)) + ",";
      j += "\"trade_face_value\":" + JsonDouble(SymbolInfoDouble(sym, SYMBOL_TRADE_FACE_VALUE)) + ",";
      j += "\"trade_liquidity_rate\":" + JsonDouble(SymbolInfoDouble(sym, SYMBOL_TRADE_LIQUIDITY_RATE)) + ",";
      j += "\"volume_min\":" + JsonDouble(SymbolInfoDouble(sym, SYMBOL_VOLUME_MIN)) + ",";
      j += "\"volume_max\":" + JsonDouble(SymbolInfoDouble(sym, SYMBOL_VOLUME_MAX)) + ",";
      j += "\"volume_step\":" + JsonDouble(SymbolInfoDouble(sym, SYMBOL_VOLUME_STEP)) + ",";
      j += "\"volume_limit\":" + JsonDouble(SymbolInfoDouble(sym, SYMBOL_VOLUME_LIMIT)) + ",";
      j += "\"swap_long\":" + JsonDouble(SymbolInfoDouble(sym, SYMBOL_SWAP_LONG)) + ",";
      j += "\"swap_short\":" + JsonDouble(SymbolInfoDouble(sym, SYMBOL_SWAP_SHORT)) + ",";
      j += "\"margin_initial\":" + JsonDouble(SymbolInfoDouble(sym, SYMBOL_MARGIN_INITIAL)) + ",";
      j += "\"margin_maintenance\":" + JsonDouble(SymbolInfoDouble(sym, SYMBOL_MARGIN_MAINTENANCE)) + ",";
      j += "\"session_volume\":" + JsonDouble(SymbolInfoDouble(sym, SYMBOL_SESSION_VOLUME)) + ",";
      j += "\"session_turnover\":" + JsonDouble(SymbolInfoDouble(sym, SYMBOL_SESSION_TURNOVER)) + ",";
      j += "\"session_interest\":" + JsonDouble(SymbolInfoDouble(sym, SYMBOL_SESSION_INTEREST)) + ",";
      j += "\"session_buy_orders_volume\":" + JsonDouble(SymbolInfoDouble(sym, SYMBOL_SESSION_BUY_ORDERS_VOLUME)) + ",";
      j += "\"session_sell_orders_volume\":" + JsonDouble(SymbolInfoDouble(sym, SYMBOL_SESSION_SELL_ORDERS_VOLUME)) + ",";
      j += "\"session_open\":" + JsonDouble(SymbolInfoDouble(sym, SYMBOL_SESSION_OPEN)) + ",";
      j += "\"session_close\":" + JsonDouble(SymbolInfoDouble(sym, SYMBOL_SESSION_CLOSE)) + ",";
      j += "\"session_aw\":" + JsonDouble(SymbolInfoDouble(sym, SYMBOL_SESSION_AW)) + ",";
      j += "\"session_price_settlement\":" + JsonDouble(SymbolInfoDouble(sym, SYMBOL_SESSION_PRICE_SETTLEMENT)) + ",";
      j += "\"session_price_limit_min\":" + JsonDouble(SymbolInfoDouble(sym, SYMBOL_SESSION_PRICE_LIMIT_MIN)) + ",";
      j += "\"session_price_limit_max\":" + JsonDouble(SymbolInfoDouble(sym, SYMBOL_SESSION_PRICE_LIMIT_MAX)) + ",";
      j += "\"margin_hedged\":" + JsonDouble(SymbolInfoDouble(sym, SYMBOL_MARGIN_HEDGED)) + ",";
      j += "\"price_change\":" + JsonDouble(SymbolInfoDouble(sym, SYMBOL_PRICE_CHANGE)) + ",";
      j += "\"price_volatility\":" + JsonDouble(SymbolInfoDouble(sym, SYMBOL_PRICE_VOLATILITY)) + ",";
      j += "\"price_theoretical\":" + JsonDouble(SymbolInfoDouble(sym, SYMBOL_PRICE_THEORETICAL)) + ",";
      j += "\"price_greeks_delta\":" + JsonDouble(SymbolInfoDouble(sym, SYMBOL_PRICE_DELTA)) + ",";
      j += "\"price_greeks_theta\":" + JsonDouble(SymbolInfoDouble(sym, SYMBOL_PRICE_THETA)) + ",";
      j += "\"price_greeks_gamma\":" + JsonDouble(SymbolInfoDouble(sym, SYMBOL_PRICE_GAMMA)) + ",";
      j += "\"price_greeks_vega\":" + JsonDouble(SymbolInfoDouble(sym, SYMBOL_PRICE_VEGA)) + ",";
      j += "\"price_greeks_rho\":" + JsonDouble(SymbolInfoDouble(sym, SYMBOL_PRICE_RHO)) + ",";
      j += "\"price_greeks_omega\":" + JsonDouble(SymbolInfoDouble(sym, SYMBOL_PRICE_OMEGA)) + ",";
      j += "\"price_sensitivity\":" + JsonDouble(SymbolInfoDouble(sym, SYMBOL_PRICE_SENSITIVITY)) + ",";
      j += "\"basis\":" + JsonQuote(SymbolInfoString(sym, SYMBOL_BASIS)) + ",";
      j += "\"category\":" + JsonQuote(SymbolInfoString(sym, SYMBOL_CATEGORY)) + ",";
      j += "\"currency_base\":" + JsonQuote(SymbolInfoString(sym, SYMBOL_CURRENCY_BASE)) + ",";
      j += "\"currency_profit\":" + JsonQuote(SymbolInfoString(sym, SYMBOL_CURRENCY_PROFIT)) + ",";
      j += "\"currency_margin\":" + JsonQuote(SymbolInfoString(sym, SYMBOL_CURRENCY_MARGIN)) + ",";
      j += "\"bank\":" + JsonQuote(SymbolInfoString(sym, SYMBOL_BANK)) + ",";
      j += "\"description\":" + JsonQuote(SymbolInfoString(sym, SYMBOL_DESCRIPTION)) + ",";
      j += "\"exchange\":" + JsonQuote(SymbolInfoString(sym, SYMBOL_EXCHANGE)) + ",";
      j += "\"formula\":" + JsonQuote(SymbolInfoString(sym, SYMBOL_FORMULA)) + ",";
      j += "\"isin\":" + JsonQuote(SymbolInfoString(sym, SYMBOL_ISIN)) + ",";
      j += "\"name\":" + JsonQuote(sym) + ",";
      j += "\"page\":" + JsonQuote(SymbolInfoString(sym, SYMBOL_PAGE)) + ",";
      j += "\"path\":" + JsonQuote(SymbolInfoString(sym, SYMBOL_PATH)) + "}";
      RespondRaw(command_id, true, j);
      return;
     }
   RespondError(command_id,"METHOD_NOT_IMPLEMENTED","unknown CSymbolInfo method: "+method);
  }

void DispatchOrder(const string command_id,const string object_id,const string method,string &args[])
  {
   COrderInfo *p=GetOrder(object_id); if(CheckPointer(p)==POINTER_INVALID) { RespondError(command_id,"OBJECT_CREATE_FAILED","COrderInfo allocation failed"); return; }
   COrderInfo *obj=p;
   if(method=="Ticket") { RespondULong(command_id, true, (ulong)(obj.Ticket())); return; }
   if(method=="TimeSetup") { RespondLong(command_id, true, (long)(obj.TimeSetup())); return; }
   if(method=="TimeSetupMsc") { RespondLong(command_id, true, (long)(obj.TimeSetupMsc())); return; }
   if(method=="OrderType") { RespondLong(command_id, true, (long)(obj.OrderType())); return; }
   if(method=="State") { RespondLong(command_id, true, (long)(obj.State())); return; }
   if(method=="TimeExpiration") { RespondLong(command_id, true, (long)(obj.TimeExpiration())); return; }
   if(method=="TimeDone") { RespondLong(command_id, true, (long)(obj.TimeDone())); return; }
   if(method=="TimeDoneMsc") { RespondLong(command_id, true, (long)(obj.TimeDoneMsc())); return; }
   if(method=="TypeFilling") { RespondLong(command_id, true, (long)(obj.TypeFilling())); return; }
   if(method=="TypeTime") { RespondLong(command_id, true, (long)(obj.TypeTime())); return; }
   if(method=="Magic") { RespondULong(command_id, true, (ulong)(obj.Magic())); return; }
   if(method=="PositionId") { RespondULong(command_id, true, (ulong)(obj.PositionId())); return; }
   if(method=="TypeDescription") { RespondString(command_id, true, obj.TypeDescription()); return; }
   if(method=="StateDescription") { RespondString(command_id, true, obj.StateDescription()); return; }
   if(method=="TypeFillingDescription") { RespondString(command_id, true, obj.TypeFillingDescription()); return; }
   if(method=="TypeTimeDescription") { RespondString(command_id, true, obj.TypeTimeDescription()); return; }
   if(method=="Symbol") { RespondString(command_id, true, obj.Symbol()); return; }
   if(method=="Comment") { RespondString(command_id, true, obj.Comment()); return; }
   if(method=="VolumeInitial") { RespondDouble(command_id, true, (double)(obj.VolumeInitial())); return; }
   if(method=="VolumeCurrent") { RespondDouble(command_id, true, (double)(obj.VolumeCurrent())); return; }
   if(method=="PriceOpen") { RespondDouble(command_id, true, (double)(obj.PriceOpen())); return; }
   if(method=="StopLoss") { RespondDouble(command_id, true, (double)(obj.StopLoss())); return; }
   if(method=="TakeProfit") { RespondDouble(command_id, true, (double)(obj.TakeProfit())); return; }
   if(method=="PriceCurrent") { RespondDouble(command_id, true, (double)(obj.PriceCurrent())); return; }
   if(method=="PriceStopLimit") { RespondDouble(command_id, true, (double)(obj.PriceStopLimit())); return; }
   if(method=="InfoInteger") { long v=0; bool ok=obj.InfoInteger((ENUM_ORDER_PROPERTY_INTEGER)ParseEnumCode(args,0),v); RespondRaw(command_id,true,PropertyLongJson(ok,v,ok?"":"InfoInteger failed")); return; }
   if(method=="InfoDouble") { double v=0; bool ok=obj.InfoDouble((ENUM_ORDER_PROPERTY_DOUBLE)ParseEnumCode(args,0),v); RespondRaw(command_id,true,PropertyDoubleJson(ok,v,ok?"":"InfoDouble failed")); return; }
   if(method=="InfoString") { string v=""; bool ok=obj.InfoString((ENUM_ORDER_PROPERTY_STRING)ParseEnumCode(args,0),v); RespondRaw(command_id,true,PropertyStringJson(ok,v,ok?"":"InfoString failed")); return; }
   if(method=="StoreState") { obj.StoreState(); RespondBool(command_id,true,true); return; }
   if(method=="CheckState") { RespondBool(command_id,true,obj.CheckState()); return; }
   if(method=="Select") { RespondBool(command_id,true,obj.Select(ArgULong(args,0))); return; }
   if(method=="SelectByIndex") { RespondBool(command_id,true,obj.SelectByIndex((int)ArgLong(args,0))); return; }
   if(method=="OrdersTotal") { RespondLong(command_id,true,(long)OrdersTotal()); return; }
   if(method=="OrdersGet")
     {
      string filter_sym=""; string filter_grp=""; ulong filter_tkt=0;
      if(ArraySize(args)>0 && args[0]!="null" && StringLen(args[0])>0)
        {
         if(StringFind(args[0],"{")>=0)
           {
            JsonGetString(args[0],"symbol",filter_sym);
            JsonGetString(args[0],"group",filter_grp);
            filter_tkt=JsonGetULong(args[0],"ticket",0);
           }
         else
           {
            filter_sym=ArgString(args,0);
            if(ArraySize(args)>1) filter_grp=ArgString(args,1);
            if(ArraySize(args)>2) filter_tkt=ArgULong(args,2);
           }
        }
      string out="[";
      int count=OrdersTotal();
      bool first=true;
      for(int i=0;i<count;i++)
        {
         ulong ticket=OrderGetTicket(i);
         if(ticket==0) continue;
         string sym=OrderGetString(ORDER_SYMBOL);
         if(filter_tkt!=0 && ticket!=filter_tkt) continue;
         if(StringLen(filter_sym)>0 && sym!=filter_sym) continue;
         if(StringLen(filter_grp)>0 && !MatchSymbolGroup(sym,filter_grp)) continue;
         if(!first) out+=",";
         first=false;
         out+="{\"ticket\":"+JsonULong(ticket)+
              ",\"symbol\":"+JsonQuote(sym)+
              ",\"order_type\":"+JsonLong(OrderGetInteger(ORDER_TYPE))+
              ",\"state\":"+JsonLong(OrderGetInteger(ORDER_STATE))+
              ",\"volume_initial\":"+JsonDouble(OrderGetDouble(ORDER_VOLUME_INITIAL))+
              ",\"volume_current\":"+JsonDouble(OrderGetDouble(ORDER_VOLUME_CURRENT))+
              ",\"price_open\":"+JsonDouble(OrderGetDouble(ORDER_PRICE_OPEN))+
              ",\"sl\":"+JsonDouble(OrderGetDouble(ORDER_SL))+
              ",\"tp\":"+JsonDouble(OrderGetDouble(ORDER_TP))+
              ",\"price_current\":"+JsonDouble(OrderGetDouble(ORDER_PRICE_CURRENT))+
              ",\"price_stop_limit\":"+JsonDouble(OrderGetDouble(ORDER_PRICE_STOPLIMIT))+
              ",\"time_setup\":"+JsonLong(OrderGetInteger(ORDER_TIME_SETUP))+
              ",\"time_done\":"+JsonLong(OrderGetInteger(ORDER_TIME_DONE))+
              ",\"time_expiration\":"+JsonLong(OrderGetInteger(ORDER_TIME_EXPIRATION))+
              ",\"type_filling\":"+JsonLong(OrderGetInteger(ORDER_TYPE_FILLING))+
              ",\"type_time\":"+JsonLong(OrderGetInteger(ORDER_TYPE_TIME))+
              ",\"magic\":"+JsonULong(OrderGetInteger(ORDER_MAGIC))+
              ",\"position_id\":"+JsonULong(OrderGetInteger(ORDER_POSITION_ID))+
              ",\"comment\":"+JsonQuote(OrderGetString(ORDER_COMMENT))+
              "}";
        }
      out+="]";
      RespondRaw(command_id,true,out);
      return;
     }
   RespondError(command_id,"METHOD_NOT_IMPLEMENTED","unknown COrderInfo method: "+method);
  }

void DispatchHistory(const string command_id,const string object_id,const string method,string &args[])
  {
   CHistoryOrderInfo *p=GetHistory(object_id); if(CheckPointer(p)==POINTER_INVALID) { RespondError(command_id,"OBJECT_CREATE_FAILED","CHistoryOrderInfo allocation failed"); return; }
   CHistoryOrderInfo *obj=p;
   if(method=="TimeSetup") { RespondLong(command_id, true, (long)(obj.TimeSetup())); return; }
   if(method=="TimeSetupMsc") { RespondLong(command_id, true, (long)(obj.TimeSetupMsc())); return; }
   if(method=="OrderType") { RespondLong(command_id, true, (long)(obj.OrderType())); return; }
   if(method=="State") { RespondLong(command_id, true, (long)(obj.State())); return; }
   if(method=="TimeExpiration") { RespondLong(command_id, true, (long)(obj.TimeExpiration())); return; }
   if(method=="TimeDone") { RespondLong(command_id, true, (long)(obj.TimeDone())); return; }
   if(method=="TimeDoneMsc") { RespondLong(command_id, true, (long)(obj.TimeDoneMsc())); return; }
   if(method=="TypeFilling") { RespondLong(command_id, true, (long)(obj.TypeFilling())); return; }
   if(method=="TypeTime") { RespondLong(command_id, true, (long)(obj.TypeTime())); return; }
   if(method=="Magic") { RespondULong(command_id, true, (ulong)(obj.Magic())); return; }
   if(method=="PositionId") { RespondULong(command_id, true, (ulong)(obj.PositionId())); return; }
   if(method=="TypeDescription") { RespondString(command_id, true, obj.TypeDescription()); return; }
   if(method=="StateDescription") { RespondString(command_id, true, obj.StateDescription()); return; }
   if(method=="TypeFillingDescription") { RespondString(command_id, true, obj.TypeFillingDescription()); return; }
   if(method=="TypeTimeDescription") { RespondString(command_id, true, obj.TypeTimeDescription()); return; }
   if(method=="Symbol") { RespondString(command_id, true, obj.Symbol()); return; }
   if(method=="Comment") { RespondString(command_id, true, obj.Comment()); return; }
   if(method=="VolumeInitial") { RespondDouble(command_id, true, (double)(obj.VolumeInitial())); return; }
   if(method=="VolumeCurrent") { RespondDouble(command_id, true, (double)(obj.VolumeCurrent())); return; }
   if(method=="PriceOpen") { RespondDouble(command_id, true, (double)(obj.PriceOpen())); return; }
   if(method=="StopLoss") { RespondDouble(command_id, true, (double)(obj.StopLoss())); return; }
   if(method=="TakeProfit") { RespondDouble(command_id, true, (double)(obj.TakeProfit())); return; }
   if(method=="PriceCurrent") { RespondDouble(command_id, true, (double)(obj.PriceCurrent())); return; }
   if(method=="PriceStopLimit") { RespondDouble(command_id, true, (double)(obj.PriceStopLimit())); return; }
   if(method=="InfoInteger") { long v=0; bool ok=obj.InfoInteger((ENUM_ORDER_PROPERTY_INTEGER)ParseEnumCode(args,0),v); RespondRaw(command_id,true,PropertyLongJson(ok,v,ok?"":"InfoInteger failed")); return; }
   if(method=="InfoDouble") { double v=0; bool ok=obj.InfoDouble((ENUM_ORDER_PROPERTY_DOUBLE)ParseEnumCode(args,0),v); RespondRaw(command_id,true,PropertyDoubleJson(ok,v,ok?"":"InfoDouble failed")); return; }
   if(method=="InfoString") { string v=""; bool ok=obj.InfoString((ENUM_ORDER_PROPERTY_STRING)ParseEnumCode(args,0),v); RespondRaw(command_id,true,PropertyStringJson(ok,v,ok?"":"InfoString failed")); return; }
   if(method=="Ticket")
     {
      if(ArraySize(args)==0) RespondULong(command_id,true,obj.Ticket());
      else { obj.Ticket(ArgULong(args,0)); RespondBool(command_id,true,true); }
      return;
     }
   if(method=="SelectByIndex")
     {
      bool selected=HistorySelect(0,TimeCurrent());
      if(selected) selected=obj.SelectByIndex((int)ArgLong(args,0));
      RespondBool(command_id,true,selected);
      return;
     }
   if(method=="HistoryOrdersTotal")
     {
      HistorySelect(0,TimeCurrent());
      RespondLong(command_id,true,(long)HistoryOrdersTotal());
      return;
     }
   if(method=="HistoryOrdersGet")
     {
      HistorySelect(0,TimeCurrent());
      string filter_sym=""; string filter_grp=""; ulong filter_tkt=0; ulong filter_pos=0;
      if(ArraySize(args)>0 && args[0]!="null" && StringLen(args[0])>0)
        {
         if(StringFind(args[0],"{")>=0)
           {
            JsonGetString(args[0],"symbol",filter_sym);
            JsonGetString(args[0],"group",filter_grp);
            filter_tkt=JsonGetULong(args[0],"ticket",0);
            filter_pos=JsonGetULong(args[0],"position",0);
           }
         else
           {
            filter_sym=ArgString(args,0);
            if(ArraySize(args)>1) filter_grp=ArgString(args,1);
            if(ArraySize(args)>2) filter_tkt=ArgULong(args,2);
            if(ArraySize(args)>3) filter_pos=ArgULong(args,3);
           }
        }
      string out="[";
      int count=HistoryOrdersTotal();
      bool first=true;
      for(int i=0;i<count;i++)
        {
         ulong ticket=HistoryOrderGetTicket(i);
         if(ticket==0) continue;
         string sym=HistoryOrderGetString(ticket,ORDER_SYMBOL);
         ulong pos=HistoryOrderGetInteger(ticket,ORDER_POSITION_ID);
         if(filter_tkt!=0 && ticket!=filter_tkt) continue;
         if(filter_pos!=0 && pos!=filter_pos) continue;
         if(StringLen(filter_sym)>0 && sym!=filter_sym) continue;
         if(StringLen(filter_grp)>0 && !MatchSymbolGroup(sym,filter_grp)) continue;
         if(!first) out+=",";
         first=false;
         out+="{\"ticket\":"+JsonULong(ticket)+
              ",\"symbol\":"+JsonQuote(sym)+
              ",\"order_type\":"+JsonLong(HistoryOrderGetInteger(ticket,ORDER_TYPE))+
              ",\"state\":"+JsonLong(HistoryOrderGetInteger(ticket,ORDER_STATE))+
              ",\"volume_initial\":"+JsonDouble(HistoryOrderGetDouble(ticket,ORDER_VOLUME_INITIAL))+
              ",\"volume_current\":"+JsonDouble(HistoryOrderGetDouble(ticket,ORDER_VOLUME_CURRENT))+
              ",\"price_open\":"+JsonDouble(HistoryOrderGetDouble(ticket,ORDER_PRICE_OPEN))+
              ",\"sl\":"+JsonDouble(HistoryOrderGetDouble(ticket,ORDER_SL))+
              ",\"tp\":"+JsonDouble(HistoryOrderGetDouble(ticket,ORDER_TP))+
              ",\"price_current\":"+JsonDouble(HistoryOrderGetDouble(ticket,ORDER_PRICE_CURRENT))+
              ",\"price_stop_limit\":"+JsonDouble(HistoryOrderGetDouble(ticket,ORDER_PRICE_STOPLIMIT))+
              ",\"time_setup\":"+JsonLong(HistoryOrderGetInteger(ticket,ORDER_TIME_SETUP))+
              ",\"time_done\":"+JsonLong(HistoryOrderGetInteger(ticket,ORDER_TIME_DONE))+
              ",\"time_expiration\":"+JsonLong(HistoryOrderGetInteger(ticket,ORDER_TIME_EXPIRATION))+
              ",\"type_filling\":"+JsonLong(HistoryOrderGetInteger(ticket,ORDER_TYPE_FILLING))+
              ",\"type_time\":"+JsonLong(HistoryOrderGetInteger(ticket,ORDER_TYPE_TIME))+
              ",\"magic\":"+JsonULong(HistoryOrderGetInteger(ticket,ORDER_MAGIC))+
              ",\"position_id\":"+JsonULong(pos)+
              ",\"comment\":"+JsonQuote(HistoryOrderGetString(ticket,ORDER_COMMENT))+
              "}";
        }
      out+="]";
      RespondRaw(command_id,true,out);
      return;
     }
   RespondError(command_id,"METHOD_NOT_IMPLEMENTED","unknown CHistoryOrderInfo method: "+method);
  }

void DispatchPosition(const string command_id,const string object_id,const string method,string &args[])
  {
   CPositionInfo *p=GetPosition(object_id); if(CheckPointer(p)==POINTER_INVALID) { RespondError(command_id,"OBJECT_CREATE_FAILED","CPositionInfo allocation failed"); return; }
   CPositionInfo *obj=p;
   if(method=="Time") { RespondLong(command_id, true, (long)(obj.Time())); return; }
   if(method=="TimeMsc") { RespondLong(command_id, true, (long)(obj.TimeMsc())); return; }
   if(method=="TimeUpdate") { RespondLong(command_id, true, (long)(obj.TimeUpdate())); return; }
   if(method=="TimeUpdateMsc") { RespondLong(command_id, true, (long)(obj.TimeUpdateMsc())); return; }
   if(method=="PositionType") { RespondLong(command_id, true, (long)(obj.PositionType())); return; }
   if(method=="Magic") { RespondULong(command_id, true, (ulong)(obj.Magic())); return; }
   if(method=="Identifier") { RespondULong(command_id, true, (ulong)(obj.Identifier())); return; }
   if(method=="TypeDescription") { RespondString(command_id, true, obj.TypeDescription()); return; }
   if(method=="Symbol") { RespondString(command_id, true, obj.Symbol()); return; }
   if(method=="Comment") { RespondString(command_id, true, obj.Comment()); return; }
   if(method=="Volume") { RespondDouble(command_id, true, (double)(obj.Volume())); return; }
   if(method=="PriceOpen") { RespondDouble(command_id, true, (double)(obj.PriceOpen())); return; }
   if(method=="StopLoss") { RespondDouble(command_id, true, (double)(obj.StopLoss())); return; }
   if(method=="TakeProfit") { RespondDouble(command_id, true, (double)(obj.TakeProfit())); return; }
   if(method=="PriceCurrent") { RespondDouble(command_id, true, (double)(obj.PriceCurrent())); return; }
   if(method=="Commission") { RespondDouble(command_id, true, (double)(obj.Commission())); return; }
   if(method=="Swap") { RespondDouble(command_id, true, (double)(obj.Swap())); return; }
   if(method=="Profit") { RespondDouble(command_id, true, (double)(obj.Profit())); return; }
   if(method=="InfoInteger") { long v=0; bool ok=obj.InfoInteger((ENUM_POSITION_PROPERTY_INTEGER)ParseEnumCode(args,0),v); RespondRaw(command_id,true,PropertyLongJson(ok,v,ok?"":"InfoInteger failed")); return; }
   if(method=="InfoDouble") { double v=0; bool ok=obj.InfoDouble((ENUM_POSITION_PROPERTY_DOUBLE)ParseEnumCode(args,0),v); RespondRaw(command_id,true,PropertyDoubleJson(ok,v,ok?"":"InfoDouble failed")); return; }
   if(method=="InfoString") { string v=""; bool ok=obj.InfoString((ENUM_POSITION_PROPERTY_STRING)ParseEnumCode(args,0),v); RespondRaw(command_id,true,PropertyStringJson(ok,v,ok?"":"InfoString failed")); return; }
   if(method=="Select") { RespondBool(command_id,true,obj.Select(ArgString(args,0))); return; }
   if(method=="SelectByIndex") { RespondBool(command_id,true,obj.SelectByIndex((int)ArgLong(args,0))); return; }
   if(method=="SelectByMagic") { RespondBool(command_id,true,obj.SelectByMagic(ArgString(args,0),ArgULong(args,1))); return; }
   if(method=="SelectByTicket") { RespondBool(command_id,true,obj.SelectByTicket(ArgULong(args,0))); return; }
   if(method=="StoreState") { obj.StoreState(); RespondBool(command_id,true,true); return; }
   if(method=="CheckState") { RespondBool(command_id,true,obj.CheckState()); return; }
   if(method=="PositionsTotal") { RespondLong(command_id,true,(long)PositionsTotal()); return; }
   if(method=="PositionsGet")
     {
      string filter_sym=""; string filter_grp=""; ulong filter_tkt=0;
      if(ArraySize(args)>0 && args[0]!="null" && StringLen(args[0])>0)
        {
         if(StringFind(args[0],"{")>=0)
           {
            JsonGetString(args[0],"symbol",filter_sym);
            JsonGetString(args[0],"group",filter_grp);
            filter_tkt=JsonGetULong(args[0],"ticket",0);
           }
         else
           {
            filter_sym=ArgString(args,0);
            if(ArraySize(args)>1) filter_grp=ArgString(args,1);
            if(ArraySize(args)>2) filter_tkt=ArgULong(args,2);
           }
        }
      string out="[";
      int count=PositionsTotal();
      bool first=true;
      for(int i=0;i<count;i++)
        {
         ulong ticket=PositionGetTicket(i);
         if(ticket==0) continue;
         string sym=PositionGetString(POSITION_SYMBOL);
         if(filter_tkt!=0 && ticket!=filter_tkt) continue;
         if(StringLen(filter_sym)>0 && sym!=filter_sym) continue;
         if(StringLen(filter_grp)>0 && !MatchSymbolGroup(sym,filter_grp)) continue;
         if(!first) out+=",";
         first=false;
         out+="{\"ticket\":"+JsonULong(ticket)+
              ",\"identifier\":"+JsonULong(PositionGetInteger(POSITION_IDENTIFIER))+
              ",\"symbol\":"+JsonQuote(sym)+
              ",\"position_type\":"+JsonLong(PositionGetInteger(POSITION_TYPE))+
              ",\"volume\":"+JsonDouble(PositionGetDouble(POSITION_VOLUME))+
              ",\"price_open\":"+JsonDouble(PositionGetDouble(POSITION_PRICE_OPEN))+
              ",\"price_current\":"+JsonDouble(PositionGetDouble(POSITION_PRICE_CURRENT))+
              ",\"sl\":"+JsonDouble(PositionGetDouble(POSITION_SL))+
              ",\"tp\":"+JsonDouble(PositionGetDouble(POSITION_TP))+
              ",\"commission\":"+JsonDouble(0.0)+
              ",\"swap\":"+JsonDouble(PositionGetDouble(POSITION_SWAP))+
              ",\"profit\":"+JsonDouble(PositionGetDouble(POSITION_PROFIT))+
              ",\"magic\":"+JsonULong(PositionGetInteger(POSITION_MAGIC))+
              ",\"comment\":"+JsonQuote(PositionGetString(POSITION_COMMENT))+
              ",\"time\":"+JsonLong(PositionGetInteger(POSITION_TIME))+
              ",\"time_update\":"+JsonLong(PositionGetInteger(POSITION_TIME_UPDATE))+
              "}";
        }
      out+="]";
      RespondRaw(command_id,true,out);
      return;
     }
   RespondError(command_id,"METHOD_NOT_IMPLEMENTED","unknown CPositionInfo method: "+method);
  }

void DispatchDeal(const string command_id,const string object_id,const string method,string &args[])
  {
   CDealInfo *p=GetDeal(object_id); if(CheckPointer(p)==POINTER_INVALID) { RespondError(command_id,"OBJECT_CREATE_FAILED","CDealInfo allocation failed"); return; }
   CDealInfo *obj=p;
   if(method=="Order") { RespondULong(command_id, true, (ulong)(obj.Order())); return; }
   if(method=="Time") { RespondLong(command_id, true, (long)(obj.Time())); return; }
   if(method=="TimeMsc") { RespondLong(command_id, true, (long)(obj.TimeMsc())); return; }
   if(method=="DealType") { RespondLong(command_id, true, (long)(obj.DealType())); return; }
   if(method=="Entry") { RespondLong(command_id, true, (long)(obj.Entry())); return; }
   if(method=="Magic") { RespondULong(command_id, true, (ulong)(obj.Magic())); return; }
   if(method=="PositionId") { RespondULong(command_id, true, (ulong)(obj.PositionId())); return; }
   if(method=="TypeDescription") { RespondString(command_id, true, obj.TypeDescription()); return; }
   if(method=="EntryDescription") { RespondString(command_id, true, obj.EntryDescription()); return; }
   if(method=="Symbol") { RespondString(command_id, true, obj.Symbol()); return; }
   if(method=="Comment") { RespondString(command_id, true, obj.Comment()); return; }
   if(method=="Volume") { RespondDouble(command_id, true, (double)(obj.Volume())); return; }
   if(method=="Price") { RespondDouble(command_id, true, (double)(obj.Price())); return; }
   if(method=="Commision") { RespondDouble(command_id, true, (double)(obj.Commission())); return; }
   if(method=="Swap") { RespondDouble(command_id, true, (double)(obj.Swap())); return; }
   if(method=="Profit") { RespondDouble(command_id, true, (double)(obj.Profit())); return; }
   if(method=="InfoInteger") { long v=0; bool ok=obj.InfoInteger((ENUM_DEAL_PROPERTY_INTEGER)ParseEnumCode(args,0),v); RespondRaw(command_id,true,PropertyLongJson(ok,v,ok?"":"InfoInteger failed")); return; }
   if(method=="InfoDouble") { double v=0; bool ok=obj.InfoDouble((ENUM_DEAL_PROPERTY_DOUBLE)ParseEnumCode(args,0),v); RespondRaw(command_id,true,PropertyDoubleJson(ok,v,ok?"":"InfoDouble failed")); return; }
   if(method=="InfoString") { string v=""; bool ok=obj.InfoString((ENUM_DEAL_PROPERTY_STRING)ParseEnumCode(args,0),v); RespondRaw(command_id,true,PropertyStringJson(ok,v,ok?"":"InfoString failed")); return; }
   if(method=="Ticket")
     {
      if(ArraySize(args)==0) RespondULong(command_id,true,obj.Ticket());
      else
        {
         ulong ticket=ArgULong(args,0);
         bool selected=HistoryDealSelect(ticket);
         obj.Ticket(selected ? ticket : 0);
         RespondBool(command_id,true,selected);
        }
      return;
     }
   if(method=="SelectByIndex")
     {
      bool selected=HistorySelect(0,TimeCurrent());
      if(selected) selected=obj.SelectByIndex((int)ArgLong(args,0));
      RespondBool(command_id,true,selected);
      return;
     }
   if(method=="HistoryDealsTotal")
     {
      HistorySelect(0,TimeCurrent());
      RespondLong(command_id,true,(long)HistoryDealsTotal());
      return;
     }
   if(method=="HistoryDealsGet")
     {
      HistorySelect(0,TimeCurrent());
      string filter_sym=""; string filter_grp=""; ulong filter_tkt=0; ulong filter_pos=0;
      if(ArraySize(args)>0 && args[0]!="null" && StringLen(args[0])>0)
        {
         if(StringFind(args[0],"{")>=0)
           {
            JsonGetString(args[0],"symbol",filter_sym);
            JsonGetString(args[0],"group",filter_grp);
            filter_tkt=JsonGetULong(args[0],"ticket",0);
            filter_pos=JsonGetULong(args[0],"position",0);
           }
         else
           {
            filter_sym=ArgString(args,0);
            if(ArraySize(args)>1) filter_grp=ArgString(args,1);
            if(ArraySize(args)>2) filter_tkt=ArgULong(args,2);
            if(ArraySize(args)>3) filter_pos=ArgULong(args,3);
           }
        }
      string out="[";
      int count=HistoryDealsTotal();
      bool first=true;
      for(int i=0;i<count;i++)
        {
         ulong ticket=HistoryDealGetTicket(i);
         if(ticket==0) continue;
         string sym=HistoryDealGetString(ticket,DEAL_SYMBOL);
         ulong pos=HistoryDealGetInteger(ticket,DEAL_POSITION_ID);
         if(filter_tkt!=0 && ticket!=filter_tkt) continue;
         if(filter_pos!=0 && pos!=filter_pos) continue;
         if(StringLen(filter_sym)>0 && sym!=filter_sym) continue;
         if(StringLen(filter_grp)>0 && !MatchSymbolGroup(sym,filter_grp)) continue;
         if(!first) out+=",";
         first=false;
         out+="{\"ticket\":"+JsonULong(ticket)+
              ",\"order\":"+JsonULong(HistoryDealGetInteger(ticket,DEAL_ORDER))+
              ",\"position_id\":"+JsonULong(pos)+
              ",\"symbol\":"+JsonQuote(sym)+
              ",\"deal_type\":"+JsonLong(HistoryDealGetInteger(ticket,DEAL_TYPE))+
              ",\"entry\":"+JsonLong(HistoryDealGetInteger(ticket,DEAL_ENTRY))+
              ",\"volume\":"+JsonDouble(HistoryDealGetDouble(ticket,DEAL_VOLUME))+
              ",\"price\":"+JsonDouble(HistoryDealGetDouble(ticket,DEAL_PRICE))+
              ",\"commission\":"+JsonDouble(HistoryDealGetDouble(ticket,DEAL_COMMISSION))+
              ",\"swap\":"+JsonDouble(HistoryDealGetDouble(ticket,DEAL_SWAP))+
              ",\"profit\":"+JsonDouble(HistoryDealGetDouble(ticket,DEAL_PROFIT))+
              ",\"magic\":"+JsonULong(HistoryDealGetInteger(ticket,DEAL_MAGIC))+
              ",\"comment\":"+JsonQuote(HistoryDealGetString(ticket,DEAL_COMMENT))+
              ",\"time\":"+JsonLong(HistoryDealGetInteger(ticket,DEAL_TIME))+
              "}";
        }
      out+="]";
      RespondRaw(command_id,true,out);
      return;
     }
   RespondError(command_id,"METHOD_NOT_IMPLEMENTED","unknown CDealInfo method: "+method);
  }

void DispatchTerminal(const string command_id,const string object_id,const string method,string &args[])
  {
   CTerminalInfo *p=GetTerminal(object_id); if(CheckPointer(p)==POINTER_INVALID) { RespondError(command_id,"OBJECT_CREATE_FAILED","CTerminalInfo allocation failed"); return; }
   CTerminalInfo *obj=p;
   if(method=="TerminalInfo") { RespondRaw(command_id, true, TerminalInfoJson(obj)); return; }
   RespondError(command_id,"METHOD_NOT_IMPLEMENTED","unknown CTerminalInfo method: "+method);
  }

//------------------------ read-only market data -----------------------------
ENUM_TIMEFRAMES MarketTimeframe(const string name)
  {
   ENUM_TIMEFRAMES frames[]={PERIOD_M1,PERIOD_M2,PERIOD_M3,PERIOD_M4,PERIOD_M5,
      PERIOD_M6,PERIOD_M10,PERIOD_M12,PERIOD_M15,PERIOD_M20,PERIOD_M30,PERIOD_H1,
      PERIOD_H2,PERIOD_H3,PERIOD_H4,PERIOD_H6,PERIOD_H8,PERIOD_H12,PERIOD_D1,
      PERIOD_W1,PERIOD_MN1};
   for(int i=0;i<ArraySize(frames);i++)
      if(EnumToString(frames[i])=="PERIOD_"+name) return frames[i];
   return PERIOD_CURRENT;
  }

void DispatchMarketData(const string id,const string method,string &args[])
  {
   bool bars=(method=="Bars");
   if((!bars && method!="Ticks") || ArraySize(args)!=(bars ? 7 : 6))
     { RespondError(id,"BAD_REQUEST","invalid history operation"); return; }
   string symbol=ArgString(args,0),mode=ArgString(args,bars ? 2 : 1);
   long start=ArgLong(args,bars ? 3 : 2),end=ArgLong(args,bars ? 4 : 3);
   long requested=ArgLong(args,bars ? 5 : 4),capacity=ArgLong(args,bars ? 6 : 5);
   bool range=(mode=="range"),by_date=(mode=="date_count");
   bool indexed=(bars && mode=="position"),latest=(!bars && mode=="latest");
   if(symbol=="" || (!range && !by_date && !indexed && !latest) ||
      start<0 || capacity<1 || capacity>1000 ||
      (range && (end<start || requested!=0)) ||
      (!range && (requested<1 || requested>capacity)) ||
      (!bars && !latest && start==0) ||
      (latest && start!=0) || (indexed && start>2147483647))
     { RespondError(id,"BAD_REQUEST","invalid history route or bounds"); return; }
   int limit=(int)capacity,requested_count=(int)requested;
   ENUM_TIMEFRAMES timeframe=PERIOD_CURRENT;
   if(bars)
     {
      timeframe=MarketTimeframe(ArgString(args,1));
      if(timeframe==PERIOD_CURRENT)
        { RespondError(id,"UNSUPPORTED_TIMEFRAME","explicit timeframe required"); return; }
      int period=(timeframe==PERIOD_MN1 ? 2419200 : PeriodSeconds(timeframe));
      if(range && MathCeil((double)(end-start)/period)+1>limit)
        { RespondError(id,"DATA_LIMIT_EXCEEDED","narrow the bar date range"); return; }
     }
   if(!SymbolSelect(symbol,true))
     { RespondError(id,"DATA_NOT_READY","symbol history is unavailable"); return; }
   string payload="[";
   int count=0;
   ResetLastError();
   if(bars)
     {
      MqlRates rates[];
      int copied=0;
      if(range) copied=CopyRates(symbol,timeframe,(datetime)start,(datetime)end,rates);
      else if(indexed) copied=CopyRates(symbol,timeframe,(int)start,requested_count,rates);
      else
        {
         int oldest=iBarShift(symbol,timeframe,(datetime)start,false);
         if(oldest<0)
           { RespondError(id,"DATA_NOT_READY","bar date could not be located"); return; }
         if(iTime(symbol,timeframe,oldest)<(datetime)start) oldest--;
         if(oldest>=0)
           {
            int available=(int)MathMin(requested_count,oldest+1);
            int first=oldest-available+1;
            copied=CopyRates(symbol,timeframe,first,available,rates);
           }
        }
      if(copied<0 || GetLastError()!=0 || !SeriesInfoInteger(symbol,timeframe,SERIES_SYNCHRONIZED))
        { RespondError(id,"DATA_NOT_READY","bar history copy failed or is incomplete"); return; }
      if(copied>(range ? limit : requested_count))
        { RespondError(id,"DATA_LIMIT_EXCEEDED","narrow the bar date range"); return; }
      for(int i=0;i<copied;i++)
        {
         if(count>0) payload+=",";
         payload+="{\"time\":"+JsonLong((long)rates[i].time)+
            ",\"open\":"+JsonDouble(rates[i].open)+",\"high\":"+JsonDouble(rates[i].high)+
            ",\"low\":"+JsonDouble(rates[i].low)+",\"close\":"+JsonDouble(rates[i].close)+
            ",\"tick_volume\":"+JsonLong(rates[i].tick_volume)+
            ",\"spread\":"+JsonLong(rates[i].spread)+
            ",\"real_volume\":"+JsonLong(rates[i].real_volume)+"}";
         count++;
        }
     }
   else
     {
      MqlTick ticks[];
      int copied=CopyTicks(symbol,ticks,COPY_TICKS_ALL,(ulong)start,
         (uint)(range ? limit+1 : requested_count));
      if(copied<0 || GetLastError()!=0)
        { RespondError(id,"DATA_NOT_READY","tick history copy failed or is incomplete"); return; }
      for(int i=0;i<copied;i++)
        {
         if(range && (ticks[i].time_msc<start || ticks[i].time_msc>end)) continue;
         if(count>=(range ? limit : requested_count))
           { RespondError(id,"DATA_LIMIT_EXCEEDED","narrow the tick date range"); return; }
         if(count>0) payload+=",";
         payload+="{\"time_msc\":"+JsonLong(ticks[i].time_msc)+
            ",\"bid\":"+JsonDouble(ticks[i].bid)+",\"ask\":"+JsonDouble(ticks[i].ask)+
            ",\"last\":"+JsonDouble(ticks[i].last)+",\"volume\":"+JsonULong(ticks[i].volume)+
            ",\"flags\":"+JsonLong((long)ticks[i].flags)+
            ",\"volume_real\":"+JsonDouble(ticks[i].volume_real)+"}";
         count++;
        }
     }
   payload+="]";
   if(StringLen(payload)>900000)
     { RespondError(id,"DATA_LIMIT_EXCEEDED","history frame is too large"); return; }
   RespondRaw(id,true,payload);
  }

//------------------------------ call parser ----------------------------------
void ProcessCall(const string frame)
  {
   string command_id="",object_id="",class_name="",method="",args_raw="[]";
   if(!JsonGetString(frame,"command_id",command_id) ||
      !JsonGetString(frame,"object_id",object_id) ||
      !JsonGetString(frame,"class",class_name) ||
      !JsonGetString(frame,"method",method))
     {
      RespondError(command_id,"BAD_REQUEST","missing call fields"); return;
     }
   JsonExtractRaw(frame,"args",args_raw);
   string args[]; JsonArrayTokens(args_raw,args);

   if(class_name=="MarketData") DispatchMarketData(command_id,method,args);
   else if(class_name=="Trade") DispatchTrade(command_id,object_id,method,args);
   else if(class_name=="AccountInfo") DispatchAccount(command_id,object_id,method,args);
   else if(class_name=="SymbolInfo") DispatchSymbol(command_id,object_id,method,args);
   else if(class_name=="OrderInfo") DispatchOrder(command_id,object_id,method,args);
   else if(class_name=="HistoryOrderInfo") DispatchHistory(command_id,object_id,method,args);
   else if(class_name=="PositionInfo") DispatchPosition(command_id,object_id,method,args);
   else if(class_name=="DealInfo") DispatchDeal(command_id,object_id,method,args);
   else if(class_name=="TerminalInfo") DispatchTerminal(command_id,object_id,method,args);
   else RespondError(command_id,"UNKNOWN_CLASS","unknown native class: "+class_name);
  }

void ProcessFrame(const string frame)
  {
   string kind="";
   if(!JsonGetString(frame,"kind",kind)) return;
   if(kind=="hello_ack") { g_authenticated=true; return; }
   if(kind=="call") { ProcessCall(frame); return; }
  }

void PumpSocket()
  {
   if(g_socket==INVALID_HANDLE || !SocketIsConnected(g_socket)) return;
   uint available=SocketIsReadable(g_socket);
   while(available>0)
     {
      uchar bytes[];
      int got=SocketRead(g_socket,bytes,(uint)MathMin(available,65536),10);
      if(got<=0) break;
      string chunk=CharArrayToString(bytes,0,got,CP_UTF8);
      g_rx+=chunk;
      int nl=StringFind(g_rx,"\n");
      while(nl>=0)
        {
         string frame=StringSubstr(g_rx,0,nl);
         g_rx=StringSubstr(g_rx,nl+1);
         if(StringLen(frame)>0) ProcessFrame(frame);
         nl=StringFind(g_rx,"\n");
        }
      available=SocketIsReadable(g_socket);
     }
  }

void DisconnectBridge()
  {
   g_authenticated=false;
   g_rx="";
   if(g_socket!=INVALID_HANDLE) { SocketClose(g_socket); g_socket=INVALID_HANDLE; }
  }

bool ConnectBridge()
  {
   DisconnectBridge();
   g_socket=SocketCreate();
   if(g_socket==INVALID_HANDLE)
     {
      const int error=GetLastError();
      if(InpVerboseReconnectLogs || error!=g_last_connect_error)
         Print("PythonBridge: SocketCreate failed: ",error);
      g_last_connect_error=error;
      return false;
     }
   SocketTimeouts(g_socket,InpConnectTimeoutMs,InpConnectTimeoutMs);
   if(!SocketConnect(g_socket,InpBridgeHost,InpBridgePort,InpConnectTimeoutMs))
     {
      const int error=GetLastError();
      if(InpVerboseReconnectLogs || error!=g_last_connect_error)
         Print("PythonBridge: SocketConnect failed: ",error);
      g_last_connect_error=error;
      DisconnectBridge(); return false;
     }
   string hello="{\"v\":\"@i64:1\",\"kind\":\"hello\",\"token\":"+JsonQuote(InpAuthToken)+
                ",\"terminal\":{\"login\":"+JsonULong((ulong)AccountInfoInteger(ACCOUNT_LOGIN))+
                ",\"server\":"+JsonQuote(AccountInfoString(ACCOUNT_SERVER))+
                ",\"build\":"+JsonLong((long)TerminalInfoInteger(TERMINAL_BUILD))+"}}";
   if(!SendJson(hello)) { DisconnectBridge(); return false; }
   g_last_connect_error=-1;
   Print("PythonBridge: connected to ",InpBridgeHost,":",InpBridgePort);
   return true;
  }

//----------------------------- terminal lock ---------------------------------
bool AcquireTerminalLock()
  {
   g_lock_name="PythonTradeBridge.Lock."+IntegerToString((long)AccountInfoInteger(ACCOUNT_LOGIN))+"."+AccountInfoString(ACCOUNT_SERVER);
   if(InpForceLockRecovery && GlobalVariableCheck(g_lock_name)) GlobalVariableDel(g_lock_name);
   if(!GlobalVariableCheck(g_lock_name)) GlobalVariableSet(g_lock_name,0.0);

   // Keep the owner value below 2^53 so the terminal global double retains it exactly.
   long chart_component=(long)(ChartID()%1000000);
   long time_component=(long)(TimeLocal()%1000000000);
   g_lock_owner=(double)(time_component*1000000+chart_component);
   if(g_lock_owner==0.0) g_lock_owner=1.0;

   g_lock_owned=GlobalVariableSetOnCondition(g_lock_name,g_lock_owner,0.0);
   return g_lock_owned;
  }

void ReleaseTerminalLock()
  {
   if(!g_lock_owned) return;
   if(StringLen(g_lock_name)>0 && GlobalVariableCheck(g_lock_name))
     {
      double current=GlobalVariableGet(g_lock_name);
      if(current==g_lock_owner) GlobalVariableDel(g_lock_name);
     }
   g_lock_owned=false;
  }

void FreeObjects()
  {
   for(int i=0;i<ArraySize(g_trade_objs);i++) if(CheckPointer(g_trade_objs[i])==POINTER_DYNAMIC) delete g_trade_objs[i];
   for(int i=0;i<ArraySize(g_account_objs);i++) if(CheckPointer(g_account_objs[i])==POINTER_DYNAMIC) delete g_account_objs[i];
   for(int i=0;i<ArraySize(g_symbol_objs);i++) if(CheckPointer(g_symbol_objs[i])==POINTER_DYNAMIC) delete g_symbol_objs[i];
   for(int i=0;i<ArraySize(g_order_objs);i++) if(CheckPointer(g_order_objs[i])==POINTER_DYNAMIC) delete g_order_objs[i];
   for(int i=0;i<ArraySize(g_history_objs);i++) if(CheckPointer(g_history_objs[i])==POINTER_DYNAMIC) delete g_history_objs[i];
   for(int i=0;i<ArraySize(g_position_objs);i++) if(CheckPointer(g_position_objs[i])==POINTER_DYNAMIC) delete g_position_objs[i];
   for(int i=0;i<ArraySize(g_deal_objs);i++) if(CheckPointer(g_deal_objs[i])==POINTER_DYNAMIC) delete g_deal_objs[i];
   for(int i=0;i<ArraySize(g_terminal_objs);i++) if(CheckPointer(g_terminal_objs[i])==POINTER_DYNAMIC) delete g_terminal_objs[i];
  }

//----------------------------- event handlers --------------------------------
int OnInit()
  {
   if(StringLen(InpAuthToken)<16)
     {
      Print("PythonBridge: InpAuthToken must contain at least 16 characters.");
      return INIT_PARAMETERS_INCORRECT;
     }
   if(!AcquireTerminalLock())
     {
      Print("PythonBridge: another bridge EA owns the terminal-local lock.");
      return INIT_FAILED;
     }
   EventSetMillisecondTimer((int)MathMax(10,InpPollMs));
   ConnectBridge();
   return INIT_SUCCEEDED;
  }

void OnDeinit(const int reason)
  {
   EventKillTimer();
   DisconnectBridge();
   FreeObjects();
   ReleaseTerminalLock();
  }

void OnTimer()
  {
   if(g_socket==INVALID_HANDLE || !SocketIsConnected(g_socket))
     {
      ulong now=GetTickCount64();
      if(now-g_last_connect_try>=InpReconnectMs)
        {
         g_last_connect_try=now;
         ConnectBridge();
        }
      return;
     }
   PumpSocket();
  }

void OnTradeTransaction(const MqlTradeTransaction &trans,
                        const MqlTradeRequest &request,
                        const MqlTradeResult &result)
  {
   if(g_socket==INVALID_HANDLE || !SocketIsConnected(g_socket) || !g_authenticated) return;
   string cmd=CommandForRequest(result.request_id);
   string payload="{"
      "\"transaction_type\":"+JsonLong((long)trans.type)+
      ",\"deal\":"+JsonULong(trans.deal)+
      ",\"order\":"+JsonULong(trans.order)+
      ",\"symbol\":"+JsonQuote(trans.symbol)+
      ",\"type\":"+JsonLong((long)trans.type)+
      ",\"order_type\":"+JsonLong((long)trans.order_type)+
      ",\"order_state\":"+JsonLong((long)trans.order_state)+
      ",\"deal_type\":"+JsonLong((long)trans.deal_type)+
      ",\"price\":"+JsonDouble(trans.price)+
      ",\"volume\":"+JsonDouble(trans.volume)+
      ",\"price_trigger\":"+JsonDouble(trans.price_trigger)+
      ",\"price_sl\":"+JsonDouble(trans.price_sl)+
      ",\"price_tp\":"+JsonDouble(trans.price_tp)+
      ",\"position\":"+JsonULong(trans.position)+
      ",\"position_by\":"+JsonULong(trans.position_by)+
      ",\"request\":"+RequestJson(request)+
      ",\"result\":"+ResultJson(result)+
      "}";
   string msg="{\"v\":\"@i64:1\",\"kind\":\"event\",\"event_type\":\"trade_transaction\",\"command_id\":"+
              (StringLen(cmd)>0 ? JsonQuote(cmd) : "null")+
              ",\"request_id\":"+JsonULong(result.request_id)+
              ",\"payload\":"+payload+"}";
   SendJson(msg);
  }
