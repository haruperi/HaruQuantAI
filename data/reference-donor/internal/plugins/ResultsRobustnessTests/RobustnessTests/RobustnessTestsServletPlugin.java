/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.pluginlib.SQPluginManager
 *  com.strategyquant.pluginlib.annotations.Category
 *  com.strategyquant.pluginlib.annotations.License
 *  com.strategyquant.pluginlib.annotations.Name
 *  com.strategyquant.pluginlib.annotations.ShortDesc
 *  com.strategyquant.tradinglib.Result
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.crosscheck.ICrossCheck
 *  com.strategyquant.tradinglib.crosscheck.MonteCarloCrossCheckMethod
 *  com.strategyquant.tradinglib.results.AbstractResultsPlugin
 *  jakarta.servlet.Servlet
 *  net.xeoh.plugins.base.annotations.PluginImplementation
 *  net.xeoh.plugins.base.annotations.meta.Author
 *  org.eclipse.jetty.server.Handler
 *  org.eclipse.jetty.servlet.ServletContextHandler
 *  org.eclipse.jetty.servlet.ServletHolder
 *  org.json.JSONObject
 */
package com.strategyquant.plugin.Results.impl.RobustnessTests;

import com.strategyquant.plugin.Results.impl.RobustnessTests.RobustnessTestsServlet;
import com.strategyquant.pluginlib.SQPluginManager;
import com.strategyquant.pluginlib.annotations.Category;
import com.strategyquant.pluginlib.annotations.License;
import com.strategyquant.pluginlib.annotations.Name;
import com.strategyquant.pluginlib.annotations.ShortDesc;
import com.strategyquant.tradinglib.Result;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.crosscheck.ICrossCheck;
import com.strategyquant.tradinglib.crosscheck.MonteCarloCrossCheckMethod;
import com.strategyquant.tradinglib.results.AbstractResultsPlugin;
import jakarta.servlet.Servlet;
import net.xeoh.plugins.base.annotations.PluginImplementation;
import net.xeoh.plugins.base.annotations.meta.Author;
import org.eclipse.jetty.server.Handler;
import org.eclipse.jetty.servlet.ServletContextHandler;
import org.eclipse.jetty.servlet.ServletHolder;
import org.json.JSONObject;

@Author(name="Tomas Brynda")
@Name(name="Robustness tests Servlet Plugin - SQ")
@Category(name="Server Extension")
@License(text="")
@ShortDesc(text="Server API for Robustness tests tab")
@PluginImplementation
public class RobustnessTestsServletPlugin
extends AbstractResultsPlugin {
    private ServletContextHandler dataContext;
    private RobustnessTestsServlet servlet;

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
            this.servlet = new RobustnessTestsServlet(this.rgProvider);
            this.dataContext = new ServletContextHandler(1);
            this.dataContext.setContextPath("/rtresults/");
            this.dataContext.addServlet(new ServletHolder((Servlet)this.servlet), "/*");
        }
        return this.dataContext;
    }

    public boolean containsResult(ResultsGroup rg) throws Exception {
        Result result = rg.mainResult();
        for (ICrossCheck plugin : SQPluginManager.getPlugins(ICrossCheck.class)) {
            if (!MonteCarloCrossCheckMethod.class.isAssignableFrom(plugin.getClass()) || result.getInt(plugin.getSettingName() + "_NumberOfSimulations") <= 0) continue;
            return true;
        }
        return false;
    }

    public String getKey() {
        return "monteCarloTests";
    }

    public JSONObject getInitializationData() throws Exception {
        return null;
    }
}

