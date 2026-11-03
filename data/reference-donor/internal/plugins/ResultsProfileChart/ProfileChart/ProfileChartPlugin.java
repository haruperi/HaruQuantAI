/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.pluginlib.annotations.Category
 *  com.strategyquant.pluginlib.annotations.License
 *  com.strategyquant.pluginlib.annotations.Name
 *  com.strategyquant.pluginlib.annotations.ShortDesc
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.results.AbstractResultsPlugin
 *  com.strategyquant.tradinglib.results.SpecialValues
 *  jakarta.servlet.Servlet
 *  net.xeoh.plugins.base.annotations.PluginImplementation
 *  net.xeoh.plugins.base.annotations.meta.Author
 *  org.eclipse.jetty.server.Handler
 *  org.eclipse.jetty.servlet.ServletContextHandler
 *  org.eclipse.jetty.servlet.ServletHolder
 *  org.json.JSONObject
 */
package com.strategyquant.plugin.Results.impl.ProfileChart;

import com.strategyquant.plugin.Results.impl.ProfileChart.ProfileChartServlet;
import com.strategyquant.pluginlib.annotations.Category;
import com.strategyquant.pluginlib.annotations.License;
import com.strategyquant.pluginlib.annotations.Name;
import com.strategyquant.pluginlib.annotations.ShortDesc;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.results.AbstractResultsPlugin;
import com.strategyquant.tradinglib.results.SpecialValues;
import jakarta.servlet.Servlet;
import net.xeoh.plugins.base.annotations.PluginImplementation;
import net.xeoh.plugins.base.annotations.meta.Author;
import org.eclipse.jetty.server.Handler;
import org.eclipse.jetty.servlet.ServletContextHandler;
import org.eclipse.jetty.servlet.ServletHolder;
import org.json.JSONObject;

@Author(name="SQ")
@Name(name="ProfileChart Servlet Plugin - SQ")
@Category(name="Server Extension")
@License(text="")
@ShortDesc(text="Server API for Profile Chart results tab")
@PluginImplementation
public class ProfileChartPlugin
extends AbstractResultsPlugin {
    private ServletContextHandler dataContext;

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
            this.dataContext = new ServletContextHandler(1);
            this.dataContext.setContextPath("/profilechart/");
            this.dataContext.addServlet(new ServletHolder((Servlet)new ProfileChartServlet(this.rgProvider)), "/*");
        }
        return this.dataContext;
    }

    public boolean containsResult(ResultsGroup rg) throws Exception {
        if (rg == null) {
            return false;
        }
        String pathsStr = rg.specialValues().getString(SpecialValues.ProfileChartPaths, "");
        return pathsStr != null && !pathsStr.isEmpty();
    }

    public String getKey() {
        return "profileChart";
    }

    public JSONObject getInitializationData() {
        return null;
    }
}

