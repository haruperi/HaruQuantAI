/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.ValuesMap
 *  com.strategyquant.pluginlib.annotations.Category
 *  com.strategyquant.pluginlib.annotations.License
 *  com.strategyquant.pluginlib.annotations.Name
 *  com.strategyquant.pluginlib.annotations.ShortDesc
 *  com.strategyquant.tradinglib.connection.Connection
 *  com.strategyquant.tradinglib.connection.ConnectionManager
 *  com.strategyquant.tradinglib.plugindef.connection.IConnectionPlugin
 *  net.xeoh.plugins.base.annotations.PluginImplementation
 *  net.xeoh.plugins.base.annotations.meta.Author
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Connection.impl.Test;

import com.strategyquant.lib.ValuesMap;
import com.strategyquant.plugin.Connection.impl.Test.TestConnection;
import com.strategyquant.pluginlib.annotations.Category;
import com.strategyquant.pluginlib.annotations.License;
import com.strategyquant.pluginlib.annotations.Name;
import com.strategyquant.pluginlib.annotations.ShortDesc;
import com.strategyquant.tradinglib.connection.Connection;
import com.strategyquant.tradinglib.connection.ConnectionManager;
import com.strategyquant.tradinglib.plugindef.connection.IConnectionPlugin;
import net.xeoh.plugins.base.annotations.PluginImplementation;
import net.xeoh.plugins.base.annotations.meta.Author;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@Author(name="Mark Fric")
@Name(name="TestConnection - connection simulation")
@Category(name="Connection")
@License(text="")
@ShortDesc(text="Short description")
@PluginImplementation
public class TestConnectionPlugin
implements IConnectionPlugin {
    public static final Logger Log = LoggerFactory.getLogger((String)"TestConnectionPlugin");

    public String getProduct() {
        return "SQTRADERSQUANT_OLD";
    }

    public int getPreferredPosition() {
        return 0;
    }

    public void initPlugin() {
    }

    public String getPluginName() {
        return "TestConnectionPlugin";
    }

    public Connection createConnection(ConnectionManager connectionManager, String connectionName, ValuesMap connParams) throws Exception {
        return new TestConnection(this, connectionManager, connectionName, connParams);
    }

    public boolean isDataFeed() {
        return true;
    }

    public boolean isExecutionEngine() {
        return true;
    }
}

