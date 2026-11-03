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
 *  com.strategyquant.tradinglib.BadStrategyException
 *  com.strategyquant.tradinglib.CorrelationType
 *  com.strategyquant.tradinglib.Databank
 *  com.strategyquant.tradinglib.conditions.Condition
 *  com.strategyquant.tradinglib.correlation.CorrelationTypes
 *  com.strategyquant.tradinglib.correlation.FitPortfolio
 *  com.strategyquant.tradinglib.customanalysis.CustomAnalysisInfo
 *  com.strategyquant.tradinglib.fitnessfunction.IFitnessFunction
 *  com.strategyquant.tradinglib.project.ProjectConfigHelper
 *  com.strategyquant.tradinglib.project.ProjectEngine
 *  com.strategyquant.tradinglib.project.SQProject
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
package com.strategyquant.plugin.Settings.impl.Rankings;

import com.strategyquant.lib.L;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.plugin.Settings.impl.Rankings.SettingsRankingsServlet;
import com.strategyquant.pluginlib.annotations.Category;
import com.strategyquant.pluginlib.annotations.License;
import com.strategyquant.pluginlib.annotations.Name;
import com.strategyquant.pluginlib.annotations.ShortDesc;
import com.strategyquant.tradinglib.BadStrategyException;
import com.strategyquant.tradinglib.CorrelationType;
import com.strategyquant.tradinglib.Databank;
import com.strategyquant.tradinglib.conditions.Condition;
import com.strategyquant.tradinglib.correlation.CorrelationTypes;
import com.strategyquant.tradinglib.correlation.FitPortfolio;
import com.strategyquant.tradinglib.customanalysis.CustomAnalysisInfo;
import com.strategyquant.tradinglib.fitnessfunction.IFitnessFunction;
import com.strategyquant.tradinglib.project.ProjectConfigHelper;
import com.strategyquant.tradinglib.project.ProjectEngine;
import com.strategyquant.tradinglib.project.SQProject;
import com.strategyquant.tradinglib.servlet.IServletPlugin;
import com.strategyquant.tradinglib.task.settings.ISettingTabPlugin;
import com.strategyquant.tradinglib.task.settings.TaskSettingsData;
import com.strategyquant.tradinglib.taskImpl.ISQTask;
import jakarta.servlet.Servlet;
import java.io.Serializable;
import java.util.ArrayList;
import java.util.List;
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
@Name(name="Ranking plugin")
@Category(name="Settings")
@License(text="")
@ShortDesc(text="Short description")
@PluginImplementation
public class SettingsRankingsPlugin
implements ISettingTabPlugin,
IServletPlugin {
    public static final Logger Log = LoggerFactory.getLogger(SettingsRankingsPlugin.class);
    private ServletContextHandler dataContext;
    private SettingsRankingsServlet servlet;

    public Handler getHandler() {
        if (this.dataContext == null) {
            this.servlet = new SettingsRankingsServlet();
            this.dataContext = new ServletContextHandler(1);
            this.dataContext.setContextPath("/rankingsettings/");
            this.dataContext.addServlet(new ServletHolder((Servlet)this.servlet), "/*");
        }
        return this.dataContext;
    }

    public String getProduct() {
        return "SQUANT";
    }

    public int getPreferredPosition() {
        return 70;
    }

    public void initPlugin() throws Exception {
    }

    private void fixSettings(Element elSettings) {
        Element elRankings = XMLUtil.tryAddElement((Element)elSettings, (String)this.getSettingName());
        XMLUtil.tryAddIntNode((Element)elRankings, (String)"MaxStrategies", (int)500);
        try {
            XMLUtil.getChildElem((Element)elRankings, (String)"FitnessCriteria");
        }
        catch (Exception e) {
            Element elFitnessCriteria = XMLUtil.tryAddElement((Element)elRankings, (String)"FitnessCriteria");
            elFitnessCriteria.setAttribute("method", "ComputeFromStrategyResult");
            Element elRanking = XMLUtil.tryAddElement((Element)elFitnessCriteria, (String)"Ranking");
            elRanking.setAttribute("type", "NetProfit");
        }
        if (elRankings.getChild("StopCondition") == null) {
            Element elStopCondition = XMLUtil.tryAddElement((Element)elRankings, (String)"StopCondition");
            elStopCondition.setAttribute("type", "never");
        }
        if (elRankings.getChild("FitPortfolio") == null) {
            Element elFitPortfolio = XMLUtil.tryAddElement((Element)elRankings, (String)"FitPortfolio");
            XMLUtil.tryAddElement((Element)elFitPortfolio, (String)"Correlation");
        }
        XMLUtil.tryAddIntNode((Element)elRankings, (String)"ConditionsType", (int)1);
        XMLUtil.tryAddElement((Element)elRankings, (String)"Conditions");
    }

    public void readSettings(String projectName, ISQTask task, Element elSettings, TaskSettingsData data) {
        String taskType;
        Element elRankings;
        block40: {
            this.fixSettings(elSettings);
            elRankings = null;
            try {
                elRankings = XMLUtil.getChildElem((Element)elSettings, (String)this.getSettingName());
            }
            catch (Exception e) {
                data.addError(this.getSettingName(), null, e.getMessage());
                return;
            }
            taskType = task.getType();
            try {
                Element elMaxStrategies = XMLUtil.getChildElem((Element)elRankings, (String)"MaxStrategies");
                int maxStrategies = Integer.parseInt(elMaxStrategies.getText());
                data.addParam("MaxStrategies", (Serializable)Integer.valueOf(maxStrategies));
            }
            catch (Exception e) {
                data.addError(this.getSettingName(), "MaxStrategies", L.t((String)"Max strategies count not set or invalid", (Object[])new Object[0]));
                return;
            }
            if (taskType.equals("Build") || taskType.equals("Retest") || taskType.equals("AutomaticRetest")) {
                try {
                    data.addParam("Conditions", (Serializable)ProjectConfigHelper.getConditions((Element)elRankings.getChild("Conditions")));
                }
                catch (Exception e) {
                    data.addError(this.getSettingName(), "Conditions", L.t((String)"Cannot load custom filters.", (Object[])new Object[0]));
                    return;
                }
            }
            if (taskType.equals("Retest") || taskType.equals("AutomaticRetest")) {
                try {
                    data.addParam("DeleteFailedStrategies", (Serializable)Boolean.valueOf(XMLUtil.getBoolean((Element)elRankings, (String)"DeleteFailedStrategies", (boolean)false)));
                }
                catch (Exception e) {
                    data.addError(this.getSettingName(), "DeleteFailedStrategies", L.t((String)"Cannot load option DeleteFailedStrategies.", (Object[])new Object[0]));
                    return;
                }
                try {
                    data.addParam("ForceRunCrossChecks", (Serializable)Boolean.valueOf(XMLUtil.getBoolean((Element)elRankings, (String)"ForceRunCrossChecks", (boolean)false)));
                }
                catch (Exception e) {
                    data.addError(this.getSettingName(), "ForceRunCrossChecks", L.t((String)"Cannot load option ForceRunCrossChecks.", (Object[])new Object[0]));
                    return;
                }
            }
            if (taskType.equals("Build")) {
                try {
                    try {
                        data.addParam("DismissTooSimilarStrategies", (Serializable)Boolean.valueOf(XMLUtil.getBoolean((Element)elRankings, (String)"DismissTooSimilarStrategies", (boolean)true)));
                    }
                    catch (Exception e) {
                        data.addError(this.getSettingName(), "DismissTooSimilarStrategies", L.t((String)"Cannot load option DismissTooSimilarStrategies.", (Object[])new Object[0]));
                        return;
                    }
                    Element elStopCondition = XMLUtil.getChildElem((Element)elRankings, (String)"StopCondition");
                    String stopConditionType = elStopCondition.getAttributeValue("type").toString();
                    data.addParam("StopConditionType", (Serializable)((Object)stopConditionType));
                    if (stopConditionType.equals("passed-count")) {
                        try {
                            int maxStrategiesPassed = Integer.parseInt(elStopCondition.getAttributeValue("passedStrategies"));
                            data.addParam("MaxStrategiesPassed", (Serializable)Integer.valueOf(maxStrategiesPassed));
                            break block40;
                        }
                        catch (Exception e) {
                            data.addError(this.getSettingName(), "PassedStrategies", L.t((String)"Passed strategies count not set or has invalid value", (Object[])new Object[0]));
                            return;
                        }
                    }
                    if (!stopConditionType.equals("time-limit")) break block40;
                    try {
                        int days = Integer.parseInt(elStopCondition.getAttributeValue("days"));
                        int hours = Integer.parseInt(elStopCondition.getAttributeValue("hours"));
                        int minutes = Integer.parseInt(elStopCondition.getAttributeValue("minutes"));
                        long time = days * 24 * 3600 * 1000 + hours * 3600 * 1000 + minutes * 60 * 1000;
                        if (time <= 0L) {
                            throw new Exception("Build run time must be greater than 0 ms.");
                        }
                        data.addParam("MaxBuildRunTime", (Serializable)Long.valueOf(time));
                    }
                    catch (Exception e) {
                        data.addError(this.getSettingName(), "TimeLimit", L.t((String)"Build run time limit not set or has invalid value", (Object[])new Object[0]));
                        return;
                    }
                }
                catch (Exception e) {
                    data.addError(this.getSettingName(), "StopCondition", L.t((String)"Stop condition type not set", (Object[])new Object[0]));
                    return;
                }
            }
        }
        if (taskType.equals("Build") || taskType.equals("Retest") || taskType.equals("AutomaticRetest")) {
            try {
                data.addParam("StrategyDismissSettings", (Serializable)Integer.valueOf(ProjectConfigHelper.getDismissBadStrategiesSettings((Element)elRankings)));
                data.addParam("StrategyDismissWarnings", (Serializable)Boolean.valueOf(ProjectConfigHelper.getDismissBadStrategiesWarnings((Element)elRankings)));
            }
            catch (Exception e) {
                data.addError(this.getSettingName(), "Conditions", L.t((String)"Cannot load automatic filters.", (Object[])new Object[0]) + " " + e.getMessage());
                return;
            }
        }
        if (taskType.equals("Build")) {
            try {
                FitPortfolio fitPortfolio = new FitPortfolio();
                Element elFitPortfolio = XMLUtil.getChildElem((Element)elRankings, (String)"FitPortfolio");
                fitPortfolio.active = XMLUtil.getBooleanAttr((Element)elFitPortfolio, (String)"active", (boolean)false);
                String databankName = XMLUtil.getStringAttr((Element)elFitPortfolio, (String)"databank", (String)"Existing portfolio");
                SQProject project = ProjectEngine.get((String)projectName);
                if (databankName.equals("") || databankName.equals("null") || project.isAppProject()) {
                    databankName = "Existing portfolio";
                }
                fitPortfolio.databank = (Databank)project.getDatabanks().get((Object)databankName);
                if (fitPortfolio.databank == null) {
                    Log.error(String.format("Databank for Fit Portfolio not found('%s')", databankName));
                    if (!ProjectEngine.get((String)projectName).getDatabanks().containsKey((Object)"Existing portfolio")) {
                        Log.debug("ExistingPortfolio databank does not exist. Creating it...");
                        fitPortfolio.databank = ProjectEngine.get((String)projectName).getDatabanks().add("Existing portfolio");
                    }
                }
                if (fitPortfolio.databank == null) {
                    data.addError(this.getSettingName(), "Databank", L.t((String)"No suitable databank set for Fit Portfolio ('%s')", (Object[])new Object[]{databankName}));
                    return;
                }
                Element elCorrelation = XMLUtil.getChildElem((Element)elFitPortfolio, (String)"Correlation");
                fitPortfolio.corrMax = XMLUtil.getDoubleAttr((Element)elCorrelation, (String)"max", (double)0.3);
                String type = XMLUtil.getStringAttr((Element)elCorrelation, (String)"type", (String)"ProfitLoss");
                fitPortfolio.corrType = (CorrelationType)CorrelationTypes.getInstance().findClassByName(type);
                fitPortfolio.corrPeriod = XMLUtil.getIntAttr((Element)elCorrelation, (String)"period", (int)10);
                fitPortfolio.corrAllowNegative = XMLUtil.getBooleanAttr((Element)elCorrelation, (String)"allowNegative", (boolean)false);
                fitPortfolio.corrAddEmptyPeriods = XMLUtil.getBooleanAttr((Element)elCorrelation, (String)"addEmptyPeriods", (boolean)false);
                data.addParam("FitPortfolio", (Serializable)fitPortfolio);
            }
            catch (Exception e) {
                data.addError(this.getSettingName(), null, e.getMessage());
                return;
            }
        }
        try {
            data.addParam("UseFitnessByIndex", (Serializable)Boolean.valueOf(false));
            Element elFitnessCriteria = XMLUtil.getChildElem((Element)elRankings, (String)"FitnessCriteria");
            String useFitnessByIndex = elFitnessCriteria.getAttributeValue("useFitnessByIndex");
            if (useFitnessByIndex != null && useFitnessByIndex.equals("true")) {
                data.addParam("UseFitnessByIndex", (Serializable)Boolean.valueOf(true));
            }
        }
        catch (Exception e) {
            data.addError(this.getSettingName(), "FitnessFunction", L.t((String)"Cannot load fitnessByInd function.", (Object[])new Object[0]) + " " + e.getMessage());
            return;
        }
        try {
            IFitnessFunction ff = ProjectConfigHelper.getFitnessFunction((Element)elRankings);
            data.addParam("FitnessFunction", (Serializable)ff);
        }
        catch (Exception e) {
            data.addError(this.getSettingName(), "FitnessFunction", L.t((String)"Cannot load fitness function.", (Object[])new Object[0]) + " " + e.getMessage());
            return;
        }
        try {
            Element elCA = elRankings.getChild("CustomAnalysis");
            CustomAnalysisInfo ca = new CustomAnalysisInfo();
            ca.loadRankingConfig(elCA);
            data.addParam("CustomAnalysis", (Serializable)ca);
        }
        catch (Exception e) {
            data.addError(this.getSettingName(), "CustomAnalysis", L.t((String)"Cannot load custom analysis.", (Object[])new Object[0]) + " " + e.getMessage());
            return;
        }
    }

    public void getStrategyConfigSettings(Element elSettings, JSONArray settingsArray) throws Exception {
        Element elRankings = XMLUtil.tryAddElement((Element)elSettings, (String)this.getSettingName());
        IFitnessFunction ff = ProjectConfigHelper.getFitnessFunction((Element)elRankings);
        Element elMaxStrategies = XMLUtil.getChildElem((Element)elRankings, (String)"MaxStrategies");
        String maxStrategies = elMaxStrategies != null ? "" + Integer.parseInt(elMaxStrategies.getText()) : L.t((String)"N/A", (Object[])new Object[0]);
        settingsArray.put((Object)new JSONObject().put("key", (Object)L.t((String)"Maximum top strategies to store", (Object[])new Object[0])).put("value", (Object)maxStrategies));
        String databankColumnName = ff.getFitnessDatabankColumnName();
        String fitnessComputation = ff.getFitnessName() + ": " + databankColumnName;
        if (databankColumnName.equals("Weighted")) {
            fitnessComputation = fitnessComputation + "\nGoals: " + ff.printWeightedGoals();
        }
        settingsArray.put((Object)new JSONObject().put("key", (Object)L.t((String)"Fitness computation", (Object[])new Object[0])).put("value", (Object)fitnessComputation));
        String settings = "";
        try {
            Element elAutomaticDismissal = elRankings.getChild("AutomaticDismissal");
            List problemElems = elAutomaticDismissal.getChildren("Problem");
            for (int i = 0; i < problemElems.size(); ++i) {
                Element problemElem = (Element)problemElems.get(i);
                if (!XMLUtil.elementIs((Element)problemElem, (String)"dismiss")) continue;
                int code = Integer.parseInt(problemElem.getAttributeValue("code"));
                String reason = BadStrategyException.reasonToShortText((int)code);
                settings = settings + reason;
                settings = settings + "\n";
            }
            settingsArray.put((Object)new JSONObject().put("key", (Object)L.t((String)"Automatic filters", (Object[])new Object[0])).put("value", (Object)(settings.isEmpty() ? L.t((String)"None", (Object[])new Object[0]) : settings)));
        }
        catch (Exception e) {
            settingsArray.put((Object)new JSONObject().put("key", (Object)L.t((String)"Automatic filters", (Object[])new Object[0])).put("value", (Object)L.t((String)"None", (Object[])new Object[0])));
        }
        try {
            ArrayList conditions = ProjectConfigHelper.getConditions((Element)elRankings.getChild("Conditions"));
            settings = "";
            for (int i = 0; i < conditions.size(); ++i) {
                Condition condition = (Condition)conditions.get(i);
                if (!condition.isUsed()) continue;
                settings = settings + condition.toString();
                settings = settings + "\n";
            }
            settingsArray.put((Object)new JSONObject().put("key", (Object)L.t((String)"Custom filters", (Object[])new Object[0])).put("value", (Object)(settings.isEmpty() ? L.t((String)"None", (Object[])new Object[0]) : settings)));
        }
        catch (Exception e) {
            settingsArray.put((Object)new JSONObject().put("key", (Object)L.t((String)"Custom filters", (Object[])new Object[0])).put("value", (Object)L.t((String)"None", (Object[])new Object[0])));
        }
    }

    public String getSettingName() {
        return "Rankings";
    }

    public String getName() {
        return L.tsq((String)"Rankings");
    }

    public JSONObject getInitializationData() throws Exception {
        JSONObject data = new JSONObject();
        data.put("fitnessMethods", (Object)this.servlet.getFitnessMethods());
        return data;
    }
}

