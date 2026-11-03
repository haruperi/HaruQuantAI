/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.project;

import com.strategyquant.tradinglib.Databank;
import java.util.Comparator;

public class DatabankPositionComparator
implements Comparator<Databank> {
    @Override
    public int compare(Databank databank, Databank databank2) {
        if (databank.isDefault() && databank2.isDefault()) {
            if (databank.getName().equals("Results")) {
                return -1;
            }
            if (databank2.getName().equals("Results")) {
                return 1;
            }
            return 0;
        }
        if (databank.isDefault() && !databank2.isDefault()) {
            return -1;
        }
        if (!databank.isDefault() && databank2.isDefault()) {
            return 1;
        }
        return databank.getPosition() - databank2.getPosition();
    }
}

