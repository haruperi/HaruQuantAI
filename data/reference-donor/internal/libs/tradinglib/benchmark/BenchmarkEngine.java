/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.DataInfo
 *  com.strategyquant.datalib.InstrumentInfo
 *  com.strategyquant.datalib.data.DataException
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.datalib.data.io.VersatileData
 *  com.strategyquant.datalib.data.io.newDataFormat.DataBinWriterNew
 *  com.strategyquant.datalib.instrument.InstrumentManager
 *  com.strategyquant.gridlib.client.GridClient
 *  com.strategyquant.gridlib.client.GridMessage
 *  com.strategyquant.gridlib.client.IGridMessageListener
 *  com.strategyquant.gridlib.client.JobDetails
 *  com.strategyquant.gridlib.client.SQGrid
 *  com.strategyquant.lib.IRandomGenerator
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.lib.random.MersenneTwisterRng
 *  com.strategyquant.lib.time.SQTimeOld
 *  com.strategyquant.lib.utils.SQUUID
 *  it.unimi.dsi.fastutil.objects.ObjectArrayList
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.benchmark;

import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.InstrumentInfo;
import com.strategyquant.datalib.data.DataException;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.datalib.data.io.VersatileData;
import com.strategyquant.datalib.data.io.newDataFormat.DataBinWriterNew;
import com.strategyquant.datalib.instrument.InstrumentManager;
import com.strategyquant.gridlib.client.GridClient;
import com.strategyquant.gridlib.client.GridMessage;
import com.strategyquant.gridlib.client.IGridMessageListener;
import com.strategyquant.gridlib.client.JobDetails;
import com.strategyquant.gridlib.client.SQGrid;
import com.strategyquant.lib.IRandomGenerator;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.lib.random.MersenneTwisterRng;
import com.strategyquant.lib.time.SQTimeOld;
import com.strategyquant.lib.utils.SQUUID;
import com.strategyquant.tradinglib.ChartSetup;
import com.strategyquant.tradinglib.MoneyManagementMethod;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.RiskManagementMethod;
import com.strategyquant.tradinglib.TradingOption;
import com.strategyquant.tradinglib.backtest.BacktestDataType;
import com.strategyquant.tradinglib.benchmark.BenchmarkJob;
import com.strategyquant.tradinglib.benchmark.BenchmarkJob2;
import com.strategyquant.tradinglib.benchmark.BenchmarkProgressEngine;
import com.strategyquant.tradinglib.benchmark.BenchmarkResult;
import com.strategyquant.tradinglib.engine.ChartSetups;
import com.strategyquant.tradinglib.fitnessfunction.IFitnessFunction;
import com.strategyquant.tradinglib.moneymanagement.MoneyManagementMethodsList;
import com.strategyquant.tradinglib.riskmanagement.RiskManagementMethodsList;
import it.unimi.dsi.fastutil.objects.ObjectArrayList;
import java.io.File;
import java.io.Serializable;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.ThreadPoolExecutor;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class BenchmarkEngine {
    public static final Logger Log = LoggerFactory.getLogger((String)"BenchmarkEngine");
    public static final long TOTAL_TICKS = 17000000L;
    private static final int TOTAL_SINGLETHREAD_TESTS = 10;
    private static final String DATA_NAME = "BENCHMARK_DATA_TICK";
    private BenchmarkProgressEngine progressEngine;
    private ChartSetups chartSetups;
    private MoneyManagementMethod moneyManagementMethod;
    private RiskManagementMethod riskManagementMethod;
    private IFitnessFunction fitnessFunction;
    private ArrayList<TradingOption> options;
    private Element elStrategy;
    private String jobGroupID;
    private GridClient gridClient;
    private int totalTrades;
    private int finishedJobsCount;
    private ArrayList<BenchmarkResult> benchmarkResults = new ArrayList();
    private ThreadPoolExecutor executor;
    private ObjectArrayList<VersatileData> bigArray;
    private long dataLoadTime;

    public ArrayList<BenchmarkResult> getBenchmarkResults() {
        return this.benchmarkResults;
    }

    public BenchmarkEngine(BenchmarkProgressEngine benchmarkProgressEngine) throws Exception {
        this.progressEngine = benchmarkProgressEngine;
        this.moneyManagementMethod = MoneyManagementMethodsList.create("FixedSize", 0.1);
        this.riskManagementMethod = RiskManagementMethodsList.create("AllowAllTrades", new Object[0]);
        this.fitnessFunction = null;
        this.options = new ArrayList();
        this.elStrategy = XMLUtil.fileToXmlElement((File)new File(MainApp.getDataPath() + "internal/web/benchmark/benchmark_strategy1.sqw"));
        this.jobGroupID = SQUUID.randomUUID();
        this.gridClient = SQGrid.getGridClient();
        this.gridClient.registerMessageListener(this.jobGroupID, new IGridMessageListener(){

            public void messageReceived(GridMessage gridMessage) {
                BenchmarkEngine.this.processMessage(gridMessage);
            }
        });
        this.executor = (ThreadPoolExecutor)Executors.newFixedThreadPool(40);
    }

    public void initData() throws Exception {
        File file;
        String string;
        long l = System.currentTimeMillis();
        this.progressEngine.reset("Init data", 17000000L);
        String string2 = "History";
        String string3 = "TICK";
        int n = 1;
        DataInfo dataInfo = DataManager.getDataInfo((String)string2, (String)DATA_NAME);
        if (dataInfo != null && dataInfo.rows > 0) {
            string = DataManager.getDataFileName((String)string2, (String)DATA_NAME, (String)string3, (String)"No Session");
            file = new File(string);
            if (file.exists()) {
                this.progressEngine.setProgress(100L);
                this.initChartSetup();
                return;
            }
            DataManager.deleteData((String)string2, (String)DATA_NAME);
        }
        if (!InstrumentManager.checkInstrumentExists((String)DATA_NAME)) {
            InstrumentManager.addInstrument((String)DATA_NAME, (String)DATA_NAME, (double)100000.0, (double)1.0E-4, (double)1.0E-5, (double)0.0, (double)0.0, (String)"<Method type=\"None\" use=\"true\"><Params/></Method>", (byte)3);
        }
        DataManager.addData((String)string2, (String)DATA_NAME, (String)DATA_NAME, (int)n, (int)1);
        dataInfo = DataManager.getDataInfo((String)string2, (String)DATA_NAME);
        string = DataBinWriterNew.getInstance((int)2, (String)MainApp.getDataPath(), (InstrumentInfo)dataInfo.symbolInfo);
        string.setFileName(DataManager.getDataFileName((String)string2, (String)DATA_NAME, (String)string3, (String)"No Session"));
        string.open();
        file = new VersatileData();
        int n2 = this.generateBenchmarkData((DataBinWriterNew)string, dataInfo, (VersatileData)file);
        string.close();
        DataManager.updateData((String)string2, (String)dataInfo.symbol, (long)SQTime.toLong((int)2000, (int)1, (int)1), (long)((VersatileData)file).time, (int)n2, (long)0L, (int)1, (String)string3, null);
        this.initChartSetup();
        this.dataLoadTime = System.currentTimeMillis() - l;
    }

    public void deleteData() {
        DataManager.deleteData((String)"History", (String)DATA_NAME);
    }

    private void initChartSetup() throws DataException {
        this.chartSetups = new ChartSetups();
        this.chartSetups.add(new ChartSetup("History", DATA_NAME, "H1", SQTimeOld.toLong((int)2000, (int)6, (int)1), SQTimeOld.toLong((int)2001, (int)6, (int)30), 3.5, "No Session"));
        this.chartSetups.getMainSetup().setTestPrecision(3);
    }

    private int generateBenchmarkData(DataBinWriterNew dataBinWriterNew, DataInfo dataInfo, VersatileData versatileData) throws Exception {
        MersenneTwisterRng mersenneTwisterRng = new MersenneTwisterRng(12345L);
        int n = 0;
        int n2 = 0;
        int n3 = 0;
        while ((long)n3 < 17000000L) {
            n = this.generateTestData(versatileData, (IRandomGenerator)mersenneTwisterRng, n);
            dataBinWriterNew.writeData(versatileData);
            this.progressEngine.setProgress(n2);
            ++n2;
            ++n3;
        }
        return n2;
    }

    private int generateTestData(VersatileData versatileData, IRandomGenerator iRandomGenerator, int n) {
        boolean bl;
        boolean bl2;
        if (versatileData.time == Long.MIN_VALUE) {
            versatileData.time = SQTime.toLong((int)2000, (int)1, (int)1);
            versatileData.ask = 1.5;
            versatileData.bid = 1.5003;
            versatileData.volume = 1.0;
            return 1;
        }
        versatileData.time += (long)(100 + iRandomGenerator.nextInt(1500));
        boolean bl3 = bl2 = iRandomGenerator.nextInt(10) <= 4;
        if (bl2) {
            versatileData.time = SQTime.addSeconds((long)versatileData.time, (int)(1 + iRandomGenerator.nextInt(7)));
        }
        int n2 = iRandomGenerator.nextInt(10);
        boolean bl4 = bl = iRandomGenerator.nextInt(10) <= 2;
        versatileData.ask = !bl ? (n > 0 ? (versatileData.ask += (double)n2 * 1.0E-4) : (versatileData.ask -= (double)n2 * 1.0E-4)) : ((n *= -1) > 0 ? (versatileData.ask -= (double)n2 * 1.0E-4) : (versatileData.ask += (double)n2 * 1.0E-4));
        int n3 = 1 + iRandomGenerator.nextInt(10);
        versatileData.bid = versatileData.ask + (double)n3 * 1.0E-4;
        return n;
    }

    public void startTest(boolean bl, int n, int n2) throws Exception {
        String string = (bl ? "Single threaded" : "Multi threaded") + " data in " + BacktestDataType.toString(n) + ", tests count: " + n2;
        BenchmarkResult benchmarkResult = new BenchmarkResult(string);
        try {
            if (bl) {
                this.progressEngine.reset(string, n2);
                this.runSingleThreadTest(n2, true);
            } else {
                this.progressEngine.reset(string, n2);
                this.runMultiThreadTest(n2, true);
            }
        }
        catch (Error | Exception throwable) {
            benchmarkResult.setError(throwable);
            Log.info("ERROR - skipping this test", throwable);
            throwable.printStackTrace(System.out);
        }
        if (!benchmarkResult.isError()) {
            try {
                long l = System.currentTimeMillis();
                if (bl) {
                    this.progressEngine.reset(string, n2);
                    this.runSingleThreadTest(n2, false);
                } else {
                    this.progressEngine.reset(string, n2);
                    this.runMultiThreadTest(n2, false);
                }
                long l2 = System.currentTimeMillis() - l;
                double d = (double)l2 / (double)n2;
                double d2 = 3600000.0 / d;
                benchmarkResult.setResult(l2, this.dataLoadTime, d, d2, this.totalTrades);
            }
            catch (Error | Exception throwable) {
                benchmarkResult.setError(throwable);
                Log.info("ERROR - skipping this test", throwable);
                throwable.printStackTrace(System.out);
            }
        }
        this.benchmarkResults.add(benchmarkResult);
    }

    private void runSingleThreadTest(int n, boolean bl) throws Exception {
        if (bl) {
            Log.info("--- Running SingleThreadTest Initialization, tests :" + (n /= 2));
        } else {
            Log.info("--- Running SingleThreadTest, tests :" + n);
        }
        this.totalTrades = 0;
        for (int i = 0; i < n && !this.progressEngine.isStopped(); ++i) {
            int n2;
            String string = String.format("Strategy 0.%d", i);
            BenchmarkJob benchmarkJob = new BenchmarkJob(string, this.getJobParams(string));
            ResultsGroup resultsGroup = benchmarkJob.call();
            this.totalTrades = n2 = resultsGroup.portfolio().stats((byte)0, (byte)10, (byte)127).getInt("NumberOfTrades");
            Log.info("------ Test " + i + " finished");
            this.progressEngine.setProgress(i);
        }
    }

    private Map<String, Serializable> getJobParams(String string) {
        HashMap<String, Serializable> hashMap = new HashMap<String, Serializable>();
        hashMap.put("StrategyName", (Serializable)((Object)string));
        hashMap.put("StrategyXml", (Serializable)this.elStrategy.clone());
        hashMap.put("MoneyManagement.Method", this.moneyManagementMethod);
        hashMap.put("RiskManagement", this.riskManagementMethod);
        hashMap.put("FitnessFunction", this.fitnessFunction);
        hashMap.put("TradingOptions", this.options);
        hashMap.put("MoneyManagement.InitialCapital", Double.valueOf(10000.0));
        hashMap.put("OutOfSample", null);
        hashMap.put("ChartSetups", this.chartSetups.getClone());
        hashMap.put("UseRobustnessTests", Boolean.valueOf(false));
        hashMap.put("RTMethods", null);
        hashMap.put("RTNumberOfSimulations", Integer.valueOf(20));
        hashMap.put("RTForEverySetup", Boolean.valueOf(true));
        return hashMap;
    }

    private Map<String, Serializable> getJobParams3(String string) {
        HashMap<String, Serializable> hashMap = new HashMap<String, Serializable>();
        hashMap.put("StrategyName", (Serializable)((Object)string));
        hashMap.put("StrategyXml", (Serializable)this.elStrategy.clone());
        hashMap.put("MoneyManagement.Method", this.moneyManagementMethod);
        hashMap.put("RiskManagement", this.riskManagementMethod);
        hashMap.put("FitnessFunction", this.fitnessFunction);
        hashMap.put("TradingOptions", this.options);
        hashMap.put("MoneyManagement.InitialCapital", Integer.valueOf(10000));
        hashMap.put("OutOfSample", null);
        hashMap.put("ChartSetups", this.chartSetups.getClone());
        hashMap.put("UseRobustnessTests", Boolean.valueOf(false));
        hashMap.put("RTMethods", null);
        hashMap.put("RTNumberOfSimulations", Integer.valueOf(20));
        hashMap.put("RTForEverySetup", Boolean.valueOf(true));
        hashMap.put("BigArray", (Serializable)this.bigArray);
        return hashMap;
    }

    private void runMultiThreadTest(int n, boolean bl) throws Exception {
        if (bl) {
            n = 1;
            Log.info("--- Running MultiThreadTest Initialization, tests :" + n);
        } else {
            Log.info("--- Running MultiThreadTest, tests :" + n);
        }
        ArrayList<BenchmarkJob> arrayList = new ArrayList<BenchmarkJob>();
        this.totalTrades = 0;
        this.finishedJobsCount = 0;
        for (int i = 0; i < n; ++i) {
            String string = String.format("Strategy 0.%d", i);
            BenchmarkJob benchmarkJob = new BenchmarkJob(string, this.getJobParams(string));
            arrayList.add(benchmarkJob);
        }
        this.gridClient.executeOnGrid(this.jobGroupID, arrayList);
        do {
            Thread.sleep(100L);
        } while ((this.gridClient.countRunningJobs(this.jobGroupID) != 0L || this.gridClient.countWaitingJobs(this.jobGroupID) != 0L) && !this.progressEngine.isStopped());
        this.gridClient.stop(this.jobGroupID);
    }

    protected void processMessage(GridMessage gridMessage) {
        if (gridMessage.getMessageID() == 1) {
            JobDetails jobDetails = gridMessage.getJobDetails();
            if (jobDetails.isSuccess()) {
                ResultsGroup resultsGroup = (ResultsGroup)gridMessage.getData();
                try {
                    int n = resultsGroup.portfolio().stats((byte)0, (byte)10, (byte)127).getInt("NumberOfTrades");
                    resultsGroup.clear();
                    this.totalTrades = n;
                }
                catch (Exception exception) {
                    exception.printStackTrace();
                }
                this.progressEngine.setProgress(this.finishedJobsCount);
            } else {
                Log.error("Job finished unsuccessfully!!!");
            }
        }
    }

    public void printResults() {
        Log.info("----------------------------------------------------------");
        Log.info("--- BENCHMARK RESULTS ---");
        Log.info("----------------------------------------------------------");
        Log.info("TEST NAME                       \t|\tDURATION\t|\tSTR. AVG TIME\t|\tSTRATEGIES PER HOUR\t|\tCHECKSUM(TRADES)\t|\tTIME PER TICK");
        for (BenchmarkResult benchmarkResult : this.benchmarkResults) {
            Log.info(benchmarkResult.toString());
        }
    }

    private void runMultiThreadTest2(int n, boolean bl) throws Exception {
        Object object;
        if (bl) {
            n = 1;
            Log.info("--- Running MultiThreadTest Initialization, tests :" + n);
        } else {
            Log.info("--- Running MultiThreadTest, tests :" + n);
        }
        ArrayList arrayList = new ArrayList();
        for (int i = 0; i < n; ++i) {
            String object2 = String.format("Strategy 0.%d", i);
            object = new BenchmarkJob(object2, this.getJobParams(object2));
            Future future = this.executor.submit(object);
            arrayList.add(future);
        }
        for (Future future : arrayList) {
            try {
                object = (ResultsGroup)future.get();
                try {
                    int n2 = ((ResultsGroup)object).portfolio().stats((byte)0, (byte)10, (byte)127).getInt("NumberOfTrades");
                    if (object != null) {
                        ((ResultsGroup)object).clear();
                    }
                    this.totalTrades = n2;
                }
                catch (Exception exception) {
                    exception.printStackTrace();
                }
                this.progressEngine.setProgress(this.finishedJobsCount);
            }
            catch (InterruptedException | ExecutionException exception) {
                exception.printStackTrace();
            }
        }
    }

    private void runMultiThreadTest3(int n, boolean bl) throws Exception {
        Object object;
        if (bl) {
            n = 1;
            Log.info("--- Running MultiThreadTest Initialization, tests :" + n);
        } else {
            Log.info("--- Running MultiThreadTest, tests :" + n);
        }
        ArrayList arrayList = new ArrayList();
        for (int i = 0; i < n; ++i) {
            String object2 = String.format("Strategy 0.%d", i);
            object = new BenchmarkJob2(object2, this.getJobParams3(object2));
            Future future = this.executor.submit(object);
            arrayList.add(future);
        }
        for (Future future : arrayList) {
            try {
                object = (ResultsGroup)future.get();
                try {
                    int n2 = 0;
                    if (object != null) {
                        ((ResultsGroup)object).clear();
                    }
                    this.totalTrades = n2;
                }
                catch (Exception exception) {
                    exception.printStackTrace();
                }
                this.progressEngine.setProgress(this.finishedJobsCount);
            }
            catch (InterruptedException | ExecutionException exception) {
                exception.printStackTrace();
            }
        }
    }
}

