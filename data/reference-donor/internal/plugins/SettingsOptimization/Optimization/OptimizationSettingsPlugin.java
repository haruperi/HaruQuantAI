/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.pluginlib.annotations.Category
 *  com.strategyquant.pluginlib.annotations.License
 *  com.strategyquant.pluginlib.annotations.Name
 *  com.strategyquant.pluginlib.annotations.ShortDesc
 *  com.strategyquant.tradinglib.optimization.OptimizationSettings
 *  com.strategyquant.tradinglib.optimization.Parameter
 *  com.strategyquant.tradinglib.optimization.ParametersSettings
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
package com.strategyquant.plugin.Settings.impl.Optimization;

import com.strategyquant.lib.L;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.plugin.Settings.impl.Optimization.OptimizationServlet;
import com.strategyquant.pluginlib.annotations.Category;
import com.strategyquant.pluginlib.annotations.License;
import com.strategyquant.pluginlib.annotations.Name;
import com.strategyquant.pluginlib.annotations.ShortDesc;
import com.strategyquant.tradinglib.optimization.OptimizationSettings;
import com.strategyquant.tradinglib.optimization.Parameter;
import com.strategyquant.tradinglib.optimization.ParametersSettings;
import com.strategyquant.tradinglib.servlet.IServletPlugin;
import com.strategyquant.tradinglib.task.settings.ISettingTabPlugin;
import com.strategyquant.tradinglib.task.settings.TaskSettingsData;
import com.strategyquant.tradinglib.taskImpl.ISQTask;
import jakarta.servlet.Servlet;
import java.io.Serializable;
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
@Name(name="Optimization setting plugin")
@Category(name="Settings")
@License(text="")
@ShortDesc(text="Short description")
@PluginImplementation
public class OptimizationSettingsPlugin
implements ISettingTabPlugin,
IServletPlugin {
    public static final Logger Log = LoggerFactory.getLogger(OptimizationSettingsPlugin.class);
    private ServletContextHandler connectionContext;

    public Handler getHandler() {
        if (this.connectionContext == null) {
            this.connectionContext = new ServletContextHandler(1);
            this.connectionContext.setContextPath("/optimization/");
            this.connectionContext.addServlet(new ServletHolder((Servlet)new OptimizationServlet()), "/*");
        }
        return this.connectionContext;
    }

    public String getProduct() {
        return "SQMANAGERSQUANTSQTRADERTESTAPPSQEDITOR";
    }

    public int getPreferredPosition() {
        return 5;
    }

    public void initPlugin() throws Exception {
    }

    private void fixSettings(Element elSettings) {
        Element elAutomaticSettings;
        Element elOptimizationMethod;
        Element elSource;
        String sourceType;
        Element elOptimization = XMLUtil.tryAddElement((Element)elSettings, (String)this.getSettingName());
        String optimizationType = elOptimization.getAttributeValue("type");
        if (optimizationType == null) {
            elOptimization.setAttribute("type", String.valueOf(1));
            Element elSimpleOptimization = XMLUtil.tryAddElement((Element)elOptimization, (String)"SimpleOptimization");
            elSimpleOptimization.setAttribute("type", String.valueOf(10));
        }
        if ((sourceType = (elSource = XMLUtil.tryAddElement((Element)elOptimization, (String)"Source")).getAttributeValue("type")) == null) {
            elSource.setAttribute("type", String.valueOf(1));
        }
        if ((elOptimizationMethod = XMLUtil.tryAddElement((Element)elOptimization, (String)"OptimizationMethod")).getAttributeValue("settings") == null) {
            elOptimizationMethod.setAttribute("settings", "automatic");
        }
        if (elOptimizationMethod.getAttributeValue("method") == null) {
            elOptimizationMethod.setAttribute("method", "brute-force");
        }
        if (elOptimizationMethod.getAttributeValue("maxSteps") == null) {
            elOptimizationMethod.setAttribute("maxSteps", "20");
        }
        if (elOptimizationMethod.getAttributeValue("symmetricVariables") == null) {
            elOptimizationMethod.setAttribute("symmetricVariables", "true");
        }
        if (elOptimizationMethod.getAttributeValue("symmetryDisabled") == null) {
            elOptimizationMethod.setAttribute("symmetryDisabled", "false");
        }
        if ((elAutomaticSettings = XMLUtil.tryAddElement((Element)elOptimization, (String)"AutomaticSettings")).getAttributeValue("distribution") == null) {
            elAutomaticSettings.setAttribute("distribution", "20");
        }
        if (elAutomaticSettings.getAttributeValue("maxSteps") == null) {
            elAutomaticSettings.setAttribute("maxSteps", "4");
        }
        Element elWhatToParametrize = XMLUtil.tryAddElement((Element)elOptimization, (String)"WhatToParametrize");
        XMLUtil.tryAddBooleanNode((Element)elWhatToParametrize, (String)"Periods", (boolean)true);
        XMLUtil.tryAddBooleanNode((Element)elWhatToParametrize, (String)"Shifts", (boolean)true);
        XMLUtil.tryAddBooleanNode((Element)elWhatToParametrize, (String)"ExitParamsUsed", (boolean)true);
        XMLUtil.tryAddBooleanNode((Element)elWhatToParametrize, (String)"ExitParamsUnused", (boolean)true);
        XMLUtil.tryAddBooleanNode((Element)elWhatToParametrize, (String)"Constants", (boolean)true);
        XMLUtil.tryAddBooleanNode((Element)elWhatToParametrize, (String)"OtherParams", (boolean)true);
        XMLUtil.tryAddBooleanNode((Element)elWhatToParametrize, (String)"BooleanParams", (boolean)true);
        XMLUtil.tryAddBooleanNode((Element)elWhatToParametrize, (String)"TradingOptions", (boolean)true);
        Element elManualSettings = XMLUtil.tryAddElement((Element)elOptimization, (String)"ManualSettings");
        XMLUtil.tryAddElement((Element)elManualSettings, (String)"Params");
        XMLUtil.tryAddElement((Element)elManualSettings, (String)"SpecialRelations");
    }

    /*
     * Enabled force condition propagation
     * Lifted jumps to return sites
     */
    public void readSettings(String projectName, ISQTask task, Element elSettings, TaskSettingsData data) {
        this.fixSettings(elSettings);
        OptimizationSettings settings = new OptimizationSettings(projectName);
        try {
            settings.setFromXML(elSettings, elSettings.getChild("Optimization"));
            settings.verify();
            data.addParam("OptimizationSettings", (Serializable)settings);
            data.addParam("DatabankTarget", (Serializable)settings.outputDatabank);
        }
        catch (Exception e) {
            data.addError(this.getSettingName(), null, e.getMessage());
        }
        Element optimizationElem = null;
        Element optimizationMethodElem = null;
        boolean manualMode = false;
        try {
            optimizationElem = XMLUtil.getChildElem((Element)elSettings, (String)"Optimization");
            optimizationMethodElem = XMLUtil.getChildElem((Element)optimizationElem, (String)"OptimizationMethod");
        }
        catch (Exception e) {
            data.addError(this.getSettingName(), null, e.getMessage());
            return;
        }
        try {
            manualMode = optimizationMethodElem.getAttributeValue("settings").equals("manual");
        }
        catch (Exception e) {
            data.addError(this.getSettingName(), null, "Cannot get Parameter settings type");
            return;
        }
        if (optimizationMethodElem.getAttributeValue("method") == null) {
            data.addError(this.getSettingName(), "method", "Method not set");
            return;
        }
        if (settings.isOptimizationConfigurable()) {
            return;
        }
        if (manualMode) {
            boolean someParamsUsed = false;
            for (Element paramElem : XMLUtil.getNestedElements((Element)optimizationElem, (String)"Param")) {
                boolean use = XMLUtil.elementIs((Element)paramElem, (String)"use");
                String name = paramElem.getAttributeValue("name").trim();
                if (!use) continue;
                someParamsUsed = true;
                try {
                    this.checkParameter(paramElem, data);
                }
                catch (Exception e) {
                    data.addError(this.getSettingName(), "", "Invalid manual settings of Parameter '" + name + "' - " + e.getMessage());
                }
            }
            if (someParamsUsed) return;
        }
        try {
            Element automaticSettingsElem = XMLUtil.getChildElem((Element)optimizationElem, (String)"AutomaticSettings");
            if (XMLUtil.tryGetIntAttr((Element)automaticSettingsElem, (String)"distribution") < 0) {
                data.addError(this.getSettingName(), "distribution", L.t((String)"Cannot get distribution value", (Object[])new Object[0]));
            }
            if (XMLUtil.tryGetIntAttr((Element)automaticSettingsElem, (String)"maxSteps") >= 0) return;
            data.addError(this.getSettingName(), "maxSteps", L.t((String)"Cannot get maxSteps value", (Object[])new Object[0]));
            return;
        }
        catch (Exception e) {
            data.addError(this.getSettingName(), "AutomaticSettings", e.getMessage());
        }
    }

    private void checkParameter(Element paramElem, TaskSettingsData settingsData) throws Exception {
        byte type = Parameter.getType((String)paramElem.getAttributeValue("type"));
        if (type == 4 || type == 1) {
            double start = Double.parseDouble(paramElem.getAttributeValue("start"));
            double stop = Double.parseDouble(paramElem.getAttributeValue("stop"));
            double step = Double.parseDouble(paramElem.getAttributeValue("step"));
            Double.parseDouble(paramElem.getAttributeValue("value"));
            ParametersSettings.checkParamValid((double)start, (double)stop, (double)step);
        } else if (type == 5) {
            int start = (int)Double.parseDouble(paramElem.getAttributeValue("start"));
            int stop = (int)Double.parseDouble(paramElem.getAttributeValue("stop"));
            int step = (int)Double.parseDouble(paramElem.getAttributeValue("step"));
            if (start > stop) {
                throw new Exception(L.t((String)"Start time must be before stop time", (Object[])new Object[0]));
            }
            ParametersSettings.checkTimeParamValid((int)start, (int)stop, (int)step);
        } else {
            paramElem.getAttributeValue("value").equals("true");
        }
    }

    public void getStrategyConfigSettings(Element elSettings, JSONArray settingsArray) throws Exception {
    }

    public String getSettingName() {
        return "Optimization";
    }

    public String getName() {
        return L.tsq((String)"Optimization");
    }

    public JSONObject getInitializationData() throws Exception {
        return null;
    }
}

