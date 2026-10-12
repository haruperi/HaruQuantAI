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

// Per-proxy native objects. Each Python proxy ID gets its own C* instance.
string g_trade_ids[];        CTrade *g_trade_objs[];
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
   int sent=SocketSend(g_socket,bytes,(uint)(count-1));
   return sent==(count-1);
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
CTrade* GetTrade(const string id)
  {
   for(int i=0;i<ArraySize(g_trade_ids);i++) if(g_trade_ids[i]==id) return g_trade_objs[i];
   int n=ArraySize(g_trade_ids); ArrayResize(g_trade_ids,n+1); ArrayResize(g_trade_objs,n+1);
   g_trade_ids[n]=id; g_trade_objs[n]=new CTrade; return g_trade_objs[n];
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
   CTrade *p=GetTrade(object_id);
   if(CheckPointer(p)==POINTER_INVALID) { RespondError(command_id,"OBJECT_CREATE_FAILED","CTrade allocation failed"); return; }
   CTrade *obj=p;

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
   if(method=="Login") { RespondULong(command_id, true, (ulong)(obj.Login())); return; }
   if(method=="TradeMode") { RespondLong(command_id, true, (long)(obj.TradeMode())); return; }
   if(method=="TradeModeDescription") { RespondString(command_id, true, obj.TradeModeDescription()); return; }
   if(method=="Leverage") { RespondULong(command_id, true, (ulong)(obj.Leverage())); return; }
   if(method=="StopoutMode") { RespondLong(command_id, true, (long)(obj.StopoutMode())); return; }
   if(method=="StopoutModeDescription") { RespondString(command_id, true, obj.StopoutModeDescription()); return; }
   if(method=="MarginMode") { RespondLong(command_id, true, (long)(obj.MarginMode())); return; }
   if(method=="MarginModeDescription") { RespondString(command_id, true, obj.MarginModeDescription()); return; }
   if(method=="TradeAllowed") { RespondBool(command_id, true, obj.TradeAllowed()); return; }
   if(method=="TradeExpert") { RespondBool(command_id, true, obj.TradeExpert()); return; }
   if(method=="LimitOrders") { RespondLong(command_id, true, (long)(obj.LimitOrders())); return; }
   if(method=="Balance") { RespondDouble(command_id, true, (double)(obj.Balance())); return; }
   if(method=="Credit") { RespondDouble(command_id, true, (double)(obj.Credit())); return; }
   if(method=="Profit") { RespondDouble(command_id, true, (double)(obj.Profit())); return; }
   if(method=="Equity") { RespondDouble(command_id, true, (double)(obj.Equity())); return; }
   if(method=="Margin") { RespondDouble(command_id, true, (double)(obj.Margin())); return; }
   if(method=="FreeMargin") { RespondDouble(command_id, true, (double)(obj.FreeMargin())); return; }
   if(method=="MarginLevel") { RespondDouble(command_id, true, (double)(obj.MarginLevel())); return; }
   if(method=="MarginCall") { RespondDouble(command_id, true, (double)(obj.MarginCall())); return; }
   if(method=="MarginStopOut") { RespondDouble(command_id, true, (double)(obj.MarginStopOut())); return; }
   if(method=="Name") { RespondString(command_id, true, obj.Name()); return; }
   if(method=="Server") { RespondString(command_id, true, obj.Server()); return; }
   if(method=="Currency") { RespondString(command_id, true, obj.Currency()); return; }
   if(method=="Company") { RespondString(command_id, true, obj.Company()); return; }
   if(method=="CurrencyDigits") { RespondLong(command_id, true, (long)AccountInfoInteger(ACCOUNT_CURRENCY_DIGITS)); return; }
   if(method=="FifoClose") { RespondBool(command_id, true, (bool)AccountInfoInteger(ACCOUNT_FIFO_CLOSE)); return; }
   if(method=="MarginInitial") { RespondDouble(command_id, true, AccountInfoDouble(ACCOUNT_MARGIN_INITIAL)); return; }
   if(method=="MarginMaintenance") { RespondDouble(command_id, true, AccountInfoDouble(ACCOUNT_MARGIN_MAINTENANCE)); return; }
   if(method=="Assets") { RespondDouble(command_id, true, AccountInfoDouble(ACCOUNT_ASSETS)); return; }
   if(method=="Liabilities") { RespondDouble(command_id, true, AccountInfoDouble(ACCOUNT_LIABILITIES)); return; }
   if(method=="CommissionBlocked") { RespondDouble(command_id, true, AccountInfoDouble(ACCOUNT_COMMISSION_BLOCKED)); return; }
   if(method=="InfoInteger") { RespondLong(command_id,true,obj.InfoInteger((ENUM_ACCOUNT_INFO_INTEGER)ParseEnumCode(args,0))); return; }
   if(method=="InfoDouble") { RespondDouble(command_id,true,obj.InfoDouble((ENUM_ACCOUNT_INFO_DOUBLE)ParseEnumCode(args,0))); return; }
   if(method=="InfoString") { RespondString(command_id,true,obj.InfoString((ENUM_ACCOUNT_INFO_STRING)ParseEnumCode(args,0))); return; }
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
   RespondError(command_id,"METHOD_NOT_IMPLEMENTED","unknown CDealInfo method: "+method);
  }

void DispatchTerminal(const string command_id,const string object_id,const string method,string &args[])
  {
   CTerminalInfo *p=GetTerminal(object_id); if(CheckPointer(p)==POINTER_INVALID) { RespondError(command_id,"OBJECT_CREATE_FAILED","CTerminalInfo allocation failed"); return; }
   CTerminalInfo *obj=p;
   if(method=="Build") { RespondLong(command_id, true, (long)(obj.Build())); return; }
   if(method=="IsConnected") { RespondBool(command_id, true, obj.IsConnected()); return; }
   if(method=="IsDLLsAllowed") { RespondBool(command_id, true, obj.IsDLLsAllowed()); return; }
   if(method=="IsTradeAllowed") { RespondBool(command_id, true, obj.IsTradeAllowed()); return; }
   if(method=="IsEmailEnabled") { RespondBool(command_id, true, obj.IsEmailEnabled()); return; }
   if(method=="IsFtpEnabled") { RespondBool(command_id, true, obj.IsFtpEnabled()); return; }
   if(method=="MaxBars") { RespondLong(command_id, true, (long)(obj.MaxBars())); return; }
   if(method=="CodePage") { RespondLong(command_id, true, (long)(obj.CodePage())); return; }
   if(method=="CPUCores") { RespondLong(command_id, true, (long)(obj.CPUCores())); return; }
   if(method=="MemoryPhysical") { RespondLong(command_id, true, (long)(obj.MemoryPhysical())); return; }
   if(method=="MemoryTotal") { RespondLong(command_id, true, (long)(obj.MemoryTotal())); return; }
   if(method=="MemoryAvailable") { RespondLong(command_id, true, (long)(obj.MemoryAvailable())); return; }
   if(method=="MemoryUsed") { RespondLong(command_id, true, (long)(obj.MemoryUsed())); return; }
   if(method=="IsX64") { RespondBool(command_id, true, obj.IsX64()); return; }
   if(method=="OpenCLSupport") { RespondLong(command_id, true, (long)(obj.OpenCLSupport())); return; }
   if(method=="DiskSpace") { RespondLong(command_id, true, (long)(obj.DiskSpace())); return; }
   if(method=="Language") { RespondString(command_id, true, obj.Language()); return; }
   if(method=="Name") { RespondString(command_id, true, obj.Name()); return; }
   if(method=="Company") { RespondString(command_id, true, obj.Company()); return; }
   if(method=="Path") { RespondString(command_id, true, obj.Path()); return; }
   if(method=="DataPath") { RespondString(command_id, true, obj.DataPath()); return; }
   if(method=="CommonDataPath") { RespondString(command_id, true, obj.CommonDataPath()); return; }
   if(method=="InfoInteger") { RespondLong(command_id,true,obj.InfoInteger((ENUM_TERMINAL_INFO_INTEGER)ParseEnumCode(args,0))); return; }
   if(method=="InfoString") { RespondString(command_id,true,obj.InfoString((ENUM_TERMINAL_INFO_STRING)ParseEnumCode(args,0))); return; }
   if(method=="CommunityAccount") { RespondBool(command_id, true, (bool)TerminalInfoInteger(TERMINAL_COMMUNITY_ACCOUNT)); return; }
   if(method=="CommunityConnection") { RespondBool(command_id, true, (bool)TerminalInfoInteger(TERMINAL_COMMUNITY_CONNECTION)); return; }
   if(method=="TradeAPIDisabled") { RespondBool(command_id, true, false); return; }
   if(method=="NotificationsEnabled") { RespondBool(command_id, true, (bool)TerminalInfoInteger(TERMINAL_NOTIFICATIONS_ENABLED)); return; }
   if(method=="MQID") { RespondBool(command_id, true, (bool)TerminalInfoInteger(TERMINAL_MQID)); return; }
   if(method=="PingLast") { RespondLong(command_id, true, (long)TerminalInfoInteger(TERMINAL_PING_LAST)); return; }
   if(method=="CommunityBalance") { RespondDouble(command_id, true, TerminalInfoDouble(TERMINAL_COMMUNITY_BALANCE)); return; }
   if(method=="Retransmission") { RespondDouble(command_id, true, TerminalInfoDouble(TERMINAL_RETRANSMISSION)); return; }
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
