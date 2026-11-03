/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.pluginlib.annotations.Category
 *  com.strategyquant.pluginlib.annotations.License
 *  com.strategyquant.pluginlib.annotations.Name
 *  com.strategyquant.pluginlib.annotations.ShortDesc
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.optimization.WalkForwardMatrixResult
 *  com.strategyquant.tradinglib.results.AbstractResultsPlugin
 *  jakarta.servlet.Servlet
 *  net.xeoh.plugins.base.annotations.PluginImplementation
 *  net.xeoh.plugins.base.annotations.meta.Author
 *  org.eclipse.jetty.server.Handler
 *  org.eclipse.jetty.servlet.ServletContextHandler
 *  org.eclipse.jetty.servlet.ServletHolder
 *  org.json.JSONObject
 */
package com.strategyquant.plugin.Results.impl.WalkForward;

import com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardServlet;
import com.strategyquant.pluginlib.annotations.Category;
import com.strategyquant.pluginlib.annotations.License;
import com.strategyquant.pluginlib.annotations.Name;
import com.strategyquant.pluginlib.annotations.ShortDesc;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.optimization.WalkForwardMatrixResult;
import com.strategyquant.tradinglib.results.AbstractResultsPlugin;
import jakarta.servlet.Servlet;
import net.xeoh.plugins.base.annotations.PluginImplementation;
import net.xeoh.plugins.base.annotations.meta.Author;
import org.eclipse.jetty.server.Handler;
import org.eclipse.jetty.servlet.ServletContextHandler;
import org.eclipse.jetty.servlet.ServletHolder;
import org.json.JSONObject;

@Author(name="Tomas Brynda")
@Name(name="WalkForward Servlet Plugin - SQ")
@Category(name="Server Extension")
@License(text="")
@ShortDesc(text="Server API for results WalkForward tab")
@PluginImplementation
public class WalkForwardPlugin
extends AbstractResultsPlugin {
    private ServletContextHandler dataContext;
    private WalkForwardServlet servlet;

    public String getProduct() {
        return "SQUANTAlgoWizardBACKTESTNODE";
    }

    public int getPreferredPosition() {
        return 0;
    }

    public void initPlugin() throws Exception {
    }

    public Handler getHandler() {
        if (this.dataContext == null) {
            this.servlet = new WalkForwardServlet(this.rgProvider);
            this.dataContext = new ServletContextHandler(1);
            this.dataContext.setContextPath("/walkforward/");
            this.dataContext.addServlet(new ServletHolder((Servlet)this.servlet), "/*");
        }
        return this.dataContext;
    }

    public boolean containsResult(ResultsGroup rg) throws Exception {
        WalkForwardMatrixResult mwfResult = (WalkForwardMatrixResult)rg.mainResult().get("WalkForwardResult");
        return mwfResult != null;
    }

    public String getKey() {
        return "wfResult";
    }

    public JSONObject getInitializationData() throws Exception {
        return null;
    }
}

