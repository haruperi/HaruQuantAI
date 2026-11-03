/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.app.MainApp
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.portfolioMaster;

import com.strategyquant.lib.L;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.tradinglib.CorrelationType;
import com.strategyquant.tradinglib.Databank;
import com.strategyquant.tradinglib.MoneyManagementMethod;
import com.strategyquant.tradinglib.conditions.Condition;
import com.strategyquant.tradinglib.correlation.CorrelationTypes;
import com.strategyquant.tradinglib.moneymanagement.MoneyManagementMethodsList;
import com.strategyquant.tradinglib.portfolioMaster.PortfolioMasterFitness;
import com.strategyquant.tradinglib.portfolioMaster.PortfolioMasterFitnessList;
import com.strategyquant.tradinglib.project.ProjectConfigHelper;
import java.io.Serializable;
import java.math.BigInteger;
import java.util.ArrayList;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class PortfolioMasterSettings
implements Serializable {
    private static final Logger Log = LoggerFactory.getLogger(PortfolioMasterSettings.class);
    public static String PMFitnessValue = "PMFitnessValue";
    public boolean useBruteForce;
    public int populationSize;
    public int generations;
    public boolean runContinually;
    public boolean restartAfterStagnation;
    public int generationLimit;
    public BigInteger numberOfPossiblePortfolios;
    public Databank databankSource;
    public Databank databankTarget;
    public int maxStrategiesInDatabank;
    public boolean limitDateRange;
    public long dateRangeFrom;
    public long dateRangeTo;
    public int IsPct;
    public boolean reverseSample;
    public int maxStrategiesSector;
    public int minStrategiesInPortfolio;
    public int maxStrategiesInPortfolio;
    public PortfolioMasterFitness fitnessFunction;
    public byte fitnessSampleType;
    public double maxCorrelation;
    public CorrelationType correlationType;
    public byte correlationSampleType;
    public int correlationPeriod;
    public boolean allowNegativeCorrelation;
    public boolean addEmptyPeriods;
    public ArrayList<Condition> conditions = null;
    public ArrayList<String> selectedKeys = null;
    public float initialCapital;
    public boolean mmMethodOptional;
    public MoneyManagementMethod mmMethod;

    public void loadFromXml(Element element, String string) throws Exception {
        Object object;
        Object object2;
        Object object3;
        String string2 = XMLUtil.getNodeValue((Element)element, (String)"SearchType", (String)"bruteforce");
        this.useBruteForce = string2.equals("bruteforce");
        this.databankSource = ProjectConfigHelper.getInputDatabank(string, element.getParentElement());
        if (this.databankSource == null) {
            throw new Exception(L.t((String)"Source databank not found", (Object[])new Object[0]));
        }
        this.databankTarget = ProjectConfigHelper.getOutputDatabank(string, element.getParentElement());
        if (this.databankTarget == null) {
            throw new Exception(L.t((String)"Target databank not found", (Object[])new Object[0]));
        }
        Element element2 = element.getParentElement().getChild("Databanks");
        if (element2 == null) {
            throw new Exception("Databanks element not found");
        }
        boolean bl = element2.getAttributeValue("retestSelected", "false").equals("true");
        if (bl) {
            object3 = XMLUtil.getChildElem((Element)element.getParentElement(), (String)"SelectedStrategies");
            object2 = new ArrayList<String>();
            object = object3.getChildren("Strategy");
            for (int i = 0; i < object.size(); ++i) {
                Element element3 = (Element)object.get(i);
                ((ArrayList)object2).add(element3.getText());
            }
            this.selectedKeys = object2;
        }
        this.maxStrategiesInDatabank = XMLUtil.getInt((Element)element, (String)"MaxStrategiesDatabank", (int)100);
        this.populationSize = XMLUtil.getInt((Element)element, (String)"GenPopulationSize", (int)100);
        this.generations = XMLUtil.getInt((Element)element, (String)"GenGenerations", (int)700);
        this.runContinually = XMLUtil.getBoolean((Element)element, (String)"GenRunContinually", (boolean)false);
        this.restartAfterStagnation = XMLUtil.getBoolean((Element)element, (String)"GenRestartAfterStagnation", (boolean)true);
        this.generationLimit = XMLUtil.getInt((Element)element, (String)"GenGenerationLimit", (int)500);
        this.minStrategiesInPortfolio = XMLUtil.getInt((Element)element, (String)"MinStrategies", (int)2);
        this.maxStrategiesInPortfolio = XMLUtil.getInt((Element)element, (String)"MaxStrategies", (int)8);
        this.maxStrategiesSector = XMLUtil.getInt((Element)element, (String)"MaxStrategiesSector", (int)3);
        object3 = XMLUtil.getNodeValue((Element)element, (String)"DateRange", (String)"full");
        this.limitDateRange = ((String)object3).equals("limited");
        if (this.limitDateRange) {
            this.dateRangeFrom = XMLUtil.parseDate((String)XMLUtil.getNodeValue((Element)element, (String)"DateRangeFrom", (String)"0"));
            this.dateRangeTo = XMLUtil.parseDate((String)XMLUtil.getNodeValue((Element)element, (String)"DateRangeTo", (String)"0"));
        }
        this.IsPct = XMLUtil.getInt((Element)element, (String)"DateRangeIsPct", (int)70);
        this.reverseSample = XMLUtil.getBoolean((Element)element, (String)"DateRangeReverse", (boolean)false);
        this.maxCorrelation = XMLUtil.getDouble((Element)element, (String)"CorrMax", (double)0.3);
        object2 = XMLUtil.getNodeValue((Element)element, (String)"CorrType", (String)"ProfitLoss");
        this.correlationType = (CorrelationType)CorrelationTypes.getInstance().findClassByName((String)object2);
        this.correlationPeriod = XMLUtil.getInt((Element)element, (String)"CorrPeriod", (int)10);
        this.correlationSampleType = XMLUtil.getByte((Element)element, (String)"CorrSampleType", (byte)10);
        this.allowNegativeCorrelation = XMLUtil.getBoolean((Element)element, (String)"CorrAllowNegative", (boolean)true);
        this.addEmptyPeriods = XMLUtil.getBoolean((Element)element, (String)"CorrAddEmptyPeriods", (boolean)false);
        this.fitnessSampleType = (byte)10;
        object = XMLUtil.getNodeValue((Element)element, (String)"FitnessType", (String)"NetProfitIS");
        if (((String)object).endsWith(PortfolioMasterFitness.SampleKeyIS)) {
            object = SQUtils.replaceLast((String)object, (String)PortfolioMasterFitness.SampleKeyIS, (String)"");
        } else if (((String)object).endsWith(PortfolioMasterFitness.SampleKeyFull)) {
            object = SQUtils.replaceLast((String)object, (String)PortfolioMasterFitness.SampleKeyFull, (String)"");
            this.fitnessSampleType = (byte)127;
        }
        this.fitnessFunction = (PortfolioMasterFitness)PortfolioMasterFitnessList.getInstance().findClassByName((String)object);
        this.conditions = ProjectConfigHelper.getConditions(element.getChild("Conditions"));
        this.mmMethodOptional = XMLUtil.getBoolean((Element)element, (String)"MMMethodOptional", (boolean)false);
        try {
            Element element4 = element.getChild("MoneyManagement");
            if (element4 == null) {
                throw new Exception("MoneyManagement method missing in XML, null value.");
            }
            this.mmMethod = ProjectConfigHelper.getMoneyManagement(element4);
        }
        catch (Exception exception) {
            Log.error("Error loading Money Management method, using FixedSize(0.1) - " + exception.getMessage(), (Throwable)exception);
            this.mmMethod = MoneyManagementMethodsList.create("FixedSize", 0.1);
        }
        this.initialCapital = (float)this.mmMethod.getInitialCapital();
    }

    public ArrayList<String> getKeys() throws Exception {
        ArrayList<String> arrayList = this.selectedKeys != null ? this.selectedKeys : this.databankSource.getRecordKeys();
        if (!MainApp.v571hfnsHw().aDm88fRJB2() && arrayList.size() > 4) {
            throw new Exception(L.t((String)"Portfolio Master in Pro version is a trial, and limited to maximum 4 source strategies for portfolio builder. Upgrade your license to Ultimate version to build portfolio from more strategies.", (Object[])new Object[0]));
        }
        return arrayList;
    }
}

