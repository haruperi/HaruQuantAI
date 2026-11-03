/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.pluginlib.annotations.Category
 *  com.strategyquant.pluginlib.annotations.License
 *  com.strategyquant.pluginlib.annotations.Name
 *  com.strategyquant.pluginlib.annotations.ShortDesc
 *  com.strategyquant.tradinglib.results.AbstractBacktestPlugin
 *  jakarta.servlet.Servlet
 *  net.xeoh.plugins.base.annotations.PluginImplementation
 *  net.xeoh.plugins.base.annotations.meta.Author
 *  org.eclipse.jetty.server.Handler
 *  org.eclipse.jetty.servlet.ServletContextHandler
 *  org.eclipse.jetty.servlet.ServletHolder
 */
package com.strategyquant.plugin.Servlet.impl.AlgoWizard;

import com.strategyquant.plugin.Servlet.impl.AlgoWizard.AlgoWizardServlet;
import com.strategyquant.pluginlib.annotations.Category;
import com.strategyquant.pluginlib.annotations.License;
import com.strategyquant.pluginlib.annotations.Name;
import com.strategyquant.pluginlib.annotations.ShortDesc;
import com.strategyquant.tradinglib.results.AbstractBacktestPlugin;
import jakarta.servlet.Servlet;
import net.xeoh.plugins.base.annotations.PluginImplementation;
import net.xeoh.plugins.base.annotations.meta.Author;
import org.eclipse.jetty.server.Handler;
import org.eclipse.jetty.servlet.ServletContextHandler;
import org.eclipse.jetty.servlet.ServletHolder;

@Author(name="Tomas Brynda")
@Name(name="AlgoWizard Servlet Plugin")
@Category(name="Server Extension")
@License(text="")
@ShortDesc(text="AlgoWizard plugin")
@PluginImplementation
public class AlgoWizardServletPlugin
extends AbstractBacktestPlugin {
    private ServletContextHandler dataContext;

    public String getProduct() {
        return "SQUANTSQEDITORAlgoWizardBACKTESTNODEAlgoWizardStandalone";
    }

    public int getPreferredPosition() {
        return 0;
    }

    public void initPlugin() throws Exception {
    }

    public Handler getHandler() {
        if (this.dataContext == null) {
            this.dataContext = new ServletContextHandler(1);
            this.dataContext.setContextPath("/algowizard/");
            this.dataContext.addServlet(new ServletHolder((Servlet)new AlgoWizardServlet(this.backtester, this.rgProvider)), "/*");
        }
        return this.dataContext;
    }
}

