package com.strategyquant.plugin.Databank.impl.FilterByCorrelation;

import org.eclipse.jetty.server.Handler;
import org.eclipse.jetty.servlet.ServletContextHandler;
import org.eclipse.jetty.servlet.ServletHolder;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.strategyquant.pluginlib.annotations.Category;
import com.strategyquant.pluginlib.annotations.License;
import com.strategyquant.pluginlib.annotations.Name;
import com.strategyquant.pluginlib.annotations.ShortDesc;
import com.strategyquant.tradinglib.servlet.IServletPlugin;

import net.xeoh.plugins.base.annotations.PluginImplementation;
import net.xeoh.plugins.base.annotations.meta.Author;

import com.strategyquant.lib.constants.*;

@Author(name = "Tomas Brynda")
@Name(name = "Filter by correlation")
@Category(name = "DatabankActions")
@License(text = "")
@ShortDesc(text = "")
@PluginImplementation
public class DatabankFilterByCorrelationPlugin implements IServletPlugin {

    private static final Logger Log = LoggerFactory.getLogger(DatabankFilterByCorrelationPlugin.class);
    private ServletContextHandler connectionContext;

    //------------------------------------------------------------------------
    //------------------------------------------------------------------------
    //------------------------------------------------------------------------

    @Override
    public String getProduct() {
        return SQConst.CODE_SQ;
    }

    //------------------------------------------------------------------------

    @Override
    public int getPreferredPosition() {
        return 0;
    }

    //------------------------------------------------------------------------

    @Override
    public void initPlugin() throws Exception {
    }

    //------------------------------------------------------------------------

    @Override
    public Handler getHandler() {
        if(connectionContext == null){
            connectionContext = new ServletContextHandler(ServletContextHandler.SESSIONS);
            connectionContext.setContextPath("/filterByCorrelation/");
            connectionContext.addServlet(new ServletHolder(new DatabankFilterByCorrelationServlet()),"/*");
        }
        return connectionContext;
    }
}