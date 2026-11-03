/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.engine.stockpicker.signals.entry;

import com.strategyquant.tradinglib.engine.stockpicker.signals.entry.PickerEntrySignal;
import java.io.Serializable;
import java.util.Comparator;

public class PickerEntrySignalComparatorByRevScore
implements Comparator<PickerEntrySignal>,
Serializable {
    @Override
    public int compare(PickerEntrySignal pickerEntrySignal, PickerEntrySignal pickerEntrySignal2) {
        double d = pickerEntrySignal.posScore;
        double d2 = pickerEntrySignal2.posScore;
        if (d == d2) {
            return pickerEntrySignal2.symbol.compareTo(pickerEntrySignal.symbol);
        }
        if (d < d2) {
            return -1;
        }
        return 1;
    }
}

