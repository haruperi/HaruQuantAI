/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.lib.snippets.compile.SQStructure
 *  com.strategyquant.pluginlib.SQPluginManager
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.taskImpl;

import com.strategyquant.lib.L;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.lib.snippets.compile.SQStructure;
import com.strategyquant.pluginlib.SQPluginManager;
import com.strategyquant.tradinglib.Databank;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.databank.DefaultDatabankFilter;
import com.strategyquant.tradinglib.databank.OptimizeDatabankFilter;
import com.strategyquant.tradinglib.project.ProgressEngine;
import com.strategyquant.tradinglib.project.ProjectEngine;
import com.strategyquant.tradinglib.project.ProjectGlobalLog;
import com.strategyquant.tradinglib.project.SQProject;
import com.strategyquant.tradinglib.project.TaskStat;
import com.strategyquant.tradinglib.task.settings.ISettingTabPlugin;
import com.strategyquant.tradinglib.task.settings.SettingError;
import com.strategyquant.tradinglib.task.settings.TaskSettingsData;
import com.strategyquant.tradinglib.taskImpl.ISQTask;
import com.strategyquant.tradinglib.util.ResultComparatorByName;
import java.io.File;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public abstract class AbstractTask
implements ISQTask {
    public static final Logger Log = LoggerFactory.getLogger(AbstractTask.class);
    protected String projectName;
    protected String customName;
    protected String configFileName;
    private Element taskConfig;
    protected String title;
    protected int taskIndex;
    protected boolean active = true;
    protected ArrayList<ISettingTabPlugin> settingTabPlugins;
    protected TaskSettingsData settingsData = new TaskSettingsData();
    protected ProgressEngine progressEngine;
    protected String taskLogPrefix;
    protected SQProject project;
    private int numberOfRuns = 0;
    protected String logMessage;
    private Comparator<ResultsGroup> comparatorByName = new ResultComparatorByName();
    private long taskStarted;

    public AbstractTask(String string, ProgressEngine progressEngine) throws Exception {
        this.projectName = string;
        this.progressEngine = progressEngine;
    }

    public String getProduct() {
        return "SQUANT";
    }

    @Override
    public Element getDefaultConfig(String string) throws Exception {
        try {
            if (this.getPluginFolderName() == null) {
                throw new Exception("Property 'pluginFolderName' is not set.");
            }
            String string2 = SQStructure.PLUGINS_DIR + "/" + this.getPluginFolderName();
            File file = new File(string2 + "/" + "task.xml");
            if (!file.exists()) {
                file = new File(string2 + "/" + string);
            }
            if (!file.exists()) {
                string2 = SQStructure.USER_EXTEND_PLUGINS + "/" + this.getPluginFolderName();
                file = new File(string2 + "/" + "task.xml");
            }
            return XMLUtil.fileToXmlElement((File)file).clone();
        }
        catch (Exception exception) {
            Log.error("Cannot get task default config. Exc.", (Throwable)exception);
            throw new Exception(L.t((String)"Cannot get task default config.", (Object[])new Object[0]), exception);
        }
    }

    @Override
    public boolean isActive() {
        return this.active;
    }

    @Override
    public void setActive(boolean bl) {
        this.active = bl;
    }

    @Override
    public String getCustomName() {
        return this.customName;
    }

    @Override
    public void setCustomName(String string) {
        this.customName = string;
    }

    @Override
    public void setTitle(String string) {
        this.title = string;
    }

    @Override
    public String getTitle() {
        if (this.title == null) {
            return this.getCustomName();
        }
        return this.title;
    }

    @Override
    public void setConfigFileName(String string) {
        this.configFileName = string;
    }

    @Override
    public String getTaskXMLFileName() {
        return this.configFileName;
    }

    @Override
    public TaskSettingsData getSettingsData() {
        return this.settingsData;
    }

    @Override
    public void setConfig(Element element, boolean bl, boolean bl2) {
        if (bl && this.taskConfig != null && XMLUtil.elementToString((Element)element).equals(XMLUtil.elementToString((Element)this.taskConfig))) {
            return;
        }
        this.taskConfig = element;
        this.settingsData.clear();
        if (element == null) {
            this.settingsData.addError(null, null, "Invalid Task XML configuration - missing Settings.");
        } else if (bl2) {
            for (int i = 0; i < this.settingTabPlugins.size(); ++i) {
                this.settingTabPlugins.get(i).readSettings(this.projectName, this, element, this.settingsData);
            }
        }
    }

    @Override
    public Element getConfig() {
        return this.taskConfig;
    }

    public void initPlugin() throws Exception {
        this.settingTabPlugins = new ArrayList();
        if (this.getSettings() != null) {
            ArrayList arrayList = SQPluginManager.getPlugins(ISettingTabPlugin.class);
            for (ISettingTabPlugin iSettingTabPlugin : arrayList) {
                if (!this.isInArray(iSettingTabPlugin.getSettingName())) continue;
                this.settingTabPlugins.add(iSettingTabPlugin);
            }
        }
    }

    protected boolean isInArray(String string) {
        String[] stringArray = this.getSettings();
        for (int i = 0; i < stringArray.length; ++i) {
            if (!string.equals(stringArray[i])) continue;
            return true;
        }
        return false;
    }

    @Override
    public String getErrorsDescription() {
        String string = "";
        for (SettingError settingError : this.settingsData.getErrors()) {
            String string2 = AbstractTask.formatWSError(settingError.settingName, settingError.fieldName, settingError.errorMsg);
            Log.error(string2);
            string = string + string2 + "\n";
        }
        return string;
    }

    public static String formatWSError(String string, String string2, String string3) {
        StringBuilder stringBuilder = new StringBuilder("Error: ");
        stringBuilder.append(string3);
        if (string2 != null) {
            stringBuilder.append(" in field: ");
            stringBuilder.append(string2);
        }
        stringBuilder.append(", in setting: ");
        stringBuilder.append(string);
        return stringBuilder.toString();
    }

    protected void setDatabankFilter(Databank databank, boolean bl) {
        try {
            int n = 100000;
            if (this.settingsData.getParams().containsKey("MaxStrategies")) {
                n = (Integer)this.settingsData.getParams().get("MaxStrategies");
            }
            if (this.getType().equals("Optimize")) {
                databank.applyFilter(new OptimizeDatabankFilter(n));
            } else if (!this.getType().equals("Retest") && !this.getType().equals("AutomaticRetest")) {
                databank.applyFilter(new DefaultDatabankFilter(n, bl));
            }
            Log.debug("Ranking settings set for databank '{}'. ", (Object)databank.getName());
        }
        catch (Exception exception) {
            Log.error("Project '" + this.projectName + "', Task '" + this.getCustomName() + "' - Cannot set databank filter do databank '" + databank.getName() + "'.", (Throwable)exception);
        }
    }

    public String getTaskXML() {
        try {
            Element element = this.getTaskElement();
            return element != null ? XMLUtil.elementToString((Element)element) : null;
        }
        catch (Exception exception) {
            Log.error("Cannot get task config", (Throwable)exception);
            return null;
        }
    }

    public Element getTaskElement() {
        return this.taskConfig;
    }

    @Override
    public void setTaskLogPrefix(String string) {
        this.taskLogPrefix = string;
    }

    @Override
    public void afterFinish() {
        this.removeDatabankFilters();
        this.synchronizeOutputDatabank();
    }

    @Override
    public void increaseNumberOfRuns() {
        ++this.numberOfRuns;
    }

    @Override
    public int getNumberOfRuns() {
        return this.numberOfRuns;
    }

    private void removeDatabankFilters() {
        Databank[] databankArray = this.getUsedDatabanks();
        if (databankArray != null && databankArray.length > 0) {
            for (int i = 0; i < databankArray.length; ++i) {
                if (databankArray[i] == null) continue;
                try {
                    databankArray[i].removeFilter();
                    continue;
                }
                catch (Exception exception) {
                    Log.error("Cannot remove databank filter from databank '" + databankArray[i].getName() + "'");
                }
            }
        }
    }

    private void synchronizeOutputDatabank() {
        boolean bl = false;
        try {
            bl = Boolean.parseBoolean(MainApp.settings().get("syncDatabanksAfterTaskDone", "false"));
        }
        catch (Exception exception) {
            Log.error("Unable to read SyncDatabanksAfterTaskDone setting. Skipping synchronization...", (Throwable)exception);
        }
        if (!bl) {
            return;
        }
        Databank databank = this.getOutputDatabank();
        if (databank != null && !databank.getSyncType().equals("Auto-sync never")) {
            databank.synchronizeNow(true, String.format("Task %s/%s done, synchronize output databank %s/%s.", this.projectName, this.getTitle(), this.projectName, databank.getName()));
        }
    }

    @Override
    public abstract void start() throws Exception;

    protected abstract int getRunningStatus();

    protected abstract Databank[] getUsedDatabanks();

    protected abstract Databank getOutputDatabank();

    @Override
    public void logTaskStarted(ProjectGlobalLog projectGlobalLog) {
        this.taskStarted = System.currentTimeMillis();
        projectGlobalLog.printEmptyLine();
        projectGlobalLog.printSeparator();
        projectGlobalLog.print(L.t((String)"TASK STARTED at %s", (Object[])new Object[]{SQTime.getLogTime((boolean)true, (boolean)true)}));
        projectGlobalLog.print(L.t((String)"Task: %s, Type: %s", (Object[])new Object[]{this.getTitle(), this.getType()}));
        String string = this.getDatabanksStats(true);
        projectGlobalLog.print(L.t((String)"Databanks before start: %s", (Object[])new Object[]{string}));
    }

    @Override
    public void logTaskFinished(ProjectGlobalLog projectGlobalLog) {
        long l = System.currentTimeMillis() - this.taskStarted;
        String string = SQUtils.formatDuration((long)l);
        String string2 = this.getDatabanksStats(true);
        projectGlobalLog.printEmptyLine();
        projectGlobalLog.print(L.t((String)"TASK FINISHED at %s in %s", (Object[])new Object[]{SQTime.getLogTime((boolean)true, (boolean)true), string}));
        projectGlobalLog.print(L.t((String)"Databanks after finish: %s", (Object[])new Object[]{string2}));
        projectGlobalLog.printEmptyLine();
        if (this.project == null) {
            try {
                this.project = ProjectEngine.get(this.projectName);
            }
            catch (Exception exception) {
                Log.error("Exc.", (Throwable)exception);
            }
        }
        if (this.project != null) {
            this.project.setGlobalStats(TaskStat.MILLISECONDS, this.getCustomName().hashCode(), L.t((String)"Duration", (Object[])new Object[0]), l, 3);
        }
    }

    protected String getDatabanksContents() {
        StringBuilder stringBuilder = new StringBuilder();
        try {
            SQProject sQProject = ProjectEngine.get(this.projectName);
            ArrayList<Databank> arrayList = sQProject.getDatabanks().list();
            for (int i = 0; i < arrayList.size(); ++i) {
                Databank databank = arrayList.get(i);
                if (databank.size() == 0 || databank.getName().equals("Results")) continue;
                this.printDatabankContents(stringBuilder, databank);
            }
        }
        catch (Exception exception) {
            stringBuilder.append("EXCEPTION: ");
            stringBuilder.append(exception.getMessage());
            stringBuilder.append("\n");
        }
        return stringBuilder.toString();
    }

    private void printDatabankContents(StringBuilder stringBuilder, Databank databank) throws Exception {
        stringBuilder.append("-------------- ");
        stringBuilder.append(databank.getName());
        stringBuilder.append("\n");
        ArrayList<ResultsGroup> arrayList = databank.getRecords();
        List<ResultsGroup> list = arrayList.subList(0, databank.size());
        Collections.sort(list, this.comparatorByName);
        for (int i = 0; i < list.size(); ++i) {
            ResultsGroup resultsGroup = list.get(i);
            int n = resultsGroup.portfolio().stats((byte)0, (byte)10, (byte)127).getInt("NumberOfTrades");
            double d = resultsGroup.portfolio().stats((byte)0, (byte)10, (byte)127).getDouble("NetProfit");
            stringBuilder.append(resultsGroup.getName());
            stringBuilder.append("\t\t\t\t");
            stringBuilder.append(n);
            stringBuilder.append("\t\t");
            stringBuilder.append(d);
            stringBuilder.append("\n");
        }
    }

    private String getDatabanksStats(boolean bl) {
        String string = "";
        try {
            SQProject sQProject = ProjectEngine.get(this.projectName);
            ArrayList<Databank> arrayList = sQProject.getDatabanks().list();
            for (int i = 0; i < arrayList.size(); ++i) {
                Databank databank = arrayList.get(i);
                if (!bl && databank.size() == 0) continue;
                string = string + databank.getName() + " (" + databank.size() + "), ";
            }
        }
        catch (Exception exception) {
            string = "cannot get databanks";
        }
        if (string.endsWith(", ")) {
            string = string.substring(0, string.length() - 2);
        }
        return string;
    }

    protected String formatIntOrDouble(double d) {
        if (d > 1000.0) {
            return String.format("%.0f", d);
        }
        return String.format("%.2f", d);
    }

    protected void printLog(String string) {
        this.logMessage = string == null || string.isEmpty() ? string : "\n" + string;
        this.progressEngine.printToLog(string);
    }

    @Override
    public int getIndex() {
        return this.taskIndex;
    }

    @Override
    public void setIndex(int n) {
        this.taskIndex = n;
    }

    @Override
    public double getCustomValue(String string) {
        return 0.0;
    }

    protected void checkSpecialTrialLimitation() throws Exception {
        if (MainApp.v571hfnsHw().bDm88fRJA3()) {
            throw new Exception(L.t((String)"Task '%s' is available only in full version, not in this special trial.", (Object[])new Object[]{this.getName()}));
        }
    }
}

