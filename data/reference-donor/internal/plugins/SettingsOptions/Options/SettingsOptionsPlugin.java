/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.pluginlib.annotations.Category
 *  com.strategyquant.pluginlib.annotations.License
 *  com.strategyquant.pluginlib.annotations.Name
 *  com.strategyquant.pluginlib.annotations.ShortDesc
 *  com.strategyquant.tradinglib.TradingOption
 *  com.strategyquant.tradinglib.options.TradingOptions
 *  com.strategyquant.tradinglib.options.TradingOptionsList
 *  com.strategyquant.tradinglib.options.parameters.ReservedBars
 *  com.strategyquant.tradinglib.propertygrid.IPGParameter
 *  com.strategyquant.tradinglib.servlet.IServletPlugin
 *  com.strategyquant.tradinglib.simulator.Engines
 *  com.strategyquant.tradinglib.strategyConfig.StrategyConfig
 *  com.strategyquant.tradinglib.task.settings.ISettingTabPlugin
 *  com.strategyquant.tradinglib.task.settings.TaskSettingsData
 *  com.strategyquant.tradinglib.taskImpl.ISQTask
 *  jakarta.servlet.Servlet
 *  net.xeoh.plugins.base.annotations.PluginImplementation
 *  net.xeoh.plugins.base.annotations.meta.Author
 *  org.eclipse.jetty.server.Handler
 *  org.eclipse.jetty.servlet.ServletContextHandler
 *  org.eclipse.jetty.servlet.ServletHolder
 *  org.jdom2.Element
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Settings.impl.Options;

import com.strategyquant.lib.L;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.plugin.Settings.impl.Options.SettingsOptionsServlet;
import com.strategyquant.pluginlib.annotations.Category;
import com.strategyquant.pluginlib.annotations.License;
import com.strategyquant.pluginlib.annotations.Name;
import com.strategyquant.pluginlib.annotations.ShortDesc;
import com.strategyquant.tradinglib.TradingOption;
import com.strategyquant.tradinglib.options.TradingOptions;
import com.strategyquant.tradinglib.options.TradingOptionsList;
import com.strategyquant.tradinglib.options.parameters.ReservedBars;
import com.strategyquant.tradinglib.propertygrid.IPGParameter;
import com.strategyquant.tradinglib.servlet.IServletPlugin;
import com.strategyquant.tradinglib.simulator.Engines;
import com.strategyquant.tradinglib.strategyConfig.StrategyConfig;
import com.strategyquant.tradinglib.task.settings.ISettingTabPlugin;
import com.strategyquant.tradinglib.task.settings.TaskSettingsData;
import com.strategyquant.tradinglib.taskImpl.ISQTask;
import jakarta.servlet.Servlet;
import java.io.Serializable;
import java.util.ArrayList;
import net.xeoh.plugins.base.annotations.PluginImplementation;
import net.xeoh.plugins.base.annotations.meta.Author;
import org.eclipse.jetty.server.Handler;
import org.eclipse.jetty.servlet.ServletContextHandler;
import org.eclipse.jetty.servlet.ServletHolder;
import org.jdom2.Element;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@Author(name="Tamas Takacs")
@Name(name="Options plugin")
@Category(name="Settings")
@License(text="")
@ShortDesc(text="Short description")
@PluginImplementation
public class SettingsOptionsPlugin
implements ISettingTabPlugin,
IServletPlugin {
    public static final Logger Log = LoggerFactory.getLogger(SettingsOptionsPlugin.class);
    private ServletContextHandler dataContext;

    public Handler getHandler() {
        if (this.dataContext == null) {
            this.dataContext = new ServletContextHandler(1);
            this.dataContext.setContextPath("/options/");
            this.dataContext.addServlet(new ServletHolder((Servlet)new SettingsOptionsServlet()), "/*");
        }
        return this.dataContext;
    }

    public String getProduct() {
        return "SQUANTAlgoWizardAlgoWizardStandaloneAlgoWizardCloudBACKTESTNODE";
    }

    public int getPreferredPosition() {
        return 50;
    }

    public void initPlugin() throws Exception {
    }

    private void fixSettings(Element elSettings) {
        Element elOptions = XMLUtil.tryAddElement((Element)elSettings, (String)this.getSettingName());
        this.fixBuildTradingOptions(elOptions);
    }

    private void fixBuildTradingOptions(Element elOptions) {
    }

    public void readSettings(String projectName, ISQTask task, Element elSettings, TaskSettingsData settingsData) {
        this.fixSettings(elSettings);
        Element elOptions = null;
        try {
            elOptions = XMLUtil.getChildElem((Element)elSettings, (String)"Options");
        }
        catch (Exception e) {
            settingsData.addError(this.getSettingName(), null, L.t((String)"Options settings not found in XML config", (Object[])new Object[0]));
            return;
        }
        try {
            TradingOptions options = TradingOptionsList.getInstance().parseOptionsFromXml(elOptions.getChild("BuildTradingOptions"));
            settingsData.addParam("TradingOptions", (Serializable)options);
            for (int a = 0; a < options.size(); ++a) {
                TradingOption option = (TradingOption)options.get(a);
                if (option == null || !(option instanceof ReservedBars)) continue;
                settingsData.addParam("ReservedBars", (Serializable)Integer.valueOf(option.isUsed() ? ((ReservedBars)option).ReservedBars : 0));
                break;
            }
        }
        catch (Exception e) {
            settingsData.addError(this.getSettingName(), null, "Cannot parse Options settings - " + e.getMessage());
            return;
        }
    }

    public void getStrategyConfigSettings(Element elSettings, JSONArray settingsArray) throws Exception {
        Element elOptions = null;
        try {
            elOptions = XMLUtil.getChildElem((Element)elSettings, (String)"Options");
        }
        catch (Exception e) {
            return;
        }
        TradingOptions tradingOptions = TradingOptionsList.getInstance().parseOptionsFromXml(elOptions.getChild("BuildTradingOptions"));
        String engineKey = Engines.getEngineKey((String)StrategyConfig.getEngineName((Element)elSettings));
        for (TradingOption option : tradingOptions) {
            ArrayList params = option.getParams();
            for (IPGParameter parameter : params) {
                try {
                    if (engineKey != null && !this.isOfferedForEngine(parameter, engineKey)) continue;
                    settingsArray.put((Object)new JSONObject().put("key", (Object)parameter.getName()).put("value", (Object)parameter.print()));
                }
                catch (Exception e) {
                    Log.error("Error while printing option value. Exc. ", (Throwable)e);
                }
            }
        }
    }

    private boolean isOfferedForEngine(IPGParameter parameter, String engineKey) {
        String allowedEngines = parameter.getEngine();
        if (allowedEngines == null || allowedEngines.isEmpty()) {
            return true;
        }
        return SQUtils.checkEngine((String)engineKey, (String)allowedEngines);
    }

    public String getSettingName() {
        return "Options";
    }

    public String getName() {
        return L.tsq((String)"Trading options");
    }

    public JSONObject getInitializationData() throws Exception {
        return null;
    }
}

