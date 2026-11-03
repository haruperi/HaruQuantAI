/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  ch.qos.logback.classic.Level
 *  ch.qos.logback.classic.Logger
 *  ch.qos.logback.classic.LoggerContext
 *  org.eclipse.jetty.server.handler.ContextHandler
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.strategyquant;

import ch.qos.logback.classic.Level;
import ch.qos.logback.classic.Logger;
import ch.qos.logback.classic.LoggerContext;
import com.strategyquant.allTimeStats.AllTimeStats;
import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.basket.BasketOfStocksManager;
import com.strategyquant.datalib.broker.BrokerManager;
import com.strategyquant.datalib.customData.CustomDataManager;
import com.strategyquant.datalib.data.DataException;
import com.strategyquant.datalib.data.DataFolderSweeper;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.datalib.data.io.DataCsvLoader;
import com.strategyquant.datalib.data.io.ImportDataInfo;
import com.strategyquant.datalib.data.io.columns.AskCol;
import com.strategyquant.datalib.data.io.columns.BidCol;
import com.strategyquant.datalib.data.io.columns.CloseCol;
import com.strategyquant.datalib.data.io.columns.DateCol;
import com.strategyquant.datalib.data.io.columns.DateTimeCol;
import com.strategyquant.datalib.data.io.columns.DefaultCol;
import com.strategyquant.datalib.data.io.columns.HighCol;
import com.strategyquant.datalib.data.io.columns.LowCol;
import com.strategyquant.datalib.data.io.columns.OpenCol;
import com.strategyquant.datalib.data.io.columns.TimeCol;
import com.strategyquant.datalib.data.io.columns.VolumeCol;
import com.strategyquant.datalib.data.io.newDataFormat.DataBinWriterNew;
import com.strategyquant.datalib.dataseries.DoubleListCache;
import com.strategyquant.datalib.instrument.InstrumentManager;
import com.strategyquant.datalib.session.SessionManager;
import com.strategyquant.gridlib.client.SQGrid;
import com.strategyquant.jobslib.JobEngine;
import com.strategyquant.lib.L;
import com.strategyquant.lib.L88OaFjjon.G8SyrBEfO8;
import com.strategyquant.lib.L88OaFjjon.Lewgre21g;
import com.strategyquant.lib.L88OaFjjon.Tu5UdlpFO9;
import com.strategyquant.lib.L88OaFjjon.V571hfnsHw;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.app.LauncherConfig;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.lib.app.impl.MainAppStandardImpl;
import com.strategyquant.lib.app.webserver.MainAppWebServer;
import com.strategyquant.lib.constants.SQPaths;
import com.strategyquant.lib.customization.Customization;
import com.strategyquant.lib.hw.HardwareInfo;
import com.strategyquant.lib.hw.OperatingSystem;
import com.strategyquant.lib.language.LFileGen;
import com.strategyquant.lib.memory.MemoryUsageChecker;
import com.strategyquant.lib.snippets.compile.SQStructure;
import com.strategyquant.lib.sourcecode.XMLIndicatorsAnalyzer;
import com.strategyquant.lib.tempfiles.TempFilesManager;
import com.strategyquant.lib.time.SQTimeOld;
import com.strategyquant.lib.whitelabel.Brokers;
import com.strategyquant.pluginlib.SQPluginManager;
import com.strategyquant.pluginlib.program.Program;
import com.strategyquant.strategyquant.MainWindow;
import com.strategyquant.strategyquant.SQInstaller;
import com.strategyquant.strategyquant.SQWebServer;
import com.strategyquant.tradinglib.Blocks;
import com.strategyquant.tradinglib.DatabankColumn;
import com.strategyquant.tradinglib.MemoryCleaner;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.backtest.TestfilesUtils;
import com.strategyquant.tradinglib.blocks.BlocksConfigGenerator;
import com.strategyquant.tradinglib.blocks.CustomBlocks;
import com.strategyquant.tradinglib.blocks.random.BlocksConfig;
import com.strategyquant.tradinglib.crosscheck.ICrossCheck;
import com.strategyquant.tradinglib.databank.DatabankColumns;
import com.strategyquant.tradinglib.equitychartnew.addons.IEquityChartAddon;
import com.strategyquant.tradinglib.exchange.IExchange;
import com.strategyquant.tradinglib.fitnessfunction.IFitnessFunction;
import com.strategyquant.tradinglib.formulas.Formulas;
import com.strategyquant.tradinglib.generator.Checkers;
import com.strategyquant.tradinglib.generator.Negaters;
import com.strategyquant.tradinglib.generator.StrategyGeneratorCache;
import com.strategyquant.tradinglib.historyData.HistoryDataManager;
import com.strategyquant.tradinglib.historyData.SpecialSymbolsManager;
import com.strategyquant.tradinglib.optimization.ParametersSettings;
import com.strategyquant.tradinglib.performance.Performance;
import com.strategyquant.tradinglib.plugindef.app.IAppPlugin;
import com.strategyquant.tradinglib.plugindef.connection.IConnectionPlugin;
import com.strategyquant.tradinglib.project.IProject;
import com.strategyquant.tradinglib.project.IProjectCondition;
import com.strategyquant.tradinglib.project.ProjectEngine;
import com.strategyquant.tradinglib.project.SQProject;
import com.strategyquant.tradinglib.project.StrategiesSaver;
import com.strategyquant.tradinglib.project.console.CLILogger;
import com.strategyquant.tradinglib.project.console.SQConsole;
import com.strategyquant.tradinglib.project.websocket.DataToSend;
import com.strategyquant.tradinglib.project.websocket.SQWebSocketManager;
import com.strategyquant.tradinglib.project.websocket.WSDataObjects;
import com.strategyquant.tradinglib.project.websocket.channels.ProjectChannels;
import com.strategyquant.tradinglib.results.IResultPlugin;
import com.strategyquant.tradinglib.results.file.ILoaderPlugin;
import com.strategyquant.tradinglib.results.file.ISaverPlugin;
import com.strategyquant.tradinglib.results.stats.StatsComputer;
import com.strategyquant.tradinglib.results.stats.computer.OrderPLComputer;
import com.strategyquant.tradinglib.servlet.IServletPlugin;
import com.strategyquant.tradinglib.talib.TALibBlocks;
import com.strategyquant.tradinglib.task.settings.ISettingTabPlugin;
import com.strategyquant.tradinglib.taskImpl.ISQTask;
import com.strategyquant.webguilib.BrowserGUI;
import com.strategyquant.webguilib.WebServer;
import com.strategyquant.webguilib.config.RemoteAccessConfig;
import com.strategyquant.webguilib.servlet.MainServlet;
import java.io.File;
import java.io.IOException;
import java.lang.management.GarbageCollectorMXBean;
import java.lang.management.ManagementFactory;
import java.nio.file.FileVisitOption;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;
import java.util.ArrayList;
import java.util.Locale;
import java.util.Scanner;
import java.util.TimeZone;
import java.util.Timer;
import java.util.TimerTask;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;
import java.util.logging.FileHandler;
import java.util.logging.Handler;
import java.util.logging.SimpleFormatter;
import java.util.stream.Stream;
import org.eclipse.jetty.server.handler.ContextHandler;
import org.json.JSONObject;
import org.slf4j.LoggerFactory;

public class SQApp
extends MainAppStandardImpl {
    public static final org.slf4j.Logger Log = LoggerFactory.getLogger(SQApp.class);
    private WebServer webServer;
    private SQConsole consoleAppInstance;
    private static String p = "StrategyQuant X";
    private static String lpc = SQApp.lpc();
    private static String ps = "SQ";

    public static void main(String[] stringArray) {
        SQApp.main(stringArray, false);
    }

    public static void main(String[] stringArray, boolean bl) {
        System.setProperty("algoWizardType", "Embedded");
        System.setProperty("org.eclipse.jetty.server.Request.maxFormContentSize", "200000000");
        appArgs = stringArray;
        runInConsole = bl;
        if (!SQApp.runInConsole()) {
            SQApp.hideConsoleForUIApp();
            MainApp.setMultiInstance(true);
            MainApp.addInstance(new SQApp(new MainWindow()));
            MainApp.settings().load();
            SQApp.activateDebugLoggingLevel();
            MainApp.start();
        } else {
            MainApp.setMultiInstance(true);
            MainApp.addInstance(new SQApp(null));
            MainApp.settings().load();
            MainApp.start();
        }
    }

    private static void hideConsoleForUIApp() {
        if (new File(MainApp.getDataPath() + "/console.txt").exists()) {
            return;
        }
        OperatingSystem operatingSystem = new OperatingSystem();
        if (operatingSystem.isWindows()) {
            // empty if block
        }
    }

    private static void activateDebugLoggingLevel() {
        LoggerContext loggerContext = (LoggerContext)LoggerFactory.getILoggerFactory();
        if (Boolean.parseBoolean(MainApp.settings().get("debugLevelActive", "false"))) {
            Logger logger = loggerContext.getLogger("root");
            logger.setLevel(Level.DEBUG);
            Log.info("Activated debug logging level.");
        } else {
            Logger logger = loggerContext.getLogger(ContextHandler.class);
            logger.setLevel(Level.ERROR);
        }
    }

    private static void redirectLogMessagesToFile(java.util.logging.Logger logger, String string) throws IOException {
        FileHandler fileHandler = new FileHandler(string);
        fileHandler.setFormatter(new SimpleFormatter());
        for (Handler handler : logger.getHandlers()) {
            logger.removeHandler(handler);
        }
        logger.addHandler(fileHandler);
    }

    private static String lpc() {
        if (MainApp.isBrazilianEdition()) {
            return "SQBR";
        }
        return "GENBUILDER";
    }

    public SQApp(MainWindow mainWindow) {
        super("SQUANT", p, lpc, mainWindow, ps);
        if (mainWindow != null) {
            this.webServer = mainWindow.getWebServer();
        }
    }

    @Override
    protected boolean initApp() throws Exception {
        Object object;
        Object object2;
        Log.info("SQX version: " + this.getAppVersion());
        if (MainApp.runInConsole()) {
            Object object3;
            Log.debug("HW: " + HardwareInfo.getInfo());
            Log.debug("Properties: " + System.getProperties());
            object2 = ManagementFactory.getRuntimeMXBean();
            object = object2.getInputArguments();
            Object object4 = object.iterator();
            while (object4.hasNext()) {
                object3 = object4.next();
                Log.debug("Runtime args: " + (String)object3);
            }
            object4 = ManagementFactory.getGarbageCollectorMXBeans();
            object3 = object4.iterator();
            while (object3.hasNext()) {
                GarbageCollectorMXBean garbageCollectorMXBean = (GarbageCollectorMXBean)object3.next();
                Log.debug("GC bean: " + garbageCollectorMXBean.getName());
            }
        } else {
            Object object5;
            Log.info("HW: " + HardwareInfo.getInfo());
            Log.info("Properties: " + System.getProperties());
            object2 = ManagementFactory.getRuntimeMXBean();
            object = object2.getInputArguments();
            Object object6 = object.iterator();
            while (object6.hasNext()) {
                object5 = object6.next();
                Log.info("Runtime args: " + (String)object5);
            }
            object6 = ManagementFactory.getGarbageCollectorMXBeans();
            object5 = object6.iterator();
            while (object5.hasNext()) {
                GarbageCollectorMXBean garbageCollectorMXBean = (GarbageCollectorMXBean)object5.next();
                Log.info("GC bean: " + garbageCollectorMXBean.getName());
            }
        }
        this.deleteDeprecatedFiles();
        Log.debug("Computer name: " + System.getenv("COMPUTERNAME") + ", User name: " + System.getProperty("user.name") + ", SQ version: " + MainApp.printAppVersion(true));
        object2 = new Locale("en", "US");
        Locale.setDefault((Locale)object2);
        System.setProperty("java.net.preferIPv4Stack", "true");
        this.checkWritable();
        this.setTimeZone();
        this.iUKTXv8M();
        if (!this.isRunInConsole()) {
            BrowserGUI.getInstance().showLicenseLoadingScreen();
            this.checkMaxLoadingTime();
        }
        try {
            this.createUserFolders();
            this.updateLoadingInfo(L.t("Initializing database & settings...", new Object[0]));
            Log.debug("Main app constructor");
            this.updateLoadingInfo(L.t("Loading customizations...", new Object[0]));
            Customization.load(true);
            HistoryDataManager.get().initAsync();
            this.updateLoadingInfo(L.t("Compiling snippets...", new Object[0]));
            this.checkSnippets();
            this.updateLoadingInfo(L.t("Loading performance settings...", new Object[0]));
            Performance.init();
            MemoryCleaner.init();
            MemoryUsageChecker.init();
            this.updateLoadingInfo(L.t("Initializing building blocks...", new Object[0]));
            this.initBlocks();
            this.updateLoadingInfo(L.t("Loading plugins...", new Object[0]));
            this.initPluginSystem();
            this.initPrograms();
            this.renameSQ4DatabankFiles();
            this.copyUpdaterFiles();
            this.updateLoadingInfo(L.t("Initializing stats computer...", new Object[0]));
            this.initStatsComputer(false);
            this.initEngines();
            MainApp.enableRequests();
            this.updateLoadingInfo(L.t("Initializing communication channels...", new Object[0]));
            ProjectChannels.init();
            TestfilesUtils.deleteTestingFiles();
            TempFilesManager.get().init();
            this.updateLoadingInfo(L.t("Checking data...", new Object[0]));
            this.checkData();
            this.updateLoadingInfo(L.t("Loading GUI...", new Object[0]));
            object = new DoubleListCache();
        }
        catch (Exception exception) {
            Log.error("Error during initialization.", (Throwable)exception);
            if (!runInConsole) {
                MainApp.showErrorDialog(L.t("Error", new Object[0]), L.t("Error during initialization.", new Object[0]) + "\n" + exception.getMessage());
            }
            MainApp.exitJVM("Error during initialization - " + exception.getMessage(), 1);
        }
        catch (Error error) {
            Log.error("Error during initialization.", (Throwable)error);
            if (!runInConsole) {
                MainApp.showErrorDialog(L.t("Error", new Object[0]), L.t("Error during initialization.", new Object[0]) + "\n" + error.getMessage());
            }
            MainApp.exitJVM("Error during initialization - " + error.getMessage(), 1);
        }
        Log.debug("Initialization of all components performed successfully.");
        return true;
    }

    private void createUserFolders() {
        File file;
        File file2;
        File file3;
        File file4;
        File file5;
        Log.debug("Creating user folders...");
        File file6 = new File(SQStructure.USER_LIBS);
        if (!file6.exists()) {
            file6.mkdirs();
        }
        if (!(file5 = new File(SQStructure.USER_EXTEND)).exists()) {
            file5.mkdirs();
        }
        if (!(file4 = new File(SQStructure.USER_EXTEND_SNIPPETS)).exists()) {
            file4.mkdirs();
        }
        if (!(file3 = new File(SQStructure.USER_EXTEND_PLUGINS)).exists()) {
            file3.mkdirs();
        }
        if (!(file2 = new File(SQStructure.USER_EXTEND_RESULTS_PLUGINS)).exists()) {
            file2.mkdirs();
        }
        if (!(file = new File(SQStructure.USER_EXTEND_SNIPPETS + "/SQ/Blocks")).exists()) {
            file.mkdirs();
        }
    }

    private void checkMaxLoadingTime() {
        ScheduledExecutorService scheduledExecutorService = Executors.newSingleThreadScheduledExecutor();
        scheduledExecutorService.schedule(new Runnable(){

            @Override
            public void run() {
                if (!MainApp.AppLoaded) {
                    MainApp.showErrorDialog(L.t("Please restart the program.", new Object[0]), L.t("StrategyQuant X couldn't load correctly.", new Object[0]) + "\n" + L.t("We did some cleanup, it should work now.", new Object[0]));
                }
            }
        }, 5L, TimeUnit.MINUTES);
    }

    private void deleteDeprecatedFiles() {
        block6: {
            Scanner scanner = null;
            try {
                File file = new File(SQStructure.INTERNAL_DIR_PATH + "deprecated.dat");
                if (file.exists()) {
                    String string = SQUtils.fileToString(file);
                    scanner = new Scanner(string);
                    while (scanner.hasNextLine()) {
                        String string2 = scanner.nextLine();
                        File file2 = new File(MainApp.getDataPath() + string2);
                        if (!file2.exists()) continue;
                        file2.delete();
                    }
                }
            }
            catch (Exception exception) {
                if (scanner == null) break block6;
                scanner.close();
            }
        }
        try {
            new File(SQStructure.INTERNAL_DIR_PATH + "extend\\Snippets\\SQ\\TradingOptions\\UseInitialSL.java").delete();
        }
        catch (Exception exception) {
            // empty catch block
        }
    }

    private void copyUpdaterFiles() {
        String string = "StrategyQuantX.exe";
        File file = new File(MainApp.getDataPath() + "internal/" + string);
        if (file.exists()) {
            Path path = Paths.get(MainApp.getDataPath() + "internal/" + string, new String[0]);
            Path path2 = Paths.get(MainApp.getDataPath() + string, new String[0]);
            try {
                Files.move(path, path2, StandardCopyOption.REPLACE_EXISTING);
                Log.info("Updated updater - copied from /internal");
            }
            catch (IOException iOException) {
                Log.error("Move of updater failed. " + iOException.getMessage(), (Throwable)iOException);
            }
        }
    }

    private void renameSQ4DatabankFiles() {
        String string2 = MainApp.getDataPath() + "user/projects";
        try (Stream<Path> stream = Files.find(Paths.get(string2, new String[0]), 5, (path, basicFileAttributes) -> String.valueOf(path).endsWith(".sq4"), new FileVisitOption[0]);){
            stream.map(String::valueOf).forEach(string -> {
                File file = new File((String)string);
                String string2 = string.replace(".sq4", ".sqx");
                Log.info("Renaming file {} to {}", string, (Object)string2);
                file.renameTo(new File(string2));
            });
        }
        catch (IOException iOException) {
            Log.error("Cannot rename .sq4 files in databanks", (Throwable)iOException);
        }
    }

    public void renameFiles(String string) {
    }

    @Override
    protected void afterInit() throws Exception {
        AllTimeStats.getInstance().start();
        if (this.isRunInConsole()) {
            Log.info(L.t("HTTP API started, you can access it on http://localhost:%d/call?cmd=-h", MainAppWebServer.port));
            Log.debug("Starting app in command line mode.");
            this.consoleAppInstance = new SQConsole(this);
            this.consoleAppInstance.run(appArgs);
            BasketOfStocksManager.getInstance().synhronizeAsync(new Runnable(){

                @Override
                public void run() {
                    try {
                        SQWebSocketManager.addToDataQueue(WSDataObjects.getBaskets(), "SQUANT", "QDM", "AlgoWizard");
                        SQWebSocketManager.addToDataQueue(WSDataObjects.getData("", "add"), "SQUANT", "QDM", "AlgoWizard");
                    }
                    catch (Exception exception) {
                        Log.error("Error while sending WS messages about stockgroup synchronization.", (Throwable)exception);
                    }
                }
            });
            BrokerManager.getInstance().synhronizeAsync(new Runnable(){

                @Override
                public void run() {
                    try {
                        SQWebSocketManager.addToDataQueue(WSDataObjects.getBrokers(), "SQUANT", "QDM", "AlgoWizard");
                    }
                    catch (Exception exception) {
                        Log.error("Error while sending WS messages about stockgroup synchronization.", (Throwable)exception);
                    }
                }
            });
        } else {
            SQInstaller sQInstaller = new SQInstaller();
            sQInstaller.checkForUpdatesAsync();
        }
    }

    private void setTimeZone() {
        this.timeZone = TimeZone.getDefault();
        SQTimeOld.setDefaultTimeZone();
        SQTime.init();
    }

    private void initBlocks() throws Exception {
        Blocks.init();
        Formulas.init();
        Negaters.init();
        Checkers.init();
        StrategyBase.init();
        new ParametersSettings();
        this.regenerateWizardConfig(false);
        TALibBlocks.init();
        XMLIndicatorsAnalyzer.init();
        CustomBlocks.load();
    }

    private void regenerateWizardConfig(boolean bl) {
        try {
            String string = MainApp.getDataPath() + "internal/web/SQWIZARD/branding/global/config.xml";
            File file = new File(string);
            boolean bl2 = true;
            long l = new File(SQStructure.SNIPPETS_JAR_PATH).lastModified();
            try {
                long l2 = Long.valueOf(SQUtils.fileToString(new File(SQStructure.WIZARD_HASH_PATH)));
            }
            catch (Exception exception) {
                // empty catch block
            }
            if (bl || bl2 || !file.exists()) {
                BlocksConfigGenerator blocksConfigGenerator = new BlocksConfigGenerator();
                blocksConfigGenerator.run(string);
                SQUtils.stringToFile(new File(SQStructure.WIZARD_HASH_PATH), l + "");
            }
        }
        catch (Exception exception) {
            Log.error("Cannot regenerate Wizard config.xml. Exc.", (Throwable)exception);
        }
    }

    private void initStatsComputer(boolean bl) throws Exception {
        Log.debug("Initializing stats computer...");
        if (bl) {
            StatsComputer.clearGlobalStatsValues();
        } else {
            StatsComputer.registerOrderComputer(new OrderPLComputer());
        }
        for (DatabankColumn databankColumn : DatabankColumns.get().getAvailableClasses()) {
            StatsComputer.registerDatabankColumn(databankColumn);
        }
        StatsComputer.createDependencyGraph();
    }

    private void updateLoadingInfo(String string) {
        if (MainApp.electronWS == null) {
            return;
        }
        MainApp.sendMessage("loadingInfo", string);
    }

    private void iUKTXv8M() {
        boolean bl = false;
        try {
            Object object;
            Log.debug("Verifying license.");
            Brokers.init();
            Log.debug("Verifying license. Step 2");
            G8SyrBEfO8 g8SyrBEfO8 = G8SyrBEfO8.getInstance();
            g8SyrBEfO8.rR6Ivukeqw(g8SyrBEfO8.eyGcvZ1s());
            Log.info("Hardware ID: " + g8SyrBEfO8.getHardwareID());
            Log.debug("Verifying license. Step 3");
            try {
                if (g8SyrBEfO8.licenseFileExists()) {
                    Log.debug("Verifying license. Step 4");
                    g8SyrBEfO8.verifyLicenseFromFile();
                    object = Executors.newSingleThreadScheduledExecutor();
                    object.schedule(new Runnable(){

                        @Override
                        public void run() {
                            G8SyrBEfO8.checkLicense();
                        }
                    }, 5L, TimeUnit.MINUTES);
                }
            }
            catch (Exception exception) {
                MainApp.license.setLicense(g8SyrBEfO8.getLastCheckedLicenseCode());
                MainApp.license.setError(exception.getMessage());
                Log.error("License verification failed. Exc. ", (Throwable)exception);
            }
            Tu5UdlpFO9.init(SQStructure.INTERNAL_DIR_PATH);
            if (this.isRunInConsole()) {
                Log.debug("Verifying license. Step 5 CLI");
                object = null;
                if (appArgs.length > 0 && (appArgs[0].startsWith("liccheck") || appArgs[0].startsWith("license"))) {
                    try {
                        String[] stringArray;
                        String string = appArgs[0];
                        bl = appArgs[0].startsWith("liccheck");
                        if (string.contains("=") && (stringArray = string.split("=")).length == 2 && (stringArray[0].equals("license") || stringArray[0].equals("liccheck"))) {
                            object = stringArray[1].trim();
                        }
                    }
                    catch (Exception exception) {
                        Log.error("Error while parsing license code from app args.", (Throwable)exception);
                    }
                } else if (!G8SyrBEfO8.getInstance().verified()) {
                    Log.debug("Verifying license. Step 6 CLI");
                    object = Tu5UdlpFO9.odz0Gyiqhr();
                }
                if (object != null && !((String)object).isEmpty()) {
                    Log.info("Verifying license ...");
                    g8SyrBEfO8.verifyLicenseOnline((String)object);
                    if (g8SyrBEfO8.isItTrial() || g8SyrBEfO8.isItPartnerTrial() || g8SyrBEfO8.isItFullMbg()) {
                        Tu5UdlpFO9.pzi7BBRxNg(g8SyrBEfO8.getLicenseCode());
                    } else {
                        Tu5UdlpFO9.pzi7BBRxNg("");
                    }
                }
            } else {
                Log.debug("Verifying license. Step 5");
                Log.info("License dialog initing");
                object = Tu5UdlpFO9.odz0Gyiqhr();
                if (object != null && !((String)object).isEmpty()) {
                    MainApp.license.setLicense((String)object);
                }
                Log.debug("Verifying license. Step 6");
                if (!G8SyrBEfO8.getInstance().verified()) {
                    Log.debug("Verifying license. Step 7");
                    BrowserGUI.getInstance().loadLicenseDialogForm();
                    Log.debug("Verifying license. Step 8");
                    if (g8SyrBEfO8.isItTrial() || g8SyrBEfO8.isItPartnerTrial() || g8SyrBEfO8.isItFullMbg()) {
                        Tu5UdlpFO9.pzi7BBRxNg(g8SyrBEfO8.getLicenseCode());
                    } else {
                        Tu5UdlpFO9.pzi7BBRxNg("");
                    }
                }
            }
            if (!G8SyrBEfO8.getInstance().verified()) {
                Log.info("Missing license.");
                MainApp.exitJVM("Missing license.", 1);
            }
            Lewgre21g.g5Tq3ZdPHp("L-" + MainApp.v571hfnsHw().eHvc2JguAd());
            object = Executors.newSingleThreadScheduledExecutor();
            object.scheduleAtFixedRate(() -> G8SyrBEfO8.checkLicense(), 3L, 3L, TimeUnit.DAYS);
            Log.debug("License was successfully verified.");
        }
        catch (Error | Exception throwable) {
            Log.info("Failed to check license - " + throwable.getMessage());
            Log.error("Failed to check license. Exc. ", throwable);
            MainApp.exitJVM("Failed to check license", 1);
        }
        if (bl) {
            Log.info("Exit after license check");
            MainApp.exitJVM("Exit after license check");
        }
    }

    private void initEngines() throws Exception {
        this.updateLoadingInfo(L.t("Initializing engines...", new Object[0]));
        SessionManager.init(SQPaths.dataDirPath);
        InstrumentManager.init(SQPaths.dataDirPath);
        DataManager.init(SQPaths.dataDirPath);
        DataFolderSweeper.get().init();
        BasketOfStocksManager.init(SQPaths.dataDirPath);
        BrokerManager.init(SQPaths.dataDirPath);
        CustomDataManager.init(SQPaths.customDataDirPath);
        JobEngine.init(new JobEngine(0));
        LauncherConfig.getInstance();
        SQProject.init();
        ResultsGroup.init();
        this.addAlias("EURUSD_tick", "EURUSD");
        this.addAlias("EURUSD_fhdb", "EURUSD");
        this.addAlias("GBPUSD_fhdb", "EURUSD");
        this.addAlias("GBPUSD_fhdb - MT4", "EURUSD");
        this.addAlias("EURUSD_fhdb - MT4", "EURUSD");
        this.addAlias("CADCHF_dukasM1", "EURUSD");
        this.addAlias("EURUSD_M1", "EURUSD");
        this.addAlias("AUDCAD_tick", "EURUSD");
        this.addAlias("USDJPY_tick", "USDJPY");
        this.addAlias("EURJPY_M1", "USDJPY");
        HistoryDataManager.get().checkRenamedHistoryTickers();
        SpecialSymbolsManager.updateAll();
        this.updateLoadingInfo(L.t("Loading data...", new Object[0]));
        long l = System.currentTimeMillis();
        InstrumentManager.list();
        DataManager.list();
        SessionManager.getSessions();
        CustomDataManager.list();
        BrokerManager.getInstance().getAllBrokers();
        BasketOfStocksManager.getInstance().getGroups();
        HistoryDataManager.get().getStockExchange(null);
        HistoryDataManager.get().getFuturesExchange(null);
        Log.info("Data loaded in {} ms", (Object)(System.currentTimeMillis() - l));
        this.updateLoadingInfo(L.t("Loading projects...", new Object[0]));
        l = System.currentTimeMillis();
        ProjectEngine.list();
        Log.info("Projects loaded in {} ms", (Object)(System.currentTimeMillis() - l));
    }

    private void addAlias(String string, String string2) throws DataException {
    }

    private void importInstruments() {
    }

    private void initBackgroundTasks() throws Exception {
    }

    protected void initPluginSystem() {
        try {
            Log.debug("Initializing plugins...");
            SQPluginManager.setWorkDirectory(MainApp.getDataPath());
            SQPluginManager.initForProduct(this.getProductCode(), null);
            SQPluginManager.loadPlugins(IAppPlugin.class);
            SQPluginManager.loadPlugins(IConnectionPlugin.class);
            SQPluginManager.loadPlugins(ISettingTabPlugin.class);
            SQPluginManager.loadPlugins(IServletPlugin.class);
            SQPluginManager.loadPlugins(ISQTask.class);
            SQPluginManager.loadPlugins(ILoaderPlugin.class);
            SQPluginManager.loadPlugins(ISaverPlugin.class);
            SQPluginManager.loadPlugins(IProject.class);
            SQPluginManager.loadPlugins(IFitnessFunction.class);
            SQPluginManager.loadPlugins(IEquityChartAddon.class);
            SQPluginManager.loadPlugins(ICrossCheck.class);
            SQPluginManager.loadPlugins(IResultPlugin.class);
            SQPluginManager.loadPlugins(IProjectCondition.class);
            SQPluginManager.loadPlugins(IExchange.class);
        }
        catch (Exception exception) {
            Log.error("Exception while loading plugins:", (Throwable)exception);
            this.webServer.showErrorDialog("Exception while loading plugins", exception.getMessage());
        }
        System.gc();
    }

    protected void initPrograms() {
        com.strategyquant.tradinglib.results.file.FileHandler fileHandler = new com.strategyquant.tradinglib.results.file.FileHandler();
        Program.register("Loader", fileHandler);
        Program.register("Saver", fileHandler);
        System.gc();
    }

    private void checkData() {
        DataManager.checkData();
        CustomDataManager.checkData();
    }

    private void importSymbols() throws Exception {
        this.testImportData("History", "TEST_GBPUSD_M1", "M1", 1, MainApp.getDataPath() + "tests/toimport/GBPUSD_M1.csv");
        this.testImportData("History", "TEST_USDJPY_M1", "H1", 1, MainApp.getDataPath() + "tests/toimport/USDJPY_M1_SAMPLE.csv");
    }

    private void testImportData(String string, String string2, String string3, int n, String string4) {
        try {
            Object object;
            DataInfo dataInfo = DataManager.getDataInfo(string, string2);
            if (dataInfo != null && dataInfo.rows > 0) {
                object = DataManager.getDataFileName(string, string2, string3, "No Session");
                File file = new File((String)object);
                if (file.exists()) {
                    return;
                }
                DataManager.deleteData(string, string2);
            }
            if (!InstrumentManager.checkInstrumentExists(string2)) {
                InstrumentManager.addInstrument(string2, string2, 100000.0, 1.0E-4, 1.0E-5, 1.0, 0.0, "<Method type=\"None\" use=\"true\"><Params/></Method>", (byte)3);
            }
            DataManager.addData(string, string2, string2, n, 1);
            dataInfo = DataManager.getDataInfo(string, string2);
            object = string3.equals("TICK") ? DataBinWriterNew.getInstance(2, MainApp.getDataPath(), dataInfo.symbolInfo) : DataBinWriterNew.getInstance(1, MainApp.getDataPath(), dataInfo.symbolInfo);
            ((DataBinWriterNew)object).setFileName(DataManager.getDataFileName(string, string2, string3, "No Session"));
            ((DataBinWriterNew)object).open();
            this.importData(string, string3, (DataBinWriterNew)object, dataInfo, string4);
            ((DataBinWriterNew)object).close();
        }
        catch (Exception exception) {
            Log.error("Exc.", (Throwable)exception);
        }
    }

    private void importData(String string, String string2, DataBinWriterNew dataBinWriterNew, DataInfo dataInfo, String string3) throws Exception {
        ImportDataInfo importDataInfo = new ImportDataInfo();
        importDataInfo.filePath = string3;
        importDataInfo.rowCount = 10;
        importDataInfo.skipCols = 0;
        importDataInfo.skipRows = 0;
        importDataInfo.separator = ",";
        if (string2.equals("TICK")) {
            importDataInfo.dateFormat = "yyyy.MM.dd HH:mm:ss";
            importDataInfo.columnTypes = SQApp.getTickColumnList();
            importDataInfo.hasTwoVolumes = true;
        } else {
            importDataInfo.dateFormat = "yyyy.MM.dd";
            importDataInfo.columnTypes = SQApp.getOHLCColumnList();
        }
        if (dataInfo.symbol.equals("TS_Test_1")) {
            importDataInfo.dateFormat = "MM/dd/yyyy HH:mm";
            importDataInfo.skipRows = 1;
            importDataInfo.hasTwoVolumes = true;
            importDataInfo.columnTypes = SQApp.getOHLCV2ColumnList();
        }
        DataCsvLoader dataCsvLoader = new DataCsvLoader();
        dataCsvLoader.setParams(importDataInfo, dataInfo, null);
        long l = 0L;
        long l2 = 0L;
        int n = 0;
        long l3 = 0L;
        try {
            dataCsvLoader.openFile();
            while (dataCsvLoader.readData()) {
                if (!dataCsvLoader.isDataCorrect()) continue;
                dataBinWriterNew.writeData(dataCsvLoader.tickData);
                if (l == 0L) {
                    l = dataCsvLoader.tickData.time;
                }
                l2 = dataCsvLoader.tickData.time;
                ++n;
            }
            dataCsvLoader.close();
            DataCsvLoader.reset();
            DataManager.updateData(string, dataInfo.symbol, l, l2, n, l3, 1, string2, "Etc/UCT");
        }
        catch (Exception exception) {
            dataCsvLoader.close();
            throw exception;
        }
    }

    public static ArrayList<DefaultCol> getTickColumnList() {
        ArrayList<DefaultCol> arrayList = new ArrayList<DefaultCol>();
        arrayList.add(new DateTimeCol());
        arrayList.add(new BidCol());
        arrayList.add(new AskCol());
        arrayList.add(new VolumeCol());
        arrayList.add(new VolumeCol());
        return arrayList;
    }

    public static ArrayList<DefaultCol> getOHLCColumnList() {
        ArrayList<DefaultCol> arrayList = new ArrayList<DefaultCol>();
        arrayList.add(new DateCol());
        arrayList.add(new TimeCol());
        arrayList.add(new OpenCol());
        arrayList.add(new HighCol());
        arrayList.add(new LowCol());
        arrayList.add(new CloseCol());
        arrayList.add(new VolumeCol());
        return arrayList;
    }

    public static ArrayList<DefaultCol> getOHLCV2ColumnList() {
        ArrayList<DefaultCol> arrayList = new ArrayList<DefaultCol>();
        arrayList.add(new DateCol());
        arrayList.add(new TimeCol());
        arrayList.add(new OpenCol());
        arrayList.add(new HighCol());
        arrayList.add(new LowCol());
        arrayList.add(new CloseCol());
        arrayList.add(new VolumeCol());
        arrayList.add(new VolumeCol());
        return arrayList;
    }

    @Override
    public void beforeExit() {
        super.beforeExit();
        DataToSend dataToSend = new DataToSend("ExitApp", new JSONObject().put("save", (Object)"true"));
        SQWebSocketManager.addToDataQueue(dataToSend, "TASKMANAGER");
        SQWebSocketManager.addToDataQueue(dataToSend, "BUILDER");
        if (MainApp.v571hfnsHw().gWfGtoRYJG()) {
            StrategiesSaver.saveAll(false, "Save all strategies before exiting SQX.");
        }
        AllTimeStats.getInstance().end();
    }

    @Override
    public void exitApp(boolean bl) {
        super.exitApp();
        this.generateAppVersionFileForUpdater();
        if (DataManager.get() != null) {
            DataManager.flushUpdatedData();
        }
        HistoryDataManager.get().dispose();
        if (!this.isRunInConsole()) {
            if (!MainApp.AppLoaded) {
                String string = SQStructure.INTERNAL_DIR_PATH + "/web/SQUANT/filesMD5.txt";
                Log.debug("StrategyQuant X couldn't load correctly. Deleting hash file " + string);
                new File(string).delete();
            }
            if (ProjectEngine.isInitialized()) {
                ProjectEngine.stopAll();
            }
            SQApp.saveWindowSettings();
            MainApp.settings().save();
            TempFilesManager.get().destroy();
            try {
                if (SQGrid.started()) {
                    SQGrid.getGridClient().close();
                }
            }
            catch (Exception exception) {
                Log.error("Error while closing grid engine", (Throwable)exception);
            }
            new Timer().schedule(new TimerTask(){

                @Override
                public void run() {
                    MainApp.exitJVM("ok");
                }
            }, bl ? 3000L : 0L);
        } else {
            MainApp.settings().save();
            TempFilesManager.get().destroy();
            try {
                SQGrid.getGridClient().waitForAllTaskFinished();
                SQGrid.getGridClient().close();
            }
            catch (Exception exception) {
                Log.error("Error while closing grid engine", (Throwable)exception);
            }
            this.consoleAppInstance.exit();
        }
    }

    @Override
    public boolean isRunInConsole() {
        return SQApp.runInConsole();
    }

    private static void saveWindowSettings() {
    }

    public void regenerateLangs() throws Exception {
        LFileGen lFileGen = new LFileGen();
        lFileGen.start();
    }

    @Override
    public String getFrameTitle() {
        V571hfnsHw v571hfnsHw = MainApp.v571hfnsHw();
        File file = new File(MainApp.getDataPath() + "/education.txt");
        if (file.exists()) {
            return "StrategyQuant X";
        }
        String string = " StrategyQuant ";
        string = string + MainApp.printAppVersion(v571hfnsHw.printEdition(), false);
        if (v571hfnsHw.aJg1L21A0t()) {
            string = string + String.format(" for %s", v571hfnsHw.inygRmSMx7() != null ? v571hfnsHw.inygRmSMx7().getName() : "Unknown");
        }
        if (v571hfnsHw.aVwpAOwrF1()) {
            string = string + " - Licensed to: " + v571hfnsHw.oOkoIeUsMG() + " - " + v571hfnsHw.fSECzwVwpK();
        }
        string = string + " " + v571hfnsHw.printType(v571hfnsHw.eHvc2JguAd());
        String string2 = MainApp.settings().get("headerCustomText", null);
        if (string2 != null && !string2.trim().isEmpty()) {
            string = string + " - " + string2;
        }
        return string;
    }

    @Override
    public boolean initWebServer() {
        if (this.webServer != null) {
            CLILogger.log("Web server is already running.");
            return true;
        }
        try {
            this.webServer = new SQWebServer();
            this.webServer.start();
            RemoteAccessConfig.getInstance().forceRemoteAccessEnabled();
            return true;
        }
        catch (Exception exception) {
            Log.error("Cannot start web server", (Throwable)exception);
            return false;
        }
    }

    @Override
    public void reloadApp() {
        try {
            Log.debug("Reloading app...");
            this.regenerateWizardConfig(true);
            BlocksConfig.getConfig().reload();
            StrategyGeneratorCache.clear();
            this.initStatsComputer(true);
            MainServlet.getConfigsCache = null;
            try {
                StrategyBase.reload();
            }
            catch (Exception exception) {
                Log.error("!!! Exception reloading StrategyBase", (Throwable)exception);
            }
            DataToSend dataToSend = new DataToSend("ReloadUI", new JSONObject().put("reload", (Object)"true"));
            SQWebSocketManager.addToDataQueue(dataToSend, "SQUANT");
        }
        catch (Exception exception) {
            Log.error("Error while reloading app ...", (Throwable)exception);
        }
    }
}

