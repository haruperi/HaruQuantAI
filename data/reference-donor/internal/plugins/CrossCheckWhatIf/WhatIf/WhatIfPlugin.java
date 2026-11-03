/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.gridlib.client.GridJob
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SettingsMap
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.tradinglib.ChartSetup
 *  com.strategyquant.tradinglib.DatabankColumn
 *  com.strategyquant.tradinglib.Directions
 *  com.strategyquant.tradinglib.Order
 *  com.strategyquant.tradinglib.OrdersList
 *  com.strategyquant.tradinglib.PlTypes
 *  com.strategyquant.tradinglib.Result
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.SampleTypes
 *  com.strategyquant.tradinglib.WhatIf
 *  com.strategyquant.tradinglib.conditions.Condition
 *  com.strategyquant.tradinglib.crosscheck.CrossCheckDataNotExistException
 *  com.strategyquant.tradinglib.crosscheck.CrossCheckMethod
 *  com.strategyquant.tradinglib.crosscheck.ICrossCheck
 *  com.strategyquant.tradinglib.databank.DatabankColumns
 *  com.strategyquant.tradinglib.engine.ChartSetups
 *  com.strategyquant.tradinglib.project.ILastEventListener
 *  com.strategyquant.tradinglib.project.ProjectConfigHelper
 *  com.strategyquant.tradinglib.servlet.IServletPlugin
 *  com.strategyquant.tradinglib.task.settings.TaskSettingsData
 *  jakarta.servlet.Servlet
 *  net.xeoh.plugins.base.annotations.PluginImplementation
 *  org.eclipse.jetty.server.Handler
 *  org.eclipse.jetty.servlet.ServletContextHandler
 *  org.eclipse.jetty.servlet.ServletHolder
 *  org.jdom2.Element
 */
package com.strategyquant.plugin.CrossCheck.impl.WhatIf;

import com.strategyquant.gridlib.client.GridJob;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SettingsMap;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.plugin.CrossCheck.impl.WhatIf.WhatIfServlet;
import com.strategyquant.tradinglib.ChartSetup;
import com.strategyquant.tradinglib.DatabankColumn;
import com.strategyquant.tradinglib.Directions;
import com.strategyquant.tradinglib.Order;
import com.strategyquant.tradinglib.OrdersList;
import com.strategyquant.tradinglib.PlTypes;
import com.strategyquant.tradinglib.Result;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.SampleTypes;
import com.strategyquant.tradinglib.WhatIf;
import com.strategyquant.tradinglib.conditions.Condition;
import com.strategyquant.tradinglib.crosscheck.CrossCheckDataNotExistException;
import com.strategyquant.tradinglib.crosscheck.CrossCheckMethod;
import com.strategyquant.tradinglib.crosscheck.ICrossCheck;
import com.strategyquant.tradinglib.databank.DatabankColumns;
import com.strategyquant.tradinglib.engine.ChartSetups;
import com.strategyquant.tradinglib.project.ILastEventListener;
import com.strategyquant.tradinglib.project.ProjectConfigHelper;
import com.strategyquant.tradinglib.servlet.IServletPlugin;
import com.strategyquant.tradinglib.task.settings.TaskSettingsData;
import jakarta.servlet.Servlet;
import java.util.ArrayList;
import net.xeoh.plugins.base.annotations.PluginImplementation;
import org.eclipse.jetty.server.Handler;
import org.eclipse.jetty.servlet.ServletContextHandler;
import org.eclipse.jetty.servlet.ServletHolder;
import org.jdom2.Element;

@PluginImplementation
public class WhatIfPlugin
extends CrossCheckMethod
implements IServletPlugin {
    private ServletContextHandler dataContext;

    public ICrossCheck clone(SettingsMap settings) {
        WhatIfPlugin crossCheck = new WhatIfPlugin();
        crossCheck.settings = settings != null ? settings : this.settings.clone();
        return crossCheck;
    }

    public String getName() {
        return NameWhatIf;
    }

    public String getShortName() {
        return L.t((String)"What If", (Object[])new Object[0]);
    }

    public String getDescription() {
        return L.tsq((String)"This cross check allows you to apply various What-If scenarios to the list of orders, for example what if the strategy trades only on particular days.<br/>It creates simulations by filtering the existing orders from the main backtest, it doesn't retest the strategies again.");
    }

    public String getSettingName() {
        return "WhatIf";
    }

    public int getType() {
        return 0;
    }

    public int getPreferredPosition() {
        return 220;
    }

    public Handler getHandler() {
        if (this.dataContext == null) {
            this.dataContext = new ServletContextHandler(1);
            this.dataContext.setContextPath("/whatIf/");
            this.dataContext.addServlet(new ServletHolder((Servlet)new WhatIfServlet()), "/*");
        }
        return this.dataContext;
    }

    public void fixSettings(Element elSettings) {
        super.fixSettings(elSettings);
        Element elMethodSettings = elSettings.getChild("Settings");
        XMLUtil.tryAddElement((Element)elMethodSettings, (String)"Methods");
    }

    public void readSettings(Element elSettings, TaskSettingsData data) throws Exception {
        this.fixSettings(elSettings);
        Element elMethodSettings = elSettings.getChild("Settings");
        this.settings.set("WhatIfMethods", (Object)ProjectConfigHelper.getWhatIfMethods((Element)elMethodSettings.getChild("Methods")));
        this.readConditions(elSettings);
    }

    public boolean runTest(ResultsGroup rg, int index, double globalATR, GridJob gridJob, boolean singleThreaded, ILastEventListener lastEventListener, String strategyName) throws Exception {
        this.checkSpecialTrialLimitation();
        ArrayList methods = (ArrayList)this.settings.get("WhatIfMethods");
        String mainResultKey = rg.getMainResultKey();
        Result result = rg.subResult(mainResultKey);
        SettingsMap settings = result.getSettings();
        SettingsMap clonedSettings = this.cloneSettings(settings);
        OrdersList orders = rg.orders();
        OrdersList ordersSimulation = orders.filterWithClone(mainResultKey, (byte)0, (byte)127);
        for (int m = 0; m < methods.size(); ++m) {
            ((WhatIf)methods.get(m)).filter(ordersSimulation);
        }
        String ccSetupName = "CrossCheck_WhatIf";
        for (int i = 0; i < ordersSimulation.size(); ++i) {
            Order o = ordersSimulation.get(i);
            o.SetupName = ccSetupName;
            o.IsInPortfolio = 0;
        }
        rg.addSubresult(ccSetupName, clonedSettings);
        orders.addAll(ordersSimulation);
        Result ccResult = rg.subResult(ccSetupName);
        ccResult.setSpecial(true);
        ccResult.computeAllStats(rg.specialValues(), rg.getOOS());
        if (this.backtestProgressListener != null) {
            this.backtestProgressListener.increaseProgressStep();
        }
        return this.checkConditions(rg, index);
    }

    public boolean doesRetest() {
        return false;
    }

    public boolean doesForEverySetup() {
        return false;
    }

    public ChartSetups getChartSetups(ChartSetup mainChartSetup) {
        return null;
    }

    public String printSettings(Element elMethod) throws Exception {
        if (elMethod == null) {
            throw new NullPointerException();
        }
        if (!XMLUtil.elementIs((Element)elMethod, (String)"use")) {
            return "Not used";
        }
        Element settingsEl = elMethod.getChild("Settings");
        String settings = "";
        ArrayList methods = ProjectConfigHelper.getWhatIfMethods((Element)settingsEl.getChild("Methods"));
        for (int i = 0; i < methods.size(); ++i) {
            WhatIf method = (WhatIf)methods.get(i);
            settings = settings + method.printFormatedName();
            settings = settings + "\n";
        }
        settings = settings + "\n";
        Element conditionsEl = elMethod.getChild("AcceptanceSettings").getChild("Conditions");
        ArrayList conditions = ProjectConfigHelper.getConditions((Element)conditionsEl);
        for (int i = 0; i < conditions.size(); ++i) {
            Condition condition = (Condition)conditions.get(i);
            if (!condition.isUsed()) continue;
            settings = settings + condition.toString();
            settings = settings + "\n";
        }
        return settings;
    }

    public int getBadStrategyReason() {
        return 10037;
    }

    public int getNumberOfSimulations() {
        return 0;
    }

    public double getStatsValue(ResultsGroup rg, String columnName, Element elColumn, Object ... params) throws Exception {
        if (!rg.getResultKeys().contains("CrossCheck_WhatIf")) {
            throw new CrossCheckDataNotExistException(this.getName());
        }
        byte direction = XMLUtil.getByteAttr((Element)elColumn, (String)"direction", (byte)0);
        byte sampleType = this.getSampleType(elColumn, params);
        byte plType = XMLUtil.getByteAttr((Element)elColumn, (String)"plType", (byte)10);
        DatabankColumn column = (DatabankColumn)DatabankColumns.get().findClassByName(columnName);
        return column.getNumericValue(rg, "CrossCheck_WhatIf", direction, plType, sampleType);
    }

    public String printSpecialValue(ResultsGroup rg, String columnName, Element elColumn, Object ... params) throws Exception {
        if (!rg.getResultKeys().contains("CrossCheck_WhatIf")) {
            throw new CrossCheckDataNotExistException(this.getName());
        }
        byte direction = XMLUtil.getByteAttr((Element)elColumn, (String)"direction", (byte)0);
        byte sampleType = this.getSampleType(elColumn, params);
        byte plType = XMLUtil.getByteAttr((Element)elColumn, (String)"plType", (byte)10);
        DatabankColumn column = (DatabankColumn)DatabankColumns.get().findClassByName(columnName);
        return column.getValue(rg, rg.getMainResultKey(), direction, plType, sampleType);
    }

    public String getColumnTitle(String columnName, Element elColumn, Object ... params) {
        byte direction = XMLUtil.getByteAttr((Element)elColumn, (String)"direction", (byte)0);
        byte sampleType = this.getSampleType(elColumn, params);
        byte plType = XMLUtil.getByteAttr((Element)elColumn, (String)"plType", (byte)10);
        String title = this.getColumnTitleTemplate();
        title = title.replace("#columnName#", columnName);
        title = title.replace(", #sampleType#", sampleType == 127 ? "" : ", " + SampleTypes.typeToString((byte)sampleType));
        title = title.replace(", #direction#", direction == 0 ? "" : ", " + Directions.typeToString((byte)direction));
        title = title.replace(", #plType#", plType == 10 ? "" : ", " + PlTypes.typeToString((byte)plType));
        return title;
    }

    public String getColumnTitleTemplate() {
        return "#columnName# (" + this.getShortName() + ", #sampleType#, #direction#, #plType#)";
    }

    public boolean doesCreateSubjobs() {
        return false;
    }

    public boolean hasStatsValue(ResultsGroup rg, String columnName, Element elColumn, Object ... params) throws Exception {
        return rg.getResultKeys().contains("CrossCheck_WhatIf");
    }

    public boolean disabledForSpecialTrial() {
        return true;
    }
}

