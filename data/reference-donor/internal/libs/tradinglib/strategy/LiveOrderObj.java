/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.InstrumentInfo
 *  com.strategyquant.datalib.TickEvent
 *  com.strategyquant.datalib.TradingException
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.SQUtils
 *  it.unimi.dsi.fastutil.objects.ObjectArrayList
 */
package com.strategyquant.tradinglib.strategy;

import com.strategyquant.datalib.InstrumentInfo;
import com.strategyquant.datalib.TickEvent;
import com.strategyquant.datalib.TradingException;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.tradinglib.IActionEventListener;
import com.strategyquant.tradinglib.ILiveOrder;
import com.strategyquant.tradinglib.OrderCloseTypes;
import com.strategyquant.tradinglib.OrderTypes;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.Trader;
import com.strategyquant.tradinglib.event.ITradingEventListener;
import it.unimi.dsi.fastutil.objects.ObjectArrayList;

public class LiveOrderObj
implements ILiveOrder {
    private Trader trader;
    private byte orderType;
    private byte originalOrderType;
    private byte workingStatus;
    private byte orderStatus;
    private byte closeType;
    private String symbol;
    private int symbolHash;
    private String strategyName;
    public String setupName;
    private double size;
    private double openPrice = -1.0;
    private double originalOpenPrice;
    private byte slType;
    private double sl = -9.9999999E7;
    public double modifiedSL = -9.9999999E7;
    private byte modifiedSLType = (byte)-1;
    private double initialSL = -9.9999999E7;
    private double pt = -9.9999999E7;
    public double modifiedPT = -9.9999999E7;
    private String comment;
    private double maxSlippage;
    private int barsInTrade;
    private long openTime;
    private long originalOpenTime;
    private int orderId;
    private double closePrice;
    private byte lastAction;
    private long closeTime;
    private byte nextAction;
    private int errorCode;
    private String errorMessage;
    private int magicNumber = 0;
    private long expirationDate;
    private InstrumentInfo instrumentInfo;
    private double pl;
    private double plInPips;
    private double ask;
    private double bid;
    private double lastPLPrice = -1.0;
    private double lastPLCommSwap = 0.0;
    private double commSwap = 0.0;
    private float pipsMAE = 0.0f;
    private float pipsMFE = 0.0f;
    private boolean ambiguous = false;
    boolean filled = true;
    ObjectArrayList<IActionEventListener> barActionListeners = null;
    ObjectArrayList<IActionEventListener> tickActionListeners = null;
    ObjectArrayList<IActionEventListener> orderFilledListeners = null;
    private byte waitingBars = 0;
    private boolean isNettingMode = false;
    private double lastOpenPrice = 0.0;
    private float slippageInMoney = 0.0f;
    private byte exitIndex = (byte)-1;
    private float atrOnOpen = 0.0f;
    private int barsValid = 0;
    private byte eod = (byte)-1;
    private int exitAfterBars = 0;
    private int slptValidFrom = 0;
    private boolean onBarOpen = true;
    public double lastPrice = 0.0;

    public LiveOrderObj(Trader trader, InstrumentInfo instrumentInfo, byte by, String string) {
        this.init(trader, instrumentInfo, by, string);
    }

    public LiveOrderObj(Trader trader, InstrumentInfo instrumentInfo, byte by, String string, double d) {
        this.init(trader, instrumentInfo, by, string, d);
    }

    void init(Trader trader, InstrumentInfo instrumentInfo, byte by, String string) {
        this.closeType = 0;
        this.openPrice = -1.0;
        this.originalOpenPrice = 0.0;
        this.slType = 0;
        this.sl = -9.9999999E7;
        this.modifiedSL = -9.9999999E7;
        this.modifiedSLType = (byte)-1;
        this.initialSL = -9.9999999E7;
        this.pt = -9.9999999E7;
        this.modifiedPT = -9.9999999E7;
        this.comment = null;
        this.openTime = 0L;
        this.originalOpenTime = 0L;
        this.orderId = 0;
        this.closePrice = 0.0;
        this.lastAction = 0;
        this.closeTime = 0L;
        this.nextAction = 0;
        this.errorCode = 0;
        this.errorMessage = null;
        this.magicNumber = 0;
        this.expirationDate = 0L;
        this.pl = 0.0;
        this.ask = 0.0;
        this.bid = 0.0;
        this.lastPLPrice = -1.0;
        this.commSwap = 0.0;
        this.slippageInMoney = 0.0f;
        this.pipsMAE = 0.0f;
        this.pipsMFE = 0.0f;
        this.ambiguous = false;
        this.filled = true;
        this.setSymbol(string);
        this.strategyName = trader.getStrategyName();
        this.setupName = trader.getSetupName();
        if (this.setupName == null) {
            this.setupName = string;
        }
        this.nextAction = 1;
        this.errorCode = 0;
        this.trader = trader;
        this.orderType = by;
        this.originalOrderType = by;
        this.workingStatus = (byte)-10;
        this.orderStatus = 0;
        this.size = 0.0;
        this.barsInTrade = 0;
        this.maxSlippage = 0.0;
        this.expirationDate = 0L;
        this.instrumentInfo = instrumentInfo;
        if (this.barActionListeners != null) {
            this.barActionListeners.clear();
        }
        if (this.tickActionListeners != null) {
            this.tickActionListeners.clear();
        }
        if (this.orderFilledListeners != null) {
            this.orderFilledListeners.clear();
        }
        this.exitIndex = (byte)-1;
        this.atrOnOpen = 0.0f;
        this.barsValid = 0;
        this.eod = (byte)-1;
        this.exitAfterBars = 0;
        this.slptValidFrom = 0;
        this.onBarOpen = true;
    }

    void init(Trader trader, InstrumentInfo instrumentInfo, byte by, String string, double d) {
        this.init(trader, instrumentInfo, by, string);
        if (by == 1 || by == 2) {
            return;
        }
        this.openPrice = this.originalOpenPrice = this.fixPrice(d);
    }

    private void setSymbol(String string) {
        this.symbol = string;
        this.symbolHash = string.hashCode();
    }

    @Override
    public double getSL() {
        return this.sl;
    }

    @Override
    public double getInitialSL() {
        return this.initialSL;
    }

    public void setInitialSL(double d) {
        this.initialSL = d;
    }

    @Override
    public double getPL() {
        this.computePL();
        return this.pl;
    }

    @Override
    public double getPLInPips() {
        this.computePL();
        return this.plInPips;
    }

    public void computePL() {
        if (!OrderTypes.isMarketOrder(this.orderType)) {
            this.pl = 0.0;
            this.plInPips = 0.0;
            return;
        }
        double d = this.orderStatus == 3 ? this.closePrice : LiveOrderObj.getClosePriceByType(this.orderType, this.bid, this.ask);
        if (d != this.lastPLPrice || this.commSwap != this.lastPLCommSwap) {
            double d2 = 0.0;
            d2 = this.orderType == 1 ? d - this.openPrice : this.openPrice - d;
            this.pl = SQUtils.round((double)(d2 * this.size * this.instrumentInfo.pointValue), (int)2) + this.commSwap;
            this.plInPips = d2 / this.instrumentInfo.tickSize;
            this.lastPLPrice = d;
            this.lastPLCommSwap = this.commSwap;
        }
    }

    @Override
    public byte getSLType() {
        return this.slType;
    }

    @Override
    public LiveOrderObj setSL(double d) {
        return this.setSL((byte)2, d);
    }

    @Override
    public LiveOrderObj setSL(byte by, double d) {
        if (this.getWorkingStatus() == -10) {
            this.slType = by;
            this.sl = this.fixPrice(d);
            if (this.initialSL == -9.9999999E7) {
                this.initialSL = this.sl;
            }
            return this;
        }
        this.modifiedSLType = by;
        this.sl = this.modifiedSL = this.fixPrice(d);
        return this;
    }

    @Override
    public ILiveOrder setSLType(byte by) {
        this.slType = by;
        return this;
    }

    @Override
    public double getPT() {
        return this.pt;
    }

    @Override
    public LiveOrderObj setPT(double d) {
        return this.setPT((byte)3, d);
    }

    @Override
    public LiveOrderObj setPT(byte by, double d) {
        if (this.getWorkingStatus() == -10) {
            this.pt = this.fixPrice(d);
            return this;
        }
        this.pt = this.modifiedPT = this.fixPrice(d);
        return this;
    }

    @Override
    public String getComment() {
        return this.comment;
    }

    @Override
    public LiveOrderObj setComment(String string) {
        if (this.getWorkingStatus() == -10) {
            this.comment = string;
        }
        return this;
    }

    @Override
    public int getMagicNumber() {
        return this.magicNumber;
    }

    @Override
    public LiveOrderObj setMagicNumber(int n) {
        if (this.getWorkingStatus() == -10) {
            this.magicNumber = n;
        }
        return this;
    }

    @Override
    public double getMaxSlippage() {
        return this.maxSlippage;
    }

    @Override
    public LiveOrderObj setMaxSlippage(double d) {
        if (this.getWorkingStatus() == -10) {
            this.maxSlippage = d;
        }
        return this;
    }

    @Override
    public long getExpiration() {
        return this.expirationDate;
    }

    @Override
    public LiveOrderObj setExpiration(long l) {
        if (this.getWorkingStatus() == -10) {
            this.expirationDate = l;
        }
        return this;
    }

    @Override
    public int getSymbolHash() {
        return this.symbolHash;
    }

    @Override
    public String getSymbol() {
        return this.symbol;
    }

    @Override
    public byte getOrderType() {
        return this.orderType;
    }

    @Override
    public byte getCloseType() {
        return this.closeType;
    }

    @Override
    public byte getOriginalOrderType() {
        return this.originalOrderType;
    }

    public void setOriginalOrderType(byte by) {
        this.originalOrderType = by;
    }

    public void setOpenTime(long l) {
        this.openTime = l;
    }

    @Override
    public long getOpenTime() {
        return this.openTime;
    }

    public void setOriginalOpenTime(long l) {
        this.originalOpenTime = l;
    }

    @Override
    public long getOriginalOpenTime() {
        return this.originalOpenTime;
    }

    public void setOpenPrice(double d) {
        this.openPrice = d;
    }

    @Override
    public double getOpenPrice() {
        return this.openPrice;
    }

    public void setOriginalOpenPrice(double d) {
        this.originalOpenPrice = d;
    }

    @Override
    public double getOriginalOpenPrice() {
        return this.originalOpenPrice;
    }

    public void setOrderId(int n) {
        this.orderId = n;
    }

    @Override
    public int getOrderId() {
        return this.orderId;
    }

    @Override
    public int getBarsInTrade() {
        return this.barsInTrade;
    }

    public void increaseBarsInTrade() {
        ++this.barsInTrade;
    }

    public void resetBarsInTrade() {
        this.barsInTrade = 0;
    }

    public void setClosePrice(double d) {
        this.closePrice = d;
    }

    @Override
    public double getClosePrice() {
        return this.closePrice;
    }

    public void setWorkingStatus(byte by) {
        this.workingStatus = by;
    }

    public void setOrderStatus(byte by) {
        this.orderStatus = by;
    }

    @Override
    public boolean isSuccessful() {
        return this.errorCode == 0;
    }

    @Override
    public boolean isFilled() {
        return this.filled;
    }

    public void setLastAction(byte by) {
        this.lastAction = by;
    }

    public void setCloseTime(long l) {
        this.closeTime = l;
    }

    @Override
    public long getCloseTime() {
        return this.closeTime;
    }

    @Override
    public double getSize() {
        return this.size;
    }

    @Override
    public ILiveOrder Send() throws TradingException {
        if (!this.trader.IsMarketOpen()) {
            return this;
        }
        if (this.nextAction != 3 || this.isModified()) {
            ILiveOrder iLiveOrder = this.trader.send(this, this.nextAction, 0, null);
            this.nextAction = (byte)3;
            return iLiveOrder;
        }
        return this;
    }

    @Override
    public ILiveOrder SendAsync() throws TradingException {
        throw new TradingException("Not used");
    }

    @Override
    public ILiveOrder SendAsync(ITradingEventListener iTradingEventListener) throws TradingException {
        throw new TradingException("Not used");
    }

    @Override
    public boolean isModified() {
        if (this.modifiedPT != -9.9999999E7 && this.modifiedPT != this.pt) {
            return true;
        }
        if (this.modifiedSLType != -1 && this.modifiedSLType != this.slType) {
            return true;
        }
        return this.modifiedSL != -9.9999999E7 && this.modifiedSL != this.sl;
    }

    @Override
    public ILiveOrder ModifyAsync() throws TradingException {
        throw new TradingException("Not used");
    }

    @Override
    public ILiveOrder ModifyAsync(ITradingEventListener iTradingEventListener) throws TradingException {
        throw new TradingException("Not used");
    }

    @Override
    public ILiveOrder Close(byte by) throws TradingException {
        if (!this.trader.IsMarketOpen()) {
            return this;
        }
        return this.trader.send(this, (byte)2, by, 0, null);
    }

    @Override
    public ILiveOrder CloseAsync() throws TradingException {
        throw new TradingException("Not used");
    }

    @Override
    public ILiveOrder CloseAsync(ITradingEventListener iTradingEventListener) throws TradingException {
        throw new TradingException("Not used");
    }

    @Override
    public byte getWorkingStatus() {
        return this.workingStatus;
    }

    @Override
    public byte getPositionStatus() {
        return this.orderStatus;
    }

    public LiveOrderObj setError(int n, String string) {
        this.errorCode = n;
        this.errorMessage = string;
        return this;
    }

    @Override
    public int getErrorCode() {
        return this.errorCode;
    }

    @Override
    public String getErrorMessage() {
        return this.errorMessage;
    }

    @Override
    public String getStrategyName() {
        return this.strategyName;
    }

    @Override
    public String getSetupName() {
        return this.setupName;
    }

    @Override
    public ILiveOrder setSize(double d) {
        this.size = d;
        return this;
    }

    @Override
    public ILiveOrder computeSizeIfMissing() throws TradingException {
        if (this.getSize() <= 0.0) {
            this.size = 0.0;
        }
        return this;
    }

    @Override
    public void refuse(String string) {
        this.orderStatus = (byte)10;
        this.errorMessage = string;
    }

    @Override
    public boolean isRefused() {
        return this.orderStatus == 10;
    }

    @Override
    public int getDirection() {
        return OrderTypes.isLongOrder(this.orderType) ? 1 : -1;
    }

    public void setCloseType(byte by) {
        this.closeType = by;
    }

    private double fixPrice(double d) {
        if (d == -9.9999999E7) {
            return d;
        }
        return SQUtils.fixPrice((double)this.instrumentInfo.tickStep, (double)d, (int)this.instrumentInfo.decimals);
    }

    public void setSLFromModified() {
        if (this.modifiedSL != -9.9999999E7) {
            this.sl = this.modifiedSL;
            if (this.initialSL == -9.9999999E7) {
                this.initialSL = this.sl;
            }
            this.modifiedSL = -9.9999999E7;
        }
        if (this.modifiedSLType != -1) {
            this.slType = this.modifiedSLType;
            this.modifiedSLType = (byte)-1;
        }
    }

    public void setPTFromModified() {
        if (this.modifiedPT != -9.9999999E7) {
            this.pt = this.modifiedPT;
            this.modifiedPT = -9.9999999E7;
        }
    }

    public void fillOrder(TickEvent tickEvent) {
        this.openTime = tickEvent.getTime();
        this.orderType = this.orderType == 3 || this.orderType == 5 || this.orderType == 7 ? 1 : 2;
        this.orderStatus = 1;
        this.barsInTrade = 0;
    }

    public static double getPriceByType(int n, double d, double d2) {
        if (n == 1 || n == 5 || n == 3 || n == 7) {
            return d2;
        }
        return d;
    }

    public static double getClosePriceByType(int n, double d, double d2) {
        if (n == 1 || n == 5 || n == 3 || n == 7) {
            return d;
        }
        return d2;
    }

    public double getPriceByType(int n, double d, double d2, double d3) {
        double d4 = LiveOrderObj.getPriceByType(n, d, d2);
        if (n == 1) {
            d4 += d3 * this.instrumentInfo.tickSize;
            d4 = SQUtils.fixPrice((double)this.instrumentInfo.tickStep, (double)d4, (int)this.instrumentInfo.decimals);
        } else if (n == 2) {
            d4 -= d3 * this.instrumentInfo.tickSize;
            d4 = SQUtils.fixPrice((double)this.instrumentInfo.tickStep, (double)d4, (int)this.instrumentInfo.decimals);
        }
        return d4;
    }

    @Override
    public boolean isPendingOrder() {
        return this.orderType == 3 || this.orderType == 4 || this.orderType == 5 || this.orderType == 6;
    }

    @Override
    public boolean isMarketOrder() {
        return this.orderType == 1 || this.orderType == 2;
    }

    public boolean isExitOrder() {
        return this.orderType == 100 || this.orderType == 101 || this.orderType == 102 || this.orderType == 103;
    }

    @Override
    public boolean isClosedOrder() {
        return this.orderStatus != 1 && this.orderStatus != 2;
    }

    @Override
    public InstrumentInfo getInstrumentInfo() {
        return this.instrumentInfo;
    }

    public void setTickData(double d, double d2) {
        this.ask = d;
        this.bid = d2;
    }

    public double getBid() {
        return this.bid;
    }

    public double getAsk() {
        return this.ask;
    }

    public double getClosePriceWithSlippage(double d, double d2, byte by) {
        if (d == 0.0) {
            return d2;
        }
        byte by2 = this.getOrderTypeFromSLPT(by == 2 ? -1 : 1);
        if (by2 == 6) {
            return SQUtils.fixPrice((double)this.instrumentInfo.tickStep, (double)(d2 -= d * this.instrumentInfo.tickSize), (int)this.instrumentInfo.decimals);
        }
        if (by2 == 5) {
            return SQUtils.fixPrice((double)this.instrumentInfo.tickStep, (double)(d2 += d * this.instrumentInfo.tickSize), (int)this.instrumentInfo.decimals);
        }
        return d2;
    }

    public byte getOrderTypeFromSLPT(int n) {
        if (n == -1) {
            return this.getDirection() == 1 ? (byte)6 : 5;
        }
        return this.getDirection() == 1 ? (byte)4 : 3;
    }

    @Override
    public boolean isLong() {
        return this.orderType == 1 || this.orderType == 3 || this.orderType == 5 || this.orderType == 7;
    }

    public void setCommSwap(double d) {
        this.commSwap = d;
    }

    @Override
    public double getCommSwap() {
        return this.commSwap;
    }

    public void setMAE(float f) {
        this.pipsMAE = f;
    }

    public void setMFE(float f) {
        this.pipsMFE = f;
    }

    @Override
    public float getMAE() {
        return this.pipsMAE;
    }

    @Override
    public float getMFE() {
        return this.pipsMFE;
    }

    public Trader getTrader() {
        return this.trader;
    }

    public void setOrderType(byte by) {
        this.orderType = by;
    }

    public void transformMAE_MFE() {
        this.pipsMAE = (float)((double)this.pipsMAE / this.instrumentInfo.tickSize);
        this.pipsMFE = (float)((double)this.pipsMFE / this.instrumentInfo.tickSize);
    }

    public boolean isAmbiguous() {
        return this.ambiguous;
    }

    public void setAmbiguous() {
        this.ambiguous = true;
    }

    public void setFilled(boolean bl) {
        this.filled = bl;
    }

    public String toString() {
        StringBuilder stringBuilder = new StringBuilder();
        stringBuilder.append(SQTime.toDateMinuteString((long)this.originalOpenTime));
        stringBuilder.append("/");
        stringBuilder.append(SQTime.toDateMinuteString((long)this.openTime));
        stringBuilder.append(" : ");
        stringBuilder.append(OrderTypes.toString(this.orderType));
        stringBuilder.append(" : ");
        stringBuilder.append(this.openPrice);
        stringBuilder.append(" - ");
        stringBuilder.append(SQTime.toDateMinuteString((long)this.closeTime));
        if (this.closeType > 0) {
            stringBuilder.append(" : ");
            stringBuilder.append(OrderCloseTypes.toString(this.closeType));
            stringBuilder.append(" : ");
            stringBuilder.append(this.closePrice);
            stringBuilder.append(", bars=");
            stringBuilder.append(this.barsInTrade);
        }
        return stringBuilder.toString();
    }

    @Override
    public void registerEvent(int n, IActionEventListener iActionEventListener) throws TradingException {
        if (n == 2) {
            if (this.barActionListeners == null) {
                this.barActionListeners = new ObjectArrayList();
            }
            if (this.barActionListeners.size() > 10) {
                throw new TradingException("Too many bar action listeners!");
            }
            this.barActionListeners.add((Object)iActionEventListener);
        } else if (n == 4) {
            if (this.tickActionListeners == null) {
                this.tickActionListeners = new ObjectArrayList();
            }
            if (this.tickActionListeners.size() > 10) {
                throw new TradingException("Too many tick action listeners!");
            }
            this.tickActionListeners.add((Object)iActionEventListener);
        } else if (n == 7) {
            if (this.orderFilledListeners == null) {
                this.orderFilledListeners = new ObjectArrayList();
            }
            if (this.orderFilledListeners.size() > 10) {
                throw new TradingException("Too many order fill listeners!");
            }
            this.orderFilledListeners.add((Object)iActionEventListener);
        } else {
            throw new TradingException("Unknown updateEventType parameter. Only BarOpen and BarTick are supported!");
        }
    }

    public void evaluateActionListeners(int n, StrategyBase strategyBase) throws TradingException {
        block4: {
            block5: {
                block3: {
                    if (n != 2 && n != 3 || this.barActionListeners == null || this.barActionListeners.size() <= 0) break block3;
                    for (int i = 0; i < this.barActionListeners.size(); ++i) {
                        ((IActionEventListener)this.barActionListeners.get(i)).OnActionEvent(strategyBase);
                    }
                    break block4;
                }
                if (n != 4 || this.tickActionListeners == null || this.tickActionListeners.size() <= 0) break block5;
                for (int i = 0; i < this.tickActionListeners.size(); ++i) {
                    ((IActionEventListener)this.tickActionListeners.get(i)).OnActionEvent(strategyBase);
                }
                break block4;
            }
            if (n != 7 || this.orderFilledListeners == null || this.orderFilledListeners.size() <= 0) break block4;
            for (int i = 0; i < this.orderFilledListeners.size(); ++i) {
                ((IActionEventListener)this.orderFilledListeners.get(i)).OnActionEvent(strategyBase);
            }
        }
    }

    public void setWaitingBars(int n) {
        this.waitingBars = (byte)n;
    }

    public int getWaitingBars() {
        return this.waitingBars;
    }

    @Override
    public double getLastOpenPrice() {
        return this.lastOpenPrice;
    }

    public void setLastOpenPrice(double d) {
        this.lastOpenPrice = d;
    }

    @Override
    public boolean isNettingMode() {
        return this.isNettingMode;
    }

    public void setNettingMode(boolean bl) {
        this.isNettingMode = bl;
    }

    @Override
    public float getSlippageInMoney() {
        return this.slippageInMoney;
    }

    public void setSlippageInMoney(double d) {
        this.slippageInMoney = (float)d;
    }

    @Override
    public ILiveOrder setExitIndex(byte by) {
        this.exitIndex = by;
        return this;
    }

    @Override
    public byte getExitIndex() {
        return this.exitIndex;
    }

    @Override
    public boolean usesATM() {
        return this.exitIndex != -1;
    }

    public void setATROnOpen(double d) {
        this.atrOnOpen = (float)d;
    }

    @Override
    public float getATROnOpen() {
        return this.atrOnOpen;
    }

    @Override
    public boolean isMarketOpen() {
        if (this.trader == null) {
            return true;
        }
        return this.trader.IsMarketOpen();
    }

    public int getBarsValid() {
        return this.barsValid;
    }

    public void setBarsValid(int n) {
        this.barsValid = n;
    }

    public void setEOD(byte by) {
        this.eod = by;
    }

    public byte getEOD() {
        return this.eod;
    }

    public void setExitAfterBars(int n) {
        this.exitAfterBars = n;
    }

    public int getExitAfterBars() {
        return this.exitAfterBars;
    }

    public void setSLPTValidFrom(int n) {
        this.slptValidFrom = n;
    }

    public int getSLPTValidFrom() {
        return this.slptValidFrom;
    }
}

