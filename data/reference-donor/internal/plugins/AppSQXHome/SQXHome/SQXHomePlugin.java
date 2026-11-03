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
package com.strategyquant.plugin.App.impl.SQXHome;

import com.strategyquant.plugin.App.impl.SQXHome.SQXHomeServlet;
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

@Author(name="Tomas Brynda")
@Name(name="SQXHome")
@Category(name="App")
@License(text="")
@ShortDesc(text="Short description")
@PluginImplementation
public class SQXHomePlugin
implements IAppPlugin,
IServletPlugin {
    public static final Logger Log = LoggerFactory.getLogger(SQXHomePlugin.class);
    private ServletContextHandler dataContext;

    public String getName() {
        return "SQX Home";
    }

    public String getProduct() {
        return "SQUANT";
    }

    public int getPreferredPosition() {
        return 11;
    }

    public void initPlugin() throws Exception {
    }

    public String getContextPath() {
        return "/sqxhome";
    }

    public String getAppCode() {
        return "SQXHOME";
    }

    public String getTooltip() {
        return "SQX Home screen";
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
            this.dataContext.setContextPath("/sqxhome/");
            this.dataContext.addServlet(new ServletHolder((Servlet)new SQXHomeServlet()), "/*");
        }
        return this.dataContext;
    }
}

