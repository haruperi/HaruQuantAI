/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.order;

import com.strategyquant.tradinglib.ILiveOrder;
import com.strategyquant.tradinglib.order.ILiveOrdersList;
import java.util.ArrayList;
import java.util.Iterator;

public class LiveOrdersListObj
implements ILiveOrdersList {
    protected ArrayList<ILiveOrder> list = new ArrayList();

    @Override
    public Iterator<ILiveOrder> iterator() {
        return new Iterator<ILiveOrder>(){
            private final Iterator<ILiveOrder> iter;
            {
                this.iter = LiveOrdersListObj.this.list.iterator();
            }

            @Override
            public boolean hasNext() {
                return this.iter.hasNext();
            }

            @Override
            public ILiveOrder next() {
                return this.iter.next();
            }

            @Override
            public void remove() {
                throw new UnsupportedOperationException("No changes allowed");
            }
        };
    }

    @Override
    public int size() {
        return this.list.size();
    }

    public void add(ILiveOrder iLiveOrder) {
        this.list.add(iLiveOrder);
    }

    public void addAll(ArrayList<ILiveOrder> arrayList) {
        this.list.addAll(arrayList);
    }

    public void addAll(LiveOrdersListObj liveOrdersListObj) {
        for (ILiveOrder iLiveOrder : liveOrdersListObj) {
            this.list.add(iLiveOrder);
        }
    }

    public void remove(ILiveOrder iLiveOrder) {
        this.list.remove(iLiveOrder);
    }

    public ILiveOrder get(int n) {
        return this.list.get(n);
    }

    public Iterator<ILiveOrder> iteratorMutable() {
        return new Iterator<ILiveOrder>(){
            private final Iterator<ILiveOrder> iter;
            {
                this.iter = LiveOrdersListObj.this.list.iterator();
            }

            @Override
            public boolean hasNext() {
                return this.iter.hasNext();
            }

            @Override
            public ILiveOrder next() {
                return this.iter.next();
            }

            @Override
            public void remove() {
                this.iter.remove();
            }
        };
    }
}

