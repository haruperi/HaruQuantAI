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
 *  jakarta.servlet.DispatcherType
 *  jakarta.servlet.Servlet
 *  net.xeoh.plugins.base.annotations.PluginImplementation
 *  net.xeoh.plugins.base.annotations.meta.Author
 *  org.eclipse.jetty.server.Handler
 *  org.eclipse.jetty.servlet.FilterHolder
 *  org.eclipse.jetty.servlet.ServletContextHandler
 *  org.eclipse.jetty.servlet.ServletHolder
 *  org.eclipse.jetty.servlets.CrossOriginFilter
 *  org.json.JSONObject
 */
package com.strategyquant.plugin.Results.impl.EquityChart;

import com.strategyquant.plugin.Results.impl.EquityChart.EquityChartServlet;
import com.strategyquant.pluginlib.annotations.Category;
import com.strategyquant.pluginlib.annotations.License;
import com.strategyquant.pluginlib.annotations.Name;
import com.strategyquant.pluginlib.annotations.ShortDesc;
import com.strategyquant.pluginlib.program.IProgram;
import com.strategyquant.pluginlib.program.Program;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.results.AbstractResultsPlugin;
import jakarta.servlet.DispatcherType;
import jakarta.servlet.Servlet;
import java.util.EnumSet;
import java.util.Map;
import net.xeoh.plugins.base.annotations.PluginImplementation;
import net.xeoh.plugins.base.annotations.meta.Author;
import org.eclipse.jetty.server.Handler;
import org.eclipse.jetty.servlet.FilterHolder;
import org.eclipse.jetty.servlet.ServletContextHandler;
import org.eclipse.jetty.servlet.ServletHolder;
import org.eclipse.jetty.servlets.CrossOriginFilter;
import org.json.JSONObject;

@Author(name="Tamas Takacs")
@Name(name="EquityChart Servlet Plugin - SQ")
@Category(name="Server Extension")
@License(text="")
@ShortDesc(text="Server API for results equity chart tab")
@PluginImplementation
public class EquityChartPlugin
extends AbstractResultsPlugin
implements IProgram {
    private ServletContextHandler dataContext;
    private EquityChartServlet servlet;

    public String getProduct() {
        return "SQUANTAlgoWizardBACKTESTNODE";
    }

    public int getPreferredPosition() {
        return 0;
    }

    public void initPlugin() throws Exception {
        if (!Program.isRegistered((String)"ResultsEquityChart")) {
            Program.register((String)"ResultsEquityChart", (IProgram)this);
        }
    }

    public Handler getHandler() {
        if (this.dataContext == null) {
            this.servlet = new EquityChartServlet(this.rgProvider);
            this.dataContext = new ServletContextHandler(1);
            this.dataContext.setContextPath("/equitychart/");
            this.addCrossOrigin(this.dataContext);
            this.dataContext.addServlet(new ServletHolder((Servlet)this.servlet), "/*");
        }
        return this.dataContext;
    }

    private void addCrossOrigin(ServletContextHandler context) {
        FilterHolder cors = context.addFilter(CrossOriginFilter.class, "/*", EnumSet.of(DispatcherType.REQUEST));
        cors.setInitParameter("allowedOrigins", "*");
        cors.setInitParameter("Access-Control-Allow-Origin", "*");
        cors.setInitParameter("allowedMethods", "GET,POST,HEAD");
        cors.setInitParameter("allowedHeaders", "X-Requested-With,Content-Type,Accept,Origin");
    }

    public boolean containsResult(ResultsGroup rg) {
        return true;
    }

    public String getKey() {
        return "equityChart";
    }

    public JSONObject getInitializationData() throws Exception {
        JSONObject data = new JSONObject();
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

