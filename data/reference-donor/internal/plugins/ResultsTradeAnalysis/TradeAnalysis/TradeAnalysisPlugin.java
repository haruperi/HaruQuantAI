/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.pluginlib.annotations.Category
 *  com.strategyquant.pluginlib.annotations.License
 *  com.strategyquant.pluginlib.annotations.Name
 *  com.strategyquant.pluginlib.annotations.ShortDesc
 *  com.strategyquant.pluginlib.program.IProgram
 *  com.strategyquant.pluginlib.program.Program
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.results.AbstractResultsPlugin
 *  jakarta.servlet.Servlet
 *  net.xeoh.plugins.base.annotations.PluginImplementation
 *  net.xeoh.plugins.base.annotations.meta.Author
 *  org.eclipse.jetty.server.Handler
 *  org.eclipse.jetty.servlet.ServletContextHandler
 *  org.eclipse.jetty.servlet.ServletHolder
 *  org.json.JSONObject
 */
package com.strategyquant.plugin.Results.impl.TradeAnalysis;

import com.strategyquant.plugin.Results.impl.TradeAnalysis.TradeAnalysisServlet;
import com.strategyquant.pluginlib.annotations.Category;
import com.strategyquant.pluginlib.annotations.License;
import com.strategyquant.pluginlib.annotations.Name;
import com.strategyquant.pluginlib.annotations.ShortDesc;
import com.strategyquant.pluginlib.program.IProgram;
import com.strategyquant.pluginlib.program.Program;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.results.AbstractResultsPlugin;
import jakarta.servlet.Servlet;
import java.util.Map;
import net.xeoh.plugins.base.annotations.PluginImplementation;
import net.xeoh.plugins.base.annotations.meta.Author;
import org.eclipse.jetty.server.Handler;
import org.eclipse.jetty.servlet.ServletContextHandler;
import org.eclipse.jetty.servlet.ServletHolder;
import org.json.JSONObject;

@Author(name="Tamas Takacs")
@Name(name="Trade Analysis Servlet Plugin - SQ")
@Category(name="Server Extension")
@License(text="")
@ShortDesc(text="Server API for results Trade Analysis tab")
@PluginImplementation
public class TradeAnalysisPlugin
extends AbstractResultsPlugin
implements IProgram {
    private ServletContextHandler dataContext;
    private TradeAnalysisServlet servlet;

    public String getProduct() {
        return "SQUANTAlgoWizardBACKTESTNODE";
    }

    public int getPreferredPosition() {
        return 0;
    }

    public void initPlugin() throws Exception {
        if (!Program.isRegistered((String)"ResultsTradeAnalysis")) {
            Program.register((String)"ResultsTradeAnalysis", (IProgram)this);
        }
    }

    public Handler getHandler() {
        if (this.dataContext == null) {
            this.servlet = new TradeAnalysisServlet(this.rgProvider);
            this.dataContext = new ServletContextHandler(1);
            this.dataContext.setContextPath("/tradeanalysis/");
            this.dataContext.addServlet(new ServletHolder((Servlet)this.servlet), "/*");
        }
        return this.dataContext;
    }

    public boolean containsResult(ResultsGroup rg) {
        return true;
    }

    public String getKey() {
        return "tradeAnalysis";
    }

    public JSONObject getInitializationData() throws Exception {
        JSONObject data = new JSONObject();
        data.put("types", (Object)this.servlet.getTypes());
        data.put("lastSettings", (Object)this.servlet.loadLastSettings());
        return data;
    }

    public Object call(String methodName, Object ... parameters) throws Exception {
        if (methodName.equals("printResultsGroup")) {
            this.servlet.rg = (ResultsGroup)parameters[0];
            return this.servlet.execute("print", (Map)parameters[1], null);
        }
        return this.servlet.execute(methodName, parameters == null ? null : (Map)parameters[0], null);
    }
}

