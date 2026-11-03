/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.ailib.chat.QProduct
 *  com.strategyquant.ailib.chat.SQAITurns
 *  com.strategyquant.ailib.model.SQAIModelFactory
 *  com.strategyquant.pluginlib.annotations.Category
 *  com.strategyquant.pluginlib.annotations.License
 *  com.strategyquant.pluginlib.annotations.Name
 *  com.strategyquant.pluginlib.annotations.ShortDesc
 *  com.strategyquant.tradinglib.servlet.IServletPlugin
 *  jakarta.servlet.MultipartConfigElement
 *  jakarta.servlet.Servlet
 *  net.xeoh.plugins.base.annotations.PluginImplementation
 *  net.xeoh.plugins.base.annotations.meta.Author
 *  org.eclipse.jetty.server.Handler
 *  org.eclipse.jetty.servlet.ServletContextHandler
 *  org.eclipse.jetty.servlet.ServletHolder
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Servlet.impl.SQAI;

import com.strategyquant.ailib.chat.QProduct;
import com.strategyquant.ailib.chat.SQAITurns;
import com.strategyquant.ailib.model.SQAIModelFactory;
import com.strategyquant.plugin.Servlet.impl.SQAI.SQAIServlet;
import com.strategyquant.pluginlib.annotations.Category;
import com.strategyquant.pluginlib.annotations.License;
import com.strategyquant.pluginlib.annotations.Name;
import com.strategyquant.pluginlib.annotations.ShortDesc;
import com.strategyquant.tradinglib.servlet.IServletPlugin;
import jakarta.servlet.MultipartConfigElement;
import jakarta.servlet.Servlet;
import net.xeoh.plugins.base.annotations.PluginImplementation;
import net.xeoh.plugins.base.annotations.meta.Author;
import org.eclipse.jetty.server.Handler;
import org.eclipse.jetty.servlet.ServletContextHandler;
import org.eclipse.jetty.servlet.ServletHolder;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@Author(name="StrategyQuant")
@Name(name="SQAI Plugin")
@Category(name="Server Extension")
@License(text="")
@ShortDesc(text="AI chat panel backend")
@PluginImplementation
public class SQAIPlugin
implements IServletPlugin {
    private static final Logger Log = LoggerFactory.getLogger((String)"SQAIPlugin");

    public String getProduct() {
        return "SQUANTQDM";
    }

    public int getPreferredPosition() {
        return 0;
    }

    public void initPlugin() throws Exception {
        SQAIModelFactory.initModel();
        SQAITurns.initWakeups();
    }

    public Handler getHandler() {
        try {
            ServletContextHandler ctx = new ServletContextHandler(0);
            ctx.setContextPath("/sqai");
            ServletHolder holder = new ServletHolder("sqai", (Servlet)new SQAIServlet());
            holder.getRegistration().setMultipartConfig(new MultipartConfigElement("./tmp", 0x4000000L, 0x4600000L, 0x100000));
            ctx.addServlet(holder, "/*");
            Log.info("Q backend registered at /sqai for " + QProduct.name());
            return ctx;
        }
        catch (Exception e) {
            Log.error("Failed to initialize SQAI backend", (Throwable)e);
            return null;
        }
    }
}

