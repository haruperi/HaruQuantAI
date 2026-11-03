/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.pluginlib.SQPluginManager
 *  com.strategyquant.pluginlib.annotations.Category
 *  com.strategyquant.pluginlib.annotations.License
 *  com.strategyquant.pluginlib.annotations.Name
 *  com.strategyquant.pluginlib.annotations.ShortDesc
 *  com.strategyquant.tradinglib.crosscheck.CrossCheckComparator
 *  com.strategyquant.tradinglib.crosscheck.ICrossCheck
 *  com.strategyquant.tradinglib.project.ProjectConfigHelper
 *  com.strategyquant.tradinglib.servlet.IServletPlugin
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
package com.strategyquant.plugin.Settings.impl.CrossChecks;

import com.strategyquant.lib.L;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.plugin.Settings.impl.CrossChecks.CrossChecksServlet;
import com.strategyquant.pluginlib.SQPluginManager;
import com.strategyquant.pluginlib.annotations.Category;
import com.strategyquant.pluginlib.annotations.License;
import com.strategyquant.pluginlib.annotations.Name;
import com.strategyquant.pluginlib.annotations.ShortDesc;
import com.strategyquant.tradinglib.crosscheck.CrossCheckComparator;
import com.strategyquant.tradinglib.crosscheck.ICrossCheck;
import com.strategyquant.tradinglib.project.ProjectConfigHelper;
import com.strategyquant.tradinglib.servlet.IServletPlugin;
import com.strategyquant.tradinglib.task.settings.ISettingTabPlugin;
import com.strategyquant.tradinglib.task.settings.TaskSettingsData;
import com.strategyquant.tradinglib.taskImpl.ISQTask;
import jakarta.servlet.Servlet;
import java.io.Serializable;
import java.util.ArrayList;
import java.util.Comparator;
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

@Author(name="Tomas Brynda")
@Name(name="Cross checks setting plugin")
@Category(name="Settings")
@License(text="")
@ShortDesc(text="NA")
@PluginImplementation
public class CrossChecksPlugin
implements ISettingTabPlugin,
IServletPlugin {
    public static final Logger Log = LoggerFactory.getLogger(CrossChecksPlugin.class);
    private static final String tabTitle = "Cross checks";
    private static final CrossCheckComparator csComparator = new CrossCheckComparator();
    private ServletContextHandler dataContext;
    private CrossChecksServlet servlet;

    public Handler getHandler() {
        if (this.dataContext == null) {
            this.servlet = new CrossChecksServlet();
            this.dataContext = new ServletContextHandler(1);
            this.dataContext.setContextPath("/crosschecks/");
            this.dataContext.addServlet(new ServletHolder((Servlet)this.servlet), "/*");
        }
        return this.dataContext;
    }

    public String getProduct() {
        return "SQUANT";
    }

    public int getPreferredPosition() {
        return 60;
    }

    public void initPlugin() throws Exception {
    }

    public void readSettings(String projectName, ISQTask task, Element elSettings, TaskSettingsData data) {
        try {
            Element elCrossChecks = XMLUtil.tryAddElement((Element)elSettings, (String)this.getSettingName());
            boolean globalCCUse = XMLUtil.elementIs((Element)elCrossChecks, (String)"use");
            boolean evaluateAll = XMLUtil.elementIs((Element)elCrossChecks, (String)"evaluateAll");
            ArrayList<ICrossCheck> crossChecks = new ArrayList<ICrossCheck>();
            if (globalCCUse) {
                String engineKey = ProjectConfigHelper.getEngineKey((Element)elSettings);
                if (engineKey == null) {
                    throw new Exception(L.t((String)"Engine cannot be resolved from project settings.", (Object[])new Object[0]));
                }
                for (Element elMethod : elCrossChecks.getChildren()) {
                    String crossCheckName = elMethod.getName();
                    try {
                        boolean ccUse = XMLUtil.elementIs((Element)elMethod, (String)"use");
                        if (!ccUse || !MainApp.getLicenseInfo().isProEdition()) continue;
                        ICrossCheck crossCheck = this.getCrossCheckPlugin(elMethod.getName());
                        if (crossCheck != null) {
                            if (!SQUtils.checkEngine((String)engineKey, (String)crossCheck.forEngine())) {
                                Log.info("Cross check '{}' is not compatible with engine '{}', supported engines '{}'. Skipping!!!", new Object[]{crossCheck.getName(), engineKey, crossCheck.forEngine()});
                                continue;
                            }
                            crossCheck.readSettings(elMethod, data);
                            crossChecks.add(crossCheck);
                            continue;
                        }
                        Log.error("Cannot find cross check plugin '" + elMethod.getName() + "'");
                    }
                    catch (Exception e) {
                        String error = L.t((String)"Cannot load settings of Cross check '%s'.", (Object[])new Object[]{crossCheckName}) + " " + e.getMessage();
                        Log.error(projectName + " - " + error, (Throwable)e);
                        data.addError(tabTitle, null, error);
                    }
                }
            }
            data.addParam("UseRobustnessTests", (Serializable)Boolean.valueOf(MainApp.getLicenseInfo() != null && MainApp.getLicenseInfo().isProEdition() ? globalCCUse : false));
            data.addParam("CrossChecks.EvaluateAll", (Serializable)Boolean.valueOf(evaluateAll));
            crossChecks.sort((Comparator<ICrossCheck>)csComparator);
            data.addParam("CrossChecks", crossChecks);
        }
        catch (Exception e) {
            String error = L.t((String)"Cannot load CrossChecks settings. %s", (Object[])new Object[0]) + " " + e.getMessage();
            Log.error(error, (Throwable)e);
            data.addError(tabTitle, null, error);
        }
    }

    private ICrossCheck getCrossCheckPlugin(String name) {
        ArrayList plugins = SQPluginManager.getPlugins(ICrossCheck.class);
        for (int i = 0; i < plugins.size(); ++i) {
            if (!((ICrossCheck)plugins.get(i)).getSettingName().equals(name)) continue;
            return ((ICrossCheck)plugins.get(i)).clone(null);
        }
        return null;
    }

    public void getStrategyConfigSettings(Element elSettings, JSONArray settingsArray) throws Exception {
        ArrayList plugins = SQPluginManager.getPlugins(ICrossCheck.class);
        Element elCrossChecks = XMLUtil.tryAddElement((Element)elSettings, (String)this.getSettingName());
        boolean globalCCUse = XMLUtil.elementIs((Element)elCrossChecks, (String)"use");
        for (int i = 0; i < plugins.size(); ++i) {
            ICrossCheck cs = (ICrossCheck)plugins.get(i);
            String settings = "Not used";
            if (globalCCUse) {
                for (Element elMethod : elCrossChecks.getChildren()) {
                    String crossCheckName = elMethod.getName();
                    if (!cs.getSettingName().equals(crossCheckName)) continue;
                    try {
                        ICrossCheck crossCheck = this.getCrossCheckPlugin(elMethod.getName());
                        settings = crossCheck.printSettings(elMethod);
                        if (settings == null) {
                            throw new NullPointerException();
                        }
                    }
                    catch (Exception e) {
                        settings = "N/A";
                    }
                    break;
                }
            }
            settingsArray.put((Object)new JSONObject().put("key", (Object)cs.getName()).put("value", (Object)settings));
        }
    }

    public String getSettingName() {
        return "CrossChecks";
    }

    public String getName() {
        return L.tsq((String)tabTitle);
    }

    public JSONObject getInitializationData() throws Exception {
        JSONObject data = new JSONObject();
        data.put("crosschecks", (Object)this.servlet.list());
        return data;
    }
}

