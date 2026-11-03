/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.plugin.Results.impl.PortfolioCorrelation.overlappingTrades;

import com.strategyquant.plugin.Results.impl.PortfolioCorrelation.overlappingTrades.OverlappingTrade;
import java.util.ArrayList;

public class OverlappingResult {
    public String symbol1;
    public String symbol2;
    public int count = 0;
    public ArrayList<OverlappingTrade> data = new ArrayList();
    public boolean selected = false;

    public OverlappingResult(String symbol1, String symbol2) {
        this.symbol1 = symbol1;
        this.symbol2 = symbol2;
    }
}

