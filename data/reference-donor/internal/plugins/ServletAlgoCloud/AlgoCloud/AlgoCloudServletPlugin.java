/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.pluginlib.annotations.Category
 *  com.strategyquant.pluginlib.annotations.License
 *  com.strategyquant.pluginlib.annotations.Name
 *  com.strategyquant.pluginlib.annotations.ShortDesc
 *  com.strategyquant.pluginlib.program.IProgram
 *  com.strategyquant.tradinglib.results.AbstractBacktestPlugin
 *  jakarta.servlet.Servlet
 *  net.xeoh.plugins.base.annotations.PluginImplementation
 *  net.xeoh.plugins.base.annotations.meta.Author
 *  org.eclipse.jetty.server.Handler
 *  org.eclipse.jetty.servlet.ServletContextHandler
 *  org.eclipse.jetty.servlet.ServletHolder
 */
package com.strategyquant.plugin.Servlet.impl.AlgoCloud;

import com.strategyquant.plugin.Servlet.impl.AlgoCloud.AlgoCloudServlet;
import com.strategyquant.pluginlib.annotations.Category;
import com.strategyquant.pluginlib.annotations.License;
import com.strategyquant.pluginlib.annotations.Name;
import com.strategyquant.pluginlib.annotations.ShortDesc;
import com.strategyquant.pluginlib.program.IProgram;
import com.strategyquant.tradinglib.results.AbstractBacktestPlugin;
import jakarta.servlet.Servlet;
import java.util.Map;
import net.xeoh.plugins.base.annotations.PluginImplementation;
import net.xeoh.plugins.base.annotations.meta.Author;
import org.eclipse.jetty.server.Handler;
import org.eclipse.jetty.servlet.ServletContextHandler;
import org.eclipse.jetty.servlet.ServletHolder;

@Author(name="StrategyQuant")
@Name(name="AlgoCloud Servlet Plugin")
@Category(name="Server Extension")
@License(text="")
@ShortDesc(text="Open in AlgoCloud: uploads a strategy to AlgoCloud and returns the URL to open")
@PluginImplementation
public class AlgoCloudServletPlugin
extends AbstractBacktestPlugin
implements IProgram {
    private ServletContextHandler dataContext;
    private AlgoCloudServlet servlet;

    public String getProduct() {
        return "SQUANT";
    }

    public int getPreferredPosition() {
        return 0;
    }

    public void initPlugin() throws Exception {
    }

    public Handler getHandler() {
        if (this.dataContext == null) {
            this.servlet = new AlgoCloudServlet(this.rgProvider);
            this.dataContext = new ServletContextHandler(1);
            this.dataContext.setContextPath("/algocloud/");
            this.dataContext.addServlet(new ServletHolder((Servlet)this.servlet), "/*");
        }
        return this.dataContext;
    }

    public Object call(String methodName, Object ... parameters) throws Exception {
        if (this.servlet == null) {
            this.servlet = new AlgoCloudServlet(this.rgProvider);
        }
        return this.servlet.execute(methodName, parameters == null ? null : (Map)parameters[0], null);
    }
}

