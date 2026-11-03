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
 *  jakarta.servlet.Servlet
 *  net.xeoh.plugins.base.annotations.PluginImplementation
 *  net.xeoh.plugins.base.annotations.meta.Author
 *  org.eclipse.jetty.server.Handler
 *  org.eclipse.jetty.servlet.ServletContextHandler
 *  org.eclipse.jetty.servlet.ServletHolder
 *  org.json.JSONObject
 */
package com.strategyquant.plugin.Results.impl.SourceCode;

import com.strategyquant.plugin.Results.impl.SourceCode.SourceCodeServlet;
import com.strategyquant.pluginlib.annotations.Category;
import com.strategyquant.pluginlib.annotations.License;
import com.strategyquant.pluginlib.annotations.Name;
import com.strategyquant.pluginlib.annotations.ShortDesc;
import com.strategyquant.pluginlib.program.IProgram;
import com.strategyquant.pluginlib.program.Program;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.results.AbstractResultsPlugin;
import jakarta.servlet.Servlet;
import java.util.Map;
import net.xeoh.plugins.base.annotations.PluginImplementation;
import net.xeoh.plugins.base.annotations.meta.Author;
import org.eclipse.jetty.server.Handler;
import org.eclipse.jetty.servlet.ServletContextHandler;
import org.eclipse.jetty.servlet.ServletHolder;
import org.json.JSONObject;

@Author(name="Tamas Takacs")
@Name(name="SourceCode Plugin - SQ")
@Category(name="Server Extension")
@License(text="")
@ShortDesc(text="SourceCode tab")
@PluginImplementation
public class SourceCodePlugin
extends AbstractResultsPlugin
implements IProgram {
    private ServletContextHandler dataContext;
    private SourceCodeServlet servlet;

    public String getProduct() {
        return "SQUANTAlgoWizardBACKTESTNODEAlgoWizardStandalone";
    }

    public int getPreferredPosition() {
        return 0;
    }

    public void initPlugin() throws Exception {
        Program.register((String)"ResultsSourceCode", (IProgram)this);
        SourceCodeServlet.canonicalizeStoredType();
    }

    private SourceCodeServlet servlet() {
        if (this.servlet == null) {
            this.servlet = new SourceCodeServlet(this.rgProvider);
        }
        return this.servlet;
    }

    public Object call(String methodName, Object ... parameters) throws Exception {
        return this.servlet().execute(methodName, parameters == null ? null : (Map)parameters[0], null);
    }

    public Handler getHandler() {
        if (this.dataContext == null) {
            this.dataContext = new ServletContextHandler(1);
            this.dataContext.setContextPath("/sourcecode/");
            this.dataContext.addServlet(new ServletHolder((Servlet)this.servlet()), "/*");
        }
        return this.dataContext;
    }

    public boolean containsResult(ResultsGroup rg) {
        return true;
    }

    public String getKey() {
        return "sourceCode";
    }

    public JSONObject getInitializationData() throws Exception {
        JSONObject data = new JSONObject();
        data.put("engineTypes", (Object)this.servlet().onList());
        data.put("mmTypes", (Object)this.servlet().onListMM());
        return data;
    }
}

