/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.TickEvent
 *  com.strategyquant.lib.utils.ISQCloneable
 */
package com.strategyquant.tradinglib;

import com.strategyquant.datalib.TickEvent;
import com.strategyquant.lib.utils.ISQCloneable;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.options.TradingOptionsList;
import com.strategyquant.tradinglib.propertygrid.ParametersTableItem;
import java.util.List;

public abstract class TradingOption
extends ParametersTableItem
implements ISQCloneable<TradingOption> {
    protected boolean inbuild = false;

    public boolean isInbuild() {
        return this.inbuild;
    }

    public abstract boolean OnBarUpdate(StrategyBase var1) throws Exception;

    public abstract boolean isUsedInTrading();

    public void OnTick(StrategyBase strategyBase, TickEvent tickEvent, boolean bl) throws Exception {
    }

    public TradingOption getClone() throws CloneNotSupportedException {
        try {
            List list = TradingOptionsList.getInstance().getAvailableClasses();
            for (TradingOption tradingOption : list) {
                if (!tradingOption.getClass().equals(this.getClass())) continue;
                TradingOption tradingOption2 = (TradingOption)tradingOption.getClass().newInstance();
                List<String> list2 = tradingOption2.getParametersList();
                for (int i = 0; i < list2.size(); ++i) {
                    String string = list2.get(i);
                    tradingOption2.setParameterValue(string, "" + this.getParameterValue(string));
                }
                return tradingOption2;
            }
        }
        catch (Exception exception) {
            throw new CloneNotSupportedException("Cloning TradingOption " + this.name + " failed. " + exception.getMessage());
        }
        throw new CloneNotSupportedException("Cloning failed. Cannot find TradingOption " + this.name);
    }
}

