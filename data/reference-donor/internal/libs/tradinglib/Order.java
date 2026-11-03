/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQTime
 */
package com.strategyquant.tradinglib;

import com.strategyquant.lib.SQTime;
import com.strategyquant.tradinglib.ILiveOrder;
import com.strategyquant.tradinglib.OrderCloseTypes;
import com.strategyquant.tradinglib.OrderTypes;
import java.io.Serializable;

public class Order
implements Serializable {
    public static final int NOT_DEFINED = -99999999;
    public String Symbol;
    public String SetupName;
    public String StrategyName;
    public String Comment;
    public int Ticket = 0;
    public int Order = 0;
    public byte Type;
    public byte CloseType = 0;
    public byte SampleType = (byte)127;
    public long OriginalOpenTime;
    public byte OriginalType;
    public int MagicNumber;
    public float Size;
    public float OriginalPrice;
    public long OpenTime;
    public float OpenPrice;
    public long CloseTime;
    public float ClosePrice;
    public float StopLoss = -1.0E8f;
    public float TakeProfit = -1.0E8f;
    public int Duration = 0;
    public short BarsInTrade = 0;
    public float PL = -1.0E8f;
    public float PctPL = 0.0f;
    public float PctPL_TWR = 0.0f;
    public float PipsPL = 0.0f;
    public float DD = 0.0f;
    public float PctDD = 0.0f;
    public float PipsDD = 0.0f;
    public float CommSwap = 0.0f;
    public boolean CommSwapApplied = false;
    public float MAE = 0.0f;
    public float PipsMAE = 0.0f;
    public float MFE = 0.0f;
    public float PipsMFE = 0.0f;
    public float AccountBalance = 0.0f;
    public float PctAccountBalance = 0.0f;
    public float PipsAccountBalance = 0.0f;
    public float AccountBalanceTemp = -1.0E8f;
    public float Extra1 = 0.0f;
    public byte IsInPortfolio = 1;
    public float worstDailyEquity = 0.0f;
    public float SlippageInMoney = 0.0f;
    public byte ExitIndex = (byte)-1;
    public float ATROnOpen;
    public long OrderId;

    public Order() {
    }

    public Order(ILiveOrder iLiveOrder) {
        this.setFromLiveOrder(iLiveOrder);
    }

    public Order(Order order) {
        this.setFromOrder(order);
    }

    public void setFromLiveOrder(ILiveOrder iLiveOrder) {
        this.Symbol = iLiveOrder.getSymbol();
        this.SetupName = iLiveOrder.getSetupName();
        this.StrategyName = iLiveOrder.getStrategyName();
        this.Comment = iLiveOrder.getComment();
        this.Ticket = iLiveOrder.getOrderId();
        this.Type = iLiveOrder.getOrderType();
        this.OriginalType = iLiveOrder.getOriginalOrderType();
        this.OpenPrice = (float)iLiveOrder.getOpenPrice();
        this.OriginalPrice = (float)iLiveOrder.getOriginalOpenPrice();
        this.Size = (float)iLiveOrder.getSize();
        this.ClosePrice = (float)iLiveOrder.getClosePrice();
        this.StopLoss = (float)iLiveOrder.getInitialSL();
        if (this.StopLoss == -1.0E8f) {
            this.StopLoss = 0.0f;
        }
        this.TakeProfit = (float)iLiveOrder.getPT();
        this.OpenTime = iLiveOrder.getOpenTime();
        this.OriginalOpenTime = iLiveOrder.getOriginalOpenTime();
        this.CloseTime = iLiveOrder.getCloseTime();
        this.CloseType = iLiveOrder.getCloseType();
        this.BarsInTrade = (short)(iLiveOrder.getBarsInTrade() > Short.MAX_VALUE ? Short.MAX_VALUE : iLiveOrder.getBarsInTrade());
        this.PipsMAE = iLiveOrder.getMAE();
        this.PipsMFE = iLiveOrder.getMFE();
        this.DD = 0.0f;
        this.PctDD = 0.0f;
        this.PipsDD = 0.0f;
        this.CommSwap = (float)iLiveOrder.getCommSwap();
        this.SlippageInMoney = iLiveOrder.getSlippageInMoney();
        this.MagicNumber = iLiveOrder.getMagicNumber();
        this.ExitIndex = iLiveOrder.getExitIndex();
        this.ATROnOpen = iLiveOrder.getATROnOpen();
    }

    public boolean isBalanceOrder() {
        return this.Type == 9 || this.Type == 10 || this.Type == 11;
    }

    public boolean isCanceledOrder() {
        return this.CloseType == 6 || this.CloseType == 8 || this.CloseType == 9 || this.CloseType == 4 && !this.isFilledOrder();
    }

    public boolean isPendingOrder() {
        return this.Type == 3 || this.Type == 5 || this.Type == 7 || this.Type == 4 || this.Type == 6 || this.Type == 8;
    }

    public float getPLByType(byte by) {
        switch (by) {
            case 30: {
                return this.PipsPL;
            }
            case 20: {
                return this.PctPL;
            }
        }
        return this.PL;
    }

    public float getDDByType(byte by) {
        switch (by) {
            case 30: {
                return this.PipsDD;
            }
            case 20: {
                return this.PctDD;
            }
        }
        return this.DD;
    }

    public long getTimeByPeriodType(byte by) {
        if (by == 1) {
            return this.OpenTime;
        }
        return this.CloseTime;
    }

    public boolean isLong() {
        return OrderTypes.isLongOrder(this.Type);
    }

    public boolean isShort() {
        return OrderTypes.isShortOrder(this.Type);
    }

    public String toString() {
        StringBuilder stringBuilder = new StringBuilder();
        stringBuilder.append(this.Order);
        stringBuilder.append(" - ");
        stringBuilder.append(this.Ticket);
        stringBuilder.append(" - ");
        stringBuilder.append(SQTime.toDateMinuteString((long)this.OriginalOpenTime));
        stringBuilder.append("/");
        stringBuilder.append(SQTime.toDateMinuteString((long)this.OpenTime));
        stringBuilder.append(" : ");
        stringBuilder.append(OrderTypes.toString(this.Type));
        stringBuilder.append(" : ");
        stringBuilder.append(this.OpenPrice);
        stringBuilder.append(" - ");
        stringBuilder.append(SQTime.toDateMinuteString((long)this.CloseTime));
        stringBuilder.append(" : ");
        stringBuilder.append(OrderCloseTypes.toString(this.CloseType));
        stringBuilder.append(" : ");
        stringBuilder.append(this.ClosePrice);
        stringBuilder.append(", PL: ");
        stringBuilder.append(this.PL);
        stringBuilder.append(", Symbol: ");
        stringBuilder.append(this.Symbol);
        stringBuilder.append(", Size: ");
        stringBuilder.append(this.Size);
        return stringBuilder.toString();
    }

    public boolean isRealOrder() {
        return this.CloseType != 18;
    }

    public boolean isFilledOrder() {
        return this.Type == 1 || this.Type == 2 || this.Type == 11 || this.Type == 9;
    }

    public void setFromOrder(Order order) {
        this.Symbol = order.Symbol;
        this.SetupName = order.SetupName;
        this.StrategyName = order.StrategyName;
        this.Comment = order.Comment;
        this.Ticket = order.Ticket;
        this.Order = order.Order;
        this.Type = order.Type;
        this.CloseType = order.CloseType;
        this.SampleType = order.SampleType;
        this.OriginalOpenTime = order.OriginalOpenTime;
        this.OriginalType = order.OriginalType;
        this.Size = order.Size;
        this.OriginalPrice = order.OriginalPrice;
        this.OpenTime = order.OpenTime;
        this.OpenPrice = order.OpenPrice;
        this.CloseTime = order.CloseTime;
        this.ClosePrice = order.ClosePrice;
        this.StopLoss = order.StopLoss;
        this.TakeProfit = order.TakeProfit;
        this.BarsInTrade = order.BarsInTrade;
        this.PL = order.PL;
        this.PctPL = order.PctPL;
        this.PctPL_TWR = order.PctPL_TWR;
        this.PipsPL = order.PipsPL;
        this.DD = order.DD;
        this.PctDD = order.PctDD;
        this.PipsDD = order.PipsDD;
        this.CommSwap = order.CommSwap;
        this.CommSwapApplied = order.CommSwapApplied;
        this.SlippageInMoney = order.SlippageInMoney;
        this.MAE = order.MAE;
        this.PipsMAE = order.PipsMAE;
        this.MFE = order.MFE;
        this.PipsMFE = order.PipsMFE;
        this.AccountBalance = order.AccountBalance;
        this.PctAccountBalance = order.PctAccountBalance;
        this.PipsAccountBalance = order.PipsAccountBalance;
        this.Extra1 = order.Extra1;
        this.MagicNumber = order.MagicNumber;
        this.Duration = order.Duration;
        this.IsInPortfolio = order.IsInPortfolio;
        this.ExitIndex = order.ExitIndex;
        this.ATROnOpen = order.ATROnOpen;
        this.OrderId = order.OrderId;
    }

    public int getDirection() {
        if (this.Type == 1 || this.Type == 3 || this.Type == 5 || this.Type == 7) {
            return 1;
        }
        return -1;
    }
}

