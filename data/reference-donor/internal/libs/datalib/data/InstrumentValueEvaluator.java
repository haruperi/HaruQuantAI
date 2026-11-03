/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib.data;

import com.strategyquant.datalib.historyData.dto.TickerDto;

public interface InstrumentValueEvaluator {
    public double getPointValue(TickerDto var1);

    public double getTickStep(TickerDto var1);

    public double getTickSize(TickerDto var1);

    public byte getInstrumentType(TickerDto var1);

    public String getDescriptions(TickerDto var1);

    public double getOrderSizeMultiplier(TickerDto var1);

    public double getOrderSizeStep(TickerDto var1);
}

