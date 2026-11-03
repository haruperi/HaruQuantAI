/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  it.unimi.dsi.fastutil.Stack
 *  it.unimi.dsi.fastutil.objects.ObjectArrayList
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.engine.stockpicker.signals.entry;

import com.strategyquant.tradinglib.engine.stockpicker.signals.entry.PickerEntrySignal;
import it.unimi.dsi.fastutil.Stack;
import it.unimi.dsi.fastutil.objects.ObjectArrayList;
import java.util.Collection;
import java.util.Collections;
import java.util.Comparator;
import java.util.PriorityQueue;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class PickerEntrySignals {
    public static final Logger Log = LoggerFactory.getLogger((String)"PickerEntrySignals");
    private ObjectArrayList<PickerEntrySignal> signalsForSymbol = null;
    private Stack<PickerEntrySignal> unusedSignalsStack = null;
    private PriorityQueue<PickerEntrySignal> queue = null;
    private ObjectArrayList<PickerEntrySignal> list = null;

    public void add(String string, byte by, double d, int n, double d2, double d3, int n2, int n3, byte by2) {
        if (this.signalsForSymbol == null) {
            this.signalsForSymbol = new ObjectArrayList();
        }
        PickerEntrySignal pickerEntrySignal = this.createEntrySignalObject(string, by, d, n, d2, d3, n2, n3, by2);
        this.signalsForSymbol.add((Object)pickerEntrySignal);
    }

    private PickerEntrySignal createEntrySignalObject(String string, byte by, double d, int n, double d2, double d3, int n2, int n3, byte by2) {
        if (this.unusedSignalsStack == null || this.unusedSignalsStack.isEmpty()) {
            return new PickerEntrySignal(string, by, d, n, d2, d3, n2, n3, by2);
        }
        PickerEntrySignal pickerEntrySignal = (PickerEntrySignal)this.unusedSignalsStack.pop();
        pickerEntrySignal.init(string, by, d, n, d2, d3, n2, n3, by2);
        return pickerEntrySignal;
    }

    public ObjectArrayList<PickerEntrySignal> list() {
        if (this.list == null) {
            this.list = this.createListFromQueue(this.queue);
        }
        return this.list;
    }

    public void toString(StringBuilder stringBuilder) {
        ObjectArrayList<PickerEntrySignal> objectArrayList = this.list();
        for (int i = 0; i < objectArrayList.size(); ++i) {
            PickerEntrySignal pickerEntrySignal = (PickerEntrySignal)objectArrayList.get(i);
            stringBuilder.append(pickerEntrySignal.toString());
            stringBuilder.append(", ");
        }
    }

    public String toString() {
        StringBuilder stringBuilder = new StringBuilder();
        this.toString(stringBuilder);
        return stringBuilder.toString();
    }

    public void consolidateEntrySignals(int n, Comparator<PickerEntrySignal> comparator) {
        if (this.signalsForSymbol == null) {
            return;
        }
        if (this.queue == null) {
            this.queue = new PriorityQueue<PickerEntrySignal>(comparator);
        }
        this.queue.addAll((Collection<PickerEntrySignal>)this.signalsForSymbol);
        for (int i = this.queue.size() - 1; i >= n; --i) {
            PickerEntrySignal pickerEntrySignal = this.queue.poll();
            this.addToUnusedStack(pickerEntrySignal);
        }
        this.signalsForSymbol.clear();
    }

    private ObjectArrayList<PickerEntrySignal> createListFromQueue(PriorityQueue<PickerEntrySignal> priorityQueue) {
        ObjectArrayList objectArrayList = new ObjectArrayList();
        if (priorityQueue != null) {
            while (!priorityQueue.isEmpty()) {
                PickerEntrySignal pickerEntrySignal = priorityQueue.poll();
                objectArrayList.add((Object)pickerEntrySignal);
            }
            priorityQueue.addAll((Collection<PickerEntrySignal>)objectArrayList);
            Collections.reverse(objectArrayList);
        }
        return objectArrayList;
    }

    private boolean dontCompare(ObjectArrayList<PickerEntrySignal> objectArrayList, ObjectArrayList<PickerEntrySignal> objectArrayList2) {
        if (objectArrayList == null) {
            return true;
        }
        if (objectArrayList2 == null) {
            return true;
        }
        if (objectArrayList.size() != objectArrayList2.size()) {
            return true;
        }
        for (int i = 0; i < objectArrayList.size(); ++i) {
            PickerEntrySignal pickerEntrySignal = (PickerEntrySignal)objectArrayList.get(i);
            PickerEntrySignal pickerEntrySignal2 = (PickerEntrySignal)objectArrayList2.get(i);
            if (pickerEntrySignal.symbol.equals(pickerEntrySignal2.symbol)) continue;
            return true;
        }
        return false;
    }

    private void addToUnusedStack(PickerEntrySignal pickerEntrySignal) {
        if (this.unusedSignalsStack == null) {
            this.unusedSignalsStack = new ObjectArrayList();
        }
        pickerEntrySignal.setUnused();
        this.unusedSignalsStack.push((Object)pickerEntrySignal);
    }

    public boolean isEmpty() {
        return this.queue == null || this.queue.isEmpty();
    }

    public ObjectArrayList<PickerEntrySignal> getEntrySignals() {
        return this.signalsForSymbol;
    }

    public int size() {
        int n = 0;
        if (this.queue != null) {
            n += this.queue.size();
        }
        if (this.signalsForSymbol != null) {
            n += this.signalsForSymbol.size();
        }
        return n;
    }
}

