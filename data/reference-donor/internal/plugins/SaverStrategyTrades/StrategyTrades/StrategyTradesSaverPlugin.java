/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.pluginlib.annotations.Category
 *  com.strategyquant.pluginlib.annotations.License
 *  com.strategyquant.pluginlib.annotations.Name
 *  com.strategyquant.pluginlib.annotations.ShortDesc
 *  com.strategyquant.pluginlib.program.IProgram
 *  com.strategyquant.pluginlib.program.Program
 *  com.strategyquant.tradinglib.OrdersList
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.results.file.ISaverPlugin
 *  com.strategyquant.tradinglib.tradelist.TradelistExport
 *  com.strategyquant.tradinglib.tradelist.TradelistTableView
 *  com.strategyquant.tradinglib.tradelist.TradelistViewsManager
 *  net.xeoh.plugins.base.annotations.PluginImplementation
 *  net.xeoh.plugins.base.annotations.meta.Author
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Saver.impl.StrategyTrades;

import com.strategyquant.lib.app.MainApp;
import com.strategyquant.pluginlib.annotations.Category;
import com.strategyquant.pluginlib.annotations.License;
import com.strategyquant.pluginlib.annotations.Name;
import com.strategyquant.pluginlib.annotations.ShortDesc;
import com.strategyquant.pluginlib.program.IProgram;
import com.strategyquant.pluginlib.program.Program;
import com.strategyquant.tradinglib.OrdersList;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.results.file.ISaverPlugin;
import com.strategyquant.tradinglib.tradelist.TradelistExport;
import com.strategyquant.tradinglib.tradelist.TradelistTableView;
import com.strategyquant.tradinglib.tradelist.TradelistViewsManager;
import java.util.ArrayList;
import java.util.Map;
import net.xeoh.plugins.base.annotations.PluginImplementation;
import net.xeoh.plugins.base.annotations.meta.Author;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@Author(name="Mark Fric")
@Name(name="SQ3SaverPlugin plugin")
@Category(name="File Saver")
@License(text="")
@ShortDesc(text="Short description")
@PluginImplementation
public class StrategyTradesSaverPlugin
implements ISaverPlugin,
IProgram {
    public static final Logger Log = LoggerFactory.getLogger(StrategyTradesSaverPlugin.class);
    public static final String[] extensions = new String[]{"csv", "xlsx"};

    public String getProduct() {
        return "any";
    }

    public int getPreferredPosition() {
        return 0;
    }

    public void initPlugin() throws Exception {
        Program.register((String)"SaverStrategyTrades", (IProgram)this);
    }

    public String[] getFileExtensions() {
        return extensions;
    }

    public Object call(String methodName, Object ... parameters) throws Exception {
        if (methodName.equals("save")) {
            this.save((ResultsGroup)parameters[0], (String)parameters[1], (Map)parameters[2]);
        }
        return null;
    }

    public void save(ResultsGroup rg, String fileName, Map<String, String[]> parameterMap) throws Exception {
        try {
            boolean useComma = Boolean.parseBoolean(parameterMap.get("useComma")[0]);
            String data = parameterMap.get("data")[0];
            OrdersList ordersList = data.equals("main") ? (this.shouldShowControlOrders() ? rg.orders().filter(rg.getMainResultKey(), (byte)0, (byte)127, false) : rg.orders().filterExcludingControlOrders(rg.getMainResultKey(), (byte)0, (byte)127, false)) : rg.orders();
            TradelistTableView tradelistView = TradelistViewsManager.getInstance().getSelectedTradelistView();
            if (tradelistView == null) {
                Log.error("Cannot load the list of trades. No tradelist view is set.");
            }
            ArrayList rowData = tradelistView.getData(ordersList, 0, ordersList.size(), true);
            TradelistExport export = new TradelistExport();
            if (fileName.endsWith("xlsx")) {
                export.toXlsx(rowData, fileName, useComma);
            } else {
                export.toCsv(rowData, fileName, useComma);
            }
        }
        catch (Exception ex) {
            Log.error("Failed to export trades of strategy '" + rg.getName() + "'. Exc: ", (Throwable)ex);
            throw new Exception("Failed to export trades of strategy '" + rg.getName() + "'. Reason: " + ex.getMessage());
        }
    }

    private boolean shouldShowControlOrders() {
        boolean showControlOrders = false;
        try {
            showControlOrders = Boolean.parseBoolean(MainApp.settings().get("showControlOrders", "false"));
        }
        catch (Exception exception) {
            // empty catch block
        }
        return showControlOrders;
    }

    public ISaverPlugin clone() {
        return new StrategyTradesSaverPlugin();
    }
}

