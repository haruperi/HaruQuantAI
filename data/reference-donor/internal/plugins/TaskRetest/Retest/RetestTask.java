/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.basket.BasketDto
 *  com.strategyquant.datalib.basket.BasketOfStocksManager
 *  com.strategyquant.datalib.basket.StockDto
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.datalib.dataseries.DoubleListCache
 *  com.strategyquant.gridlib.client.GridClient
 *  com.strategyquant.gridlib.client.GridMessage
 *  com.strategyquant.gridlib.client.IGridMessageListener
 *  com.strategyquant.gridlib.client.JobDetails
 *  com.strategyquant.gridlib.client.RunningStatus
 *  com.strategyquant.gridlib.client.SQGrid
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.SettingsMap
 *  com.strategyquant.lib.TaskStoppedException
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.memory.MemoryUsageChecker
 *  com.strategyquant.pluginlib.annotations.Category
 *  com.strategyquant.pluginlib.annotations.License
 *  com.strategyquant.pluginlib.annotations.Name
 *  com.strategyquant.pluginlib.annotations.ShortDesc
 *  com.strategyquant.tradinglib.ATM
 *  com.strategyquant.tradinglib.BadStrategyException
 *  com.strategyquant.tradinglib.ChartSetup
 *  com.strategyquant.tradinglib.CommissionsMethod
 *  com.strategyquant.tradinglib.CustomAnalysisMethod
 *  com.strategyquant.tradinglib.Databank
 *  com.strategyquant.tradinglib.ProjectRunInfo
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.SwapMethod
 *  com.strategyquant.tradinglib.backtest.BacktestDataInitializer
 *  com.strategyquant.tradinglib.backtest.LoadDataProgressEngine
 *  com.strategyquant.tradinglib.backtestrunner.BacktestResult
 *  com.strategyquant.tradinglib.backtestrunner.DurationStats
 *  com.strategyquant.tradinglib.conditions.Condition
 *  com.strategyquant.tradinglib.crosscheck.ICrossCheck
 *  com.strategyquant.tradinglib.customanalysis.CustomAnalysisInfo
 *  com.strategyquant.tradinglib.databank.RecordNotFoundException
 *  com.strategyquant.tradinglib.engine.ChartSetups
 *  com.strategyquant.tradinglib.exception.TaskErrorInfo
 *  com.strategyquant.tradinglib.options.TradingOptions
 *  com.strategyquant.tradinglib.project.ILastEventListener
 *  com.strategyquant.tradinglib.project.IProgressStatusListener
 *  com.strategyquant.tradinglib.project.ProgressEngine
 *  com.strategyquant.tradinglib.project.ProjectConfigHelper
 *  com.strategyquant.tradinglib.project.ProjectEngine
 *  com.strategyquant.tradinglib.project.ProjectGlobalLog
 *  com.strategyquant.tradinglib.project.ProjectResources
 *  com.strategyquant.tradinglib.project.SQProject
 *  com.strategyquant.tradinglib.project.StopPauseEngine
 *  com.strategyquant.tradinglib.results.SpecialValues
 *  com.strategyquant.tradinglib.strategy.StrategyMerger
 *  com.strategyquant.tradinglib.taskImpl.AbstractTask
 *  com.strategyquant.tradinglib.taskImpl.ISQTask
 *  net.xeoh.plugins.base.annotations.PluginImplementation
 *  net.xeoh.plugins.base.annotations.meta.Author
 *  org.jdom2.Element
 *  org.jdom2.JDOMException
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Task.impl.Retest;

import com.strategyquant.datalib.basket.BasketDto;
import com.strategyquant.datalib.basket.BasketOfStocksManager;
import com.strategyquant.datalib.basket.StockDto;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.datalib.dataseries.DoubleListCache;
import com.strategyquant.gridlib.client.GridClient;
import com.strategyquant.gridlib.client.GridMessage;
import com.strategyquant.gridlib.client.IGridMessageListener;
import com.strategyquant.gridlib.client.JobDetails;
import com.strategyquant.gridlib.client.RunningStatus;
import com.strategyquant.gridlib.client.SQGrid;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.SettingsMap;
import com.strategyquant.lib.TaskStoppedException;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.memory.MemoryUsageChecker;
import com.strategyquant.plugin.Task.impl.Retest.RetestJob;
import com.strategyquant.pluginlib.annotations.Category;
import com.strategyquant.pluginlib.annotations.License;
import com.strategyquant.pluginlib.annotations.Name;
import com.strategyquant.pluginlib.annotations.ShortDesc;
import com.strategyquant.tradinglib.ATM;
import com.strategyquant.tradinglib.BadStrategyException;
import com.strategyquant.tradinglib.ChartSetup;
import com.strategyquant.tradinglib.CommissionsMethod;
import com.strategyquant.tradinglib.CustomAnalysisMethod;
import com.strategyquant.tradinglib.Databank;
import com.strategyquant.tradinglib.ProjectRunInfo;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.SwapMethod;
import com.strategyquant.tradinglib.backtest.BacktestDataInitializer;
import com.strategyquant.tradinglib.backtest.LoadDataProgressEngine;
import com.strategyquant.tradinglib.backtestrunner.BacktestResult;
import com.strategyquant.tradinglib.backtestrunner.DurationStats;
import com.strategyquant.tradinglib.conditions.Condition;
import com.strategyquant.tradinglib.crosscheck.ICrossCheck;
import com.strategyquant.tradinglib.customanalysis.CustomAnalysisInfo;
import com.strategyquant.tradinglib.databank.RecordNotFoundException;
import com.strategyquant.tradinglib.engine.ChartSetups;
import com.strategyquant.tradinglib.exception.TaskErrorInfo;
import com.strategyquant.tradinglib.options.TradingOptions;
import com.strategyquant.tradinglib.project.ILastEventListener;
import com.strategyquant.tradinglib.project.IProgressStatusListener;
import com.strategyquant.tradinglib.project.ProgressEngine;
import com.strategyquant.tradinglib.project.ProjectConfigHelper;
import com.strategyquant.tradinglib.project.ProjectEngine;
import com.strategyquant.tradinglib.project.ProjectGlobalLog;
import com.strategyquant.tradinglib.project.ProjectResources;
import com.strategyquant.tradinglib.project.SQProject;
import com.strategyquant.tradinglib.project.StopPauseEngine;
import com.strategyquant.tradinglib.results.SpecialValues;
import com.strategyquant.tradinglib.strategy.StrategyMerger;
import com.strategyquant.tradinglib.taskImpl.AbstractTask;
import com.strategyquant.tradinglib.taskImpl.ISQTask;
import java.io.IOException;
import java.io.Serializable;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Timer;
import java.util.TimerTask;
import java.util.UUID;
import java.util.concurrent.atomic.AtomicInteger;
import net.xeoh.plugins.base.annotations.PluginImplementation;
import net.xeoh.plugins.base.annotations.meta.Author;
import org.jdom2.Element;
import org.jdom2.JDOMException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@Author(name="Tamas Takacs")
@Name(name="RetestTask plugin")
@Category(name="Task")
@License(text="")
@ShortDesc(text="Short description")
@PluginImplementation
public class RetestTask
extends AbstractTask
implements IProgressStatusListener,
ILastEventListener {
    public static final Logger Log = LoggerFactory.getLogger(RetestTask.class);
    private static final String LOCK_RETEST_TASK = "RetestTask";
    private ProjectRunInfo projectRunInfo = new ProjectRunInfo();
    private Databank inputDatabank;
    private Databank outputDatabank;
    private ArrayList<String> databankRecordKeys;
    private int lastProcessedIndex = 0;
    private AtomicInteger lastFinishedIndex = new AtomicInteger(0);
    private GridClient gridClient;
    private String jobGroupID;
    private long jobCount;
    private double slippage;
    private double minDistance;
    private CommissionsMethod commission;
    private SwapMethod swap;
    private int dismissBadStrategies;
    private boolean warningsBadStrategies;
    private TaskErrorInfo taskErrorInfo = null;
    private TradingOptions tradingOptions;
    private ATM atm;
    private ArrayList<Condition> conditions;
    private int retestBatchSize;
    private int originalRetestBatchSize;
    private long projectStartTime;
    private boolean useCrossChecks = false;
    private boolean evaluateAllCrossChecks = false;
    private ArrayList<ICrossCheck> crossChecks;
    private boolean deleteFailedStrategies = false;
    private boolean forceRunCrossChecks = false;
    private boolean singleThreadedOptimizations = true;
    private String lastSettingsXml;
    private Timer jobsCreationTimer;
    private int backtestMode = 1;
    private boolean createsSubJobs = false;
    private CustomAnalysisMethod caMethod;
    private String caInputArgs;
    private boolean caFilter;
    private String currentBasketDatabankRecordKey = null;
    private int currentBasketStockIndex = 0;
    private List<StockDto> currentBasketStocks = null;

    public RetestTask() throws Exception {
        this(null, null);
    }

    public RetestTask(String projectName, ProgressEngine progressEngine) throws Exception {
        super(projectName, progressEngine);
    }

    public boolean beforeStart() throws Exception {
        try {
            if (!RunningStatus.canBeStarted((int)this.getRunningStatus())) {
                Log.error("Cannot start project in incorrect running status: " + this.getRunningStatus());
                return false;
            }
            DoubleListCache.resetStats();
            this.progressEngine.setLogPrefix(this.taskLogPrefix);
            this.progressEngine.printToLog("================================");
            this.progressEngine.printToLog(L.t((String)"Starting strategies retesting...", (Object[])new Object[0]));
            this.progressEngine.start();
            this.project = ProjectEngine.get((String)this.projectName);
            this.project.resetTracking(false, false);
            this.projectRunInfo.reset(false, false);
            this.taskErrorInfo = null;
            this.inputDatabank = (Databank)this.settingsData.getParams().get("DatabankSource");
            this.outputDatabank = (Databank)this.settingsData.getParams().get("DatabankTarget");
            this.loadRecordKeys();
            if (this.databankRecordKeys.size() == 0) {
                this.progressEngine.printToLog(L.t((String)"No strategies to retest", (Object[])new Object[0]));
                return false;
            }
            ChartSetups setups = (ChartSetups)this.settingsData.getParams().get("ChartSetups");
            ProjectConfigHelper.checkAdditionalChartsAndCIndysExpected((String)this.projectName, (Databank)this.inputDatabank, (ChartSetup)setups.getMainSetup(), this.databankRecordKeys);
            ProjectConfigHelper.checkVolumeProfileBlocksAllowed((Databank)this.inputDatabank, this.databankRecordKeys);
            if (this.inputDatabank == this.outputDatabank) {
                this.progressEngine.printToLog(L.t((String)"Clearing results data", (Object[])new Object[0]));
                if (this.settingsData.getParams().containsKey("StrategiesToRetest")) {
                    this.outputDatabank.clearResultsData(this.databankRecordKeys);
                } else {
                    this.outputDatabank.clearResultsData();
                }
                this.progressEngine.printToLog(L.t((String)"Results data cleared", (Object[])new Object[0]));
            }
            this.lastProcessedIndex = 0;
            this.lastFinishedIndex.set(0);
            this.projectStartTime = System.currentTimeMillis();
            ProjectResources.addResources((ISQTask)this);
            Element taskSettings = this.getTaskElement();
            this.lastSettingsXml = XMLUtil.elementToString((Element)taskSettings);
            this.project.updateTrackingInfo(this.projectRunInfo);
            this.initParams();
            this.recognizeCustomAnalysisMethod();
            this.recognizeBacktestMode();
            this.computeOptimalBatchSize();
            this.initializeBacktestData();
            if (this.progressEngine.isStopped()) {
                this.progressEngine.printToLog(L.t((String)"Project stopped", (Object[])new Object[0]));
                return false;
            }
            return true;
        }
        catch (TaskStoppedException e) {
            return false;
        }
    }

    private void recognizeCustomAnalysisMethod() {
        CustomAnalysisInfo caInfo = (CustomAnalysisInfo)this.settingsData.getParams().get("CustomAnalysis");
        if (caInfo != null) {
            this.caMethod = caInfo.method;
            this.caFilter = caInfo.filter;
            this.caInputArgs = caInfo.inputArgs;
        }
    }

    private void loadRecordKeys() {
        this.databankRecordKeys = this.settingsData.getParams().containsKey("StrategiesToRetest") ? (ArrayList)this.settingsData.getParams().get("StrategiesToRetest") : this.inputDatabank.getRecordKeys();
    }

    private void recognizeBacktestMode() {
        this.backtestMode = 1;
        this.createsSubJobs = false;
        if (this.useCrossChecks) {
            for (ICrossCheck crossCheck : this.crossChecks) {
                if (!crossCheck.doesCreateSubjobs()) continue;
                this.createsSubJobs = true;
                this.backtestMode = 0;
                break;
            }
        }
    }

    private void initializeBacktestData() throws Exception {
        ArrayList chartSetups = (ArrayList)this.settingsData.getParams().get("ChartSetups");
        BacktestDataInitializer bdi = new BacktestDataInitializer(new LoadDataProgressEngine(this.progressEngine), chartSetups, this.useCrossChecks, this.crossChecks);
        bdi.prepareData();
    }

    private void computeOptimalBatchSize() {
        this.retestBatchSize = 5;
        this.singleThreadedOptimizations = true;
        int totalCores = SQGrid.getGridClient().getUsedComputedThreads();
        int strategiesToTest = this.inputDatabank.size();
        if (strategiesToTest <= totalCores / 2) {
            this.singleThreadedOptimizations = false;
        }
        Log.info("Batch size computed to: {}, SingleOptims: {}, str to test: {}, totalCores: {}, Backtest mode: {}", new Object[]{this.retestBatchSize, this.singleThreadedOptimizations, strategiesToTest, totalCores, this.backtestMode});
        this.originalRetestBatchSize = this.retestBatchSize;
    }

    public void start() throws Exception {
        if (!this.beforeStart()) {
            this.progressEngine.finish();
            return;
        }
        if (this.progressEngine != null) {
            this.jobGroupID = UUID.randomUUID().toString();
            this.jobCount = 0L;
            this.gridClient = SQGrid.getGridClient();
            this.gridClient.registerMessageListener(this.jobGroupID, new IGridMessageListener(){

                public void messageReceived(GridMessage message) {
                    RetestTask.this.processMessage(message);
                }
            });
            this.progressEngine.registerStatusListener((IProgressStatusListener)this);
        }
        if (this.backtestMode == 1) {
            this.createNewBatch(this.retestBatchSize);
            TimerTask repeatedTask = new TimerTask(){

                @Override
                public void run() {
                    try {
                        RetestTask.this.createNewBatch(RetestTask.this.retestBatchSize);
                        RetestTask.this.checkAllFinished();
                    }
                    catch (Exception e) {
                        e.printStackTrace();
                        Log.error("Timer error", (Throwable)e);
                    }
                }
            };
            this.jobsCreationTimer = new Timer("RetesterTimer");
            long delay = 200L;
            long period = 300L;
            this.jobsCreationTimer.scheduleAtFixedRate(repeatedTask, delay, period);
        } else {
            this.createSerialJobs();
        }
    }

    private synchronized void createSerialJobs() throws Exception {
        this.submitNextJob();
        long runningJobs = SQGrid.getGridClient().countRunningJobs(null);
        long waitingJobs = SQGrid.getGridClient().countWaitingJobs(null);
        int totalCores = SQGrid.getGridClient().getUsedComputedThreads();
        long freeCores = (long)totalCores - runningJobs - waitingJobs;
        if (freeCores > 8L) {
            this.submitNextJob();
        }
        if (!this.createsSubJobs) {
            if (totalCores > 8) {
                this.submitNextJob();
            }
            if (totalCores > 16) {
                this.submitNextJob();
            }
            if (totalCores > 24) {
                this.submitNextJob();
            }
            if (totalCores > 32) {
                this.submitNextJob();
            }
            if (totalCores > 40) {
                this.submitNextJob();
            }
            if (totalCores >= 47) {
                this.submitNextJob();
            }
        }
    }

    private synchronized void submitNextJob() throws Exception {
        this.createNewBatch(1);
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private synchronized boolean createNewBatch(int batchSize) throws Exception {
        long runningJobs = SQGrid.getGridClient().countRunningJobs(this.jobGroupID);
        long waitingJobs = SQGrid.getGridClient().countWaitingJobs(this.jobGroupID);
        if (batchSize != 1) {
            batchSize = this.retestBatchSize;
            if (waitingJobs > (long)batchSize) {
                int temp = (int)Math.round((double)this.retestBatchSize * 0.8);
                int limit = (int)Math.round((double)batchSize * 1.2);
                if (waitingJobs > (long)limit && temp > this.originalRetestBatchSize / 3 && temp > 1) {
                    this.retestBatchSize = temp;
                }
                return true;
            }
            if (waitingJobs == 0L) {
                int temp = (int)Math.round((double)this.retestBatchSize * 1.3);
                if (temp <= this.originalRetestBatchSize * 10) {
                    this.retestBatchSize = temp;
                }
                batchSize = this.retestBatchSize;
            }
        }
        this.progressEngine.checkPaused();
        ArrayList<RetestJob> jobsGroup = new ArrayList<RetestJob>();
        if (this.currentBasketDatabankRecordKey != null && this.currentBasketStocks != null && this.currentBasketStockIndex < this.currentBasketStocks.size()) {
            try {
                ResultsGroup rg = this.inputDatabank.getLocked(this.currentBasketDatabankRecordKey, LOCK_RETEST_TASK);
                try {
                    RetestJob job = this.createJobForStock(rg, this.currentBasketStocks.get(this.currentBasketStockIndex));
                    if (job != null) {
                        jobsGroup.add(job);
                    }
                }
                finally {
                    if (rg != null) {
                        rg.releaseLock(LOCK_RETEST_TASK);
                    }
                }
                this.updateBasketIndex(this.currentBasketStockIndex + 1);
            }
            catch (RecordNotFoundException e) {
                this.updateBasketIndex(this.currentBasketStockIndex + 1);
            }
        }
        if (jobsGroup.isEmpty()) {
            for (int i = 0; i < batchSize && this.lastProcessedIndex < this.databankRecordKeys.size(); ++i) {
                if (this.progressEngine.isStopped()) {
                    return false;
                }
                String databankKey = this.databankRecordKeys.get(this.lastProcessedIndex);
                ++this.lastProcessedIndex;
                try {
                    ResultsGroup rg = this.inputDatabank.getLocked(databankKey, LOCK_RETEST_TASK);
                    try {
                        ChartSetups cs = (ChartSetups)this.settingsData.getParams().get("ChartSetups");
                        int engine = cs.getMainSetup().getBacktestEngine();
                        String symbol = cs.getMainSetup().getSymbol();
                        if (engine == -1816889229 && DataManager.isGroupAlias((String)symbol)) {
                            BasketDto dto = BasketOfStocksManager.getInstance().getBasket(symbol);
                            if (dto == null) {
                                throw new Exception(L.t((String)"Group with name '{0}' not found.", (Object[])new Object[]{symbol}));
                            }
                            List stocks = BasketOfStocksManager.getInstance().getStocks(dto.getId().intValue());
                            if (stocks.isEmpty()) continue;
                            RetestJob job = this.createJobForStock(rg, (StockDto)stocks.get(0));
                            if (job == null) {
                                this.progressEngine.printToLog(L.t((String)"Result '%s' doesn't contain strategy, skipping!", (Object[])new Object[]{rg.getName()}));
                                continue;
                            }
                            jobsGroup.add(job);
                            if (stocks.size() <= 1) continue;
                            this.currentBasketDatabankRecordKey = databankKey;
                            this.currentBasketStockIndex = 1;
                            this.currentBasketStocks = stocks;
                            continue;
                        }
                        Map<String, Serializable> params = this.getParams(rg);
                        if (params == null) {
                            this.progressEngine.printToLog(L.t((String)"Result '%s' doesn't contain strategy, skipping!", (Object[])new Object[]{rg.getName()}));
                            continue;
                        }
                        String jobID = rg.getName() + this.jobCount++;
                        jobsGroup.add(new RetestJob(jobID, params, (StopPauseEngine)this.progressEngine, this, this.lastSettingsXml));
                        continue;
                    }
                    finally {
                        if (rg != null) {
                            rg.releaseLock(LOCK_RETEST_TASK);
                        }
                    }
                }
                catch (RecordNotFoundException recordNotFoundException) {
                    // empty catch block
                }
            }
        }
        if (jobsGroup.size() > 0) {
            this.gridClient.executeOnGrid(this.jobGroupID, jobsGroup);
            return true;
        }
        return false;
    }

    private RetestJob createJobForStock(ResultsGroup rg, StockDto stock) throws Exception {
        Map<String, Serializable> params = this.getParams(rg);
        if (params == null) {
            return null;
        }
        ChartSetups cs = (ChartSetups)params.get("ChartSetups");
        ChartSetup mainSetup = cs.getMainSetup();
        mainSetup.getMainChart().setSymbol(stock.getTicker());
        params.put("ChartSetups", (Serializable)cs.getClone());
        params.put("StrategyName", (Serializable)((Object)(rg.getName() + "_" + stock.getTicker())));
        String jobID = rg.getName() + "_" + stock.getTicker() + this.jobCount++;
        return new RetestJob(jobID, params, (StopPauseEngine)this.progressEngine, this, this.lastSettingsXml);
    }

    private void updateBasketIndex(int newIndex) {
        if (this.currentBasketStocks == null || newIndex >= this.currentBasketStocks.size()) {
            this.currentBasketDatabankRecordKey = null;
            this.currentBasketStockIndex = 0;
            this.currentBasketStocks = null;
        } else {
            this.currentBasketStockIndex = newIndex;
        }
    }

    private Map<String, Serializable> getParams(ResultsGroup rg) throws Exception {
        Element strategyXml = rg.getStrategyXml();
        if (strategyXml == null) {
            return null;
        }
        HashMap<String, Serializable> params = new HashMap<String, Serializable>();
        params.putAll(this.settingsData.getParams());
        params.put("StrategyXml", (Serializable)strategyXml);
        params.put("StrategyName", (Serializable)((Object)rg.getName()));
        params.put("StrategyNote", (Serializable)((Object)rg.specialValues().getString(SpecialValues.Note, null)));
        params.put("Slippage", Double.valueOf(this.slippage));
        params.put("MinDistance", Double.valueOf(this.minDistance));
        params.put("Commission", (Serializable)this.commission);
        params.put("Swap", (Serializable)this.swap);
        params.put("DismissBadStrategies", Integer.valueOf(this.dismissBadStrategies));
        params.put("StrategyDismissWarnings", Boolean.valueOf(this.warningsBadStrategies));
        params.put("TradingOptions", (Serializable)this.tradingOptions.getClone());
        params.put("ATM", (Serializable)(this.atm == null ? null : this.atm.getClone()));
        params.put("Conditions", this.conditions);
        params.put("CrossChecks.EvaluateAll", Boolean.valueOf(this.evaluateAllCrossChecks));
        params.put("DeleteFailedStrategies", Boolean.valueOf(this.deleteFailedStrategies));
        params.put("ForceRunCrossChecks", Boolean.valueOf(this.forceRunCrossChecks));
        params.put("IsRetester", Boolean.valueOf(true));
        if (this.backtestMode == 0) {
            params.put("SingleThreadedOptimizations", Boolean.valueOf(false));
        } else {
            params.put("SingleThreadedOptimizations", Boolean.valueOf(this.singleThreadedOptimizations));
        }
        ArrayList clonedCrossChecks = !this.useCrossChecks ? this.crossChecks : ProjectConfigHelper.cloneCrossChecks(this.crossChecks);
        params.put("CrossChecks", clonedCrossChecks);
        if (rg.specialValues().containsKey(SpecialValues.IsMergedPortfolio)) {
            params.put("PortfolioMergedStrategies", (ArrayList)StrategyMerger.getSplitResults((ResultsGroup)rg));
        }
        params.put("DateGenerated", Long.valueOf(rg.specialValues().getLong(SpecialValues.DateGenerated, -1L)));
        return params;
    }

    private void initParams() throws JDOMException, IOException, Exception {
        this.slippage = (Double)((Serializable)this.settingsData.getParams().get("Slippage"));
        this.minDistance = (Double)((Serializable)this.settingsData.getParams().get("MinDistance"));
        this.commission = (CommissionsMethod)this.settingsData.getParams().get("Commission");
        this.swap = (SwapMethod)this.settingsData.getParams().get("Swap");
        this.dismissBadStrategies = this.settingsData.getParams().get("StrategyDismissSettings") != null ? (Integer)((Serializable)this.settingsData.getParams().get("StrategyDismissSettings")) : 0;
        this.warningsBadStrategies = this.settingsData.getParams().get("StrategyDismissWarnings") != null ? (Boolean)((Serializable)this.settingsData.getParams().get("StrategyDismissWarnings")) : false;
        this.tradingOptions = (TradingOptions)this.settingsData.getParams().get("TradingOptions");
        this.atm = (ATM)this.settingsData.getParams().get("ATM");
        this.conditions = (ArrayList)this.settingsData.getParams().get("Conditions");
        this.useCrossChecks = SettingsMap.getBool(this.settingsData.getParams().get("UseRobustnessTests"), (boolean)false);
        this.crossChecks = (ArrayList)this.settingsData.getParams().get("CrossChecks");
        this.evaluateAllCrossChecks = SettingsMap.getBool(this.settingsData.getParams().get("CrossChecks.EvaluateAll"), (boolean)false);
        this.deleteFailedStrategies = SettingsMap.getBool(this.settingsData.getParams().get("DeleteFailedStrategies"), (boolean)false);
        this.forceRunCrossChecks = SettingsMap.getBool(this.settingsData.getParams().get("ForceRunCrossChecks"), (boolean)false);
    }

    protected void progressStatusChanged(int status) {
        if (status == 4) {
            this.gridClient.stop(this.jobGroupID);
            this.progressEngine.unregisterStatusListener((IProgressStatusListener)this);
            if (this.jobsCreationTimer != null) {
                this.jobsCreationTimer.cancel();
                this.jobsCreationTimer = null;
            }
        } else if (status == 3) {
            this.retestFinished();
        }
    }

    private void retestFinished() {
        this.progressEngine.unregisterStatusListener((IProgressStatusListener)this);
    }

    public void onStatusChanged(int status) {
        this.progressStatusChanged(status);
    }

    protected void processMessage(GridMessage message) {
        block32: {
            try {
                if (SQProject.isMemoryProtectionUsed()) {
                    MemoryUsageChecker.checkAvailableMemory();
                }
                if (message.getMessageID() != 1) break block32;
                try {
                    int dismissalReason = 0;
                    int backtestsInJob = 0;
                    boolean passed = false;
                    JobDetails jobDetails = message.getJobDetails();
                    DurationStats durationStats = null;
                    if (jobDetails.isSuccess()) {
                        BacktestResult result = (BacktestResult)message.getData();
                        durationStats = result.getDurationStats();
                        backtestsInJob = result.getBacktestsInJob();
                        ResultsGroup rg = result.getResult();
                        if (rg != null) {
                            String strategyName = rg.getName();
                            String deleteReason = null;
                            dismissalReason = result.getDismissalReason();
                            if (result.isDismissed()) {
                                if (result.getDismissalMessage() != null) {
                                    this.progressEngine.printToLogDebug(result.getDismissalMessage());
                                }
                                if (this.deleteFailedStrategies && !SpecialValues.FiltersResultPassed.equals(rg.specialValues().getString(SpecialValues.FiltersResultFailedReason))) {
                                    String failedReason = rg.specialValues().getString(SpecialValues.FiltersResultFailedReason);
                                    if (failedReason == null) {
                                        failedReason = "N/A";
                                    }
                                    deleteReason = L.t((String)"deleted from databank, failed: %s", (Object[])new Object[]{failedReason});
                                    if (this.inputDatabank == this.outputDatabank) {
                                        this.inputDatabank.remove(rg.getName(), true, true, true, true, LOCK_RETEST_TASK);
                                    }
                                }
                            } else {
                                if (!this.warningsBadStrategies && !rg.isStockpickerStrategy()) {
                                    rg.specialValues().set("StrategyProblems", (Object)0);
                                }
                                passed = true;
                            }
                            if (deleteReason == null) {
                                boolean caFilterResult = true;
                                boolean caRemoved = false;
                                if (this.caMethod != null) {
                                    this.caMethod.setInputArgs(this.caInputArgs);
                                    caFilterResult = this.caMethod.filterStrategy(this.project.getName(), this.project.getActiveTaskName(), this.outputDatabank.getName(), rg);
                                    if (!caFilterResult && this.caFilter) {
                                        if (this.deleteFailedStrategies) {
                                            deleteReason = L.t((String)"deleted from databank, failed: Custom analysis", (Object[])new Object[0]);
                                            if (this.inputDatabank == this.outputDatabank) {
                                                this.inputDatabank.remove(rg.getName(), true, true, true, true, LOCK_RETEST_TASK);
                                                caRemoved = true;
                                            }
                                        } else {
                                            rg.specialValues().setString(SpecialValues.FiltersResultFailedReason, BadStrategyException.getReasonAsString((int)10038));
                                            dismissalReason = 10038;
                                            result.dismiss("Failed: Custom analysis", dismissalReason);
                                        }
                                    }
                                }
                                if (!caRemoved) {
                                    if (passed && (caFilterResult || !this.caFilter)) {
                                        this.project.increaseStrategiesPassed();
                                    } else {
                                        this.project.increaseStrategiesFailed();
                                    }
                                    rg.setLastSettings(this.lastSettingsXml);
                                    rg.removeUnsavableSettings();
                                    rg.setDatabank(this.outputDatabank);
                                    if (this.inputDatabank == this.outputDatabank) {
                                        this.outputDatabank.update(rg.getName(), rg, true, LOCK_RETEST_TASK);
                                    } else {
                                        this.outputDatabank.add(rg, true);
                                    }
                                    this.outputDatabank.updateBestResults(rg);
                                }
                            }
                            this.printNewStrategyToLog(jobDetails, strategyName, deleteReason, durationStats);
                        } else {
                            String error;
                            if (result.isDismissed()) {
                                error = result.getDismissalMessage();
                                this.project.increaseStrategiesFailed();
                            } else {
                                error = "Result is null!";
                            }
                            this.printNewStrategyToLog(jobDetails, jobDetails.getJobID(), error, durationStats);
                        }
                    } else {
                        this.printNewStrategyToLog(jobDetails, jobDetails.getJobID(), null, durationStats);
                        dismissalReason = 10001;
                    }
                    long runningJobCount = this.gridClient.countRunningJobs(this.jobGroupID);
                    this.project.trackJob(jobDetails, dismissalReason, durationStats, backtestsInJob, runningJobCount, this.gridClient.countWaitingJobs(this.jobGroupID));
                    this.project.increaseTrackingInfoStep(this.databankRecordKeys.size());
                    this.project.loadTrackingInfo(this.projectRunInfo, false);
                    ProjectRunInfo tempPRI = this.project.getTrackingInfo();
                    tempPRI.infiniteProgress = false;
                    tempPRI.timeToFinish = ((long)this.databankRecordKeys.size() - this.projectRunInfo.totalJobsDone) * this.projectRunInfo.timePerStrategy;
                    tempPRI.progressPercent = 100.0f * (float)this.projectRunInfo.totalJobsDone / (float)this.databankRecordKeys.size();
                    this.project.increaseGlobalStats(this.getCustomName().hashCode(), L.t((String)"Retested", (Object[])new Object[0]), 1L, L.t((String)"Passed", (Object[])new Object[0]), passed ? 1L : 0L);
                }
                catch (Exception e) {
                    Log.error("Error while processing strategy result", (Throwable)e);
                    this.progressEngine.printToLog(L.t((String)"GRID: Error while processing strategy result - %s", (Object[])new Object[]{e.getMessage()}));
                }
                if (this.backtestMode == 0) {
                    try {
                        this.createSerialJobs();
                    }
                    catch (Exception e) {
                        Log.error("Error while creating batch of jobs", (Throwable)e);
                        this.progressEngine.printToLog(L.t((String)"GRID: Error while creating batch of jobs - %s", (Object[])new Object[]{e.getMessage()}));
                        this.progressEngine.stop();
                    }
                }
                int lfiValue = this.lastFinishedIndex.incrementAndGet();
                this.checkAllFinished();
            }
            catch (OutOfMemoryError e) {
                this.gridClient.stop(this.jobGroupID);
                this.project.onMemoryError((Error)e);
            }
        }
    }

    protected void checkAllFinished() {
        boolean allStrategiesProcessed;
        if (this.progressEngine.isFinished()) {
            if (this.jobsCreationTimer != null) {
                this.jobsCreationTimer.cancel();
                this.jobsCreationTimer = null;
            }
            return;
        }
        int lfiValue = this.lastFinishedIndex.get();
        boolean bl = allStrategiesProcessed = this.lastProcessedIndex >= this.databankRecordKeys.size() && this.currentBasketDatabankRecordKey == null;
        if (lfiValue >= this.databankRecordKeys.size() && this.gridClient.countRunningJobs(this.jobGroupID) <= 1L && this.gridClient.countWaitingJobs(this.jobGroupID) == 0L && allStrategiesProcessed) {
            if (this.jobsCreationTimer != null) {
                this.jobsCreationTimer.cancel();
                this.jobsCreationTimer = null;
            }
            this.gridClient.stop(this.jobGroupID);
            this.progressEngine.finish(System.currentTimeMillis() - this.projectStartTime);
            this.outputDatabank.updateBestResults();
            this.project.bestResults.resetLastData();
            this.project.publisher.resetLastData("best-results-channel");
        }
    }

    private void printNewStrategyToLog(JobDetails jobDetails, String strategyName, String message, DurationStats durationStats) {
        StringBuffer logText = new StringBuffer("Tested ");
        logText.append(strategyName);
        if (durationStats != null) {
            HashMap durations = durationStats.getMap();
            for (String key : durationStats.getKeys()) {
                if (key.equals(DurationStats.MainTest)) {
                    logText.append("\n   - " + key + " - ");
                } else {
                    logText.append("\n   - " + L.t((String)"Cross check", (Object[])new Object[0]) + " - " + key + " - ");
                }
                logText.append(L.t((String)"OK in %s s.", (Object[])new Object[]{String.format("%.2f", durations.get(key))}));
            }
        }
        if (message != null) {
            logText.append("\n   - " + message);
        }
        this.progressEngine.printToLogDebug(logText.toString());
    }

    public String getType() {
        return "Retest";
    }

    public String getPluginFolderName() {
        return "TaskRetest";
    }

    public String getName() {
        return L.tsq((String)"Retest strategies");
    }

    public ISQTask clone(String projectName, ProgressEngine progressEngine) throws Exception {
        RetestTask task = new RetestTask(projectName, progressEngine);
        task.settingTabPlugins = this.settingTabPlugins;
        return task;
    }

    public int getPreferredPosition() {
        return 1;
    }

    public String[] getSettings() {
        return new String[]{"Data", "Notes", "RiskMoneyManagement", "Rankings", "Options", "CrossChecks", "Databanks", "ATMs"};
    }

    protected int getRunningStatus() {
        return this.progressEngine.getRunningStatus();
    }

    protected Databank[] getUsedDatabanks() {
        return new Databank[]{this.inputDatabank, this.outputDatabank};
    }

    protected Databank getOutputDatabank() {
        return this.outputDatabank;
    }

    public void logTaskFinished(ProjectGlobalLog log) {
        super.logTaskFinished(log);
        ProjectRunInfo runInfo = this.project.getTrackingInfo();
        String text = L.t((String)"Total tested", (Object[])new Object[0]) + ": " + runInfo.totalJobsDone + ", " + L.t((String)"Time per strategy", (Object[])new Object[0]) + ": " + SQUtils.formatDuration((long)runInfo.timePerStrategy) + ", " + L.t((String)"Passed", (Object[])new Object[0]) + ": " + runInfo.strategiesPassed + ", " + L.t((String)"Failed", (Object[])new Object[0]) + ": " + runInfo.strategiesFailed;
        log.print(text);
        log.addDurationStats(runInfo);
        log.addDismissalStats(runInfo, (ISQTask)this);
        log.addAcceptedStats(runInfo, (ISQTask)this);
    }

    public void setLastEvent(String message) {
        if (this.project != null) {
            this.project.setLastEvent(message);
        }
    }

    public String getProduct() {
        return "SQUANTAlgoWizardAlgoWizardStandaloneBACKTESTNODE";
    }
}

