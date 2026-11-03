/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.gridlib.client.GridJob
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.XMLUtil
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.backtestrunner;

import com.strategyquant.gridlib.client.GridJob;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.tradinglib.BadStrategyException;
import com.strategyquant.tradinglib.ChartSetup;
import com.strategyquant.tradinglib.Databank;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.backtestrunner.BacktestResult;
import com.strategyquant.tradinglib.backtestrunner.BacktestSettings;
import com.strategyquant.tradinglib.backtestrunner.DurationStats;
import com.strategyquant.tradinglib.backtestrunner.IBacktestProgressListener;
import com.strategyquant.tradinglib.conditions.Condition;
import com.strategyquant.tradinglib.conditions.ConditionsChecker;
import com.strategyquant.tradinglib.correlation.CorrelationComputer;
import com.strategyquant.tradinglib.correlation.FitPortfolio;
import com.strategyquant.tradinglib.crosscheck.CrossCheckDataNotExistException;
import com.strategyquant.tradinglib.crosscheck.ICrossCheck;
import com.strategyquant.tradinglib.engine.BacktestEngine;
import com.strategyquant.tradinglib.engine.stockpicker.StockpickerBacktestEngine;
import com.strategyquant.tradinglib.exception.StrategyStoppedException;
import com.strategyquant.tradinglib.fitnessfunction.IFitnessFunction;
import com.strategyquant.tradinglib.project.ILastEventListener;
import com.strategyquant.tradinglib.project.ProjectConfigHelper;
import com.strategyquant.tradinglib.project.StopPauseEngine;
import com.strategyquant.tradinglib.results.SpecialValues;
import com.strategyquant.tradinglib.simulator.impl.TraderSimulators;
import com.strategyquant.tradinglib.strategy.OutOfSample;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class BacktestRunner {
    public static final Logger Log = LoggerFactory.getLogger((String)"BacktestRunner");
    private BacktestSettings backtestSettings;
    private StopPauseEngine stopPauseEngine;
    private GridJob parentGridJob = null;
    private String strategyName = "UnknownStrategy";
    private double totalProgressSteps;
    private double currentProgressStep = 0.0;
    private double progressStepWeight = 0.0;
    private int dismissalReason;
    private String dismissalMessage;
    private int dismissBadStrategies;
    private boolean fitnessComputed = false;
    private double globalATR;
    private DurationStats durationStats;
    private boolean printPartialProgress = false;
    private ILastEventListener lastEventListener;
    private boolean isEvolution = false;
    private ConditionsChecker conditionsChecker = new ConditionsChecker();
    private CorrelationComputer correlationComputer = new CorrelationComputer();
    private final String lastSettingsXml;

    public BacktestRunner(BacktestSettings backtestSettings, StopPauseEngine stopPauseEngine, GridJob gridJob, boolean bl, ILastEventListener iLastEventListener, String string) throws Exception {
        this.backtestSettings = backtestSettings;
        if (this.backtestSettings.isRetester) {
            this.dismissBadStrategies = this.backtestSettings.dismissBadStrategies;
            this.backtestSettings.dismissBadStrategies = 0;
        }
        this.stopPauseEngine = stopPauseEngine;
        this.parentGridJob = gridJob;
        this.strategyName = backtestSettings.strategyName;
        this.printPartialProgress = bl;
        this.lastEventListener = iLastEventListener;
        this.lastSettingsXml = string;
        this.durationStats = new DurationStats();
        this.computeTotalProgressSteps();
    }

    public BacktestResult execute() throws Exception {
        return this.execute(3);
    }

    public BacktestResult execute(int n) throws Exception {
        BacktestResult backtestResult;
        ResultsGroup resultsGroup;
        long l = System.currentTimeMillis();
        if (Log.isDebugEnabled()) {
            Log.debug(String.format("Backtest runner %s started", this.strategyName));
        }
        if ((resultsGroup = (backtestResult = this.runBacktestOnMainSetup(n)).getResult()) != null) {
            resultsGroup.specialValues().set(SpecialValues.DateGenerated, (Object)this.backtestSettings.dateGenerated);
            resultsGroup.specialValues().set(SpecialValues.DateLastModified, (Object)SQTime.getLocalCurrentTimeInMs());
        }
        if (resultsGroup != null && BadStrategyException.getReasonAsString(10017) == resultsGroup.specialValues().getString(SpecialValues.FiltersResultFailedReason)) {
            return backtestResult.dismiss("dismissed, strategy indicators require X reserved bars", 10017);
        }
        if (!this.backtestSettings.isRetester && backtestResult.isDismissed() && this.fitnessComputed) {
            return backtestResult;
        }
        if (!this.backtestSettings.forceRunCrossChecks && this.backtestSettings.isRetester && backtestResult.isDismissed()) {
            return backtestResult;
        }
        if (n == 3 && backtestResult.getResult() != null) {
            backtestResult = this.runAndSaveCrossChecks(backtestResult, n);
            if (!this.fitnessComputed && (resultsGroup = backtestResult.getResult()) != null) {
                this.computeFitnessOnMainData(resultsGroup, n, true);
            }
            if (backtestResult.isDismissed()) {
                return backtestResult;
            }
        }
        if (this.stopPauseEngine.isStopped()) {
            if (Log.isDebugEnabled()) {
                Log.debug("Clearing results for {}", (Object)this.strategyName);
            }
            if ((resultsGroup = backtestResult.getResult()) != null) {
                resultsGroup.clear();
            }
            return backtestResult.dismiss("Task stopped - Strategy test not finished", 10002);
        }
        double d = (double)(System.currentTimeMillis() - l) / 1000.0;
        if (Log.isDebugEnabled()) {
            Log.debug(String.format("Backtest runner %s finished in %.4f s.", this.strategyName, d));
        }
        return backtestResult;
    }

    private BacktestResult runBacktestOnMainSetup(int n) throws Exception {
        Element element2;
        Element element3;
        List list;
        Optional<Element> optional;
        ResultsGroup resultsGroup = null;
        long l = System.currentTimeMillis();
        if (this.strategyName != null) {
            this.printEvent(L.t((String)"Running backtest for %s...", (Object[])new Object[]{this.strategyName}));
        }
        ChartSetup chartSetup = (ChartSetup)this.backtestSettings.chartSetups.get(0);
        try {
            resultsGroup = this.backtestStrategy(chartSetup);
        }
        catch (BadStrategyException badStrategyException) {
            BacktestResult backtestResult = new BacktestResult(null, this.durationStats);
            backtestResult.dismiss(String.format(DurationStats.MainTest + " %s, - " + L.t((String)"dismissed", (Object[])new Object[0]) + ": %s", this.strategyName, badStrategyException.getReasonAsString()), badStrategyException.getReason());
            return backtestResult;
        }
        this.durationStats.addDuration(DurationStats.MainTest, System.currentTimeMillis() - l);
        this.currentProgressStep += 1.0;
        if (this.stopPauseEngine.isStopped()) {
            resultsGroup.clear();
            return new BacktestResult(L.t((String)"Task stopped - Strategy test not finished", (Object[])new Object[0]), 10002, this.durationStats);
        }
        this.computeFitnessOnMainData(resultsGroup, n, false);
        BacktestResult backtestResult = new BacktestResult(resultsGroup, this.durationStats);
        if (this.backtestSettings.isRetester) {
            resultsGroup.specialValues().set(SpecialValues.FiltersResultFailedReason, (Object)SpecialValues.FiltersResultPassed);
        }
        resultsGroup.setDatabank(null);
        resultsGroup.setName(this.strategyName);
        if (this.backtestSettings.mergedStrategies != null) {
            resultsGroup.setMergedResults(this.backtestSettings.mergedStrategies);
        }
        if (!this.globalConditionsPassed(resultsGroup, n)) {
            if (this.backtestSettings.isRetester) {
                resultsGroup.specialValues().set(SpecialValues.FiltersResultFailedReason, (Object)this.dismissalMessage);
            }
            backtestResult.dismiss(String.format(DurationStats.MainTest + " %s, - " + L.t((String)"dismissed", (Object[])new Object[0]) + ": %s", this.strategyName, this.dismissalMessage), this.dismissalReason);
        }
        if (this.backtestSettings.isRetester) {
            this.checkAutomaticDismissalRules(backtestResult);
        }
        if (n == 3 && !this.fitToExistingPortfolio(resultsGroup)) {
            backtestResult.dismiss(L.t((String)"Fit to existing portfolio - dismissed: %s, %s", (Object[])new Object[]{this.strategyName, this.dismissalMessage}), this.dismissalReason);
        }
        int n2 = this.backtestSettings.chartSetups.getMainSetup().getBacktestEngine();
        if (this.lastSettingsXml != null && (n2 == 56756755 || n2 == 938213070) && (optional = (list = (element3 = (element2 = XMLUtil.stringToElement((String)this.lastSettingsXml)).getChild("Options").getChild("BuildTradingOptions").getChild("Params")).getChildren()).stream().filter(element -> "Param".equals(element.getName()) && "ReservedBars".equals(element.getAttributeValue("key")) && "ReservedBars".equals(element.getAttributeValue("className"))).findFirst()).isPresent()) {
            Element element4 = optional.get();
            int n3 = Integer.valueOf(element4.getText());
            Integer n4 = 0;
            if (resultsGroup != null) {
                String string = resultsGroup.getName();
                Element element5 = resultsGroup.getStrategyXml();
                n4 = this.findParamElementsWithPeriod(element5, 0, 0, string);
                if (n4 >= n3) {
                    String string2 = BadStrategyException.getReasonAsString(10017);
                    resultsGroup.specialValues().set(SpecialValues.FiltersResultFailedReason, (Object)string2);
                }
            }
        }
        return backtestResult;
    }

    private Integer findParamElementsWithPeriod(Element element, int n, int n2, String string) {
        Object object;
        block47: {
            object = 0;
            List list = element.getChildren();
            try {
                Object object2;
                Element element2;
                int n3;
                if (list == null) break block47;
                int n4 = -1;
                boolean bl = false;
                for (n3 = 0; n3 < list.size(); ++n3) {
                    element2 = (Element)list.get(n3);
                    if (element2.getName().equals("CustomIndicators") || !element2.getName().equals("Param") || !((String)(object2 = element2.getAttributeValue("key"))).equals("#Shift#")) continue;
                    n += Integer.parseInt(element2.getText().trim());
                    break;
                }
                for (n3 = 0; n3 < list.size(); ++n3) {
                    Object object3;
                    element2 = (Element)list.get(n3);
                    if (element2.getName().equals("CustomIndicators")) continue;
                    if (element2.getName().equals("Param")) {
                        bl = false;
                        object2 = element2.getAttributeValue("key");
                        object3 = "";
                        if (((String)object2).equals("#Method#") && (object3 = element2.getAttributeValue("values")) == null) {
                            object3 = "";
                        }
                        if (((String)object2).equals("#Chart#")) {
                            n4 = Integer.parseInt(element2.getText().trim());
                        } else if (((String)object2).equals("#Bars#")) {
                            n2 += Integer.parseInt(element2.getText().trim());
                        } else if (((String)object2).toLowerCase().contains("period")) {
                            bl = true;
                        } else if (((String)object2).equals("#SlowEMA#")) {
                            bl = true;
                        } else if (((String)object2).equals("#FastEMA#")) {
                            bl = true;
                        } else if (((String)object2).equals("#SignalPeriod#")) {
                            bl = true;
                        } else if (((String)object2).equals("#Fast#")) {
                            bl = true;
                        } else if (((String)object2).equals("#Slow#")) {
                            bl = true;
                        } else if (((String)object2).equals("#Smooth#")) {
                            bl = true;
                        } else if (((String)object2).equals("#Length#")) {
                            bl = true;
                        } else if (((String)object2).equals("#Slowing#")) {
                            bl = true;
                        } else if (((String)object2).equals("#Gamma#")) {
                            bl = true;
                        } else if (((String)object2).equals("#Method#") && (((String)object3).equals("Price below SMA200=0") || ((String)object3).equals("Price above SMA200=0"))) {
                            bl = true;
                        }
                        if (object == null || n + n2 > (Integer)object) {
                            object = n + n2;
                        }
                        if (bl && n4 == 0) {
                            try {
                                if (((String)object2).equals("#Gamma#")) {
                                    if (object == null || 20 + n + n2 > (Integer)object) {
                                        object = 20 + n + n2;
                                        Log.debug(String.format("Rg Name  %s  Key value: %s", string, ((Integer)object).toString()));
                                    }
                                } else if (((String)object2).equals("#Method#") && (((String)object3).equals("Price below SMA200=0") || ((String)object3).equals("Price above SMA200=0"))) {
                                    if (object == null || 200 + n + n2 > (Integer)object) {
                                        object = 200 + n + n2;
                                        Log.debug(String.format("Rg Name  %s  Key value: %s", string, ((Integer)object).toString()));
                                    }
                                } else if (!element2.getText().isBlank() && !element2.getText().isEmpty()) {
                                    int n5 = Integer.parseInt(element2.getText().trim());
                                    if (object == null || n5 + n + n2 > (Integer)object) {
                                        object = n5 + n + n2;
                                        Log.debug(String.format("Rg Name  %s  Key value: %s", string, ((Integer)object).toString()));
                                    }
                                }
                            }
                            catch (NumberFormatException numberFormatException) {
                                Log.debug("Invalid period value: " + element2.getText());
                            }
                        }
                    } else if (element2.getName().equals("Item")) {
                        object2 = element2.getAttributeValue("key");
                        if (((String)object2).toLowerCase().contains("awo") && (object == null || 34 + n + n2 > (Integer)object)) {
                            object = 36 + n + n2;
                            Log.debug(String.format("Rg Name  %s  Key value: %s", string, ((Integer)object).toString()));
                        }
                    } else {
                        n4 = -1;
                    }
                    object2 = element2.getChildren();
                    if (object2 == null || object2.size() < 1 || (object3 = this.findParamElementsWithPeriod(element2, n, n2, string)) == null || object != null && (Integer)object3 <= (Integer)object) continue;
                    object = object3;
                }
            }
            catch (NumberFormatException numberFormatException) {
                Log.debug("Error findParamElementsWithPeriod : " + numberFormatException);
            }
        }
        return object;
    }

    private boolean fitToExistingPortfolio(ResultsGroup resultsGroup) {
        try {
            FitPortfolio fitPortfolio = this.backtestSettings.fitPortfolio;
            if (fitPortfolio != null && fitPortfolio.active) {
                Databank databank = fitPortfolio.databank;
                for (int i = 0; i < databank.getRecords().size(); ++i) {
                    ResultsGroup resultsGroup2 = databank.getRecords().get(i);
                    double d = SQUtils.round2((double)this.correlationComputer.computeCorrelation(resultsGroup2, resultsGroup, (byte)127, fitPortfolio.corrPeriod, fitPortfolio.corrType, fitPortfolio.corrAddEmptyPeriods));
                    if (d == -99.0 || !(d > fitPortfolio.corrMax) && (fitPortfolio.corrAllowNegative || !(d < 0.0))) continue;
                    this.dismissalReason = 10014;
                    this.dismissalMessage = d < 0.0 ? L.t((String)"%s correlation %.2f < 0, negative correlation not allowed", (Object[])new Object[]{resultsGroup2.getName(), d}) : L.t((String)"%s correlation %.2f > %.2f", (Object[])new Object[]{resultsGroup2.getName(), d, fitPortfolio.corrMax});
                    return false;
                }
            }
        }
        catch (Exception exception) {
            Log.error("Error", (Throwable)exception);
        }
        return true;
    }

    private void checkAutomaticDismissalRules(BacktestResult backtestResult) {
        try {
            ResultsGroup resultsGroup = backtestResult.getResult();
            int n = resultsGroup.mainResult().getStrategyProblems();
            int n2 = BadStrategyException.getFirstReason(n, this.dismissBadStrategies);
            if (n2 != 0) {
                this.dismissalReason = n2;
                this.dismissalMessage = BadStrategyException.getReasonAsString(this.dismissalReason);
                resultsGroup.specialValues().set(SpecialValues.FiltersResultFailedReason, (Object)this.dismissalMessage);
                backtestResult.dismiss(String.format(DurationStats.MainTest + " %s, - " + L.t((String)"dismissed", (Object[])new Object[0]) + ": %s", this.strategyName, this.dismissalMessage), this.dismissalReason);
            }
        }
        catch (Exception exception) {
            Log.error("Error", (Throwable)exception);
        }
    }

    private void printEvent(String string) {
        if (this.stopPauseEngine == null) {
            return;
        }
        if (this.lastEventListener != null) {
            this.lastEventListener.setLastEvent(string);
        }
        if (this.printPartialProgress) {
            this.stopPauseEngine.printToLogDebug(string);
        }
    }

    private void computeTotalProgressSteps() throws Exception {
        this.currentProgressStep = 0.0;
        int n = this.backtestSettings.chartSetups.size();
        if (n > 1) {
            ++n;
        }
        if (this.backtestSettings.useCrossChecks) {
            for (int i = 0; i < this.backtestSettings.crossChecks.size(); ++i) {
                ICrossCheck iCrossCheck = this.backtestSettings.crossChecks.get(i);
                if (iCrossCheck.doesRetest()) {
                    if (iCrossCheck.doesForEverySetup()) {
                        n += iCrossCheck.getNumberOfSimulations() * this.backtestSettings.chartSetups.size();
                        continue;
                    }
                    n += iCrossCheck.getNumberOfSimulations();
                    continue;
                }
                ++n;
            }
        }
        this.totalProgressSteps = n;
        this.progressStepWeight = 1.0 / this.totalProgressSteps;
    }

    private void computeFitnessOnMainData(ResultsGroup resultsGroup, int n, boolean bl) throws Exception {
        Databank databank;
        Object object;
        Object object2;
        IFitnessFunction iFitnessFunction = this.backtestSettings.fitnessFunction;
        if (iFitnessFunction == null) {
            object2 = "<Rankings>\r\n  <FitnessCriteria method=\"ComputeFromStrategyResult\">\r\n    <Settings>\r\n      <Ranking type=\"ReturnDDRatio\" />\r\n    </Settings>\r\n  </FitnessCriteria>\r\n</Rankings>";
            object = XMLUtil.stringToElement((String)object2);
            iFitnessFunction = ProjectConfigHelper.getFitnessFunction((Element)object);
        }
        if (!(bl || n != 3 || iFitnessFunction.getClass().getSimpleName().equals("FitnessMethodStrategyResult") || iFitnessFunction.getClass().getSimpleName().equals("FitnessExistingPortfolio"))) {
            return;
        }
        object2 = null;
        if (iFitnessFunction.getClass().getSimpleName().equals("FitnessExistingPortfolio") && (object = this.backtestSettings.fitPortfolio) != null && (databank = ((FitPortfolio)object).databank).getRecords().size() > 0) {
            ArrayList<ResultsGroup> arrayList = new ArrayList<ResultsGroup>();
            arrayList.add(resultsGroup);
            for (int i = 0; i < databank.getRecords().size(); ++i) {
                ResultsGroup resultsGroup2 = databank.getRecords().get(i);
                arrayList.add(resultsGroup2);
            }
            object2 = ResultsGroup.merge(arrayList, new String[]{"AdditionalMarket", "CrossCheck_"}, null);
            ((ResultsGroup)object2).createPortfolioResult("sum", null);
        }
        this.computeFitness(iFitnessFunction, resultsGroup, (ResultsGroup)object2, (byte)0, (byte)127);
        this.computeFitness(iFitnessFunction, resultsGroup, (ResultsGroup)object2, (byte)0, (byte)10);
        this.computeFitness(iFitnessFunction, resultsGroup, (ResultsGroup)object2, (byte)0, (byte)20);
        object = this.backtestSettings.outOfSample;
        if (object != null) {
            int n2;
            this.computeFitness(iFitnessFunction, resultsGroup, (ResultsGroup)object2, (byte)0, (byte)11);
            this.computeFitness(iFitnessFunction, resultsGroup, (ResultsGroup)object2, (byte)0, (byte)40);
            int n3 = ((OutOfSample)object).getPartsCount((byte)40);
            for (n2 = 0; n2 < n3; ++n2) {
                this.computeFitness(iFitnessFunction, resultsGroup, (ResultsGroup)object2, (byte)0, OutOfSample.getISVPart(n2 + 1));
            }
            n3 = ((OutOfSample)object).getPartsCount((byte)20);
            for (n2 = 0; n2 < n3; ++n2) {
                this.computeFitness(iFitnessFunction, resultsGroup, (ResultsGroup)object2, (byte)0, OutOfSample.getOOSPart(n2 + 1));
            }
        } else {
            resultsGroup.portfolio().setFitness((byte)11, resultsGroup.portfolio().getFitness((byte)10));
            resultsGroup.portfolio().setFitness((byte)40, 0.0);
        }
        this.fitnessComputed = true;
    }

    private boolean computeAndFilterFitnessOnCrossCheck(ResultsGroup resultsGroup, ICrossCheck iCrossCheck) throws Exception {
        if (!this.backtestSettings.fitnessFunction.getClass().getSimpleName().equals(iCrossCheck.getClass().getSimpleName())) {
            return true;
        }
        this.computeFitness(this.backtestSettings.fitnessFunction, resultsGroup, (byte)0, (byte)127);
        this.computeFitness(this.backtestSettings.fitnessFunction, resultsGroup, (byte)0, (byte)10);
        this.computeFitness(this.backtestSettings.fitnessFunction, resultsGroup, (byte)0, (byte)20);
        OutOfSample outOfSample = this.backtestSettings.outOfSample;
        if (outOfSample != null) {
            int n;
            this.computeFitness(this.backtestSettings.fitnessFunction, resultsGroup, (byte)0, (byte)11);
            this.computeFitness(this.backtestSettings.fitnessFunction, resultsGroup, (byte)0, (byte)40);
            int n2 = outOfSample.getPartsCount((byte)40);
            for (n = 0; n < n2; ++n) {
                this.computeFitness(this.backtestSettings.fitnessFunction, resultsGroup, (byte)0, OutOfSample.getISVPart(n + 1));
            }
            n2 = outOfSample.getPartsCount((byte)20);
            for (n = 0; n < n2; ++n) {
                this.computeFitness(this.backtestSettings.fitnessFunction, resultsGroup, (byte)0, OutOfSample.getOOSPart(n + 1));
            }
        } else {
            resultsGroup.portfolio().setFitness((byte)11, resultsGroup.portfolio().getFitness((byte)10));
            resultsGroup.portfolio().setFitness((byte)40, 0.0);
        }
        this.fitnessComputed = true;
        return this.globalConditionsPassed(resultsGroup, 3);
    }

    private void computeFitness(IFitnessFunction iFitnessFunction, ResultsGroup resultsGroup, byte by, byte by2) throws Exception {
        double d = iFitnessFunction.computeFitness(resultsGroup, by, by2);
        resultsGroup.portfolio().setFitness(by2, d);
        if (Log.isDebugEnabled() && by == 0 && by2 == 10) {
            Log.debug("Fitness (IS) computed to: " + d);
        }
    }

    private void computeFitness(IFitnessFunction iFitnessFunction, ResultsGroup resultsGroup, ResultsGroup resultsGroup2, byte by, byte by2) throws Exception {
        double d = iFitnessFunction.computeFitness(resultsGroup2 == null ? resultsGroup : resultsGroup2, by, by2);
        resultsGroup.portfolio().setFitness(by2, d);
        if (Log.isDebugEnabled() && by == 0 && by2 == 10) {
            Log.debug("Fitness (IS) computed to: " + d);
        }
    }

    private BacktestResult runAndSaveCrossChecks(BacktestResult backtestResult, int n) {
        if (!this.backtestSettings.useCrossChecks) {
            return backtestResult;
        }
        ResultsGroup resultsGroup = backtestResult.getResult();
        for (int i = 0; i < this.backtestSettings.crossChecks.size() && !this.stopPauseEngine.isStopped(); ++i) {
            ICrossCheck iCrossCheck = this.backtestSettings.crossChecks.get(i);
            iCrossCheck.setStopPauseEngine(this.stopPauseEngine);
            iCrossCheck.registerProgressListener(new IBacktestProgressListener(){

                @Override
                public void setProgress(int n) {
                    BacktestRunner.this.setJobProgress(n);
                }

                @Override
                public void increaseProgressStep() {
                    BacktestRunner.access$008(BacktestRunner.this);
                }
            });
            long l = System.currentTimeMillis();
            try {
                this.printEvent(L.t((String)"Running cross check %s for %s...", (Object[])new Object[]{iCrossCheck.getName(), this.strategyName}));
                boolean bl = iCrossCheck.runTest(resultsGroup, i, this.globalATR, this.parentGridJob, this.backtestSettings.singleThreadedOptimizations, this.lastEventListener, this.strategyName);
                this.durationStats.addDuration(iCrossCheck.getName(), System.currentTimeMillis() - l);
                if (!bl) {
                    if (resultsGroup.specialValues().containsKey(SpecialValues.FiltersResultFailedReason) && resultsGroup.specialValues().getString(SpecialValues.FiltersResultFailedReason).equals(SpecialValues.FiltersResultPassed)) {
                        resultsGroup.specialValues().set(SpecialValues.FiltersResultFailedReason, (Object)iCrossCheck.getDismissalMessage());
                    }
                    backtestResult.dismiss(String.format("%s, " + L.t((String)"dismissed", (Object[])new Object[0]) + ": %s", this.strategyName, iCrossCheck.getDismissalMessage()), iCrossCheck.getDismissalReason());
                    if (!this.backtestSettings.evaluateAllCrossChecks && this.fitnessComputed) {
                        return backtestResult;
                    }
                }
                if (!this.checkGlobalCrossCheckConditions(iCrossCheck, backtestResult.getResult(), n)) {
                    if (resultsGroup.specialValues().containsKey(SpecialValues.FiltersResultFailedReason) && resultsGroup.specialValues().getString(SpecialValues.FiltersResultFailedReason).equals(SpecialValues.FiltersResultPassed)) {
                        resultsGroup.specialValues().set(SpecialValues.FiltersResultFailedReason, (Object)this.dismissalMessage);
                    }
                    backtestResult.dismiss(String.format("%s, " + L.t((String)"dismissed", (Object[])new Object[0]) + ": %s", this.strategyName, this.dismissalMessage), this.dismissalReason);
                    if (!this.backtestSettings.evaluateAllCrossChecks && this.fitnessComputed) {
                        return backtestResult;
                    }
                }
                if (this.computeAndFilterFitnessOnCrossCheck(resultsGroup, iCrossCheck)) continue;
                if (resultsGroup.specialValues().containsKey(SpecialValues.FiltersResultFailedReason) && resultsGroup.specialValues().getString(SpecialValues.FiltersResultFailedReason).equals(SpecialValues.FiltersResultPassed)) {
                    resultsGroup.specialValues().set(SpecialValues.FiltersResultFailedReason, (Object)this.dismissalMessage);
                }
                backtestResult.dismiss(String.format("%s, " + L.t((String)"dismissed", (Object[])new Object[0]) + ": %s", this.strategyName, this.dismissalMessage), this.dismissalReason);
                if (this.backtestSettings.evaluateAllCrossChecks || !this.fitnessComputed) continue;
                return backtestResult;
            }
            catch (StrategyStoppedException strategyStoppedException) {
                this.durationStats.addDuration(iCrossCheck.getName(), System.currentTimeMillis() - l);
                backtestResult.dismiss(String.format("%s, " + L.t((String)"exception in cross check", (Object[])new Object[0]) + " %s - %s", this.strategyName, iCrossCheck.getName(), strategyStoppedException.getMessage()), 10004);
                continue;
            }
            catch (BadStrategyException badStrategyException) {
                if (badStrategyException.getReason() != 1 && badStrategyException.getReason() != 512) {
                    Log.error("Cross check bad strategy exception: " + badStrategyException.getMessage(), (Throwable)((Object)badStrategyException));
                }
                this.durationStats.addDuration(iCrossCheck.getName(), System.currentTimeMillis() - l);
                backtestResult.dismiss(String.format("%s, " + L.t((String)"exception in cross check", (Object[])new Object[0]) + " %s - %s", this.strategyName, iCrossCheck.getName(), badStrategyException.getMessage()), iCrossCheck.getBadStrategyReason());
                continue;
            }
            catch (Exception exception) {
                Log.error("Cross check exception: " + exception.getMessage(), (Throwable)exception);
                this.durationStats.addDuration(iCrossCheck.getName(), System.currentTimeMillis() - l);
                backtestResult.dismiss(String.format("%s, " + L.t((String)"exception in cross check", (Object[])new Object[0]) + " %s - %s", this.strategyName, iCrossCheck.getName(), exception.getMessage()), 10004);
            }
        }
        return backtestResult;
    }

    private boolean checkGlobalCrossCheckConditions(ICrossCheck iCrossCheck, ResultsGroup resultsGroup, int n) {
        int n2;
        if (n == 2) {
            return true;
        }
        ArrayList<Condition> arrayList = null;
        if (n == 1) {
            arrayList = this.backtestSettings.initialGenerationConditions;
            n2 = 100000;
        } else {
            arrayList = this.backtestSettings.rankingConditions;
            n2 = 200000;
        }
        if (arrayList != null && arrayList.size() > 0) {
            for (int i = 0; i < arrayList.size(); ++i) {
                Condition condition = arrayList.get(i);
                if (!condition.isUsed() || !condition.isCrossCheckCondition(iCrossCheck.getSettingName()) && (!condition.isPortfolioCondition() || !iCrossCheck.getSettingName().equals("RetestOnAdditionalMarkets")) || !this.fitnessComputed && condition.isFitnessCondition()) continue;
                try {
                    boolean bl = this.conditionsChecker.check(resultsGroup, condition);
                    if (bl) continue;
                    this.dismissalReason = n2 + i;
                    this.dismissalMessage = L.t((String)"%s filter: %s", (Object[])new Object[]{n == 1 ? L.t((String)"Initial population", (Object[])new Object[0]) : L.t((String)"Global", (Object[])new Object[0]), this.conditionsChecker.dismissalMessage});
                    return false;
                }
                catch (CrossCheckDataNotExistException crossCheckDataNotExistException) {
                    continue;
                }
                catch (Exception exception) {
                    Log.error("Error while checking condition", (Throwable)exception);
                    this.dismissalReason = 10003;
                    this.dismissalMessage = L.t((String)"Error while evaluating conditions: %s", (Object[])new Object[]{exception.getMessage()});
                    return false;
                }
            }
        }
        return true;
    }

    private ResultsGroup backtestStrategy(ChartSetup chartSetup) throws Exception {
        ResultsGroup resultsGroup;
        if (chartSetup.getBacktestEngine() == 1316847364 || chartSetup.getBacktestEngine() == -1816889229) {
            StockpickerBacktestEngine stockpickerBacktestEngine = new StockpickerBacktestEngine();
            stockpickerBacktestEngine.setStopPauseEngine(this.stopPauseEngine);
            stockpickerBacktestEngine.setLastEventListener(this.lastEventListener);
            if (chartSetup.getBacktestEngine() == -1816889229) {
                String string = chartSetup.getMainChart().getSymbol();
                String string2 = StockpickerBacktestEngine.createBasketName(string);
                chartSetup = chartSetup.getClone(string2);
            }
            stockpickerBacktestEngine.registerProgressListener(new IBacktestProgressListener(){

                @Override
                public void setProgress(int n) {
                    BacktestRunner.this.setJobProgress(n);
                }

                @Override
                public void increaseProgressStep() {
                }
            });
            stockpickerBacktestEngine.addSetup(this.backtestSettings.getSettingsMap(chartSetup));
            stockpickerBacktestEngine.addStrategyXml(this.backtestSettings.elStrategy);
            stockpickerBacktestEngine.setLastSettings(this.lastSettingsXml);
            resultsGroup = stockpickerBacktestEngine.runBacktest(this.backtestSettings.strategyName);
            this.globalATR = stockpickerBacktestEngine.getGlobalATR();
        } else {
            BacktestEngine backtestEngine = new BacktestEngine(TraderSimulators.getSimulator(chartSetup));
            backtestEngine.setSingleThreaded(true);
            backtestEngine.setStopPauseEngine(this.stopPauseEngine);
            backtestEngine.setLastSettings(this.lastSettingsXml);
            backtestEngine.registerProgressListener(new IBacktestProgressListener(){

                @Override
                public void setProgress(int n) {
                    BacktestRunner.this.setJobProgress(n);
                }

                @Override
                public void increaseProgressStep() {
                }
            });
            backtestEngine.addSetup(this.backtestSettings.getSettingsMap(chartSetup));
            resultsGroup = backtestEngine.runBacktest(this.backtestSettings.strategyName, this.backtestSettings.mainResultKey, false, this.backtestSettings.removeEndOfTestOrders).getResults();
            this.globalATR = backtestEngine.getGlobalATR();
        }
        return resultsGroup;
    }

    protected void setJobProgress(double d) {
        if (this.parentGridJob == null) {
            return;
        }
        double d2 = this.currentProgressStep / this.totalProgressSteps + this.progressStepWeight * d / 100.0;
        this.parentGridJob.sendProgress((int)(d2 * 100.0));
    }

    private boolean globalConditionsPassed(ResultsGroup resultsGroup, int n) {
        int n2;
        if (n == 2) {
            return true;
        }
        ArrayList<Condition> arrayList = null;
        if (n == 1) {
            arrayList = this.backtestSettings.initialGenerationConditions;
            n2 = 100000;
        } else {
            arrayList = this.backtestSettings.rankingConditions;
            n2 = 200000;
        }
        if (arrayList != null && arrayList.size() > 0) {
            for (int i = 0; i < arrayList.size(); ++i) {
                Condition condition = arrayList.get(i);
                if (!condition.isUsed() || condition.isCrossCheckCondition() || condition.isPortfolioCondition() && this.isCrossCheckRetestOnAdditionalMarketsUsed() || !this.fitnessComputed && condition.isFitnessCondition()) continue;
                try {
                    boolean bl = this.conditionsChecker.check(resultsGroup, condition);
                    if (bl) continue;
                    this.dismissalReason = n2 + i;
                    this.dismissalMessage = n == 1 ? L.t((String)"Initial population filter", (Object[])new Object[0]) + ": " + this.conditionsChecker.dismissalMessage : L.t((String)"Global filter", (Object[])new Object[0]) + ":" + this.conditionsChecker.dismissalMessage;
                    return false;
                }
                catch (Exception exception) {
                    Log.error("Error while checking condition", (Throwable)exception);
                    this.dismissalReason = 10003;
                    this.dismissalMessage = L.t((String)"Error while evaluating conditions: %s", (Object[])new Object[]{exception.getMessage()});
                    return false;
                }
            }
        }
        return true;
    }

    private boolean isCrossCheckRetestOnAdditionalMarketsUsed() {
        if (!this.backtestSettings.useCrossChecks) {
            return false;
        }
        for (int i = 0; i < this.backtestSettings.crossChecks.size(); ++i) {
            ICrossCheck iCrossCheck = this.backtestSettings.crossChecks.get(i);
            if (!iCrossCheck.getSettingName().equals("RetestOnAdditionalMarkets")) continue;
            return true;
        }
        return false;
    }

    public void stop() {
        this.stopPauseEngine.stop();
    }

    public void setStrategy(Element element) {
        this.backtestSettings.elStrategy = element;
    }

    public void setStrategyName(String string) {
        this.strategyName = string;
    }

    public void setEvolution(boolean bl) {
        this.isEvolution = bl;
    }

    public BacktestSettings getBacktestSettings() {
        return this.backtestSettings;
    }

    static /* synthetic */ double access$008(BacktestRunner backtestRunner) {
        double d = backtestRunner.currentProgressStep;
        backtestRunner.currentProgressStep = d + 1.0;
        return d;
    }
}

