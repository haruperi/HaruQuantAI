/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.basket.BasketDto
 *  com.strategyquant.datalib.basket.BasketOfStocksManager
 *  com.strategyquant.datalib.basket.StockDto
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.gridlib.client.RunningStatus
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.SettingsMap
 *  com.strategyquant.lib.TaskStoppedException
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.lib.memory.MemoryUsageChecker
 *  com.strategyquant.pluginlib.annotations.Category
 *  com.strategyquant.pluginlib.annotations.License
 *  com.strategyquant.pluginlib.annotations.Name
 *  com.strategyquant.pluginlib.annotations.ShortDesc
 *  com.strategyquant.pluginlib.program.Program
 *  com.strategyquant.tradinglib.ATM
 *  com.strategyquant.tradinglib.BadStrategyException
 *  com.strategyquant.tradinglib.ChartSetup
 *  com.strategyquant.tradinglib.CommissionsMethod
 *  com.strategyquant.tradinglib.CustomAnalysisMethod
 *  com.strategyquant.tradinglib.Databank
 *  com.strategyquant.tradinglib.ProjectRunInfo
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.StrategyBase
 *  com.strategyquant.tradinglib.SwapMethod
 *  com.strategyquant.tradinglib.TradingOption
 *  com.strategyquant.tradinglib.Variable
 *  com.strategyquant.tradinglib.WalkForwardResult
 *  com.strategyquant.tradinglib.backtest.BacktestDataInitializer
 *  com.strategyquant.tradinglib.backtest.LoadDataProgressEngine
 *  com.strategyquant.tradinglib.backtestrunner.DurationStats
 *  com.strategyquant.tradinglib.conditions.Condition
 *  com.strategyquant.tradinglib.conditions.ConditionsChecker
 *  com.strategyquant.tradinglib.crosscheck.CrossCheckDataNotExistException
 *  com.strategyquant.tradinglib.customanalysis.CustomAnalysisInfo
 *  com.strategyquant.tradinglib.databank.IDatabankFilter
 *  com.strategyquant.tradinglib.databank.OptimizeDatabankFilter
 *  com.strategyquant.tradinglib.engine.ChartSetups
 *  com.strategyquant.tradinglib.engine.stockpicker.StockpickerBacktestEngine
 *  com.strategyquant.tradinglib.fitnessfunction.IFitnessFunction
 *  com.strategyquant.tradinglib.optimization.IEngineLogListener
 *  com.strategyquant.tradinglib.optimization.INewResultListener
 *  com.strategyquant.tradinglib.optimization.ISequentialOptimizationCompleteListener
 *  com.strategyquant.tradinglib.optimization.IStepsListener
 *  com.strategyquant.tradinglib.optimization.OptimizationEngine
 *  com.strategyquant.tradinglib.optimization.OptimizationParams
 *  com.strategyquant.tradinglib.optimization.OptimizationSettings
 *  com.strategyquant.tradinglib.optimization.Parameter
 *  com.strategyquant.tradinglib.optimization.ParametersSettings
 *  com.strategyquant.tradinglib.optimization.SequentialOptimizationEngine
 *  com.strategyquant.tradinglib.optimization.SequentialOptimizationSettings
 *  com.strategyquant.tradinglib.optimization.WalkForwardMatrixResult
 *  com.strategyquant.tradinglib.optimization.WalkForwardParametersStability
 *  com.strategyquant.tradinglib.options.TradingOptions
 *  com.strategyquant.tradinglib.project.ILastEventListener
 *  com.strategyquant.tradinglib.project.ProgressEngine
 *  com.strategyquant.tradinglib.project.ProjectConfigHelper
 *  com.strategyquant.tradinglib.project.ProjectEngine
 *  com.strategyquant.tradinglib.project.ProjectGlobalLog
 *  com.strategyquant.tradinglib.project.ProjectResources
 *  com.strategyquant.tradinglib.project.SQProject
 *  com.strategyquant.tradinglib.project.StopPauseEngine
 *  com.strategyquant.tradinglib.results.SpecialValues
 *  com.strategyquant.tradinglib.robustnesstests.SequentialOptimizationResults
 *  com.strategyquant.tradinglib.taskImpl.AbstractTask
 *  com.strategyquant.tradinglib.taskImpl.ISQTask
 *  com.strategyquant.tradinglib.taskImpl.TaskException
 *  com.strategyquant.tradinglib.util.RngUtils
 *  net.xeoh.plugins.base.annotations.PluginImplementation
 *  net.xeoh.plugins.base.annotations.meta.Author
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Task.impl.Optimize;

import com.strategyquant.datalib.basket.BasketDto;
import com.strategyquant.datalib.basket.BasketOfStocksManager;
import com.strategyquant.datalib.basket.StockDto;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.gridlib.client.RunningStatus;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.SettingsMap;
import com.strategyquant.lib.TaskStoppedException;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.lib.memory.MemoryUsageChecker;
import com.strategyquant.pluginlib.annotations.Category;
import com.strategyquant.pluginlib.annotations.License;
import com.strategyquant.pluginlib.annotations.Name;
import com.strategyquant.pluginlib.annotations.ShortDesc;
import com.strategyquant.pluginlib.program.Program;
import com.strategyquant.tradinglib.ATM;
import com.strategyquant.tradinglib.BadStrategyException;
import com.strategyquant.tradinglib.ChartSetup;
import com.strategyquant.tradinglib.CommissionsMethod;
import com.strategyquant.tradinglib.CustomAnalysisMethod;
import com.strategyquant.tradinglib.Databank;
import com.strategyquant.tradinglib.ProjectRunInfo;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.SwapMethod;
import com.strategyquant.tradinglib.TradingOption;
import com.strategyquant.tradinglib.Variable;
import com.strategyquant.tradinglib.WalkForwardResult;
import com.strategyquant.tradinglib.backtest.BacktestDataInitializer;
import com.strategyquant.tradinglib.backtest.LoadDataProgressEngine;
import com.strategyquant.tradinglib.backtestrunner.DurationStats;
import com.strategyquant.tradinglib.conditions.Condition;
import com.strategyquant.tradinglib.conditions.ConditionsChecker;
import com.strategyquant.tradinglib.crosscheck.CrossCheckDataNotExistException;
import com.strategyquant.tradinglib.customanalysis.CustomAnalysisInfo;
import com.strategyquant.tradinglib.databank.IDatabankFilter;
import com.strategyquant.tradinglib.databank.OptimizeDatabankFilter;
import com.strategyquant.tradinglib.engine.ChartSetups;
import com.strategyquant.tradinglib.engine.stockpicker.StockpickerBacktestEngine;
import com.strategyquant.tradinglib.fitnessfunction.IFitnessFunction;
import com.strategyquant.tradinglib.optimization.IEngineLogListener;
import com.strategyquant.tradinglib.optimization.INewResultListener;
import com.strategyquant.tradinglib.optimization.ISequentialOptimizationCompleteListener;
import com.strategyquant.tradinglib.optimization.IStepsListener;
import com.strategyquant.tradinglib.optimization.OptimizationEngine;
import com.strategyquant.tradinglib.optimization.OptimizationParams;
import com.strategyquant.tradinglib.optimization.OptimizationSettings;
import com.strategyquant.tradinglib.optimization.Parameter;
import com.strategyquant.tradinglib.optimization.ParametersSettings;
import com.strategyquant.tradinglib.optimization.SequentialOptimizationEngine;
import com.strategyquant.tradinglib.optimization.SequentialOptimizationSettings;
import com.strategyquant.tradinglib.optimization.WalkForwardMatrixResult;
import com.strategyquant.tradinglib.optimization.WalkForwardParametersStability;
import com.strategyquant.tradinglib.options.TradingOptions;
import com.strategyquant.tradinglib.project.ILastEventListener;
import com.strategyquant.tradinglib.project.ProgressEngine;
import com.strategyquant.tradinglib.project.ProjectConfigHelper;
import com.strategyquant.tradinglib.project.ProjectEngine;
import com.strategyquant.tradinglib.project.ProjectGlobalLog;
import com.strategyquant.tradinglib.project.ProjectResources;
import com.strategyquant.tradinglib.project.SQProject;
import com.strategyquant.tradinglib.project.StopPauseEngine;
import com.strategyquant.tradinglib.results.SpecialValues;
import com.strategyquant.tradinglib.robustnesstests.SequentialOptimizationResults;
import com.strategyquant.tradinglib.taskImpl.AbstractTask;
import com.strategyquant.tradinglib.taskImpl.ISQTask;
import com.strategyquant.tradinglib.taskImpl.TaskException;
import com.strategyquant.tradinglib.util.RngUtils;
import java.io.File;
import java.io.Serializable;
import java.util.ArrayList;
import java.util.List;
import net.xeoh.plugins.base.annotations.PluginImplementation;
import net.xeoh.plugins.base.annotations.meta.Author;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@Author(name="Tamas Takacs")
@Name(name="OptimizeTask plugin")
@Category(name="Task")
@License(text="")
@ShortDesc(text="Short description")
@PluginImplementation
public class OptimizeTask
extends AbstractTask
implements ILastEventListener {
    public static final Logger Log = LoggerFactory.getLogger((String)"OptimizeTask");
    private static final String LOCK_OPTIMIZETASK = "OptimizeTask";
    private OptimizationSettings optimizationSettings;
    private Databank inputDatabank;
    private Databank outputDatabank;
    private ArrayList<String> strategies = new ArrayList();
    private IFitnessFunction fitnessFunction;
    private TradingOptions tradingOptions;
    private ATM atm;
    private ParametersSettings paramSettings;
    private Element taskSettings;
    private int totalSteps;
    private int progressPercent = 0;
    private int lastProcessedIndex = -1;
    private long cumulativeSteps = 0L;
    private int optimizedStrategies;
    private CustomAnalysisMethod caMethod;
    private String caInputArgs;
    private boolean caFilter;
    private String lastSettingsXml;
    protected ConditionsChecker conditionsChecker = new ConditionsChecker();
    protected int dismissalReason = 0;
    protected String dismissalMessage = "";
    private SequentialOptimizationEngine engine;

    public OptimizeTask() throws Exception {
        this(null, null);
    }

    public OptimizeTask(String projectName, ProgressEngine progressEngine) throws Exception {
        super(projectName, progressEngine);
        this.optimizationSettings = new OptimizationSettings(projectName);
    }

    public String getType() {
        return "Optimize";
    }

    public String getName() {
        return L.tsq((String)"Optimize strategies");
    }

    public ISQTask clone(String projectName, ProgressEngine progressEngine) throws Exception {
        OptimizeTask task = new OptimizeTask(projectName, progressEngine);
        task.settingTabPlugins = this.settingTabPlugins;
        return task;
    }

    private boolean beforeStart() throws Exception {
        try {
            if (!MainApp.getLicenseInfo().isProEdition()) {
                Log.info(MainApp.OnlyInProVersionTitle);
                return false;
            }
            this.checkSpecialTrialLimitation();
            ChartSetups setups = (ChartSetups)this.settingsData.getParams().get("ChartSetups");
            this.optimizationSettings = (OptimizationSettings)this.settingsData.getParams().get("OptimizationSettings");
            this.project = ProjectEngine.get((String)this.projectName);
            try {
                this.optimizationSettings.inputDatabank = this.optimizationSettings.inputDatabank != null ? this.optimizationSettings.inputDatabank : (Databank)this.project.getDatabanks().get((Object)"Results");
            }
            catch (Exception e) {
                throw new TaskException(7, e);
            }
            ProjectConfigHelper.checkAdditionalChartsAndCIndysExpected((String)this.projectName, (Databank)this.optimizationSettings.inputDatabank, (ChartSetup)setups.getMainSetup(), null);
            ProjectConfigHelper.checkVolumeProfileBlocksAllowed((Databank)this.optimizationSettings.inputDatabank, null);
            if (!RunningStatus.canBeStarted((int)this.getRunningStatus())) {
                Log.error("Cannot start project in incorrect running status: " + this.getRunningStatus());
                return false;
            }
            ProjectResources.addResources((ISQTask)this);
            this.taskSettings = this.getTaskElement();
            this.lastSettingsXml = XMLUtil.elementToString((Element)this.taskSettings);
            this.progressEngine.setLogPrefix(this.taskLogPrefix);
            this.progressEngine.printToLog("================================");
            this.progressEngine.printToLog(L.t((String)"Starting optimization...", (Object[])new Object[0]));
            this.progressEngine.start();
            if (this.somethingToOptimize()) {
                this.initializeBacktestData();
                this.recognizeCustomAnalysisMethod();
                if (this.progressEngine.isStopped()) {
                    this.progressEngine.printToLog(L.t((String)"Project stopped", (Object[])new Object[0]));
                    return false;
                }
                this.optimizedStrategies = 0;
                this.cumulativeSteps = 0L;
                this.totalSteps = 0;
                return true;
            }
            this.progressEngine.printToLog(L.t((String)"Nothing to optimize", (Object[])new Object[0]));
            this.progressEngine.finish();
            return false;
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

    private boolean somethingToOptimize() throws Exception {
        if (this.optimizationSettings.singleStrategy) {
            ResultsGroup rg = this.getStrategyToOptimize(this.optimizationSettings.strategyFile);
            if (rg == null) {
                return false;
            }
            ProjectConfigHelper.checkVolumeProfileBlocksAllowed((ResultsGroup)rg);
            return true;
        }
        try {
            this.inputDatabank = this.optimizationSettings.inputDatabank;
        }
        catch (Exception e) {
            return false;
        }
        if (this.inputDatabank == null) {
            return false;
        }
        int size = this.inputDatabank.getRecordsSizeNoLock();
        return size > 0;
    }

    private void initializeBacktestData() throws Exception {
        ArrayList chartSetups = (ArrayList)this.settingsData.getParams().get("ChartSetups");
        BacktestDataInitializer bdi = new BacktestDataInitializer(new LoadDataProgressEngine(this.progressEngine), chartSetups, false, null);
        bdi.prepareData();
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public void start() throws Exception {
        if (!this.beforeStart()) {
            return;
        }
        this.project.resetTracking(false, false);
        this.outputDatabank = (Databank)this.settingsData.getParams().get("DatabankTarget");
        this.outputDatabank = this.outputDatabank != null ? this.outputDatabank : (Databank)this.project.getDatabanks().get((Object)"Results");
        this.progressEngine.reset();
        this.progressEngine.start();
        this.strategies.clear();
        try {
            this.inputDatabank = this.optimizationSettings.inputDatabank;
            for (int i = 0; i < this.inputDatabank.getRecords().size(); ++i) {
                ResultsGroup strategy = (ResultsGroup)this.inputDatabank.getRecords().get(i);
                this.strategies.add(strategy.getName());
            }
        }
        catch (Exception e) {
            Log.info("Input databank not set");
            this.inputDatabank = null;
        }
        this.fitnessFunction = (IFitnessFunction)this.settingsData.getParams().get("FitnessFunction");
        this.tradingOptions = (TradingOptions)this.settingsData.getParams().get("TradingOptions");
        this.atm = (ATM)this.settingsData.getParams().get("ATM");
        this.setDatabankFilter(this.outputDatabank);
        this.progressPercent = 0;
        this.lastProcessedIndex = -1;
        try {
            if (this.optimizationSettings.singleStrategy) {
                ResultsGroup rg = this.getStrategyToOptimize(this.optimizationSettings.strategyFile);
                if (rg == null) {
                    this.progressEngine.printToLog(L.t((String)"Cannot load file to optimize, please check its path", (Object[])new Object[0]));
                } else {
                    StrategyData strategyData = this.getStrategyData(rg);
                    ++this.optimizedStrategies;
                    this.optimizeStrategy(strategyData);
                }
            } else {
                if (this.inputDatabank == null) {
                    throw new Exception(L.t((String)"Input databank not set.", (Object[])new Object[0]));
                }
                for (int a = this.lastProcessedIndex + 1; a < this.strategies.size() && !this.progressEngine.isStopped(); ++a) {
                    ResultsGroup rg = this.inputDatabank.getLocked(this.strategies.get(a), LOCK_OPTIMIZETASK);
                    StrategyData strategyData = null;
                    try {
                        strategyData = this.getStrategyData(rg);
                    }
                    finally {
                        rg.releaseLock(LOCK_OPTIMIZETASK);
                    }
                    ++this.optimizedStrategies;
                    this.optimizeStrategy(strategyData);
                    ++this.lastProcessedIndex;
                }
            }
            this.progressEngine.finish();
        }
        catch (Exception e) {
            this.progressEngine.error();
            this.progressEngine.printToLog(e.getMessage());
            Log.error("Optimization error. ", (Throwable)e);
            this.project.getTrackingInfo().error = e.getMessage();
            this.project.getTrackingInfo().errorInfo = e.getMessage();
            this.project.getTrackingInfo().errorType = 50;
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private ResultsGroup getStrategyToOptimize(File strategyFile) {
        String strategyFileName = this.optimizationSettings.strategyFile.getName();
        String strategyName = SQUtils.stripExtension((String)strategyFileName);
        ResultsGroup rg = null;
        try {
            rg = this.outputDatabank.getLocked(strategyName, LOCK_OPTIMIZETASK);
        }
        catch (Exception e) {
            Log.debug("Record not found in databank,", (Throwable)e);
        }
        finally {
            if (rg != null) {
                rg.releaseLock(LOCK_OPTIMIZETASK);
            }
        }
        if (rg == null) {
            if (strategyFile.exists()) {
                try {
                    rg = (ResultsGroup)Program.get((String)"Loader").call("loadFile", new Object[]{strategyFile.getAbsolutePath()});
                    return rg;
                }
                catch (Exception e) {
                    e.printStackTrace();
                }
            }
            return null;
        }
        return rg;
    }

    private StrategyData getStrategyData(ResultsGroup rg) throws Exception {
        StrategyData strategyData = new StrategyData();
        strategyData.strategyName = rg.getName();
        strategyData.elStrategyXml = rg.getStrategyXml();
        strategyData.dateGenerated = rg.specialValues().getLong(SpecialValues.DateGenerated, -1L);
        return strategyData;
    }

    protected void setDatabankFilter(Databank db) {
        try {
            int maxRecords = 0;
            if (this.optimizationSettings.storeAll) {
                maxRecords = (Integer)((Serializable)this.settingsData.getParams().get("MaxStrategies"));
                maxRecords = Math.max(maxRecords, 1);
            } else {
                maxRecords = 1;
            }
            db.applyFilter((IDatabankFilter)new OptimizeDatabankFilter(maxRecords));
        }
        catch (Exception e) {
            Log.error("Project '" + this.projectName + "', Task '" + this.getCustomName() + "' - Cannot set databank filter do databank '" + db.getName() + "'.", (Throwable)e);
        }
    }

    private void optimizeStrategy(StrategyData strategyData) throws Exception {
        try {
            SettingsMap settings = null;
            ChartSetups cs = (ChartSetups)this.settingsData.getParams().get("ChartSetups");
            int engine = cs.getMainSetup().getBacktestEngine();
            String symbol = cs.getMainSetup().getSymbol();
            if (engine == -1816889229 && DataManager.isGroupAlias((String)symbol)) {
                BasketDto dto = BasketOfStocksManager.getInstance().getBasket(symbol);
                if (dto == null) {
                    throw new Exception(L.t((String)"Group with name '{0}' not found.", (Object[])new Object[]{symbol}));
                }
                List stocks = BasketOfStocksManager.getInstance().getStocks(dto.getId().intValue());
                for (int i = 0; i < stocks.size(); ++i) {
                    StockDto info = (StockDto)stocks.get(i);
                    settings = this.prepareSettings(strategyData);
                    cs = (ChartSetups)settings.get("ChartSetups");
                    ChartSetup mainSetup = cs.getMainSetup();
                    mainSetup.getMainChart().setSymbol(info.getTicker());
                    StockpickerBacktestEngine.createTempStockGroup((ChartSetup)mainSetup);
                    String originalStrategyName = strategyData.strategyName + "_" + info.getTicker();
                    settings.set("StrategyName", (Object)originalStrategyName);
                    if (this.optimizationSettings.type == 4) {
                        this.runSequentialOptimization(settings, originalStrategyName, strategyData);
                        continue;
                    }
                    this.runStandardOptimization(settings, originalStrategyName, strategyData);
                }
            } else {
                settings = this.prepareSettings(strategyData);
                String originalStrategyName = strategyData.strategyName;
                if (this.optimizationSettings.type == 4) {
                    this.runSequentialOptimization(settings, originalStrategyName, strategyData);
                } else {
                    this.runStandardOptimization(settings, originalStrategyName, strategyData);
                }
            }
            if (this.optimizationSettings.type == 1 || this.optimizationSettings.type == 4) {
                this.project.increaseStrategiesPassed();
                try {
                    this.project.getTrackingInfo().increaseAcceptedReasonCount(0);
                }
                catch (Exception exception) {}
            }
        }
        catch (Exception e) {
            if (this.optimizationSettings.singleStrategy) {
                throw e;
            }
            if (this.optimizationSettings.type == 1 || this.optimizationSettings.type == 4) {
                this.project.increaseStrategiesFailed();
                try {
                    ProjectRunInfo info = this.project.getTrackingInfo();
                    int reasonCode = "Optimization error".hashCode();
                    if (!info.getDismissalCounts().containsKey(reasonCode)) {
                        this.project.setTrackingInfoReasonToDismiss(reasonCode, "Optimization error");
                    }
                    info.getDismissalCounts().addTo(reasonCode, 1);
                }
                catch (Exception exception) {
                    // empty catch block
                }
            }
            this.progressEngine.printToLog(strategyData.strategyName + " Error " + e.getMessage());
            Log.error("Optimization error in strategy " + strategyData.strategyName, (Throwable)e);
        }
    }

    private void runStandardOptimization(SettingsMap settings, final String originalStrategyName, StrategyData strategyData) throws Exception {
        OptimizationEngine engine = new OptimizationEngine(this.projectName, (StopPauseEngine)this.progressEngine, null, "OptimTask", (ILastEventListener)this, this.lastSettingsXml);
        engine.initialize(settings);
        this.cumulativeSteps += (long)this.totalSteps;
        this.totalSteps = engine.getTotalStepsCount();
        this.updateProjectInfo(0);
        engine.setNewResultListener(new INewResultListener(){
            final /* synthetic */ OptimizeTask this$0;
            {
                this.this$0 = this$0;
            }

            public void newResult(ResultsGroup resultsGroup) throws Exception {
                this.this$0.processResult(resultsGroup, originalStrategyName);
            }
        });
        engine.setLogListener(new IEngineLogListener(){

            public void processMessage(String message) {
                OptimizeTask.this.progressEngine.printToLogDebug(message);
            }
        });
        engine.setStepsListener(new IStepsListener(){

            public void step(int stepNumber) {
                OptimizeTask.this.progressPercent = (int)((double)stepNumber / (double)OptimizeTask.this.totalSteps * 100.0);
                OptimizeTask.this.updateProjectInfo(stepNumber);
            }
        });
        engine.optimize();
        this.updateIndexByFitness(settings);
    }

    private void updateIndexByFitness(SettingsMap settings) {
        if (this.shouldUpdateFitnessByIndex()) {
            Log.info("Updating fitness by index in Result databank '{}'", (Object)this.outputDatabank.getName());
            ArrayList resultsInDatabank = (ArrayList)this.outputDatabank.getRecords().clone();
            RngUtils.sortCandidatesByIndexFitness((ArrayList)resultsInDatabank, (IFitnessFunction)this.fitnessFunction);
            this.outputDatabank.refreshGrid();
        }
    }

    private boolean shouldUpdateFitnessByIndex() {
        if (this.optimizationSettings.type != 1) {
            return false;
        }
        String fitnessName = "fitnessSimple";
        boolean useFitnessByIndex = (Boolean)((Serializable)this.settingsData.getParams().getOrDefault("UseFitnessByIndex", false));
        return useFitnessByIndex;
    }

    private void runSequentialOptimization(final SettingsMap settings, final String originalStrategyName, StrategyData strategyData) throws Exception {
        SequentialOptimizationSettings chainSettings = new SequentialOptimizationSettings();
        chainSettings.distributionDown = this.paramSettings.distributionDown;
        chainSettings.distributionUp = this.paramSettings.distributionUp;
        chainSettings.steps = this.paramSettings.maxSteps;
        chainSettings.stableAreaCount = this.optimizationSettings.stableAreaCount;
        chainSettings.stabilityRangePct = this.optimizationSettings.stabilityRangePct;
        chainSettings.pctToPass = this.optimizationSettings.pctToPass;
        chainSettings.applyToStrategy = true;
        chainSettings.paramTypes = this.paramSettings.paramTypes;
        chainSettings.symmetry = this.paramSettings.symmetry;
        chainSettings.manualParams = this.paramSettings.manualMode ? this.paramSettings.params : null;
        this.engine = new SequentialOptimizationEngine(chainSettings, (StopPauseEngine)this.progressEngine, (ILastEventListener)this, this.lastSettingsXml);
        this.engine.setNewResultListener(new INewResultListener(){
            final /* synthetic */ OptimizeTask this$0;
            {
                this.this$0 = this$0;
            }

            public void newResult(ResultsGroup resultsGroup) throws Exception {
                if (resultsGroup.getName().equals(originalStrategyName)) {
                    this.this$0.processResult(resultsGroup, originalStrategyName);
                }
            }
        });
        this.engine.setLogListener(new IEngineLogListener(){

            public void processMessage(String message) {
                OptimizeTask.this.progressEngine.printToLogDebug(message);
            }
        });
        this.engine.setStepsListener(new IStepsListener(){

            public void step(int stepNumber) {
                OptimizeTask.this.progressPercent = (int)((double)stepNumber / (double)OptimizeTask.this.totalSteps * 100.0);
                OptimizeTask.this.updateProjectInfo(stepNumber);
            }
        });
        this.engine.initialize(originalStrategyName, strategyData.elStrategyXml.clone(), settings);
        this.cumulativeSteps += (long)this.totalSteps;
        this.totalSteps = this.engine.getTotalStepsCount();
        this.updateProjectInfo(0);
        this.engine.optimize(true, false, null, new ISequentialOptimizationCompleteListener(){
            final /* synthetic */ OptimizeTask this$0;
            {
                this.this$0 = this$0;
            }

            public void onFinish(boolean success, StrategyBase optimizedStrategy, SequentialOptimizationResults results, ResultsGroup optimizedRG) {
                this.this$0.onFinishSeqOpt(success, originalStrategyName, settings, optimizedStrategy, results, optimizedRG);
            }
        });
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private void onFinishSeqOpt(boolean success, String originalStrategyName, SettingsMap settings, StrategyBase optimizedStrategy, SequentialOptimizationResults results, ResultsGroup optimizedRG) {
        block29: {
            String optimizedStrategyName = originalStrategyName + " - Sequential optimized";
            if (!success || optimizedRG == null) {
                String dismissalMessageDetail = this.engine.getDismissalMessage();
                this.progressEngine.printToLog(L.t((String)"Sequential optimization evaluated as unstable, parameters not changed", (Object[])new Object[0]) + (dismissalMessageDetail != null ? " - " + dismissalMessageDetail : ""));
                ResultsGroup rg = null;
                if (this.optimizationSettings.singleStrategy) {
                    try {
                        rg = this.getStrategyToOptimize(this.optimizationSettings.strategyFile).clone();
                    }
                    catch (Exception e) {
                        Log.error("Getting original strategy from file failed", (Throwable)e);
                    }
                } else {
                    ResultsGroup existingRG = null;
                    try {
                        existingRG = this.outputDatabank.getLocked(originalStrategyName, LOCK_OPTIMIZETASK);
                        rg = existingRG.clone();
                    }
                    catch (Exception e) {
                        Log.debug("Record not found in databank,", (Throwable)e);
                    }
                    finally {
                        if (existingRG != null) {
                            existingRG.releaseLock(LOCK_OPTIMIZETASK);
                        }
                    }
                    if (rg == null) {
                        ResultsGroup originalRG = null;
                        try {
                            originalRG = this.inputDatabank.getLocked(originalStrategyName, LOCK_OPTIMIZETASK);
                            rg = originalRG.clone();
                        }
                        catch (Exception e) {
                            Log.error("Getting original strategy from databank failed", (Throwable)e);
                        }
                        finally {
                            if (originalRG != null) {
                                originalRG.releaseLock(LOCK_OPTIMIZETASK);
                            }
                        }
                    }
                }
                if (rg != null) {
                    try {
                        rg.setName(optimizedStrategyName);
                        rg.mainResult().addStrategy(optimizedStrategy);
                        rg.mainResult().addStrategyXml(optimizedStrategy.getStrategyXml());
                        rg.mainResult().setSequentialOptimizationResults(results);
                        if (this.checkSequentialOptConditions(rg, settings)) {
                            this.outputDatabank.add(rg, true);
                            break block29;
                        }
                        this.progressEngine.printToLogDebug(String.format("%s, " + L.t((String)"dismissed", (Object[])new Object[0]) + ": %s", optimizedStrategyName, this.dismissalMessage));
                    }
                    catch (Exception e) {
                        Log.error("Updating sequential optimization result failed", (Throwable)e);
                    }
                }
            } else {
                try {
                    optimizedRG.setName(optimizedStrategyName);
                    optimizedRG.mainResult().setSequentialOptimizationResults(results);
                    optimizedRG.mainResult().addStrategy(optimizedStrategy);
                    optimizedRG.mainResult().addStrategyXml(optimizedStrategy.getStrategyXml());
                    if (this.checkSequentialOptConditions(optimizedRG, settings)) {
                        this.outputDatabank.add(optimizedRG, true);
                    } else {
                        this.progressEngine.printToLogDebug(String.format("%s, " + L.t((String)"dismissed", (Object[])new Object[0]) + ": %s", optimizedStrategyName, this.dismissalMessage));
                    }
                }
                catch (Exception e) {
                    Log.error("Updating sequential optimized strategy failed", (Throwable)e);
                }
            }
        }
    }

    protected boolean checkSequentialOptConditions(ResultsGroup strategy, SettingsMap settings) {
        OptimizationSettings optSettings = (OptimizationSettings)settings.get("OptimizationSettings");
        ArrayList conditions = optSettings.conditions;
        if (conditions != null && conditions.size() > 0) {
            for (int i = 0; i < conditions.size(); ++i) {
                Condition condition = (Condition)conditions.get(i);
                if (!condition.isUsed()) continue;
                try {
                    boolean met = this.conditionsChecker.check(strategy, condition);
                    if (met) continue;
                    this.dismissalReason = 200000 + i;
                    this.dismissalMessage = this.conditionsChecker.dismissalMessage;
                    return false;
                }
                catch (CrossCheckDataNotExistException met) {
                    continue;
                }
                catch (Exception e) {
                    Log.error("Error while checking condition", (Throwable)e);
                    this.dismissalReason = 10003;
                    this.dismissalMessage = String.format("Error evaluating conditions: %s", e.getMessage());
                    return false;
                }
            }
        }
        return true;
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     * Loose catch block
     */
    protected void processResult(ResultsGroup newRG, String originalStrategyName) {
        block142: {
            ProjectRunInfo info;
            boolean isWFOptimization;
            boolean caFilterResult;
            String failedReason;
            long processStartTime;
            boolean passed;
            block141: {
                boolean isWFOptimization2;
                String deleteReason;
                block140: {
                    boolean isWFOptimization3;
                    passed = false;
                    processStartTime = System.currentTimeMillis();
                    failedReason = null;
                    if (SQProject.isMemoryProtectionUsed()) {
                        MemoryUsageChecker.checkAvailableMemory();
                    }
                    if (newRG.getOptimizationProfile() != null) {
                        // empty if block
                    }
                    caFilterResult = true;
                    newRG.removeUnsavableSettings();
                    if (!newRG.getName().equals(originalStrategyName)) break block140;
                    if (!this.optimizationSettings.dontSaveOriginalStr) {
                        if (this.outputDatabank.contains(originalStrategyName)) {
                            this.outputDatabank.update(originalStrategyName, newRG, true, LOCK_OPTIMIZETASK);
                            this.outputDatabank.updateBestResults(newRG);
                        } else {
                            caFilterResult = true;
                            if (this.caMethod != null) {
                                this.caMethod.setInputArgs(this.caInputArgs);
                                caFilterResult = this.caMethod.filterStrategy(this.project.getName(), this.project.getActiveTaskName(), this.outputDatabank.getName(), newRG);
                                if (!caFilterResult) {
                                    newRG.specialValues().setString(SpecialValues.FiltersResultFailedReason, BadStrategyException.getReasonAsString((int)10038));
                                }
                            }
                            this.outputDatabank.add(newRG, true);
                            this.outputDatabank.updateBestResults(newRG);
                            failedReason = newRG.specialValues().getString(SpecialValues.FiltersResultFailedReason);
                            if (failedReason == null || failedReason.equals(SpecialValues.FiltersResultPassed)) {
                                passed = true;
                            }
                        }
                    }
                    boolean bl = isWFOptimization3 = this.optimizationSettings.type != 1 && this.optimizationSettings.type != 4;
                    if (isWFOptimization3) {
                        if (passed) {
                            this.project.increaseStrategiesPassed();
                        } else {
                            this.project.increaseStrategiesFailed();
                        }
                    }
                    try {
                        ProjectRunInfo info2 = this.project.getTrackingInfo();
                        if (isWFOptimization3) {
                            if (passed) {
                                info2.increaseAcceptedReasonCount(0);
                            } else {
                                boolean detailedTracked = false;
                                if (this.optimizationSettings.type == 2) {
                                    try {
                                        WalkForwardMatrixResult mwfResult = (WalkForwardMatrixResult)newRG.mainResult().get("WalkForwardResult");
                                        if (mwfResult != null) {
                                            for (WalkForwardResult wfr : mwfResult.getResultList()) {
                                                if (wfr.failedConditionNames == null || wfr.failedConditionNames.isEmpty()) continue;
                                                for (String condName : wfr.failedConditionNames) {
                                                    int reasonCode = ("WF: " + condName).hashCode();
                                                    if (!info2.getDismissalCounts().containsKey(reasonCode)) {
                                                        this.project.setTrackingInfoReasonToDismiss(reasonCode, "WF: " + condName);
                                                    }
                                                    info2.getDismissalCounts().addTo(reasonCode, 1);
                                                    detailedTracked = true;
                                                }
                                            }
                                        }
                                    }
                                    catch (Exception mwfResult) {
                                        // empty catch block
                                    }
                                }
                                if (!detailedTracked) {
                                    if (failedReason != null && !failedReason.isEmpty()) {
                                        int reasonCode = failedReason.hashCode();
                                        if (!info2.getDismissalCounts().containsKey(reasonCode)) {
                                            this.project.setTrackingInfoReasonToDismiss(reasonCode, failedReason);
                                        }
                                        info2.getDismissalCounts().addTo(reasonCode, 1);
                                    } else {
                                        info2.increaseDismissalReasonCount(10000);
                                    }
                                }
                            }
                        }
                        long elapsed = System.currentTimeMillis() - processStartTime;
                        DurationStats ds = new DurationStats();
                        ds.addDuration("Optimization processing", elapsed);
                        info2.updateDurationStats(ds);
                    }
                    catch (Exception e) {
                        Log.error("Cannot update dismissal stats", (Throwable)e);
                    }
                    this.project.increaseGlobalStats(this.getCustomName().hashCode(), L.t((String)"Optimized", (Object[])new Object[0]), 1L, L.t((String)"Passed", (Object[])new Object[0]), passed ? 1L : 0L);
                    return;
                }
                if (!this.optimizationSettings.deleteFailedStr || (deleteReason = newRG.specialValues().getString(SpecialValues.FiltersResultFailedReason)).equals(SpecialValues.FiltersResultPassed)) break block141;
                this.progressEngine.printToLogDebug(L.t((String)"%s\n   - deleted from databank, failed: %s", (Object[])new Object[]{newRG.getName(), deleteReason}));
                boolean bl = isWFOptimization2 = this.optimizationSettings.type != 1 && this.optimizationSettings.type != 4;
                if (isWFOptimization2) {
                    if (passed) {
                        this.project.increaseStrategiesPassed();
                    } else {
                        this.project.increaseStrategiesFailed();
                    }
                }
                try {
                    ProjectRunInfo info3 = this.project.getTrackingInfo();
                    if (isWFOptimization2) {
                        if (passed) {
                            info3.increaseAcceptedReasonCount(0);
                        } else {
                            boolean detailedTracked = false;
                            if (this.optimizationSettings.type == 2) {
                                try {
                                    WalkForwardMatrixResult mwfResult = (WalkForwardMatrixResult)newRG.mainResult().get("WalkForwardResult");
                                    if (mwfResult != null) {
                                        for (WalkForwardResult wfr : mwfResult.getResultList()) {
                                            if (wfr.failedConditionNames == null || wfr.failedConditionNames.isEmpty()) continue;
                                            for (String condName : wfr.failedConditionNames) {
                                                int reasonCode = ("WF: " + condName).hashCode();
                                                if (!info3.getDismissalCounts().containsKey(reasonCode)) {
                                                    this.project.setTrackingInfoReasonToDismiss(reasonCode, "WF: " + condName);
                                                }
                                                info3.getDismissalCounts().addTo(reasonCode, 1);
                                                detailedTracked = true;
                                            }
                                        }
                                    }
                                }
                                catch (Exception mwfResult) {
                                    // empty catch block
                                }
                            }
                            if (!detailedTracked) {
                                if (failedReason != null && !failedReason.isEmpty()) {
                                    int reasonCode = failedReason.hashCode();
                                    if (!info3.getDismissalCounts().containsKey(reasonCode)) {
                                        this.project.setTrackingInfoReasonToDismiss(reasonCode, failedReason);
                                    }
                                    info3.getDismissalCounts().addTo(reasonCode, 1);
                                } else {
                                    info3.increaseDismissalReasonCount(10000);
                                }
                            }
                        }
                    }
                    long elapsed = System.currentTimeMillis() - processStartTime;
                    DurationStats ds = new DurationStats();
                    ds.addDuration("Optimization processing", elapsed);
                    info3.updateDurationStats(ds);
                }
                catch (Exception e) {
                    Log.error("Cannot update dismissal stats", (Throwable)e);
                }
                this.project.increaseGlobalStats(this.getCustomName().hashCode(), L.t((String)"Optimized", (Object[])new Object[0]), 1L, L.t((String)"Passed", (Object[])new Object[0]), passed ? 1L : 0L);
                return;
            }
            caFilterResult = true;
            if (this.caMethod != null && !(caFilterResult = this.caMethod.filterStrategy(this.project.getName(), this.project.getActiveTaskName(), this.outputDatabank.getName(), newRG))) {
                newRG.specialValues().setString(SpecialValues.FiltersResultFailedReason, BadStrategyException.getReasonAsString((int)10038));
            }
            if (!(this.optimizationSettings.type != 1 && this.optimizationSettings.type != 4 || this.optimizationSettings.storeAll)) {
                boolean added = this.outputDatabank.add(newRG, true);
                if (!added) {
                    newRG.clear();
                }
            } else if (this.optimizationSettings.type == 1 || this.optimizationSettings.type == 4) {
                if (caFilterResult || !this.caFilter) {
                    this.outputDatabank.add(newRG, true, false);
                }
            } else {
                WalkForwardParametersStability.compute((ResultsGroup)newRG, (OptimizationParams)this.paramSettings.params);
                this.outputDatabank.add(newRG, true, true);
            }
            failedReason = newRG.specialValues().getString(SpecialValues.FiltersResultFailedReason);
            if (failedReason == null || failedReason.equals(SpecialValues.FiltersResultPassed)) {
                passed = true;
                failedReason = null;
            }
            this.outputDatabank.updateBestResults(newRG);
            boolean bl = isWFOptimization = this.optimizationSettings.type != 1 && this.optimizationSettings.type != 4;
            if (isWFOptimization) {
                if (passed) {
                    this.project.increaseStrategiesPassed();
                } else {
                    this.project.increaseStrategiesFailed();
                }
            }
            try {
                ProjectRunInfo info4 = this.project.getTrackingInfo();
                if (isWFOptimization) {
                    if (passed) {
                        info4.increaseAcceptedReasonCount(0);
                    } else {
                        boolean detailedTracked = false;
                        if (this.optimizationSettings.type == 2) {
                            try {
                                WalkForwardMatrixResult mwfResult = (WalkForwardMatrixResult)newRG.mainResult().get("WalkForwardResult");
                                if (mwfResult != null) {
                                    for (WalkForwardResult wfr : mwfResult.getResultList()) {
                                        if (wfr.failedConditionNames == null || wfr.failedConditionNames.isEmpty()) continue;
                                        for (String condName : wfr.failedConditionNames) {
                                            int reasonCode = ("WF: " + condName).hashCode();
                                            if (!info4.getDismissalCounts().containsKey(reasonCode)) {
                                                this.project.setTrackingInfoReasonToDismiss(reasonCode, "WF: " + condName);
                                            }
                                            info4.getDismissalCounts().addTo(reasonCode, 1);
                                            detailedTracked = true;
                                        }
                                    }
                                }
                            }
                            catch (Exception mwfResult) {
                                // empty catch block
                            }
                        }
                        if (!detailedTracked) {
                            if (failedReason != null && !failedReason.isEmpty()) {
                                int reasonCode = failedReason.hashCode();
                                if (!info4.getDismissalCounts().containsKey(reasonCode)) {
                                    this.project.setTrackingInfoReasonToDismiss(reasonCode, failedReason);
                                }
                                info4.getDismissalCounts().addTo(reasonCode, 1);
                            } else {
                                info4.increaseDismissalReasonCount(10000);
                            }
                        }
                    }
                }
                long elapsed = System.currentTimeMillis() - processStartTime;
                DurationStats ds = new DurationStats();
                ds.addDuration("Optimization processing", elapsed);
                info4.updateDurationStats(ds);
            }
            catch (Exception e) {
                Log.error("Cannot update dismissal stats", (Throwable)e);
            }
            this.project.increaseGlobalStats(this.getCustomName().hashCode(), L.t((String)"Optimized", (Object[])new Object[0]), 1L, L.t((String)"Passed", (Object[])new Object[0]), passed ? 1L : 0L);
            break block142;
            catch (Exception e) {
                String message = "Error while processing strategy '" + newRG.getName() + "'";
                if (newRG != null) {
                    newRG.clear();
                }
                Log.error(message, (Throwable)e);
                this.progressEngine.printToLog(message + " - " + e.getMessage());
                boolean bl2 = isWFOptimization = this.optimizationSettings.type != 1 && this.optimizationSettings.type != 4;
                if (isWFOptimization) {
                    if (passed) {
                        this.project.increaseStrategiesPassed();
                    } else {
                        this.project.increaseStrategiesFailed();
                    }
                }
                try {
                    info = this.project.getTrackingInfo();
                    if (isWFOptimization) {
                        if (passed) {
                            info.increaseAcceptedReasonCount(0);
                        } else {
                            boolean detailedTracked = false;
                            if (this.optimizationSettings.type == 2) {
                                try {
                                    WalkForwardMatrixResult mwfResult = (WalkForwardMatrixResult)newRG.mainResult().get("WalkForwardResult");
                                    if (mwfResult != null) {
                                        for (WalkForwardResult wfr : mwfResult.getResultList()) {
                                            if (wfr.failedConditionNames == null || wfr.failedConditionNames.isEmpty()) continue;
                                            for (String condName : wfr.failedConditionNames) {
                                                int reasonCode = ("WF: " + condName).hashCode();
                                                if (!info.getDismissalCounts().containsKey(reasonCode)) {
                                                    this.project.setTrackingInfoReasonToDismiss(reasonCode, "WF: " + condName);
                                                }
                                                info.getDismissalCounts().addTo(reasonCode, 1);
                                                detailedTracked = true;
                                            }
                                        }
                                    }
                                }
                                catch (Exception mwfResult) {
                                    // empty catch block
                                }
                            }
                            if (!detailedTracked) {
                                if (failedReason != null && !failedReason.isEmpty()) {
                                    int reasonCode = failedReason.hashCode();
                                    if (!info.getDismissalCounts().containsKey(reasonCode)) {
                                        this.project.setTrackingInfoReasonToDismiss(reasonCode, failedReason);
                                    }
                                    info.getDismissalCounts().addTo(reasonCode, 1);
                                } else {
                                    info.increaseDismissalReasonCount(10000);
                                }
                            }
                        }
                    }
                    long elapsed = System.currentTimeMillis() - processStartTime;
                    DurationStats ds = new DurationStats();
                    ds.addDuration("Optimization processing", elapsed);
                    info.updateDurationStats(ds);
                }
                catch (Exception e2) {
                    Log.error("Cannot update dismissal stats", (Throwable)e2);
                }
                this.project.increaseGlobalStats(this.getCustomName().hashCode(), L.t((String)"Optimized", (Object[])new Object[0]), 1L, L.t((String)"Passed", (Object[])new Object[0]), passed ? 1L : 0L);
                break block142;
            }
            catch (OutOfMemoryError e2) {
                this.project.onMemoryError((Error)e2);
                if (newRG != null) {
                    newRG.clear();
                }
                boolean bl3 = isWFOptimization = this.optimizationSettings.type != 1 && this.optimizationSettings.type != 4;
                if (isWFOptimization) {
                    if (passed) {
                        this.project.increaseStrategiesPassed();
                    } else {
                        this.project.increaseStrategiesFailed();
                    }
                }
                try {
                    info = this.project.getTrackingInfo();
                    if (isWFOptimization) {
                        if (passed) {
                            info.increaseAcceptedReasonCount(0);
                        } else {
                            boolean detailedTracked = false;
                            if (this.optimizationSettings.type == 2) {
                                try {
                                    WalkForwardMatrixResult mwfResult = (WalkForwardMatrixResult)newRG.mainResult().get("WalkForwardResult");
                                    if (mwfResult != null) {
                                        for (WalkForwardResult wfr : mwfResult.getResultList()) {
                                            if (wfr.failedConditionNames == null || wfr.failedConditionNames.isEmpty()) continue;
                                            for (String condName : wfr.failedConditionNames) {
                                                int reasonCode = ("WF: " + condName).hashCode();
                                                if (!info.getDismissalCounts().containsKey(reasonCode)) {
                                                    this.project.setTrackingInfoReasonToDismiss(reasonCode, "WF: " + condName);
                                                }
                                                info.getDismissalCounts().addTo(reasonCode, 1);
                                                detailedTracked = true;
                                            }
                                        }
                                    }
                                }
                                catch (Exception mwfResult) {
                                    // empty catch block
                                }
                            }
                            if (!detailedTracked) {
                                if (failedReason != null && !failedReason.isEmpty()) {
                                    int reasonCode = failedReason.hashCode();
                                    if (!info.getDismissalCounts().containsKey(reasonCode)) {
                                        this.project.setTrackingInfoReasonToDismiss(reasonCode, failedReason);
                                    }
                                    info.getDismissalCounts().addTo(reasonCode, 1);
                                } else {
                                    info.increaseDismissalReasonCount(10000);
                                }
                            }
                        }
                    }
                    long elapsed = System.currentTimeMillis() - processStartTime;
                    DurationStats ds = new DurationStats();
                    ds.addDuration("Optimization processing", elapsed);
                    info.updateDurationStats(ds);
                }
                catch (Exception e3) {
                    Log.error("Cannot update dismissal stats", (Throwable)e3);
                }
                this.project.increaseGlobalStats(this.getCustomName().hashCode(), L.t((String)"Optimized", (Object[])new Object[0]), 1L, L.t((String)"Passed", (Object[])new Object[0]), passed ? 1L : 0L);
                break block142;
                {
                    catch (Throwable throwable) {
                        boolean isWFOptimization4;
                        boolean bl4 = isWFOptimization4 = this.optimizationSettings.type != 1 && this.optimizationSettings.type != 4;
                        if (isWFOptimization4) {
                            if (passed) {
                                this.project.increaseStrategiesPassed();
                            } else {
                                this.project.increaseStrategiesFailed();
                            }
                        }
                        try {
                            ProjectRunInfo info5 = this.project.getTrackingInfo();
                            if (isWFOptimization4) {
                                if (passed) {
                                    info5.increaseAcceptedReasonCount(0);
                                } else {
                                    boolean detailedTracked = false;
                                    if (this.optimizationSettings.type == 2) {
                                        try {
                                            WalkForwardMatrixResult mwfResult = (WalkForwardMatrixResult)newRG.mainResult().get("WalkForwardResult");
                                            if (mwfResult != null) {
                                                for (WalkForwardResult wfr : mwfResult.getResultList()) {
                                                    if (wfr.failedConditionNames == null || wfr.failedConditionNames.isEmpty()) continue;
                                                    for (String condName : wfr.failedConditionNames) {
                                                        int reasonCode = ("WF: " + condName).hashCode();
                                                        if (!info5.getDismissalCounts().containsKey(reasonCode)) {
                                                            this.project.setTrackingInfoReasonToDismiss(reasonCode, "WF: " + condName);
                                                        }
                                                        info5.getDismissalCounts().addTo(reasonCode, 1);
                                                        detailedTracked = true;
                                                    }
                                                }
                                            }
                                        }
                                        catch (Exception mwfResult) {
                                            // empty catch block
                                        }
                                    }
                                    if (!detailedTracked) {
                                        if (failedReason != null && !failedReason.isEmpty()) {
                                            int reasonCode = failedReason.hashCode();
                                            if (!info5.getDismissalCounts().containsKey(reasonCode)) {
                                                this.project.setTrackingInfoReasonToDismiss(reasonCode, failedReason);
                                            }
                                            info5.getDismissalCounts().addTo(reasonCode, 1);
                                        } else {
                                            info5.increaseDismissalReasonCount(10000);
                                        }
                                    }
                                }
                            }
                            long elapsed = System.currentTimeMillis() - processStartTime;
                            DurationStats ds = new DurationStats();
                            ds.addDuration("Optimization processing", elapsed);
                            info5.updateDurationStats(ds);
                        }
                        catch (Exception e4) {
                            Log.error("Cannot update dismissal stats", (Throwable)e4);
                        }
                        this.project.increaseGlobalStats(this.getCustomName().hashCode(), L.t((String)"Optimized", (Object[])new Object[0]), 1L, L.t((String)"Passed", (Object[])new Object[0]), passed ? 1L : 0L);
                        throw throwable;
                    }
                }
            }
        }
    }

    private SettingsMap prepareSettings(StrategyData strategyData) throws Exception {
        try {
            Element elConditions;
            SettingsMap settings = new SettingsMap();
            for (String key : this.settingsData.getParams().keySet()) {
                settings.set(key, this.settingsData.getParams().get(key));
            }
            settings.set("TestPrecision", (Object)1);
            settings.set("StrategyXml", (Object)strategyData.elStrategyXml);
            settings.set("StrategyLastSettings", (Object)this.taskSettings);
            this.paramSettings = new ParametersSettings();
            this.paramSettings.setFromXML(this.taskSettings, strategyData.elStrategyXml);
            StrategyBase xmlS = StrategyBase.createXmlStrategy((Element)strategyData.elStrategyXml);
            xmlS.transformToVariables(this.paramSettings.symmetry, this.paramSettings.paramTypes);
            if (this.paramSettings.manualMode) {
                OptimizationParams params = this.paramSettings.params;
                for (int a = 0; a < params.size(); ++a) {
                    Parameter param = (Parameter)params.get(a);
                    Variable var = xmlS.variables().get(param.getName());
                    if (var != null) {
                        if ("ParamTypeTradingOptions".equals(var.getParamType())) {
                            String[] toNames = var.getId().split("\\.");
                            Serializable value = null;
                            value = param.getType() == 2 ? (Serializable)Boolean.valueOf(param.getOriginalValue() == 1.0) : (Serializable)(param.getType() == 5 || param.getType() == 1 ? (Number)((int)param.getOriginalValue()) : (Number)param.getOriginalValue());
                            for (int i = 0; i < this.tradingOptions.size(); ++i) {
                                TradingOption option = (TradingOption)this.tradingOptions.get(i);
                                if (!option.getClass().getSimpleName().equals(toNames[0])) continue;
                                option.setParameterValue(toNames[1], ((Object)value).toString());
                            }
                            continue;
                        }
                        if (param.getType() == 2) {
                            var.setValue(param.getOriginalValue() == 1.0);
                            continue;
                        }
                        if (param.getType() == 5) {
                            var.setValue((int)param.getOriginalValue());
                            continue;
                        }
                        var.setValue(param.getOriginalValue());
                        continue;
                    }
                    Log.error("Unable to set original value of parameter " + param.getName() + " - Variable not found");
                }
            }
            settings.set("StrategyObject", (Object)xmlS);
            settings.set("StrategyName", (Object)strategyData.strategyName);
            settings.set("FitnessFunction", (Object)this.fitnessFunction);
            settings.set("TradingOptions", (Object)this.tradingOptions.getClone());
            settings.set("ATM", this.atm == null ? null : this.atm.getClone());
            OptimizationSettings jobOptimizationSettings = this.optimizationSettings.clone();
            jobOptimizationSettings.parameters = this.paramSettings.params;
            jobOptimizationSettings.optimizationMethod = this.paramSettings.method;
            Element elRankings = XMLUtil.getChildElem((Element)this.taskSettings, (String)"Rankings");
            Element elWalkForward = elRankings.getChild("WalkForward");
            if (elWalkForward == null) {
                throw new Exception(L.t((String)"Walk-Forward Optimization is missing Robustness settings.", (Object[])new Object[0]));
            }
            this.optimizationSettings.dontSaveOriginalStr = XMLUtil.getBoolean((Element)elWalkForward, (String)"DontSaveOriginalStr", (boolean)false);
            jobOptimizationSettings.elConditions = elConditions = XMLUtil.getChildElem((Element)elWalkForward, (String)"Conditions", (String)"<Conditions/>");
            jobOptimizationSettings.conditions = ProjectConfigHelper.getConditions((Element)elConditions);
            if (this.optimizationSettings.type == 3 || this.optimizationSettings.type == 2) {
                jobOptimizationSettings.thresholdPct = XMLUtil.getIntAttr((Element)elConditions, (String)"thresholdPct", (int)80);
                jobOptimizationSettings.robCombRows = XMLUtil.getIntAttr((Element)elConditions, (String)"robCombRows", (int)3);
                jobOptimizationSettings.robCombCols = XMLUtil.getIntAttr((Element)elConditions, (String)"robCombCols", (int)3);
                jobOptimizationSettings.robMinComb = XMLUtil.getIntAttr((Element)elConditions, (String)"robMinComb", (int)7);
                this.optimizationSettings.deleteFailedStr = XMLUtil.getBoolean((Element)elWalkForward, (String)"DeleteFailedStr", (boolean)false);
            }
            settings.set("OptimizationSettings", (Object)jobOptimizationSettings);
            settings.set("Slippage", (Object)((Double)((Serializable)this.settingsData.getParams().get("Slippage"))));
            settings.set("MinDistance", (Object)((Double)((Serializable)this.settingsData.getParams().get("MinDistance"))));
            settings.set("Commission", (Object)((CommissionsMethod)this.settingsData.getParams().get("Commission")));
            settings.set("Swap", (Object)((SwapMethod)this.settingsData.getParams().get("Swap")));
            settings.set("DateGenerated", (Object)strategyData.dateGenerated);
            return settings;
        }
        catch (Exception e) {
            throw new Exception(L.t((String)"Error while preparing settings - %s", (Object[])new Object[]{e.getMessage()}), e);
        }
    }

    protected int getRunningStatus() {
        return this.progressEngine.getRunningStatus();
    }

    private void updateProjectInfo(int curStep) {
        try {
            long generated;
            ProjectRunInfo info = this.project.getTrackingInfo();
            info.totalSteps = this.totalSteps;
            info.step = curStep;
            info.progressPercent = this.progressPercent;
            info.taskRunningTime = this.project.getCurrentTaskRunningTime();
            info.projectRunningTime = this.project.getProjectRunningTime();
            info.totalProjectRunningTime = this.project.getTotalProjectRunningTime();
            info.timeToFinish = info.step == 0 ? 0L : info.taskRunningTime / (long)info.step * (long)(info.totalSteps - info.step);
            info.infiniteProgress = false;
            info.progressPercent = 100.0f * (float)info.step / (float)info.totalSteps;
            long passed = info.strategiesPassed;
            long failed = info.strategiesFailed;
            info.totalJobsDone = generated = this.cumulativeSteps + (long)curStep;
            info.strategiesGenerated = generated;
            if (generated > 0L && info.taskRunningTime > 0L) {
                info.timePerStrategy = info.taskRunningTime / generated;
                info.strategiesPerHour = 3600000.0 * (double)generated / (double)info.taskRunningTime;
            }
            info.strategiesAccepted = passed;
            info.strategiesRejected = failed;
            long totalStrategies = passed + failed;
            if (totalStrategies > 0L) {
                info.strategiesAcceptedPct = (double)passed / (double)totalStrategies;
                info.strategiesRejectedPct = (double)failed / (double)totalStrategies;
            } else if (generated > 0L) {
                info.strategiesAcceptedPct = (double)passed / (double)generated;
                info.strategiesRejectedPct = (double)failed / (double)generated;
            }
            if (passed > 0L && info.taskRunningTime > 0L) {
                info.timePerAcceptedStrategy = info.taskRunningTime / passed;
                info.acceptedStrategiesPerHour = 3600000.0 * (double)passed / (double)info.taskRunningTime;
            }
        }
        catch (Exception e) {
            Log.error("Cannot update project info. ", (Throwable)e);
        }
    }

    public String getPluginFolderName() {
        return "TaskOptimize";
    }

    public int getPreferredPosition() {
        return 2;
    }

    public String[] getSettings() {
        return new String[]{"Data", "Options", "Notes", "RiskMoneyManagement", "Rankings", "Optimization", "ATMs"};
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
        log.print(L.t((String)"Total steps", (Object[])new Object[0]) + ": " + runInfo.totalSteps);
    }

    public void setLastEvent(String message) {
        if (this.project != null) {
            this.project.setLastEvent(message);
        }
    }

    class StrategyData {
        String strategyName;
        Element elStrategyXml;
        long dateGenerated;

        StrategyData() {
        }
    }
}

