/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  it.unimi.dsi.fastutil.ints.IntOpenHashSet
 *  it.unimi.dsi.fastutil.objects.ObjectArrayList
 *  it.unimi.dsi.fastutil.objects.ObjectListIterator
 */
package com.strategyquant.tradinglib.engine.stockpicker.signals.exit;

import com.strategyquant.tradinglib.engine.stockpicker.signals.exit.PickerExitSignal;
import it.unimi.dsi.fastutil.ints.IntOpenHashSet;
import it.unimi.dsi.fastutil.objects.ObjectArrayList;
import it.unimi.dsi.fastutil.objects.ObjectListIterator;

public class PickerExitSignals
extends ObjectArrayList<PickerExitSignal> {
    public String toString() {
        StringBuilder stringBuilder = new StringBuilder();
        this.toString(stringBuilder);
        return stringBuilder.toString();
    }

    public void toString(StringBuilder stringBuilder) {
        ObjectListIterator objectListIterator = this.iterator();
        while (objectListIterator.hasNext()) {
            PickerExitSignal pickerExitSignal = (PickerExitSignal)objectListIterator.next();
            pickerExitSignal.toString(stringBuilder);
            stringBuilder.append(", ");
        }
    }

    public void reduceCount(IntOpenHashSet intOpenHashSet) {
        for (int i = this.size() - 1; i >= 0; --i) {
            int n = ((PickerExitSignal)this.get((int)i)).symbol.hashCode();
            if (intOpenHashSet.contains(n)) continue;
            this.remove(i);
        }
    }
}

