/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.pluginlib.annotations.Category
 *  com.strategyquant.pluginlib.annotations.License
 *  com.strategyquant.pluginlib.annotations.Name
 *  com.strategyquant.pluginlib.annotations.ShortDesc
 *  com.strategyquant.tradinglib.servlet.IServletPlugin
 *  jakarta.servlet.Servlet
 *  net.xeoh.plugins.base.annotations.PluginImplementation
 *  net.xeoh.plugins.base.annotations.meta.Author
 *  org.eclipse.jetty.server.Handler
 *  org.eclipse.jetty.servlet.ServletContextHandler
 *  org.eclipse.jetty.servlet.ServletHolder
 */
package com.strategyquant.plugin.CodeEditor.impl.IndicatorTester;

import com.strategyquant.plugin.CodeEditor.impl.IndicatorTester.IndicatorTesterServlet;
import com.strategyquant.pluginlib.annotations.Category;
import com.strategyquant.pluginlib.annotations.License;
import com.strategyquant.pluginlib.annotations.Name;
import com.strategyquant.pluginlib.annotations.ShortDesc;
import com.strategyquant.tradinglib.servlet.IServletPlugin;
import jakarta.servlet.Servlet;
import net.xeoh.plugins.base.annotations.PluginImplementation;
import net.xeoh.plugins.base.annotations.meta.Author;
import org.eclipse.jetty.server.Handler;
import org.eclipse.jetty.servlet.ServletContextHandler;
import org.eclipse.jetty.servlet.ServletHolder;

@Author(name="Tomas Brynda")
@Name(name="Indicator Tester Plugin")
@Category(name="Server Extension")
@License(text="")
@ShortDesc(text="Server API for indicators testing")
@PluginImplementation
public class IndicatorTesterPlugin
implements IServletPlugin {
    private ServletContextHandler connectionContext;

    public String getProduct() {
        return "SQMANAGERSQUANTSQTRADERTESTAPPSQEDITOR";
    }

    public int getPreferredPosition() {
        return 0;
    }

    public void initPlugin() throws Exception {
    }

    public Handler getHandler() {
        if (this.connectionContext == null) {
            this.connectionContext = new ServletContextHandler(1);
            this.connectionContext.setContextPath("/indyTester/");
            this.connectionContext.addServlet(new ServletHolder((Servlet)new IndicatorTesterServlet()), "/*");
        }
        return this.connectionContext;
    }
}

