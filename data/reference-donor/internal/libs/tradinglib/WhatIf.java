/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.utils.ISQCloneable
 */
package com.strategyquant.tradinglib;

import com.strategyquant.lib.utils.ISQCloneable;
import com.strategyquant.tradinglib.OrdersList;
import com.strategyquant.tradinglib.propertygrid.ParametersTableItem;

public abstract class WhatIf
extends ParametersTableItem
implements ISQCloneable<WhatIf> {
    public abstract void filter(OrdersList var1) throws Exception;

    public WhatIf getClone() throws Exception {
        return this;
    }
}

