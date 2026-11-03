/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.order;

import com.strategyquant.tradinglib.ILiveOrder;
import java.util.Iterator;

public interface ILiveOrdersList
extends Iterable<ILiveOrder> {
    @Override
    public Iterator<ILiveOrder> iterator();

    public int size();
}

