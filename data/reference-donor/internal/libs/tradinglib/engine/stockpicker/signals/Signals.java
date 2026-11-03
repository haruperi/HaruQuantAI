/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  it.unimi.dsi.fastutil.objects.ObjectArrayList
 */
package com.strategyquant.tradinglib.engine.stockpicker.signals;

import com.strategyquant.tradinglib.OrderTypes;
import com.strategyquant.tradinglib.engine.stockpicker.signals.entry.PickerEntrySignal;
import com.strategyquant.tradinglib.engine.stockpicker.signals.entry.PickerEntrySignals;
import com.strategyquant.tradinglib.engine.stockpicker.signals.exit.PickerExitSignal;
import com.strategyquant.tradinglib.engine.stockpicker.signals.exit.PickerExitSignals;
import it.unimi.dsi.fastutil.objects.ObjectArrayList;
import java.util.Comparator;

public class Signals {
    private PickerEntrySignals entryLong = null;
    private PickerEntrySignals entryShort = null;
    public PickerExitSignals exit = null;

    public boolean longEntrySignalExists() {
        return this.entryLong != null && !this.entryLong.isEmpty();
    }

    public boolean shortEntrySignalExists() {
        return this.entryShort != null && !this.entryShort.isEmpty();
    }

    public PickerEntrySignals getLongEntrySignals() {
        return this.entryLong;
    }

    public PickerEntrySignals getShortEntrySignals() {
        return this.entryShort;
    }

    public ObjectArrayList<PickerEntrySignal> getLongEntrySignals(int n) {
        return this.entryLong == null ? null : this.entryLong.getEntrySignals();
    }

    public ObjectArrayList<PickerEntrySignal> getShortEntrySignals(int n) {
        return this.entryShort == null ? null : this.entryShort.getEntrySignals();
    }

    public String printLongEntrySignals() {
        return this.entryLong == null ? "" : this.entryLong.toString();
    }

    public String printShortEntrySignals() {
        return this.entryShort == null ? "" : this.entryShort.toString();
    }

    public String printExitSignals() {
        return this.exit == null ? "" : this.exit.toString();
    }

    public boolean exitSignalExists() {
        return this.exit != null && !this.exit.isEmpty();
    }

    public PickerExitSignals getExitSignals() {
        return this.exit;
    }

    public void addEntrySignal(int n, String string, byte by, double d, int n2, double d2, double d3, int n3, int n4, byte by2) {
        if (OrderTypes.isLongOrder(by)) {
            if (this.entryLong == null) {
                this.entryLong = new PickerEntrySignals();
            }
            this.entryLong.add(string, by, d, n2, d2, d3, n3, n4, by2);
        } else {
            if (this.entryShort == null) {
                this.entryShort = new PickerEntrySignals();
            }
            this.entryShort.add(string, by, d, n2, d2, d3, n3, n4, by2);
        }
    }

    public void addExitSignal(PickerExitSignal pickerExitSignal) {
        if (this.exit == null) {
            this.exit = new PickerExitSignals();
        }
        this.exit.add(pickerExitSignal);
    }

    public String toString() {
        return String.format("entrySigLong=%d, entrySigShort=%d, exitsig=%d", this.entryLong == null ? 0 : this.entryLong.size(), this.entryShort == null ? 0 : this.entryShort.size(), this.exit == null ? 0 : this.exit.size());
    }

    public void consolidateEntryExitSignals(int n, int n2, Comparator<PickerEntrySignal> comparator) {
        if (this.entryLong != null) {
            this.entryLong.consolidateEntrySignals(n, comparator);
        }
        if (this.entryShort != null) {
            this.entryShort.consolidateEntrySignals(n2, comparator);
        }
    }
}

