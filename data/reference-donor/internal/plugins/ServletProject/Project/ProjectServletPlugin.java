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
 *  com.strategyquant.tradinglib.servlet.IServletPlugin
 *  jakarta.servlet.Servlet
 *  net.xeoh.plugins.base.annotations.PluginImplementation
 *  net.xeoh.plugins.base.annotations.meta.Author
 *  org.eclipse.jetty.server.Handler
 *  org.eclipse.jetty.servlet.ServletContextHandler
 *  org.eclipse.jetty.servlet.ServletHolder
 */
package com.strategyquant.plugin.Servlet.impl.Project;

import com.strategyquant.plugin.Servlet.impl.Project.ProjectServlet;
import com.strategyquant.pluginlib.annotations.Category;
import com.strategyquant.pluginlib.annotations.License;
import com.strategyquant.pluginlib.annotations.Name;
import com.strategyquant.pluginlib.annotations.ShortDesc;
import com.strategyquant.pluginlib.program.IProgram;
import com.strategyquant.pluginlib.program.Program;
import com.strategyquant.tradinglib.servlet.IServletPlugin;
import jakarta.servlet.Servlet;
import java.util.Map;
import net.xeoh.plugins.base.annotations.PluginImplementation;
import net.xeoh.plugins.base.annotations.meta.Author;
import org.eclipse.jetty.server.Handler;
import org.eclipse.jetty.servlet.ServletContextHandler;
import org.eclipse.jetty.servlet.ServletHolder;

@Author(name="Tomas Brynda")
@Name(name="Project Servlet Plugin - SQ")
@Category(name="Server Extension")
@License(text="")
@ShortDesc(text="Server API for projects management")
@PluginImplementation
public class ProjectServletPlugin
implements IServletPlugin,
IProgram {
    private ServletContextHandler dataContext;
    private ProjectServlet servlet;

    public String getProduct() {
        return "SQUANTAlgoWizard";
    }

    public int getPreferredPosition() {
        return 0;
    }

    public void initPlugin() throws Exception {
        this.servlet = new ProjectServlet();
        Program.register((String)"Project", (IProgram)this);
    }

    public Handler getHandler() {
        if (this.dataContext == null) {
            this.dataContext = new ServletContextHandler(1);
            this.dataContext.setContextPath("/project/");
            this.dataContext.addServlet(new ServletHolder((Servlet)this.servlet), "/*");
        }
        return this.dataContext;
    }

    public Object call(String methodName, Object ... parameters) throws Exception {
        return this.servlet.execute(methodName, parameters == null ? null : (Map)parameters[0], null);
    }
}

