/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.broker.BrokerDto
 *  com.strategyquant.datalib.broker.BrokerManager
 */
package com.strategyquant.tradinglib.options.parameters;

import com.strategyquant.datalib.broker.BrokerDto;
import com.strategyquant.datalib.broker.BrokerManager;
import com.strategyquant.tradinglib.Editor;
import com.strategyquant.tradinglib.ForEngine;
import com.strategyquant.tradinglib.Help;
import com.strategyquant.tradinglib.Parameter;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.TradingOption;
import java.util.TreeMap;

public class BrokerOption
extends TradingOption {
    @Parameter(name="Broker", defaultValue="No filter", category="Stockpicker")
    @Editor(type=40)
    @ForEngine(value="SP")
    @Help(value="Set broker")
    public String PickerBroker;

    public BrokerOption() {
        this.inbuild = true;
    }

    @Override
    public TreeMap<String, String> getCustomOptions() {
        TreeMap<String, String> treeMap = new TreeMap<String, String>();
        for (BrokerDto brokerDto : BrokerManager.getInstance().getAllBrokers()) {
            String string = brokerDto.getName();
            treeMap.put(string, string);
        }
        treeMap.put("No filter", "No filter");
        return treeMap;
    }

    @Override
    public boolean OnBarUpdate(StrategyBase strategyBase) {
        return true;
    }

    public TradingOption clone() {
        BrokerOption brokerOption = new BrokerOption();
        brokerOption.PickerBroker = this.PickerBroker;
        return brokerOption;
    }

    @Override
    public TradingOption getClone() throws CloneNotSupportedException {
        return this.clone();
    }

    @Override
    public boolean isUsedInTrading() {
        return false;
    }
}

