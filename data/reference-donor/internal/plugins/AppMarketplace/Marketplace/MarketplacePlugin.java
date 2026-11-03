/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.pluginlib.annotations.Category
 *  com.strategyquant.pluginlib.annotations.License
 *  com.strategyquant.pluginlib.annotations.Name
 *  com.strategyquant.pluginlib.annotations.ShortDesc
 *  com.strategyquant.tradinglib.plugindef.app.IAppPlugin
 *  com.strategyquant.tradinglib.servlet.IServletPlugin
 *  jakarta.servlet.Servlet
 *  net.xeoh.plugins.base.annotations.PluginImplementation
 *  net.xeoh.plugins.base.annotations.meta.Author
 *  org.eclipse.jetty.server.Handler
 *  org.eclipse.jetty.servlet.ServletContextHandler
 *  org.eclipse.jetty.servlet.ServletHolder
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.App.impl.Marketplace;

import com.strategyquant.plugin.App.impl.Marketplace.MarketplaceServlet;
import com.strategyquant.pluginlib.annotations.Category;
import com.strategyquant.pluginlib.annotations.License;
import com.strategyquant.pluginlib.annotations.Name;
import com.strategyquant.pluginlib.annotations.ShortDesc;
import com.strategyquant.tradinglib.plugindef.app.IAppPlugin;
import com.strategyquant.tradinglib.servlet.IServletPlugin;
import jakarta.servlet.Servlet;
import net.xeoh.plugins.base.annotations.PluginImplementation;
import net.xeoh.plugins.base.annotations.meta.Author;
import org.eclipse.jetty.server.Handler;
import org.eclipse.jetty.servlet.ServletContextHandler;
import org.eclipse.jetty.servlet.ServletHolder;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@Author(name="StrategyQuant")
@Name(name="Marketplace")
@Category(name="App")
@License(text="")
@ShortDesc(text="SQX Marketplace")
@PluginImplementation
public class MarketplacePlugin
implements IAppPlugin,
IServletPlugin {
    public static final Logger Log = LoggerFactory.getLogger(MarketplacePlugin.class);
    private ServletContextHandler dataContext;

    public String getName() {
        return "MARKETPLACE";
    }

    public String getProduct() {
        return "SQUANT";
    }

    public int getPreferredPosition() {
        return 1000;
    }

    public void initPlugin() throws Exception {
    }

    public String getContextPath() {
        return "/marketplace";
    }

    public String getAppCode() {
        return "MARKETPLACE";
    }

    public String getTooltip() {
        return "MARKETPLACE";
    }

    public String getProject() {
        return null;
    }

    public String getDefaultTaskType() {
        return null;
    }

    public String getDefaultTaskName() {
        return null;
    }

    public Handler getHandler() {
        if (this.dataContext == null) {
            this.dataContext = new ServletContextHandler(1);
            this.dataContext.setContextPath("/marketplace/");
            this.dataContext.addServlet(new ServletHolder((Servlet)new MarketplaceServlet()), "/*");
        }
        return this.dataContext;
    }
}

