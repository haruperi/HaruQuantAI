/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.robustnesstests;

import com.strategyquant.tradinglib.robustnesstests.RobustnessResults;
import java.util.ArrayList;

public class MCSimulations
extends ArrayList<RobustnessResults> {
    public MCSimulations getClone() throws Exception {
        MCSimulations mCSimulations = new MCSimulations();
        for (int i = 0; i < this.size(); ++i) {
            mCSimulations.add(((RobustnessResults)this.get(i)).getClone());
        }
        return mCSimulations;
    }
}

