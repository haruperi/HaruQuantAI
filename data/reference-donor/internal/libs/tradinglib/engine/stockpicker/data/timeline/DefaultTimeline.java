/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.basket.BasketDto
 *  com.strategyquant.datalib.basket.BasketOfStocksManager
 *  com.strategyquant.lib.L
 */
package com.strategyquant.tradinglib.engine.stockpicker.data.timeline;

import com.strategyquant.datalib.basket.BasketDto;
import com.strategyquant.datalib.basket.BasketOfStocksManager;
import com.strategyquant.lib.L;
import com.strategyquant.tradinglib.engine.stockpicker.data.timeline.PickerDataTimeline;
import com.strategyquant.tradinglib.project.StopPauseEngine;

public class DefaultTimeline
extends PickerDataTimeline {
    private static DefaultTimeline instance;
    public boolean generated = false;

    public static synchronized DefaultTimeline getInstance() {
        if (instance == null) {
            instance = new DefaultTimeline();
        }
        return instance;
    }

    public void generate() throws Exception {
        String string = "[[S&P 500]]";
        Log.info("Generating default timeline ...");
        BasketDto basketDto = BasketOfStocksManager.getInstance().getBasket(string);
        if (basketDto == null) {
            throw new Exception(L.t((String)"Failed to generate default timeline. Stock group %s not found.", (Object[])new Object[]{string}));
        }
        this.init(basketDto, new StopPauseEngine());
        this.generated = true;
    }
}

