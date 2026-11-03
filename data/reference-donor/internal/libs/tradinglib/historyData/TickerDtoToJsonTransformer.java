/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.historyData.dto.TickerDto
 *  com.strategyquant.datalib.historyData.dto.TickerKind
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.historyData.HistoryDataSubscription
 *  org.json.JSONArray
 */
package com.strategyquant.tradinglib.historyData;

import com.strategyquant.datalib.historyData.dto.TickerDto;
import com.strategyquant.datalib.historyData.dto.TickerKind;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.historyData.HistoryDataSubscription;
import com.strategyquant.tradinglib.transfomer.AbstractDtoToJsonTransformer;
import org.json.JSONArray;

public class TickerDtoToJsonTransformer
extends AbstractDtoToJsonTransformer<TickerDto> {
    private TickerKind tickerKind;

    public TickerDtoToJsonTransformer(TickerKind tickerKind) {
        this.tickerKind = tickerKind;
    }

    @Override
    protected Object objectToJson(TickerDto tickerDto) {
        JSONArray jSONArray = new JSONArray();
        jSONArray.put((Object)tickerDto.getTicker());
        jSONArray.put((Object)(tickerDto.getName() == null ? "" : tickerDto.getName()));
        jSONArray.put((Object)tickerDto.getMarketName());
        if (this.tickerKind == TickerKind.STOCK) {
            jSONArray.put((Object)tickerDto.getType());
        }
        jSONArray.put((Object)(tickerDto.getDateFrom() == null ? "" : SQTime.formatDateQuick((long)tickerDto.getDateFrom().getTime())));
        boolean bl = this.tickerKind == TickerKind.STOCK ? HistoryDataSubscription.getInstance().isAllowedEquity(tickerDto.getTicker(), tickerDto.isEod()) : this.isAllowedFutures(tickerDto);
        jSONArray.put(bl);
        return jSONArray;
    }

    private boolean isAllowedFutures(TickerDto tickerDto) {
        return HistoryDataSubscription.getInstance().isAllowedFuture(tickerDto.getTicker(), tickerDto.getMarketName(), tickerDto.isEod());
    }
}

