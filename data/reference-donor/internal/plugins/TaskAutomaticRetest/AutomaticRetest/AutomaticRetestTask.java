/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.gridlib.client.GridClient
 *  com.strategyquant.gridlib.client.GridMessage
 *  com.strategyquant.gridlib.client.IGridMessageListener
 *  com.strategyquant.gridlib.client.JobDetails
 *  com.strategyquant.gridlib.client.RunningStatus
 *  com.strategyquant.gridlib.client.SQGrid
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.SettingsMap
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.memory.MemoryUsageChecker
 *  com.strategyquant.pluginlib.SQPluginManager
 *  com.strategyquant.pluginlib.annotations.Category
 *  com.strategyquant.pluginlib.annotations.License
 *  com.strategyquant.pluginlib.annotations.Name
 *  com.strategyquant.pluginlib.annotations.ShortDesc
 *  com.strategyquant.tradinglib.BadStrategyException
 *  com.strategyquant.tradinglib.CustomAnalysisMethod
 *  com.strategyquant.tradinglib.Databank
 *  com.strategyquant.tradinglib.ProjectRunInfo
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.backtest.AutoRetestStrategyConfigModifier
 *  com.strategyquant.tradinglib.backtestrunner.BacktestResult
 *  com.strategyquant.tradinglib.backtestrunner.DurationStats
 *  com.strategyquant.tradinglib.crosscheck.ICrossCheck
 *  com.strategyquant.tradinglib.customanalysis.CustomAnalysisInfo
 *  com.strategyquant.tradinglib.databank.RecordNotFoundException
 *  com.strategyquant.tradinglib.exception.TaskErrorInfo
 *  com.strategyquant.tradinglib.project.ILastEventListener
 *  com.strategyquant.tradinglib.project.IProgressStatusListener
 *  com.strategyquant.tradinglib.project.ProgressEngine
 *  com.strategyquant.tradinglib.project.ProjectConfigHelper
 *  com.strategyquant.tradinglib.project.ProjectEngine
 *  com.strategyquant.tradinglib.project.ProjectGlobalLog
 *  com.strategyquant.tradinglib.project.SQProject
 *  com.strategyquant.tradinglib.project.StopPauseEngine
 *  com.strategyquant.tradinglib.results.SpecialValues
 *  com.strategyquant.tradinglib.strategy.StrategyMerger
 *  com.strategyquant.tradinglib.task.settings.ISettingTabPlugin
 *  com.strategyquant.tradinglib.task.settings.SettingError
 *  com.strategyquant.tradinglib.task.settings.TaskSettingsData
 *  com.strategyquant.tradinglib.taskImpl.AbstractTask
 *  com.strategyquant.tradinglib.taskImpl.ISQTask
 *  net.xeoh.plugins.base.annotations.PluginImplementation
 *  net.xeoh.plugins.base.annotations.meta.Author
 *  org.jdom2.Element
 *  org.jdom2.JDOMException
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Task.impl.AutomaticRetest;

import com.strategyquant.gridlib.client.GridClient;
import com.strategyquant.gridlib.client.GridMessage;
import com.strategyquant.gridlib.client.IGridMessageListener;
import com.strategyquant.gridlib.client.JobDetails;
import com.strategyquant.gridlib.client.RunningStatus;
import com.strategyquant.gridlib.client.SQGrid;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.SettingsMap;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.memory.MemoryUsageChecker;
import com.strategyquant.plugin.Task.impl.AutomaticRetest.AutomaticRetestJob;
import com.strategyquant.plugin.Task.impl.AutomaticRetest.XmlChartCombinator;
import com.strategyquant.pluginlib.SQPluginManager;
import com.strategyquant.pluginlib.annotations.Category;
import com.strategyquant.pluginlib.annotations.License;
import com.strategyquant.pluginlib.annotations.Name;
import com.strategyquant.pluginlib.annotations.ShortDesc;
import com.strategyquant.tradinglib.BadStrategyException;
import com.strategyquant.tradinglib.CustomAnalysisMethod;
import com.strategyquant.tradinglib.Databank;
import com.strategyquant.tradinglib.ProjectRunInfo;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.backtest.AutoRetestStrategyConfigModifier;
import com.strategyquant.tradinglib.backtestrunner.BacktestResult;
import com.strategyquant.tradinglib.backtestrunner.DurationStats;
import com.strategyquant.tradinglib.crosscheck.ICrossCheck;
import com.strategyquant.tradinglib.customanalysis.CustomAnalysisInfo;
import com.strategyquant.tradinglib.databank.RecordNotFoundException;
import com.strategyquant.tradinglib.exception.TaskErrorInfo;
import com.strategyquant.tradinglib.project.ILastEventListener;
import com.strategyquant.tradinglib.project.IProgressStatusListener;
import com.strategyquant.tradinglib.project.ProgressEngine;
import com.strategyquant.tradinglib.project.ProjectConfigHelper;
import com.strategyquant.tradinglib.project.ProjectEngine;
import com.strategyquant.tradinglib.project.ProjectGlobalLog;
import com.strategyquant.tradinglib.project.SQProject;
import com.strategyquant.tradinglib.project.StopPauseEngine;
import com.strategyquant.tradinglib.results.SpecialValues;
import com.strategyquant.tradinglib.strategy.StrategyMerger;
import com.strategyquant.tradinglib.task.settings.ISettingTabPlugin;
import com.strategyquant.tradinglib.task.settings.SettingError;
import com.strategyquant.tradinglib.task.settings.TaskSettingsData;
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

@Author(name="Tomas Brynda")
@Name(name="AutomaticRetestTask plugin")
@Category(name="Task")
@License(text="")
@ShortDesc(text="Automatic Retester")
@PluginImplementation
public class AutomaticRetestTask
extends AbstractTask
implements ILastEventListener,
IProgressStatusListener {
    public static final Logger Log = LoggerFactory.getLogger(AutomaticRetestTask.class);
    private static final String LOCK_AUTORETEST = "AutomaticRetestTask";
    private ProjectRunInfo projectRunInfo = new ProjectRunInfo();
    private Databank inputDatabank;
    private Databank outputDatabank;
    private ArrayList<String> databankRecordKeys;
    private int lastProcessedIndex = 0;
    private AtomicInteger lastFinishedIndex = new AtomicInteger(0);
    private GridClient gridClient;
    private String jobGroupID;
    private long jobCount;
    private TaskErrorInfo taskErrorInfo = null;
    private int retestBatchSize;
    private int originalRetestBatchSize;
    private boolean singleThreadedOptimizations = true;
    private long projectStartTime;
    private boolean deleteFailedStrategies = false;
    private boolean forceRunCrossChecks = false;
    private Timer jobsCreationTimer;
    private TaskSettingsData strategyData = new TaskSettingsData();
    private ArrayList<ISettingTabPlugin> settingsPlugins = SQPluginManager.getPlugins(ISettingTabPlugin.class);
    private boolean useCrossChecks = false;
    private boolean evaluateAllCrossChecks = false;
    private ArrayList<ICrossCheck> crossChecks;
    private int backtestMode = 1;
    private boolean createsSubJobs = false;
    private boolean warningsBadStrategies;
    private CustomAnalysisMethod caMethod;
    private String caInputArgs;
    private boolean caFilter;
    private int combinations;

    public AutomaticRetestTask() throws Exception {
        this(null, null);
    }

    public AutomaticRetestTask(String projectName, ProgressEngine progressEngine) throws Exception {
        super(projectName, progressEngine);
    }

    public boolean beforeStart() throws Exception {
        if (!RunningStatus.canBeStarted((int)this.getRunningStatus())) {
            Log.error("Cannot start project in incorrect running status: " + this.getRunningStatus());
            return false;
        }
        this.progressEngine.setLogPrefix(this.taskLogPrefix);
        this.progressEngine.printToLog("================================");
        this.progressEngine.printToLog(L.t((String)"Starting strategies retesting...", (Object[])new Object[0]));
        this.progressEngine.start();
        this.lastProcessedIndex = 0;
        this.lastFinishedIndex.set(0);
        this.projectStartTime = System.currentTimeMillis();
        this.project = ProjectEngine.get((String)this.projectName);
        this.project.resetTracking(false, false);
        this.project.updateTrackingInfo(this.projectRunInfo);
        this.taskErrorInfo = null;
        this.outputDatabank = (Databank)this.settingsData.getParams().get("DatabankTarget");
        this.inputDatabank = (Databank)this.settingsData.getParams().get("DatabankSource");
        this.databankRecordKeys = this.inputDatabank.getRecordKeys();
        if (this.databankRecordKeys.size() == 0) {
            this.progressEngine.printToLog(L.t((String)"No strategies in databank, nothing to retest!", (Object[])new Object[0]));
            return false;
        }
        this.setDatabankFilter(this.outputDatabank, false);
        if (this.inputDatabank.getName().equals(this.outputDatabank.getName())) {
            this.outputDatabank.clearResultsData();
        }
        this.deleteFailedStrategies = SettingsMap.getBool(this.settingsData.getParams().get("DeleteFailedStrategies"), (boolean)false);
        this.forceRunCrossChecks = SettingsMap.getBool(this.settingsData.getParams().get("ForceRunCrossChecks"), (boolean)false);
        this.initParams();
        this.recognizeCustomAnalysisMethod();
        this.recognizeBacktestMode();
        this.computeOptimalBatchSize();
        return true;
    }

    private void recognizeCustomAnalysisMethod() {
        CustomAnalysisInfo caInfo = (CustomAnalysisInfo)this.settingsData.getParams().get("CustomAnalysis");
        if (caInfo != null) {
            this.caMethod = caInfo.method;
            this.caFilter = caInfo.filter;
            this.caInputArgs = caInfo.inputArgs;
        }
    }

    private void initParams() throws JDOMException, IOException, Exception {
        this.useCrossChecks = SettingsMap.getBool(this.settingsData.getParams().get("UseRobustnessTests"), (boolean)false);
        this.crossChecks = (ArrayList)this.settingsData.getParams().get("CrossChecks");
        this.warningsBadStrategies = (Boolean)((Serializable)this.settingsData.getParams().get("StrategyDismissWarnings"));
        this.evaluateAllCrossChecks = SettingsMap.getBool(this.settingsData.getParams().get("CrossChecks.EvaluateAll"), (boolean)false);
        this.deleteFailedStrategies = SettingsMap.getBool(this.settingsData.getParams().get("DeleteFailedStrategies"), (boolean)false);
        this.forceRunCrossChecks = SettingsMap.getBool(this.settingsData.getParams().get("ForceRunCrossChecks"), (boolean)false);
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

    private void computeOptimalBatchSize() throws Exception {
        this.retestBatchSize = 5;
        this.singleThreadedOptimizations = true;
        int totalCores = SQGrid.getGridClient().getUsedComputedThreads();
        int strategiesToTest = this.inputDatabank.size();
        XmlChartCombinator combinator = new XmlChartCombinator();
        List<Element> listSettingsVariations = combinator.getSettingXMLVariations(this.getTaskElement(), null);
        this.combinations = listSettingsVariations.size();
        if ((strategiesToTest *= this.combinations) <= totalCores / 2) {
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
                    AutomaticRetestTask.this.processMessage(message);
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
                        AutomaticRetestTask.this.createNewBatch(AutomaticRetestTask.this.retestBatchSize);
                        AutomaticRetestTask.this.checkAllFinished();
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

    protected void checkAllFinished() {
        if (this.progressEngine.isFinished()) {
            if (this.jobsCreationTimer != null) {
                this.jobsCreationTimer.cancel();
                this.jobsCreationTimer = null;
            }
            return;
        }
        int lfiValue = this.lastFinishedIndex.get();
        if (lfiValue >= this.databankRecordKeys.size() * this.combinations && this.gridClient.countRunningJobs(this.jobGroupID) <= 1L && this.gridClient.countWaitingJobs(this.jobGroupID) == 0L) {
            if (this.jobsCreationTimer != null) {
                this.jobsCreationTimer.cancel();
                this.jobsCreationTimer = null;
            }
            this.gridClient.stop(this.jobGroupID);
            this.progressEngine.finish(System.currentTimeMillis() - this.projectStartTime);
            this.outputDatabank.updateBestResults();
        }
    }

    private synchronized void submitNextJob() throws Exception {
        this.createNewBatch(1);
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

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private synchronized boolean createNewBatch(int batchSize) throws Exception {
        this.progressEngine.checkPaused();
        if (this.progressEngine.isStopped()) {
            return false;
        }
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
        ArrayList<AutomaticRetestJob> jobsGroup = new ArrayList<AutomaticRetestJob>();
        for (int i = 0; i < batchSize && this.lastProcessedIndex < this.databankRecordKeys.size(); ++i) {
            if (this.progressEngine.isStopped()) {
                return false;
            }
            String databankKey = this.databankRecordKeys.get(this.lastProcessedIndex);
            ++this.lastProcessedIndex;
            try {
                ResultsGroup rg = this.inputDatabank.getLocked(databankKey, LOCK_AUTORETEST);
                try {
                    List<Map<String, Serializable>> paramsList = this.getParams(rg);
                    if (paramsList == null) continue;
                    for (Map<String, Serializable> iParams : paramsList) {
                        String jobID = rg.getName() + this.jobCount++;
                        jobsGroup.add(new AutomaticRetestJob(jobID, iParams, (StopPauseEngine)this.progressEngine, this));
                    }
                    continue;
                }
                finally {
                    rg.releaseLock(LOCK_AUTORETEST);
                }
            }
            catch (RecordNotFoundException recordNotFoundException) {
                // empty catch block
            }
        }
        if (jobsGroup.size() > 0) {
            Log.debug("Created {} evaluation jobs", (Object)jobsGroup.size());
            this.gridClient.executeOnGrid(this.jobGroupID, jobsGroup);
            return true;
        }
        Log.debug("No more jobs to create");
        return false;
    }

    private List<Map<String, Serializable>> getParams(ResultsGroup rg) throws Exception {
        ArrayList<Map<String, Serializable>> result = new ArrayList<Map<String, Serializable>>();
        XmlChartCombinator combinator = new XmlChartCombinator();
        Element lastSettingsXML = XMLUtil.stringToElement((String)rg.getLastSettings());
        List<Element> listSettingsVariations = combinator.getSettingXMLVariations(this.getTaskElement(), lastSettingsXML);
        for (Element iSettingsVariation : listSettingsVariations) {
            HashMap<String, Object> params = new HashMap<String, Object>();
            AutoRetestStrategyConfigModifier.modifySettings((Element)lastSettingsXML, (Element)iSettingsVariation);
            this.strategyData.clear();
            for (int a = 0; a < this.settingsPlugins.size(); ++a) {
                ISettingTabPlugin plugin = this.settingsPlugins.get(a);
                if (!this.shouldReadSettings(plugin.getSettingName())) continue;
                plugin.readSettings(this.projectName, (ISQTask)this, lastSettingsXML, this.strategyData);
                if (!this.strategyData.hasErrors()) continue;
                SettingError firstError = (SettingError)this.strategyData.getErrors().get(0);
                this.progressEngine.printToLog(L.t((String)"Strategy %s skipped. %s setting error - %s", (Object[])new Object[]{rg.getName(), firstError.settingName, firstError.errorMsg}));
                return null;
            }
            params.putAll(this.strategyData.getParams());
            params.put("StrategyXml", rg.getStrategyXml());
            params.put("StrategyName", rg.getName());
            params.put("StrategyLastSettings", lastSettingsXML);
            params.put("IsRetester", true);
            params.put("DatabankSource", this.inputDatabank);
            params.put("DatabankTarget", this.outputDatabank);
            params.put("StrategyDismissWarnings", this.warningsBadStrategies);
            if (rg.specialValues().containsKey(SpecialValues.IsMergedPortfolio)) {
                params.put("PortfolioMergedStrategies", (ArrayList)StrategyMerger.getSplitResults((ResultsGroup)rg));
            }
            if (this.backtestMode == 0) {
                params.put("SingleThreadedOptimizations", false);
            } else {
                params.put("SingleThreadedOptimizations", this.singleThreadedOptimizations);
            }
            ArrayList clonedCrossChecks = !this.useCrossChecks ? this.crossChecks : ProjectConfigHelper.cloneCrossChecks((ArrayList)((ArrayList)params.get("CrossChecks")));
            params.put("CrossChecks", clonedCrossChecks);
            params.put("DateGenerated", rg.specialValues().getLong(SpecialValues.DateGenerated, -1L));
            result.add(params);
        }
        return result;
    }

    private boolean shouldReadSettings(String settingsName) {
        switch (settingsName) {
            case "Data": 
            case "RiskMoneyManagement": 
            case "Options": 
            case "Rankings": 
            case "CrossChecks": 
            case "ATMs": {
                return true;
            }
        }
        return false;
    }

    private void retestFinished() {
        this.progressEngine.unregisterStatusListener((IProgressStatusListener)this);
    }

    protected void processMessage(GridMessage message) {
        block33: {
            try {
                if (SQProject.isMemoryProtectionUsed()) {
                    MemoryUsageChecker.checkAvailableMemory();
                }
                if (message.getMessageID() != 1) break block33;
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
                                        this.inputDatabank.remove(rg.getName(), true, true, true, true, LOCK_AUTORETEST);
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
                                        if (this.deleteFailedStrategies && !SpecialValues.FiltersResultPassed.equals(rg.specialValues().getString(SpecialValues.FiltersResultFailedReason))) {
                                            deleteReason = L.t((String)"deleted from databank, failed: Custom analysis", (Object[])new Object[0]);
                                            if (this.inputDatabank == this.outputDatabank) {
                                                this.inputDatabank.remove(rg.getName(), true, true, true, true, LOCK_AUTORETEST);
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
                                    rg.removeUnsavableSettings();
                                    rg.setDatabank(this.outputDatabank);
                                    if (this.inputDatabank == this.outputDatabank) {
                                        this.outputDatabank.update(rg.getName(), rg, true, LOCK_AUTORETEST);
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
                                this.project.increaseStrategiesFailed();
                                error = result.getDismissalMessage();
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
                    if (this.project.getFailedJobsPercentage() > 0.7) {
                        this.progressEngine.printToLog(L.t((String)"GRID: Stopping retest, job failures (exceptions) exceeded 70%!", (Object[])new Object[0]));
                        this.progressEngine.stop();
                    }
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
        return "AutomaticRetest";
    }

    public String getPluginFolderName() {
        return "TaskAutomaticRetest";
    }

    public String getName() {
        return L.tsq((String)"Automatic retest");
    }

    public ISQTask clone(String projectName, ProgressEngine progressEngine) throws Exception {
        AutomaticRetestTask task = new AutomaticRetestTask(projectName, progressEngine);
        task.settingTabPlugins = this.settingTabPlugins;
        return task;
    }

    public int getPreferredPosition() {
        return 1;
    }

    public String[] getSettings() {
        return new String[]{"Databanks", "AutoRetestData", "RiskMoneyManagement", "Options", "CrossChecks", "Rankings", "ATMs"};
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
        String text = L.t((String)"Total", (Object[])new Object[0]) + ": " + runInfo.backtestsPerformed + ", " + L.t((String)"Time per strategy", (Object[])new Object[0]) + ": " + SQUtils.formatDuration((long)runInfo.timePerStrategy) + ", " + L.t((String)"Passed", (Object[])new Object[0]) + ": " + runInfo.strategiesPassed + ", " + L.t((String)"Failed", (Object[])new Object[0]) + ": " + runInfo.strategiesFailed;
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

    public void onStatusChanged(int status) {
        this.progressStatusChanged(status);
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
}

