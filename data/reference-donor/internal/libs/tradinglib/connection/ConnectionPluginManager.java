/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.pluginlib.SQPluginManager
 */
package com.strategyquant.tradinglib.connection;

import com.strategyquant.pluginlib.SQPluginManager;
import com.strategyquant.tradinglib.plugindef.connection.IConnectionPlugin;
import java.util.ArrayList;

public class ConnectionPluginManager {
    public static IConnectionPlugin getConnectionPlugin(String string) throws Exception {
        ArrayList arrayList = SQPluginManager.getPlugins(IConnectionPlugin.class);
        for (IConnectionPlugin iConnectionPlugin : arrayList) {
            if (!iConnectionPlugin.getPluginName().equalsIgnoreCase(string)) continue;
            return iConnectionPlugin;
        }
        throw new Exception("ConnectionPlugin named '" + string + "' was not found!");
    }
}

