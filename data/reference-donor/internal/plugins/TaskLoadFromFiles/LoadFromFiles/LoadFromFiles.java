/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.pluginlib.annotations.Category
 *  com.strategyquant.pluginlib.annotations.License
 *  com.strategyquant.pluginlib.annotations.Name
 *  com.strategyquant.pluginlib.annotations.ShortDesc
 *  com.strategyquant.pluginlib.program.IProgram
 *  com.strategyquant.pluginlib.program.Program
 *  com.strategyquant.tradinglib.Databank
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.project.ProgressEngine
 *  com.strategyquant.tradinglib.project.ProjectEngine
 *  com.strategyquant.tradinglib.project.ProjectGlobalLog
 *  com.strategyquant.tradinglib.taskImpl.AbstractTask
 *  com.strategyquant.tradinglib.taskImpl.ISQTask
 *  net.xeoh.plugins.base.annotations.PluginImplementation
 *  net.xeoh.plugins.base.annotations.meta.Author
 *  org.apache.commons.io.FileUtils
 */
package com.strategyquant.plugin.Task.impl.LoadFromFiles;

import com.strategyquant.lib.L;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.pluginlib.annotations.Category;
import com.strategyquant.pluginlib.annotations.License;
import com.strategyquant.pluginlib.annotations.Name;
import com.strategyquant.pluginlib.annotations.ShortDesc;
import com.strategyquant.pluginlib.program.IProgram;
import com.strategyquant.pluginlib.program.Program;
import com.strategyquant.tradinglib.Databank;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.project.ProgressEngine;
import com.strategyquant.tradinglib.project.ProjectEngine;
import com.strategyquant.tradinglib.project.ProjectGlobalLog;
import com.strategyquant.tradinglib.taskImpl.AbstractTask;
import com.strategyquant.tradinglib.taskImpl.ISQTask;
import java.io.File;
import java.util.Collection;
import net.xeoh.plugins.base.annotations.PluginImplementation;
import net.xeoh.plugins.base.annotations.meta.Author;
import org.apache.commons.io.FileUtils;

@Author(name="Tamas Takacs")
@Name(name="Load from files plugin")
@Category(name="Task")
@License(text="")
@ShortDesc(text="Short description")
@PluginImplementation
public class LoadFromFiles
extends AbstractTask {
    private static final int OnMissingInstrumentSkipStrategy = 0;
    private static final int OnMissingInstrumentUseInstrument = 0;
    private String sourceDirectory = null;
    private boolean includeSubdirectories = false;
    private Databank databankTarget = null;
    private int unrecognizedInstrumentAction;
    private String unrecognizedInstrument;
    private int loaded;

    public LoadFromFiles() throws Exception {
        super(null, null);
    }

    public LoadFromFiles(String projectName, ProgressEngine progressEngine) throws Exception {
        super(projectName, progressEngine);
    }

    private void init() {
        this.sourceDirectory = (String)this.settingsData.getParams().get("SourceDirectory");
        this.includeSubdirectories = (Boolean)this.settingsData.getParams().get("IncludeSubdirectories");
        this.databankTarget = (Databank)this.settingsData.getParams().get("DatabankTarget");
        this.unrecognizedInstrumentAction = (Integer)this.settingsData.getParams().get("UnrecognizedInstrumentAction");
        this.unrecognizedInstrument = (String)this.settingsData.getParams().get("Instrument");
    }

    public void start() throws Exception {
        this.init();
        this.progressEngine.setLogPrefix(this.taskLogPrefix);
        this.progressEngine.printToLog(L.t((String)"Starting...", (Object[])new Object[0]));
        this.progressEngine.start();
        this.project = ProjectEngine.get((String)this.projectName);
        this.project.bestResults.disable();
        IProgram loader = Program.get((String)"Loader");
        try {
            this.project.publisher.resetLastData("progress-channel");
            Collection files = FileUtils.listFiles((File)new File(this.sourceDirectory), (String[])new String[]{"sqx", "str"}, (boolean)this.includeSubdirectories);
            for (File file : files) {
                if (file.isDirectory()) continue;
                String reportName = SQUtils.stripExtension((String)file.getName());
                try {
                    ResultsGroup resultsGroup = (ResultsGroup)loader.call("loadFile", new Object[]{file.getAbsolutePath(), this.unrecognizedInstrumentAction == 0, this.unrecognizedInstrument});
                    if (resultsGroup != null) {
                        this.databankTarget.add(resultsGroup, true);
                        this.databankTarget.updateBestResults(resultsGroup);
                        this.progressEngine.printToLogDebug(L.t((String)"%s loaded", (Object[])new Object[]{resultsGroup.getName()}));
                        ++this.loaded;
                    }
                    this.progressEngine.checkPaused();
                    if (!this.progressEngine.isStopped()) continue;
                    break;
                }
                catch (OutOfMemoryError e) {
                    this.project.onMemoryError((Error)e);
                    break;
                }
                catch (Exception e) {
                    this.progressEngine.printToLog(L.t((String)"%s cannot be loaded. Error: %s", (Object[])new Object[]{reportName, e.getMessage()}));
                    Log.error("Error while loading strategy. Exc.", (Throwable)e);
                }
            }
        }
        catch (Exception ex) {
            Log.error("Error while loading strategies. Exc.", (Throwable)ex);
        }
        this.project.bestResults.enable();
        this.progressEngine.finish();
    }

    protected int getRunningStatus() {
        return 0;
    }

    public String getPluginFolderName() {
        return "TaskLoadFromFiles";
    }

    public int getPreferredPosition() {
        return 10;
    }

    public String getType() {
        return "LoadFromFiles";
    }

    public String getName() {
        return L.tsq((String)"Load from files");
    }

    public ISQTask clone(String projectName, ProgressEngine progressEngine) throws Exception {
        LoadFromFiles task = new LoadFromFiles(projectName, progressEngine);
        task.settingTabPlugins = this.settingTabPlugins;
        return task;
    }

    public String[] getSettings() {
        return new String[]{"LoadFromFiles"};
    }

    protected Databank[] getUsedDatabanks() {
        return new Databank[]{this.databankTarget};
    }

    protected Databank getOutputDatabank() {
        return this.databankTarget;
    }

    public void logTaskFinished(ProjectGlobalLog log) {
        super.logTaskFinished(log);
        log.print(L.t((String)"Loaded strategies", (Object[])new Object[0]) + ": " + this.loaded);
    }
}

