/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.InstrumentInfo
 *  com.strategyquant.datalib.TradingException
 */
package com.strategyquant.tradinglib;

import com.strategyquant.datalib.InstrumentInfo;
import com.strategyquant.datalib.TradingException;
import com.strategyquant.tradinglib.IActionEventListener;
import com.strategyquant.tradinglib.event.ITradingEventListener;

public interface ILiveOrder {
    public double getSL();

    public byte getSLType();

    public ILiveOrder setSL(double var1);

    public ILiveOrder setSL(byte var1, double var2);

    public ILiveOrder setSLType(byte var1);

    public double getPT();

    public ILiveOrder setPT(double var1);

    public ILiveOrder setPT(byte var1, double var2);

    public String getComment();

    public ILiveOrder setComment(String var1);

    public int getMagicNumber();

    public ILiveOrder setMagicNumber(int var1);

    public double getMaxSlippage();

    public ILiveOrder setMaxSlippage(double var1);

    public long getExpiration();

    public ILiveOrder setExpiration(long var1);

    public int getSymbolHash();

    public String getSymbol();

    public byte getOrderType();

    public byte getCloseType();

    public byte getOriginalOrderType();

    public long getOpenTime();

    public double getOpenPrice();

    public int getOrderId();

    public double getClosePrice();

    public boolean isSuccessful();

    public int getBarsInTrade();

    public long getCloseTime();

    public double getSize();

    public ILiveOrder Send() throws TradingException;

    public ILiveOrder SendAsync() throws TradingException;

    public ILiveOrder SendAsync(ITradingEventListener var1) throws TradingException;

    public boolean isModified();

    public ILiveOrder ModifyAsync() throws TradingException;

    public ILiveOrder ModifyAsync(ITradingEventListener var1) throws TradingException;

    public ILiveOrder Close(byte var1) throws TradingException;

    public ILiveOrder CloseAsync() throws TradingException;

    public ILiveOrder CloseAsync(ITradingEventListener var1) throws TradingException;

    public byte getWorkingStatus();

    public byte getPositionStatus();

    public String getStrategyName();

    public String getSetupName();

    public ILiveOrder setSize(double var1);

    public ILiveOrder computeSizeIfMissing() throws TradingException;

    public void refuse(String var1);

    public boolean isRefused();

    public int getDirection();

    public double getOriginalOpenPrice();

    public long getOriginalOpenTime();

    public boolean isPendingOrder();

    public boolean isMarketOrder();

    public boolean isClosedOrder();

    public InstrumentInfo getInstrumentInfo();

    public int getErrorCode();

    public String getErrorMessage();

    public double getPL();

    public double getPLInPips();

    public boolean isLong();

    public double getCommSwap();

    public float getMAE();

    public float getMFE();

    public boolean isFilled();

    public boolean isNettingMode();

    public double getLastOpenPrice();

    public void registerEvent(int var1, IActionEventListener var2) throws TradingException;

    public float getSlippageInMoney();

    public double getInitialSL();

    public ILiveOrder setExitIndex(byte var1);

    public byte getExitIndex();

    public boolean usesATM();

    public float getATROnOpen();

    public boolean isMarketOpen();
}

