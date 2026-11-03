/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.tradinglib.Databank
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.databank.RecordNotFoundException
 *  com.strategyquant.tradinglib.portfolioMaster.PortfolioMasterSettings
 *  com.strategyquant.tradinglib.portfolioMaster.PortfolioMasterUtils
 *  com.strategyquant.tradinglib.project.ProgressEngine
 *  com.strategyquant.tradinglib.project.SQProject
 *  org.jdom2.Content
 *  org.jdom2.Element
 */
package com.strategyquant.plugin.Task.impl.AutomaticPortfolioBuilder;

import com.strategyquant.lib.L;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.plugin.Task.impl.AutomaticPortfolioBuilder.bruteForce.BFPortfolioMasterComputer;
import com.strategyquant.plugin.Task.impl.AutomaticPortfolioBuilder.bruteForce.PortfolioMasterComputer;
import com.strategyquant.plugin.Task.impl.AutomaticPortfolioBuilder.genetic.GPortfolioMasterComputer;
import com.strategyquant.tradinglib.Databank;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.databank.RecordNotFoundException;
import com.strategyquant.tradinglib.portfolioMaster.PortfolioMasterSettings;
import com.strategyquant.tradinglib.portfolioMaster.PortfolioMasterUtils;
import com.strategyquant.tradinglib.project.ProgressEngine;
import com.strategyquant.tradinglib.project.SQProject;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import org.jdom2.Content;
import org.jdom2.Element;

public class AutomaticPortfolioBuilder {
    private static final String LockName = "AutomaticPortfolioBuilder";

    public void start(SQProject project, ProgressEngine progressEngine, PortfolioMasterSettings settings) throws Exception {
        if (settings.databankSource == null) {
            throw new Exception(L.t((String)"No input databank set.", (Object[])new Object[0]));
        }
        if (settings.databankTarget == null) {
            throw new Exception(L.t((String)"No output databank set.", (Object[])new Object[0]));
        }
        if (settings.fitnessFunction == null) {
            throw new Exception(L.t((String)"No fitness function set.", (Object[])new Object[0]));
        }
        if (settings.conditions == null) {
            throw new Exception(L.t((String)"No custom conditions set.", (Object[])new Object[0]));
        }
        ArrayList keys = settings.getKeys();
        int numberOfSelectedResults = keys.size();
        if (numberOfSelectedResults == 0) {
            throw new Exception(L.t((String)"You have to select at least 2 simple strategies to create portfolio.", (Object[])new Object[0]));
        }
        settings.numberOfPossiblePortfolios = PortfolioMasterUtils.calculateMaxNumberOfPortfolios((int)numberOfSelectedResults, (int)settings.minStrategiesInPortfolio, (int)settings.maxStrategiesInPortfolio);
        if (settings.numberOfPossiblePortfolios.compareTo(BigInteger.valueOf(0L)) == 0) {
            throw new Exception(L.t((String)"Please check your settings. Number of possible portfolios must be greater than 0.", (Object[])new Object[0]));
        }
        ArrayList<ResultsGroup> strategies = this.getClonedStrategies(keys, settings.databankSource);
        progressEngine.printToLog(L.t((String)("Number of possible portfolios: " + settings.numberOfPossiblePortfolios.toString()), (Object[])new Object[0]));
        boolean useBruteForce = settings.useBruteForce;
        if (settings.numberOfPossiblePortfolios.compareTo(BigInteger.valueOf(500L)) < 0 && !useBruteForce) {
            progressEngine.printToLog(L.t((String)"The number of possible portfolios is very small, Genetic approach doesn't make sense in this case.", (Object[])new Object[0]));
            useBruteForce = true;
        }
        if (MainApp.getLicenseInfo().isActiveSpecialTrial()) {
            throw new Exception(L.t((String)"PortfolioMaster is available only in full version, not in this special trial.", (Object[])new Object[0]));
        }
        PortfolioMasterComputer computer = null;
        computer = useBruteForce ? new BFPortfolioMasterComputer(strategies, project, progressEngine, settings) : new GPortfolioMasterComputer(strategies, project, progressEngine, settings);
        computer.execute();
    }

    private ArrayList<ResultsGroup> getClonedStrategies(ArrayList<String> keys, Databank databankSource) throws Exception {
        try {
            ArrayList<ResultsGroup> strategies = new ArrayList<ResultsGroup>();
            for (int i = 0; i < keys.size(); ++i) {
                String key = keys.get(i);
                ResultsGroup rg = null;
                try {
                    rg = databankSource.getLocked(key, LockName);
                    Element StrategyXml = rg.getStrategyXml();
                    Element elStrategy = StrategyXml.getChild("Strategy").getChild("MoneyManagement");
                    List methodList = XMLUtil.stringToElement((String)rg.getLastSettings()).getChild("RiskMoneyManagement").getChild("MoneyManagement").getChildren();
                    String InitialCapital = "";
                    String type = "";
                    List paramsList2 = new ArrayList();
                    for (int i1 = 0; i1 < methodList.size(); ++i1) {
                        Element methodElement = (Element)methodList.get(i1);
                        if (methodElement.getName().equals("Method")) {
                            if (!"true".equals(methodElement.getAttribute("use").getValue())) continue;
                            type = methodElement.getAttributeValue("type");
                            List paramsList = methodElement.getChildren("Params");
                            Element elChild = (Element)paramsList.get(0);
                            paramsList2 = elChild.getChildren();
                            break;
                        }
                        if (!methodElement.getName().equals("InitialCapital") || methodElement.getContentSize() < 1) continue;
                        InitialCapital = ((Content)methodElement.getContent().get(0)).getValue();
                    }
                    Element moneyManagement = new Element("MoneyManagement");
                    moneyManagement.setAttribute("type", type);
                    Element params = new Element("Params");
                    moneyManagement.addContent((Content)params);
                    for (Element param : paramsList2) {
                        AutomaticPortfolioBuilder.addParam(params, param.getAttributeValue("key"), param.getAttributeValue("className"), param.getText());
                    }
                    Element strategyParent = elStrategy.getParentElement();
                    int index = strategyParent.indexOf((Content)elStrategy);
                    strategyParent.setContent(index, (Content)moneyManagement);
                    rg.setStrategyXml(StrategyXml);
                    strategies.add(rg.clone(true));
                    continue;
                }
                catch (RecordNotFoundException e) {
                    throw new Exception(L.t((String)"Strategy '%s' not found.", (Object[])new Object[]{key}));
                }
                finally {
                    if (rg != null) {
                        rg.releaseLock(LockName);
                    }
                }
            }
            return strategies;
        }
        catch (Exception e) {
            throw new Exception(L.t((String)"Failed to get strategies - %s", (Object[])new Object[]{e.getMessage()}));
        }
    }

    private static void addParam(Element parent, String key, String className, String value) {
        Element param = new Element("Param");
        param.setAttribute("key", key);
        param.setAttribute("className", className);
        param.setText(value);
        parent.addContent((Content)param);
    }
}

