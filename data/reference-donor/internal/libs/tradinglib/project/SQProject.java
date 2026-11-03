/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.gridlib.client.JobDetails
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.lib.constants.SQPaths
 *  com.strategyquant.lib.memory.SQMemoryProtectionError
 *  com.strategyquant.lib.utils.JsonCreator
 *  com.strategyquant.pluginlib.SQPluginManager
 *  it.unimi.dsi.fastutil.ints.IntArrayList
 *  it.unimi.dsi.fastutil.ints.IntList
 *  org.jdom2.Content
 *  org.jdom2.Element
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.project;

import com.strategyquant.gridlib.client.JobDetails;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.lib.constants.SQPaths;
import com.strategyquant.lib.memory.SQMemoryProtectionError;
import com.strategyquant.lib.utils.JsonCreator;
import com.strategyquant.pluginlib.SQPluginManager;
import com.strategyquant.tradinglib.Databank;
import com.strategyquant.tradinglib.GeneticInfo;
import com.strategyquant.tradinglib.ProjectRunInfo;
import com.strategyquant.tradinglib.backtestrunner.DurationStats;
import com.strategyquant.tradinglib.engine.BacktestEngine;
import com.strategyquant.tradinglib.file.SQFileManager;
import com.strategyquant.tradinglib.gp.GPEvolutionMessage;
import com.strategyquant.tradinglib.plugindef.app.IAppPlugin;
import com.strategyquant.tradinglib.project.Databanks;
import com.strategyquant.tradinglib.project.DefaultProjectConfig;
import com.strategyquant.tradinglib.project.EngineCharts;
import com.strategyquant.tradinglib.project.GoToTaskException;
import com.strategyquant.tradinglib.project.ProgressEngine;
import com.strategyquant.tradinglib.project.ProjectConfigHelper;
import com.strategyquant.tradinglib.project.ProjectEngine;
import com.strategyquant.tradinglib.project.ProjectGlobalLog;
import com.strategyquant.tradinglib.project.ProjectLog;
import com.strategyquant.tradinglib.project.ProjectProgress;
import com.strategyquant.tradinglib.project.ProjectResources;
import com.strategyquant.tradinglib.project.TaskStats;
import com.strategyquant.tradinglib.project.UserConfirm;
import com.strategyquant.tradinglib.project.bestresults.BestResults;
import com.strategyquant.tradinglib.project.console.CLILogger;
import com.strategyquant.tradinglib.project.websocket.ProjectDataPublisher;
import com.strategyquant.tradinglib.taskImpl.ISQTask;
import com.strategyquant.tradinglib.taskImpl.TaskException;
import it.unimi.dsi.fastutil.ints.IntArrayList;
import it.unimi.dsi.fastutil.ints.IntList;
import java.io.File;
import java.nio.file.CopyOption;
import java.nio.file.Files;
import java.nio.file.StandardCopyOption;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.concurrent.locks.StampedLock;
import org.jdom2.Content;
import org.jdom2.Element;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class SQProject {
    private static final Logger Log = LoggerFactory.getLogger(SQProject.class);
    public static final String MemoryProtectionError = "StrategyQuant detected too big memory consumption (over 85% of memory was used)\nand automatically stopped the project.\nIt is done to prevent program freezing, it should always operate with less than 85% of memory used.\n\nThe solution is to increase the maximum available memory in Performance settings or use configuration that uses less memory.";
    public static final String OutOfMemoryError = "StrategyQuant has run out of memory\nPlease increase the maximum available memory in Performance settings or use configuration that uses less memory.";
    public static final int RunFromFirstTask = 0;
    public static final int RunFromSpecificTask = 50;
    public static final int RunOnlySpecificTask = 100;
    public static final String userConfigFileName = "project.cfx";
    private static boolean useMemoryProtection;
    private String projectName;
    private ArrayList<ISQTask> tasks;
    private Databanks databanks;
    private Element configXml = null;
    private File projectConfigFile = null;
    private String projectFolder = null;
    private boolean projectRunning = false;
    private ISQTask lastRunningTask = null;
    private ProjectRunInfo projectRunInfo = new ProjectRunInfo();
    private ProjectProgress projectProgress = new ProjectProgress();
    private GeneticInfo geneticInfo = new GeneticInfo();
    public ProgressEngine progressEngine;
    public UserConfirm userConfirm;
    public ProjectLog log;
    private ProjectGlobalLog globalLog = null;
    public EngineCharts engineCharts;
    public BestResults bestResults;
    public ProjectDataPublisher publisher;
    public boolean correctionsMade = false;
    private StampedLock runInfoLock = new StampedLock();
    private int runCycles = 1;
    private long startTime;
    private long currentTaskStartTime;
    private long pauseDuration;
    private long lastPauseTime;
    private long currentTaskPauseDuration;
    private long currentTaskLastPauseTime;
    private int runSpecification = 0;
    private String runTask = null;
    private String lastEventMessage;
    private boolean hasUnresolvedResources = false;
    private IntList tasksList = new IntArrayList();

    public SQProject(String string) throws Exception {
        this.checkProjectName(string);
        this.projectName = string = string.trim();
        this.projectFolder = this.getProjectFolderPath(string);
        this.projectConfigFile = new File(this.projectFolder + userConfigFileName);
        this.tasks = new ArrayList();
        this.databanks = new Databanks(string);
        this.progressEngine = new ProgressEngine(string);
        this.userConfirm = new UserConfirm(string);
        this.log = new ProjectLog();
        this.engineCharts = new EngineCharts(this);
        this.bestResults = new BestResults(this);
        this.publisher = new ProjectDataPublisher(this);
        this.initProject();
    }

    public static void init() {
        useMemoryProtection = Boolean.parseBoolean(MainApp.settings().get("memoryProtection", "false"));
    }

    private void initProject() throws Exception {
        File file = new File(this.projectFolder);
        if (!file.exists() && !file.mkdirs()) {
            throw new Exception(L.t((String)"Cannot create Project directory.", (Object[])new Object[0]));
        }
        if (!this.checkConfigFileExists()) {
            this.createDefaultConfigFile();
        } else {
            try {
                this.configXml = SQFileManager.loadProjectConfig(this.projectConfigFile);
            }
            catch (Exception exception) {
                Log.error("Config file of project '" + this.projectName + "' is corrupted");
                int n = MainApp.awaitUserConfirmation((String)L.t((String)"Project error", (Object[])new Object[0]), (String)L.t((String)"Config file of project '%s' is corrupted. Do you want to use default config?", (Object[])new Object[]{this.projectName}));
                if (n == 1) {
                    this.createDefaultConfigFile();
                }
                throw new Exception(L.t((String)"Project config error", (Object[])new Object[0]));
            }
        }
        this.initDatabanksFromConfig();
        this.updateProjectDatabanks();
        this.checkTasksConfig();
        this.checkUnresolvedResources();
        if (this.correctionsMade) {
            SQFileManager.updateProjectConfig(this.projectConfigFile, this.configXml);
        }
    }

    public Element checkUnresolvedResources() {
        this.hasUnresolvedResources = false;
        Element element = null;
        if (!ProjectEngine.isDefaulProject(this.projectName)) {
            try {
                element = ProjectResources.checkProjectResources(this.projectConfigFile, this.configXml);
                if (element != null) {
                    if (element.getChildren().size() > 0) {
                        this.setUnresolvedResources(true);
                    } else {
                        element = null;
                    }
                }
            }
            catch (Exception exception) {
                Log.error(String.format("Checking project '%s' resources failed. Exc.", this.getName()), (Throwable)exception);
            }
        }
        return element;
    }

    private void checkTasksConfig() throws Exception {
        try {
            if (SQProject.projectIsOlderThan136(this.configXml)) {
                this.transformProjectFile();
            }
            Element element = this.configXml.getChild("Tasks");
            List list = element.getChildren("Task");
            for (Element element2 : list) {
                Element element3;
                ISQTask iSQTask;
                Object object;
                String string = XMLUtil.getStringAttr((Element)element2, (String)"taskXMLFile", null);
                Element element4 = SQFileManager.loadTaskConfig(this.projectConfigFile, string);
                boolean bl = false;
                if (element4.getChild("Databanks") == null) {
                    object = XMLUtil.getStringAttr((Element)element2, (String)"type", null);
                    try {
                        iSQTask = this.findTaskPluginByType((String)object);
                        Element element5 = iSQTask.getDefaultConfig("task_forex.xml");
                        Element element6 = element5.getChild("Settings");
                        Element element7 = element3 = element6 != null ? element6.getChild("Databanks") : null;
                        if (element3 != null) {
                            element4.addContent((Content)element3.clone());
                            SQFileManager.updateTaskConfig(this.projectConfigFile, string, element4);
                            Log.info("Project '{}', task '{}' - injected missing <Databanks> from default config.", (Object)this.projectName, (Object)string);
                        }
                    }
                    catch (Exception exception) {
                        Log.error("Project '{}', task '{}' - could not inject default <Databanks>: {}", new Object[]{this.projectName, string, exception.getMessage()});
                    }
                }
                if ((object = element4.getChild("CrossChecks")) == null || (iSQTask = object.getChild("MonteCarloRetest")) == null || iSQTask.getChild("Settings") == null) continue;
                for (Element element6 : iSQTask.getChild("Settings").getChild("Methods").getChildren("Method")) {
                    if (!element6.getAttributeValue("type").equals("RandomizeHistoryData")) continue;
                    element3 = element6.getChild("Params").clone();
                    element3.removeContent();
                    for (Element element8 : element6.getChild("Params").getChildren("Param")) {
                        if (element8.getAttributeValue("key").equals("Probability")) {
                            element3.addContent((Content)element8.clone().setAttribute("key", "ProbabilityUp"));
                            element3.addContent((Content)element8.clone().setAttribute("key", "ProbabilityDown"));
                            continue;
                        }
                        if (!element8.getAttributeValue("key").equals("MaxChange")) continue;
                        element3.addContent((Content)element8.clone().setAttribute("key", "MaxChangeUp"));
                        element3.addContent((Content)element8.clone().setAttribute("key", "MaxChangeDown"));
                    }
                    if (element3.getChildren().isEmpty() || !element6.removeChild("Params")) continue;
                    element6.addContent((Content)element3);
                    bl = true;
                }
                if (!bl) continue;
                SQFileManager.updateTaskConfig(this.projectConfigFile, string, element4);
            }
        }
        catch (Exception exception) {
            Log.error(String.format("Checking project '%s' xml failed. Exc.", this.getName()), (Throwable)exception);
            throw exception;
        }
    }

    public static boolean projectIsOlderThan136(Element element) {
        String string = null;
        try {
            string = element.getAttributeValue("name");
            String string2 = XMLUtil.getStringAttr((Element)element, (String)"version", null);
            if (string2 == null) {
                return true;
            }
            int n = Integer.parseInt(string2.substring(0, string2.indexOf(".")));
            return n < 136;
        }
        catch (Exception exception) {
            Log.error("Error while checking project file version of project " + string, (Throwable)exception);
            return true;
        }
    }

    private void transformProjectFile() throws Exception {
        File file = new File(this.projectFolder + SQUtils.stripExtension((String)this.projectConfigFile.getName()) + "_backup." + "cfx");
        Files.copy(this.projectConfigFile.toPath(), file.toPath(), StandardCopyOption.REPLACE_EXISTING);
        if (!this.projectConfigFile.delete()) {
            throw new Exception(L.t((String)"Unable to delete old config file %s", (Object[])new Object[]{this.projectConfigFile.getAbsolutePath()}));
        }
        SQFileManager.createV136ProjectFile(this);
        if (!file.delete()) {
            Log.warn("Unable to delete old project backup file " + file.getAbsolutePath());
        }
    }

    private boolean checkConfigFileExists() {
        if (!this.projectConfigFile.exists()) {
            File file = new File(this.projectFolder + "project.xml");
            if (file.exists()) {
                try {
                    SQFileManager.xmlToCfx(file, true);
                }
                catch (Exception exception) {
                    Log.error("Error while converting xml file to cfx", (Throwable)exception);
                    this.projectConfigFile = file;
                }
            } else {
                return false;
            }
        }
        return true;
    }

    public void initTasksFromConfig() throws Exception {
        this.tasks.clear();
        Element element = this.configXml.getChild("Tasks");
        List list = element.getChildren("Task");
        boolean bl = false;
        boolean bl2 = false;
        for (Element element2 : list) {
            String string = XMLUtil.getAttr((Element)element2, (String)"type");
            String string2 = XMLUtil.getAttr((Element)element2, (String)"name");
            if (this.runSpecification == 100) {
                if (!this.runTask.equals(string2) || !string.equals("GoToTask")) continue;
                bl2 = true;
                continue;
            }
            if (this.runSpecification != 50) continue;
            if (!bl) {
                bl = this.runTask.equals(string2);
            }
            if (!bl || !string.equals("GoToTask")) continue;
            bl2 = true;
        }
        HashMap<String, Element> hashMap = SQFileManager.loadTaskConfigs(this.projectConfigFile);
        int n = 1;
        bl = false;
        for (String string2 : list) {
            String string = XMLUtil.getAttr((Element)string2, (String)"type");
            String string3 = XMLUtil.getAttr((Element)string2, (String)"name");
            String string4 = string2.getAttributeValue("title");
            String string5 = string2.getAttributeValue("taskXMLFile");
            boolean bl3 = Boolean.parseBoolean(XMLUtil.tryGetAttr((Element)string2, (String)"active", (String)"true"));
            Element element3 = (Element)hashMap.get(string5);
            ISQTask iSQTask = this.findTaskPluginByType(string);
            boolean bl4 = false;
            if (this.runSpecification == 100) {
                bl4 = this.runTask.equals(string3);
                if (bl2) {
                    bl4 = true;
                }
            } else if (this.runSpecification == 50) {
                if (!bl) {
                    bl = this.runTask.equals(string3);
                }
                if (bl) {
                    bl4 = bl3;
                }
                if (bl2 && bl3) {
                    bl4 = true;
                }
            } else {
                bl4 = bl3;
            }
            if (this.hasUnresolvedResources) {
                bl4 = false;
            }
            ISQTask iSQTask2 = iSQTask.clone(this.projectName, this.progressEngine);
            iSQTask2.setActive(bl3);
            iSQTask2.setCustomName(string3);
            iSQTask2.setConfigFileName(string5);
            iSQTask2.setTitle(string4);
            iSQTask2.setIndex(n);
            iSQTask2.setConfig(element3, true, bl4);
            this.tasks.add(iSQTask2);
            ++n;
        }
    }

    private void initDatabanksFromConfig() throws Exception {
        this.correctionsMade = this.databanks.loadFromConfig(this.configXml);
    }

    public DefaultProjectConfig getDefaultConfig() throws Exception {
        ArrayList<String> arrayList = new ArrayList<String>();
        DefaultProjectConfig defaultProjectConfig = new DefaultProjectConfig();
        defaultProjectConfig.projectConfig = this.createDefaultProjectXml();
        defaultProjectConfig.taskConfig = null;
        IAppPlugin iAppPlugin = this.getAppPlugin();
        if (iAppPlugin != null && iAppPlugin.getDefaultTaskType() != null && iAppPlugin.getDefaultTaskName() != null) {
            for (ISQTask iSQTask : SQPluginManager.getPlugins(ISQTask.class)) {
                if (!iSQTask.getType().equals(iAppPlugin.getDefaultTaskType())) continue;
                Element element = iSQTask.getDefaultConfig("task_forex.xml");
                String string = iAppPlugin.getDefaultTaskType();
                element.setAttribute("type", string);
                element.setAttribute("name", iAppPlugin.getDefaultTaskName());
                defaultProjectConfig.taskXMLFileName = this.generateTaskXMLFileName(string);
                element.setAttribute("taskXMLFile", defaultProjectConfig.taskXMLFileName);
                defaultProjectConfig.taskConfig = element.getChild("Settings").clone();
                element.removeContent();
                defaultProjectConfig.projectConfig.getChild("Tasks").addContent((Content)element);
                Element element2 = defaultProjectConfig.projectConfig.getChild("Databanks");
                element2.removeContent();
                Element element3 = defaultProjectConfig.taskConfig.getChild("Databanks");
                for (Element element4 : element3.getChildren("Databank")) {
                    Element element5 = new Element("Databank");
                    String string2 = element4.getAttributeValue("value");
                    if (arrayList.contains(string2)) continue;
                    arrayList.add(string2);
                    element5.setAttribute("name", element4.getAttributeValue("value"));
                    element5.setAttribute("view", "Default - Main data");
                    element5.setAttribute("syncType", "Auto-sync never");
                    element2.addContent((Content)element5);
                }
            }
        }
        return defaultProjectConfig;
    }

    public String generateTaskXMLFileName(String string) {
        String string2 = string + "-Task";
        String string3 = ".xml";
        ArrayList<String> arrayList = new ArrayList<String>();
        for (ISQTask object : this.tasks) {
            arrayList.add(object.getTaskXMLFileName());
        }
        for (int i = 1; i < 1000; ++i) {
            String string4 = string2 + i + string3;
            if (arrayList.contains(string4)) continue;
            return string4;
        }
        return string2 + System.currentTimeMillis() + string3;
    }

    private void createDefaultConfigFile() throws Exception {
        DefaultProjectConfig defaultProjectConfig = this.getDefaultConfig();
        SQFileManager.createV136ProjectFile(this.projectConfigFile, defaultProjectConfig);
        this.configXml = defaultProjectConfig.projectConfig;
    }

    private IAppPlugin getAppPlugin() {
        for (IAppPlugin iAppPlugin : SQPluginManager.getPlugins(IAppPlugin.class)) {
            String string = iAppPlugin.getProject();
            if (string == null || !string.equals(this.projectName)) continue;
            return iAppPlugin;
        }
        return null;
    }

    private Element createDefaultProjectXml() {
        Element element = new Element("Project");
        element.setAttribute("name", this.projectName);
        element.setAttribute("version", MainApp.getAppVersion());
        element.addContent((Content)new Element("Tasks"));
        Element element2 = new Element("Databanks");
        element2.addContent((Content)Databank.getDefaultConfig());
        element.addContent((Content)element2);
        return element;
    }

    public ISQTask addTask(String string, String string2) throws Exception {
        return this.addTask(string, string2, -1);
    }

    public ISQTask addTask(String string, String string2, int n) throws Exception {
        this.checkProjectStatus("add");
        if (this.containsTask(string)) {
            return null;
        }
        ISQTask iSQTask = this.findTaskPluginByType(string2);
        String string3 = this.generateTaskXMLFileName(string2);
        Element element = iSQTask.getDefaultConfig("task_forex.xml");
        element.setAttribute("name", string);
        element.setAttribute("type", string2);
        element.setAttribute("taskXMLFile", string3);
        Element element2 = element.getChild("Settings").clone();
        iSQTask.setConfig(element2, false, true);
        iSQTask.setCustomName(string);
        iSQTask.setConfigFileName(string3);
        element.removeContent();
        Element element3 = this.configXml.getChild("Tasks");
        if (n >= 0) {
            element3.addContent(n, (Content)element);
            this.tasks.add(n, iSQTask);
        } else {
            element3.addContent((Content)element);
            this.tasks.add(iSQTask);
        }
        this.updateProjectDatabanks();
        this.saveConfig();
        return iSQTask;
    }

    public ISQTask removeTask(String string) throws Exception {
        this.checkProjectStatus("remove");
        Element element = this.configXml.getChild("Tasks");
        List list = element.getChildren("Task");
        for (int i = 0; i < list.size(); ++i) {
            String string2 = ((Element)list.get(i)).getAttributeValue("name");
            if (!string2.equals(string)) continue;
            list.remove(i);
            break;
        }
        ISQTask iSQTask = null;
        for (int i = this.tasks.size() - 1; i >= 0; --i) {
            ISQTask iSQTask2 = this.tasks.get(i);
            if (!iSQTask2.getCustomName().equals(string)) continue;
            iSQTask = this.tasks.remove(i);
            break;
        }
        this.updateProjectDatabanks();
        this.saveConfig();
        return iSQTask;
    }

    public void checkProjectStatus(String string) throws Exception {
        if (this.getRunningStatus() != 0 && this.getRunningStatus() != 100 && this.getRunningStatus() != 3 && this.getRunningStatus() != 4 && this.getRunningStatus() != 50) {
            throw new Exception(L.t((String)"Cannot %s task while project is running", (Object[])new Object[]{string}));
        }
    }

    private void updateProjectDatabanks() {
        String string;
        ArrayList<String> arrayList = new ArrayList<String>();
        Element element = this.configXml.getChild("Tasks");
        Element element2 = this.configXml.getChild("Databanks");
        Element element3 = new Element("Databanks");
        for (Element element4 : element2.getChildren("Databank")) {
            string = element4.getAttributeValue("name");
            if (arrayList.contains(string)) continue;
            arrayList.add(string);
            element3.addContent((Content)element4.clone());
        }
        for (Element element4 : element.getChildren("Task")) {
            string = element4.getAttributeValue("type");
            try {
                ISQTask iSQTask = this.findTaskPluginByType(string);
                Element element5 = iSQTask.getDefaultConfig("task_forex.xml");
                Element element6 = element5.getChild("Settings").getChild("Databanks");
                if (element6 == null) continue;
                for (Element element7 : element6.getChildren("Databank")) {
                    String string2 = element7.getAttributeValue("value");
                    if (string2 == null || arrayList.contains(string2)) continue;
                    arrayList.add(string2);
                    Element element8 = new Element("Databank");
                    element8.setAttribute("name", string2);
                    element8.setAttribute("view", "Default");
                    element8.setAttribute("syncType", "Auto-sync never");
                    element3.addContent((Content)element8);
                    this.databanks.add(string2);
                    this.correctionsMade = true;
                }
            }
            catch (Exception exception) {
                Log.debug("Cannot read databank settings of task '" + element4.getAttributeValue("name") + "'", (Throwable)exception);
            }
        }
        if (!arrayList.contains("Results")) {
            element3.addContent((Content)Databank.getDefaultConfig());
            this.databanks.add("Results");
            this.correctionsMade = true;
        }
        this.databanks.updatePositions();
        this.configXml.removeContent((Content)element2);
        this.configXml.addContent((Content)element3);
    }

    public void moveTask(String string, int n) throws Exception {
        this.checkProjectStatus("move");
        Element element = this.configXml.getChild("Tasks");
        List list = element.getChildren("Task");
        for (int i = 0; i < list.size(); ++i) {
            Element element2 = ((Element)list.get(i)).clone();
            String string2 = element2.getAttributeValue("name");
            if (!string2.equals(string)) continue;
            if (i == n) {
                return;
            }
            list.remove(i);
            if (i > n) {
                list.add(n, element2);
                break;
            }
            list.add(n - 1, element2);
            break;
        }
        this.saveConfig();
    }

    public boolean containsTask(String string) {
        Element element = this.configXml.getChild("Tasks");
        List list = element.getChildren("Task");
        for (Element element2 : list) {
            String string2 = element2.getAttributeValue("name");
            if (!string2.equals(string)) continue;
            return true;
        }
        return false;
    }

    public Element getTaskConfigByName(String string) {
        Element element = this.configXml.getChild("Tasks");
        List list = element.getChildren("Task");
        for (Element element2 : list) {
            String string2 = element2.getAttributeValue("name");
            if (!string2.equals(string)) continue;
            return element2;
        }
        return null;
    }

    public Element getTaskSettingsByName(String string) {
        for (int i = 0; i < this.tasks.size(); ++i) {
            ISQTask iSQTask = this.tasks.get(i);
            if (!iSQTask.getCustomName().equals(string)) continue;
            return iSQTask.getConfig();
        }
        return null;
    }

    public Element getTaskSettingsByTitle(String string) {
        for (int i = 0; i < this.tasks.size(); ++i) {
            ISQTask iSQTask = this.tasks.get(i);
            if (!iSQTask.getTitle().equals(string)) continue;
            return iSQTask.getConfig();
        }
        return null;
    }

    public ISQTask getTaskByXMLFile(String string) {
        for (int i = 0; i < this.tasks.size(); ++i) {
            ISQTask iSQTask = this.tasks.get(i);
            if (!iSQTask.getTaskXMLFileName().equals(string)) continue;
            return iSQTask;
        }
        return null;
    }

    public Element getTaskSettingsByXMLFile(String string) {
        for (int i = 0; i < this.tasks.size(); ++i) {
            ISQTask iSQTask = this.tasks.get(i);
            if (!iSQTask.getTaskXMLFileName().equals(string)) continue;
            return iSQTask.getConfig();
        }
        return null;
    }

    public int getTaskElementIndex(String string) {
        Element element = this.configXml.getChild("Tasks");
        List list = element.getChildren("Task");
        for (int i = 0; i < list.size(); ++i) {
            Element element2 = (Element)list.get(i);
            String string2 = element2.getAttributeValue("name");
            if (!string2.equals(string)) continue;
            return i;
        }
        return -1;
    }

    public int getTasksCount() {
        Element element = this.configXml.getChild("Tasks");
        List list = element.getChildren("Task");
        return list.size();
    }

    public Databank addDatabank(String string, int n) throws Exception {
        if (this.databanks.containsKey(string)) {
            return (Databank)this.databanks.get(string);
        }
        Databank databank = this.databanks.add(string);
        databank.setPosition(n);
        Element element = this.configXml.getChild("Databanks");
        Element element2 = databank.getConfig();
        element.addContent((Content)element2);
        this.saveConfig();
        return databank;
    }

    public boolean removeDatabank(String string) throws Exception {
        if (!this.databanks.containsKey(string)) {
            return false;
        }
        Databank databank = (Databank)this.databanks.remove(string);
        databank.clearRecords(true, false, String.format("Remove databank %s/%s.", this.projectName, string));
        File file = new File(databank.getDatabankFolder());
        SQUtils.deleteRecursive((File)file);
        file.delete();
        Element element = this.configXml.getChild("Databanks");
        List list = element.getChildren("Databank");
        for (Element element2 : list) {
            if (!string.equals(element2.getAttributeValue("name"))) continue;
            list.remove(element2);
            break;
        }
        this.saveConfig();
        return true;
    }

    public boolean containsDatabank() {
        try {
            ArrayList<String> arrayList = this.listDatabanks();
            return !arrayList.isEmpty();
        }
        catch (Exception exception) {
            return false;
        }
    }

    public Databank getResultsDatabank() {
        try {
            return (Databank)this.databanks.get("Results");
        }
        catch (Exception exception) {
            return null;
        }
    }

    private ArrayList<String> listDatabanks() throws Exception {
        ArrayList<String> arrayList = new ArrayList<String>();
        Element element = XMLUtil.getChildElem((Element)this.configXml, (String)"Databanks");
        List list = element.getChildren("Databank");
        for (Element element2 : list) {
            String string = element2.getAttributeValue("name");
            arrayList.add(string);
        }
        return arrayList;
    }

    public boolean isRunning() {
        return this.projectRunning;
    }

    public String getActiveTaskName() {
        return this.isRunning() && this.lastRunningTask != null ? this.lastRunningTask.getCustomName() : null;
    }

    public ISQTask getLastRunningTask() {
        return this.lastRunningTask;
    }

    public void saveConfig() throws Exception {
        if (this.configXml.getAttributeValue("version") == null) {
            this.configXml.setAttribute("version", MainApp.getAppVersion());
        }
        SQFileManager.updateWholeProjectConfig(this);
    }

    private ISQTask findTaskPluginByType(String string) throws Exception {
        for (ISQTask iSQTask : SQPluginManager.getPlugins(ISQTask.class)) {
            if (!iSQTask.getType().equals(string)) continue;
            return iSQTask.clone(this.projectName, this.progressEngine);
        }
        throw new Exception(L.t((String)"Task '%s' does not exist.", (Object[])new Object[]{string}));
    }

    public ISQTask getTaskByName(String string) throws Exception {
        for (int i = 0; i < this.tasks.size(); ++i) {
            ISQTask iSQTask = this.tasks.get(i);
            if (!iSQTask.getCustomName().equals(string)) continue;
            return iSQTask;
        }
        throw new Exception(L.t((String)"Task '%s' does not exist.", (Object[])new Object[]{string}));
    }

    public boolean containsTaskByName(String string) throws Exception {
        for (int i = 0; i < this.tasks.size(); ++i) {
            ISQTask iSQTask = this.tasks.get(i);
            if (!iSQTask.getCustomName().equals(string)) continue;
            return true;
        }
        return false;
    }

    public ISQTask getTaskByHash(int n) throws Exception {
        for (int i = 0; i < this.tasks.size(); ++i) {
            ISQTask iSQTask = this.tasks.get(i);
            if (iSQTask.getCustomName().hashCode() != n) continue;
            return iSQTask;
        }
        throw new Exception(L.t((String)"Task with hash '%s' does not exist.", (Object[])new Object[]{n}));
    }

    public ISQTask getTask(int n) throws Exception {
        return this.tasks.get(n);
    }

    public IntList getTasksHashes() throws Exception {
        this.tasksList.clear();
        Element element = this.configXml.getChild("Tasks");
        List list = element.getChildren("Task");
        for (int i = 0; i < list.size(); ++i) {
            this.tasksList.add(((Element)list.get(i)).getAttributeValue("name").hashCode());
        }
        return this.tasksList;
    }

    private int getIndexOfTask(String string) throws Exception {
        for (int i = 0; i < this.tasks.size(); ++i) {
            ISQTask iSQTask = this.tasks.get(i);
            if (!iSQTask.getCustomName().equals(string)) continue;
            return i;
        }
        throw new Exception(L.t((String)"Task '%s' does not exist.", (Object[])new Object[]{string}));
    }

    public void start() throws Exception {
        int n;
        if (MainApp.v571hfnsHw().eHvc2JguAd() == null) {
            throw new Exception(L.t((String)"Missing license.", (Object[])new Object[0]));
        }
        this.resetTracking(false, true);
        this.progressEngine.reset();
        this.publisher.resetLastData("engine-channel");
        this.globalLog = null;
        Log.info("=========== Project started ===========");
        for (n = 0; n < this.tasks.size(); ++n) {
            ISQTask iSQTask = this.tasks.get(n);
            if (!this.tasks.get(n).getSettingsData().hasErrors()) continue;
            this.progressEngine.setStatus(50);
            this.projectRunInfo.errorInfo = this.isCustomProject() ? L.t((String)"Cannot start project '%s', it has config errors in task '%s'.", (Object[])new Object[]{this.getName(), iSQTask.getTitle()}) : L.t((String)"Cannot start project '%s', it has config errors.", (Object[])new Object[]{this.getName()});
            this.projectRunInfo.error = this.tasks.get(n).getErrorsDescription();
            this.projectRunInfo.errorType = 50;
            throw new Exception(this.projectRunInfo.errorInfo + "\n" + this.projectRunInfo.error);
        }
        if (this.databanks.isEmpty()) {
            throw new Exception(L.t((String)"No databanks found.", (Object[])new Object[0]));
        }
        if (this.tasks.isEmpty()) {
            throw new Exception(L.t((String)"No tasks found.", (Object[])new Object[0]));
        }
        n = 0;
        for (int i = 0; i < this.tasks.size(); ++i) {
            if (!this.tasks.get(i).isActive()) continue;
            n = 1;
            break;
        }
        if (n == 0) {
            throw new Exception(L.t((String)"No active task found.", (Object[])new Object[0]));
        }
        this.runCycles = 1;
        this.startTime = System.currentTimeMillis();
        this.pauseDuration = 0L;
        if (MainApp.runInConsoleWithoutActiveWebserver() && !MainApp.runInConsoleInInteractiveMode()) {
            this.performStartProject();
        } else {
            new Thread(){

                @Override
                public void run() {
                    SQProject.this.performStartProject();
                }
            }.start();
        }
    }

    private void waitForTaskFinish() {
        while (!this.progressEngine.isStopped()) {
            try {
                Thread.sleep(200L);
            }
            catch (InterruptedException interruptedException) {
                Log.info("Interrupted exception", (Throwable)interruptedException);
            }
        }
    }

    public void stop() {
        if (this.progressEngine.getRunningStatus() != 6 && this.progressEngine.getRunningStatus() != 4) {
            this.progressEngine.stop();
        } else {
            this.publisher.resetLastData("engine-channel");
        }
    }

    public void pause() {
        if (this.progressEngine.getRunningStatus() != 5 && this.progressEngine.getRunningStatus() != 2) {
            this.lastPauseTime = System.currentTimeMillis();
            this.currentTaskLastPauseTime = System.currentTimeMillis();
            this.progressEngine.pause();
        } else {
            this.publisher.resetLastData("engine-channel");
        }
    }

    public void resume() {
        if (this.progressEngine.getRunningStatus() != 1) {
            this.pauseDuration += System.currentTimeMillis() - this.lastPauseTime;
            this.currentTaskPauseDuration += System.currentTimeMillis() - this.currentTaskLastPauseTime;
            this.progressEngine.resume();
        } else {
            this.publisher.resetLastData("engine-channel");
        }
    }

    public void checkPaused() {
        this.progressEngine.checkPaused();
    }

    public void printToLog(String string) {
        this.progressEngine.printToLog(string);
    }

    public int getRunningStatus() {
        return this.progressEngine.getRunningStatus();
    }

    public void resetTracking(boolean bl, boolean bl2) {
        this.projectRunInfo.jobExceptionsCount = 0;
        this.projectRunInfo.totalJobsDone = 0L;
        this.projectRunInfo.runningJobs = 0L;
        this.projectRunInfo.waitingJobs = 0L;
        if (bl2) {
            this.projectRunInfo.startTime = System.currentTimeMillis();
            this.projectRunInfo.projectRunningTime = 0L;
            this.projectRunInfo.totalProjectRunningTime = 0L;
        }
        this.currentTaskStartTime = 0L;
        this.currentTaskPauseDuration = 0L;
        this.projectRunInfo.taskRunningTime = 0L;
        this.projectRunInfo.backtestsPerformed = 0L;
        this.projectRunInfo.strategiesGenerated = 0L;
        this.projectRunInfo.strategiesRejected = 0L;
        this.projectRunInfo.strategiesRejectedPct = 0.0;
        this.projectRunInfo.strategiesAccepted = 0L;
        this.projectRunInfo.strategiesAcceptedPct = 0.0;
        this.projectRunInfo.timePerStrategy = 0L;
        this.projectRunInfo.timePerAcceptedStrategy = 0L;
        this.projectRunInfo.strategiesPerHour = 0.0;
        this.projectRunInfo.acceptedStrategiesPerHour = 0.0;
        this.projectRunInfo.strategiesPassed = 0L;
        this.projectRunInfo.strategiesFailed = 0L;
        this.projectRunInfo.infiniteProgress = bl;
        this.projectRunInfo.error = null;
        this.projectRunInfo.errorInfo = null;
        this.projectRunInfo.errorType = 0;
        this.projectRunInfo.progressPercent = 0.0;
        this.projectRunInfo.resetAcceptedCounts();
        this.projectRunInfo.resetDismissalCounts();
        this.projectRunInfo.resetDurationStats();
    }

    public void trackJob(JobDetails jobDetails, int n, DurationStats durationStats, int n2, long l, long l2) {
        ++this.projectRunInfo.totalJobsDone;
        if (jobDetails != null && !jobDetails.isSuccess()) {
            ++this.projectRunInfo.jobExceptionsCount;
        }
        this.projectRunInfo.backtestsPerformed = BacktestEngine.backtestsCount.get();
        this.projectRunInfo.runningJobs = l;
        this.projectRunInfo.waitingJobs = l2;
        this.projectRunInfo.strategiesGenerated = this.projectRunInfo.totalJobsDone;
        if (n == 10007 || n == 10006) {
            ++this.projectRunInfo.strategiesAccepted;
            this.projectRunInfo.increaseAcceptedReasonCount(n);
        } else if (n > 0) {
            ++this.projectRunInfo.strategiesRejected;
            this.projectRunInfo.increaseDismissalReasonCount(n);
        } else {
            ++this.projectRunInfo.strategiesAccepted;
            this.projectRunInfo.increaseAcceptedReasonCount(n);
        }
        this.projectRunInfo.strategiesRejectedPct = this.computePct(this.projectRunInfo.strategiesRejected, this.projectRunInfo.strategiesGenerated);
        this.projectRunInfo.strategiesAcceptedPct = this.computePct(this.projectRunInfo.strategiesAccepted, this.projectRunInfo.strategiesGenerated);
        this.projectRunInfo.projectRunningTime = this.getProjectRunningTime();
        this.projectRunInfo.totalProjectRunningTime = this.getTotalProjectRunningTime();
        this.projectRunInfo.taskRunningTime = this.getCurrentTaskRunningTime();
        this.projectRunInfo.timePerStrategy = this.projectRunInfo.totalJobsDone > 0L ? this.projectRunInfo.taskRunningTime / this.projectRunInfo.totalJobsDone : 0L;
        this.projectRunInfo.timePerAcceptedStrategy = this.projectRunInfo.strategiesAccepted > 0L ? this.projectRunInfo.taskRunningTime / this.projectRunInfo.strategiesAccepted : 0L;
        this.projectRunInfo.strategiesPerHour = 3600000.0 * (double)this.projectRunInfo.totalJobsDone / (double)this.projectRunInfo.taskRunningTime;
        this.projectRunInfo.acceptedStrategiesPerHour = 3600000.0 * (double)this.projectRunInfo.strategiesAccepted / (double)this.projectRunInfo.taskRunningTime;
        if (durationStats != null) {
            this.projectRunInfo.updateDurationStats(durationStats);
        }
    }

    public void increaseGlobalStats(int n, String string, long l, String string2, long l2) {
        if (this.globalLog == null) {
            return;
        }
        this.globalLog.increaseStats(n, string, l, string2, l2);
    }

    public void setGlobalStats(String string, int n, String string2, long l, int n2, String string3) {
        if (this.globalLog == null) {
            return;
        }
        this.globalLog.setStats(string, n, string2, l, n2, string3);
    }

    public void setGlobalStats(String string, int n, String string2, long l, int n2) {
        if (this.globalLog == null) {
            return;
        }
        this.globalLog.setStats(string, n, string2, l, n2, "");
    }

    public void increaseGlobalStats(String string, int n, String string2, long l, int n2) {
        if (this.globalLog == null) {
            return;
        }
        this.globalLog.increaseStats(string, n, string2, l, n2);
    }

    private double computePct(double d, double d2) {
        if (d2 == 0.0) {
            return 0.0;
        }
        return d / d2;
    }

    public double getFailedJobsPercentage() {
        long l = this.projectRunInfo.totalJobsDone;
        int n = this.projectRunInfo.jobExceptionsCount;
        if (l < 3L) {
            return 0.0;
        }
        return (long)n / l;
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public void loadTrackingInfo(ProjectRunInfo projectRunInfo, boolean bl) {
        long l = this.runInfoLock.readLock();
        try {
            projectRunInfo.copyFrom(this.projectRunInfo, bl);
        }
        finally {
            this.runInfoLock.unlock(l);
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public void updateTrackingInfo(ProjectRunInfo projectRunInfo) {
        long l = this.runInfoLock.writeLock();
        try {
            this.projectRunInfo.copyFrom(projectRunInfo, false);
        }
        finally {
            this.runInfoLock.unlock(l);
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public ProjectRunInfo getTrackingInfo() {
        long l = this.runInfoLock.readLock();
        try {
            ProjectRunInfo projectRunInfo = this.projectRunInfo;
            return projectRunInfo;
        }
        finally {
            this.runInfoLock.unlock(l);
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public void increaseTrackingInfoStep(int n) {
        long l = this.runInfoLock.writeLock();
        try {
            ++this.projectRunInfo.step;
            this.projectRunInfo.progressPercent = n == 0 ? 100.0 : (double)this.projectRunInfo.step / (double)n * 100.0;
        }
        finally {
            this.runInfoLock.unlock(l);
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public void setTrackingInfoReasonToDismiss(int n, String string) {
        long l = this.runInfoLock.writeLock();
        try {
            this.projectRunInfo.getDismissalReasons().put(n, (Object)string);
        }
        finally {
            this.runInfoLock.unlock(l);
        }
    }

    public String getProjectFolderPath(String string) {
        return SQPaths.projectsDirPath + "/" + string + "/";
    }

    public boolean isAppProject() {
        return this.getAppPlugin() != null;
    }

    private boolean isCustomProject() {
        return !this.isAppProject();
    }

    public Element getConfig() {
        if (this.configXml.getAttributeValue("version") == null) {
            this.configXml.setAttribute("version", MainApp.getAppVersion());
        }
        return this.configXml;
    }

    public void updateConfig(Element element) throws Exception {
        this.configXml = element;
        SQFileManager.updateProjectConfig(this);
    }

    public Databanks getDatabanks() {
        return this.databanks;
    }

    public String getName() {
        return this.projectName;
    }

    public String getProjectFolder() {
        String string = this.projectFolder;
        Log.debug("Project log folder is '{}'", (Object)string);
        return string;
    }

    public void beforeStart() throws Exception {
        Databank databank;
        ArrayList<File> arrayList;
        if (this.projectName.equals("Optimizer") && ((arrayList = ProjectConfigHelper.getOptimizationStrategies(this, databank = (Databank)this.databanks.get("Results"))) == null && databank.size() > 0 || arrayList != null && databank.size() > arrayList.size())) {
            this.userConfirm.awaitConfirmation(L.t((String)"Databank not empty", (Object[])new Object[0]), L.t((String)"Do you want to remove old optimization results from Results databank?", (Object[])new Object[0]));
            if (this.userConfirm.isConfirmed()) {
                databank.removeAll(true, "Optimizer - before start, user confirmed to remove old optimization results from Results databank.");
            }
        }
    }

    public void confirm(boolean bl) {
        this.userConfirm.setConfirmed(bl);
    }

    public ProjectProgress getProgress() {
        return this.projectProgress;
    }

    public void increaseFailedJobsCount() {
        long l = this.runInfoLock.writeLock();
        try {
            ++this.projectRunInfo.jobExceptionsCount;
        }
        finally {
            this.runInfoLock.unlock(l);
        }
    }

    public void increaseStrategiesFailed() {
        long l = this.runInfoLock.writeLock();
        try {
            ++this.projectRunInfo.strategiesFailed;
        }
        finally {
            this.runInfoLock.unlock(l);
        }
    }

    public void increaseStrategiesPassed() {
        long l = this.runInfoLock.writeLock();
        try {
            ++this.projectRunInfo.strategiesPassed;
        }
        finally {
            this.runInfoLock.unlock(l);
        }
    }

    public GeneticInfo getGeneticInfo() {
        return this.geneticInfo;
    }

    public void resetGeneticInfo(boolean bl, int n) {
        this.geneticInfo.reset(bl, n);
        this.engineCharts.fitnessEvolution.reset(bl, n);
    }

    public void updateGeneticInfo(GPEvolutionMessage gPEvolutionMessage, boolean bl) {
        this.geneticInfo.update(gPEvolutionMessage);
        this.engineCharts.fitnessEvolution.addNextIslansEvodData(this.geneticInfo.getIslandsEvoData(), bl);
    }

    public void setTaskTitle(String string, String string2) throws Exception {
        this.checkProjectStatus("rename");
        Element element = this.configXml.getChild("Tasks");
        List list = element.getChildren("Task");
        for (int i = 0; i < list.size(); ++i) {
            Element element2 = (Element)list.get(i);
            String string3 = element2.getAttributeValue("name");
            if (!string3.equals(string)) continue;
            element2.setAttribute("title", string2);
            break;
        }
        this.saveConfig();
    }

    public void setTaskActive(String string, boolean bl) throws Exception {
        this.checkProjectStatus("set the status of");
        Element element = this.configXml.getChild("Tasks");
        List list = element.getChildren("Task");
        for (int i = 0; i < list.size(); ++i) {
            Element element2 = (Element)list.get(i);
            String string2 = element2.getAttributeValue("name");
            if (!string2.equals(string)) continue;
            element2.setAttribute("active", bl + "");
            break;
        }
        this.saveConfig();
    }

    public ISQTask cloneTask(String string, String string2) throws Exception {
        this.checkProjectStatus("clone");
        int n = this.getTaskElementIndex(string);
        if (n < 0) {
            throw new Exception(L.t((String)"Cannot clone task.", (Object[])new Object[0]));
        }
        Element element = this.configXml.getChild("Tasks");
        ISQTask iSQTask = this.tasks.get(n);
        Element element2 = (Element)element.getChildren().get(n);
        String string3 = XMLUtil.getAttr((Element)element2, (String)"type");
        String string4 = this.findTaskNameByType(string3);
        String string5 = string4 + " " + 1;
        for (int i = 1; i < 100 && this.containsTask(string5); ++i) {
            string5 = string4 + " " + i;
        }
        String string6 = XMLUtil.getAttr((Element)element2, (String)"title", (String)string) + " - Cloned";
        String string7 = this.generateTaskXMLFileName(string3);
        Element element3 = iSQTask.getConfig().clone();
        ISQTask iSQTask2 = iSQTask.clone(this.projectName, this.progressEngine);
        iSQTask2.setCustomName(string5);
        iSQTask2.setConfigFileName(string7);
        iSQTask2.setTitle(string6);
        iSQTask2.setIndex(n);
        iSQTask2.setConfig(element3, false, true);
        iSQTask2.setActive(true);
        Element element4 = element2.clone();
        element4.setAttribute("name", string5);
        element4.setAttribute("title", string6);
        element4.setAttribute("taskXMLFile", string7);
        if (string2 == null || string2.equals("end")) {
            element.addContent((Content)element4);
            this.tasks.add(iSQTask2);
        } else {
            element.addContent(n + 1, (Content)element4);
            this.tasks.add(n, iSQTask2);
        }
        this.saveConfig();
        return iSQTask2;
    }

    private String findTaskNameByType(String string) {
        for (ISQTask iSQTask : SQPluginManager.getPlugins(ISQTask.class)) {
            if (!iSQTask.getType().equals(string)) continue;
            return iSQTask.getName();
        }
        return null;
    }

    public void onMemoryError(Error error) {
        boolean bl = error instanceof SQMemoryProtectionError;
        this.projectRunInfo.errorType = 50;
        this.projectRunInfo.errorInfo = "Out of memory error";
        this.projectRunInfo.error = bl ? MemoryProtectionError : OutOfMemoryError;
        this.progressEngine.error();
        String string = "Project stopped - " + (error != null ? error.getMessage() : "Exceeded memory limit");
        Log.error(string);
        this.progressEngine.printToLog(string);
    }

    public static boolean isMemoryProtectionUsed() {
        return useMemoryProtection;
    }

    public void setProjectName(String string) throws Exception {
        this.checkProjectName(string);
        string = string.trim();
        File file = new File(this.projectFolder);
        File file2 = new File(this.getProjectFolderPath(string));
        Files.move(file.toPath(), file2.toPath(), new CopyOption[0]);
        this.projectName = string;
        this.projectFolder = this.getProjectFolderPath(string);
        this.projectConfigFile = new File(this.projectFolder + userConfigFileName);
        this.databanks.setProjectName(string);
        this.progressEngine.setProjectName(string);
        this.userConfirm.setProjectName(string);
        this.configXml.setAttribute("name", string);
        this.saveConfig();
    }

    private void checkProjectName(String string) throws Exception {
        if (string == null) {
            throw new Exception("Project name cannot be empty.");
        }
        String string2 = string.trim();
        if (string2.isEmpty()) {
            throw new Exception("Project name cannot be empty.");
        }
        if (string2.startsWith(".")) {
            throw new Exception("Project name cannot start with dot.");
        }
        if (string2.matches(".*[\\\\/:*?\"<>|].*")) {
            throw new Exception("Project name contains forbidden characters: \\ / : * ? \" < > |");
        }
        if (string2.matches("^(?i)(nul|prn|con|lpt[0-9]|com[0-9])(\\.|$).*")) {
            throw new Exception("Project name uses a reserved system name.");
        }
        for (int i = 0; i < string2.length(); ++i) {
            char c = string2.charAt(i);
            if (!Character.isWhitespace(c) || c == ' ') continue;
            throw new Exception("Project name cannot contain tabs or new lines.");
        }
    }

    public File getProjectConfigFile() {
        return this.projectConfigFile;
    }

    public void setRunSpecification(int n) {
        this.setRunSpecification(n, null);
    }

    public void setRunSpecification(int n, String string) {
        this.runSpecification = n;
        this.runTask = string;
    }

    public int getRunCycles() {
        return this.runCycles;
    }

    public long getStartTime() {
        return this.startTime;
    }

    public long getTotalProjectRunningTime() {
        return System.currentTimeMillis() - this.startTime;
    }

    public long getProjectRunningTime() {
        return System.currentTimeMillis() - this.startTime - this.pauseDuration;
    }

    public long getCurrentTaskRunningTime() {
        if (this.currentTaskStartTime == 0L) {
            this.currentTaskStartTime = System.currentTimeMillis();
        }
        long l = System.currentTimeMillis() - this.currentTaskStartTime - this.currentTaskPauseDuration;
        return l;
    }

    public String printGlobalLog() throws Exception {
        if (this.globalLog == null) {
            return "";
        }
        return this.globalLog.load();
    }

    public TaskStats getTaskStats(int n) {
        if (this.globalLog == null) {
            return null;
        }
        return this.globalLog.getTaskStats(n);
    }

    public void setLastEvent(String string) {
        this.lastEventMessage = string;
    }

    public String getLastEvent() {
        return this.lastEventMessage;
    }

    public JSONObject getInfo() {
        boolean bl = false;
        boolean bl2 = false;
        boolean bl3 = false;
        boolean bl4 = false;
        Element element = this.getConfig().getChild("Tasks");
        List list = element.getChildren("Task");
        for (int i = 0; i < list.size(); ++i) {
            try {
                Element element2 = ((Element)list.get(i)).getChild("Settings").getChild("WhatToBuild").getChild("BuildMode");
                if (!element2.getAttributeValue("generationType").equals("genetic-evolution")) continue;
                if (XMLUtil.getInt((Element)element2, (String)"InitGenerationType", (int)1) == 2) {
                    bl4 = true;
                }
                if (!XMLUtil.getBoolean((Element)element2, (String)"ShowLastGenerationDatabank", (boolean)false)) continue;
                bl3 = true;
                continue;
            }
            catch (Exception exception) {
                // empty catch block
            }
        }
        ArrayList<Databank> arrayList = this.getDatabanks().list();
        int n = 0;
        int n2 = 0;
        for (int i = 0; i < arrayList.size(); ++i) {
            Databank databank = arrayList.get(i);
            if (!bl && databank.getName().equals("Strategies to optimize") || !bl2 && databank.getName().equals("Strategies to improve") || !bl3 && databank.getName().equals("Last generation") || !bl4 && databank.getName().equals("Initial population")) continue;
            ++n2;
            n += databank.size();
        }
        return new JSONObject().put("projectName", (Object)this.getName()).put("filePath", (Object)this.projectConfigFile.getAbsolutePath()).put("tasks", this.getTasksCount()).put("activeTask", (Object)this.getActiveTaskName()).put("databanks", n2).put("strategies", n).put("hasUnresolvedResources", this.hasUnresolvedResources);
    }

    public ProjectGlobalLog getGlobalLog() {
        return this.globalLog;
    }

    public ArrayList<ISQTask> getTasks() {
        return this.tasks;
    }

    public String toJSON() {
        JsonCreator jsonCreator = new JsonCreator();
        jsonCreator.beginObject();
        jsonCreator.put("name", (Object)this.projectName, true);
        jsonCreator.put("xml", (Object)this.fixXMLCode(XMLUtil.elementToString((Element)this.configXml)), true);
        jsonCreator.putBeginObject("tasks");
        for (int i = 0; i < this.tasks.size(); ++i) {
            ISQTask iSQTask = this.tasks.get(i);
            jsonCreator.put(iSQTask.getTaskXMLFileName(), (Object)this.fixXMLCode(XMLUtil.elementToString((Element)iSQTask.getConfig())), i < this.tasks.size() - 1);
        }
        jsonCreator.endObject(false);
        jsonCreator.endObject(false);
        return jsonCreator.toJson();
    }

    private String fixXMLCode(String string) {
        String string2 = SQUtils.replaceAll((String)string, (String)"\\", (String)"\\\\");
        string2 = SQUtils.replaceAll((String)string2, (String)"/", (String)"\\/");
        string2 = SQUtils.replaceAll((String)string2, (String)"\r\n", (String)"\\r\\n");
        string2 = SQUtils.replaceAll((String)string2, (String)"\"", (String)"\\\"");
        return string2;
    }

    public int getRunSpecification() {
        return this.runSpecification;
    }

    private void performStartProject() {
        try {
            if (!MainApp.v571hfnsHw().gDmtOfRJBr() && this.isCustomProject()) {
                throw new Exception(MainApp.OnlyInProVersionTitle);
            }
            int n = 0;
            if (this.runSpecification == 50) {
                n = this.getIndexOfTask(this.runTask);
            }
            if (this.isCustomProject()) {
                this.globalLog = new ProjectGlobalLog(this.getProjectFolder());
            }
            while (n < this.tasks.size()) {
                this.currentTaskPauseDuration = 0L;
                this.currentTaskLastPauseTime = 0L;
                try {
                    if (this.progressEngine.isStoppedNotFinished()) {
                        Log.debug("Project stopped.");
                        break;
                    }
                    if (!this.tasks.get(n).isActive() && this.runSpecification != 100) {
                        this.progressEngine.setLogPrefix(this.tasks.get(n).getTitle());
                        this.progressEngine.printToLog(L.t((String)"SKIPPED, inactive task", (Object[])new Object[]{true}));
                    } else if (this.runSpecification != 100 || this.runTask.equals(this.tasks.get(n).getCustomName())) {
                        this.lastRunningTask = this.tasks.get(n);
                        this.projectRunning = true;
                        if (this.isCustomProject()) {
                            this.lastRunningTask.setTaskLogPrefix(this.lastRunningTask.getTitle());
                            this.lastRunningTask.logTaskStarted(this.globalLog);
                        }
                        this.lastRunningTask.increaseNumberOfRuns();
                        this.currentTaskStartTime = System.currentTimeMillis();
                        this.lastRunningTask.start();
                        this.waitForTaskFinish();
                        if (this.lastRunningTask != null) {
                            this.lastRunningTask.afterFinish();
                            if (this.isCustomProject()) {
                                this.lastRunningTask.logTaskFinished(this.globalLog);
                            }
                        }
                    }
                }
                catch (GoToTaskException goToTaskException) {
                    this.runSpecification = 0;
                    if (!goToTaskException.taskName.equals("lastTaskBreakcmd")) {
                        n = this.getIndexOfTask(goToTaskException.taskName) - 1;
                        ++this.runCycles;
                    }
                    ++this.runCycles;
                }
                ++n;
            }
            if (this.isCustomProject()) {
                this.progressEngine.setStatus(4);
                this.progressEngine.setLogPrefix(null);
                this.progressEngine.printToLog(L.t((String)"Project finished", (Object[])new Object[0]));
            }
        }
        catch (TaskException taskException) {
            String string;
            Log.error("Exc.", (Throwable)taskException);
            if (taskException.getCode() == 9) {
                string = taskException.getMessage();
            } else {
                string = SQUtils.getStackTrace((Throwable)taskException);
                string = string.substring(0, Math.min(string.length(), 300)) + "...";
            }
            this.progressEngine.setStatus(50);
            this.projectRunInfo.error = string;
            this.projectRunInfo.errorInfo = L.t((String)"Error while running project '%s'.", (Object[])new Object[]{this.getName()});
            this.projectRunInfo.errorType = 50;
            this.progressEngine.printToLog(L.t((String)"Error while running project '%s'.", (Object[])new Object[]{this.getName()}) + "\n" + string);
            CLILogger.log(L.t((String)"Error while running project '%s'.", (Object[])new Object[]{this.getName()}) + "\n" + string);
        }
        catch (Exception exception) {
            Log.error("Exc.", (Throwable)exception);
            String string = SQUtils.getStackTrace((Throwable)exception);
            string = string.substring(0, Math.min(string.length(), 300)) + "...";
            this.progressEngine.setStatus(50);
            this.projectRunInfo.error = exception.getMessage();
            this.projectRunInfo.errorInfo = L.t((String)"Error while running project '%s'.", (Object[])new Object[]{this.getName()});
            this.projectRunInfo.errorType = 50;
            this.progressEngine.printToLog(L.t((String)"Error while running project '%s'.", (Object[])new Object[]{this.getName()}) + "\n" + string);
            CLILogger.log(L.t((String)"Error while running project '%s'.", (Object[])new Object[]{this.getName()}) + "\n" + string);
        }
        finally {
            if (this.globalLog != null) {
                this.globalLog.close();
            }
            this.projectRunning = false;
            ProjectEngine.projectFinished(this.projectName);
        }
    }

    public void setUnresolvedResources(boolean bl) {
        if (ProjectEngine.isDefaulProject(this.projectName)) {
            return;
        }
        this.hasUnresolvedResources = bl;
    }

    public boolean hasUnresolvedResources() {
        return this.hasUnresolvedResources;
    }
}

