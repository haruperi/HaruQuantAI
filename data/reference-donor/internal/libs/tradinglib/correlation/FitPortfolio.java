/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.correlation;

import com.strategyquant.tradinglib.CorrelationType;
import com.strategyquant.tradinglib.Databank;
import java.io.Serializable;

public class FitPortfolio
implements Serializable {
    public boolean active;
    public Databank databank;
    public double corrMax;
    public CorrelationType corrType;
    public int corrPeriod;
    public boolean corrAllowNegative;
    public boolean corrAddEmptyPeriods;

    public FitPortfolio getClone() {
        FitPortfolio fitPortfolio = new FitPortfolio();
        fitPortfolio.active = this.active;
        fitPortfolio.databank = this.databank;
        fitPortfolio.corrMax = this.corrMax;
        fitPortfolio.corrType = this.corrType;
        fitPortfolio.corrPeriod = this.corrPeriod;
        fitPortfolio.corrAllowNegative = this.corrAllowNegative;
        fitPortfolio.corrAddEmptyPeriods = this.corrAddEmptyPeriods;
        return fitPortfolio;
    }
}

