/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.sourcecode.MissingBlockMessage
 *  com.strategyquant.lib.sourcecode.SourceCodeGenerator
 *  com.strategyquant.lib.sourcecode.SourceCodeGenerators
 *  com.strategyquant.pluginlib.annotations.Category
 *  com.strategyquant.pluginlib.annotations.License
 *  com.strategyquant.pluginlib.annotations.Name
 *  com.strategyquant.pluginlib.annotations.ShortDesc
 *  com.strategyquant.tradinglib.Databank
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.databank.DatabankExport
 *  com.strategyquant.tradinglib.project.ProgressEngine
 *  com.strategyquant.tradinglib.project.ProjectEngine
 *  com.strategyquant.tradinglib.project.ProjectGlobalLog
 *  com.strategyquant.tradinglib.project.TaskStat
 *  com.strategyquant.tradinglib.taskImpl.AbstractTask
 *  com.strategyquant.tradinglib.taskImpl.ISQTask
 *  net.xeoh.plugins.base.annotations.PluginImplementation
 *  net.xeoh.plugins.base.annotations.meta.Author
 */
package com.strategyquant.plugin.Task.impl.SaveToFiles;

import com.strategyquant.lib.L;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.sourcecode.MissingBlockMessage;
import com.strategyquant.lib.sourcecode.SourceCodeGenerator;
import com.strategyquant.lib.sourcecode.SourceCodeGenerators;
import com.strategyquant.pluginlib.annotations.Category;
import com.strategyquant.pluginlib.annotations.License;
import com.strategyquant.pluginlib.annotations.Name;
import com.strategyquant.pluginlib.annotations.ShortDesc;
import com.strategyquant.tradinglib.Databank;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.databank.DatabankExport;
import com.strategyquant.tradinglib.project.ProgressEngine;
import com.strategyquant.tradinglib.project.ProjectEngine;
import com.strategyquant.tradinglib.project.ProjectGlobalLog;
import com.strategyquant.tradinglib.project.TaskStat;
import com.strategyquant.tradinglib.taskImpl.AbstractTask;
import com.strategyquant.tradinglib.taskImpl.ISQTask;
import java.io.File;
import java.util.ArrayList;
import java.util.HashMap;
import net.xeoh.plugins.base.annotations.PluginImplementation;
import net.xeoh.plugins.base.annotations.meta.Author;

@Author(name="Tamas Takacs")
@Name(name="Save to files plugin")
@Category(name="Task")
@License(text="")
@ShortDesc(text="Short description")
@PluginImplementation
public class SaveToFiles
extends AbstractTask {
    private boolean overwriteFiles = false;
    private String destDirectorySqx = null;
    private String destDirectoryStr = null;
    private String destDirectoryDatabank = null;
    private String destDirectoryTrades = null;
    private String destDirectoryHtml = null;
    private String destDirectoryPdf = null;
    private String destDirectorySC = null;
    private boolean saveInSqxFormat = false;
    private boolean saveInStrFormat = false;
    private boolean exportDatabank = false;
    private boolean exportTrades = false;
    private boolean saveInHtmlFormat = false;
    private boolean saveInPdfFormat = false;
    private boolean saveSourceCode = false;
    private Databank databankSource = null;
    private int savedStr;
    private int savedSqx;
    private int savedDatabank;
    private int savedTrades;
    private int savedHtml;
    private int savedPdf;
    private int savedSc;
    private boolean MNActive;
    private int MNValue;
    private String data;
    private String format;
    private boolean useComma;
    private boolean setNoteActive;
    private String setNoteType;
    private String setNoteCustom;
    private String sourceCodeType;
    private SourceCodeGenerator generator;
    private String sourceCodeFormat;

    public SaveToFiles() throws Exception {
        super(null, null);
    }

    public SaveToFiles(String projectName, ProgressEngine progressEngine) throws Exception {
        super(projectName, progressEngine);
    }

    private void init() throws Exception {
        this.savedStr = 0;
        this.savedSqx = 0;
        this.savedDatabank = 0;
        this.savedTrades = 0;
        this.overwriteFiles = (Boolean)this.settingsData.getParams().get("OverwriteFiles");
        this.destDirectorySqx = (String)this.settingsData.getParams().get("DestDirectorySqx");
        this.destDirectoryStr = (String)this.settingsData.getParams().get("DestDirectoryStr");
        this.destDirectoryDatabank = (String)this.settingsData.getParams().get("DestDirectoryDatabank");
        this.destDirectoryTrades = (String)this.settingsData.getParams().get("DestDirectoryTrades");
        this.destDirectoryHtml = (String)this.settingsData.getParams().get("DestDirectoryHtml");
        this.destDirectoryPdf = (String)this.settingsData.getParams().get("DestDirectoryPdf");
        this.destDirectorySC = (String)this.settingsData.getParams().get("DestDirectorySC");
        this.saveInSqxFormat = (Boolean)this.settingsData.getParams().get("SaveInSqxFormat");
        this.saveInStrFormat = (Boolean)this.settingsData.getParams().get("SaveInStrFormat");
        this.exportDatabank = (Boolean)this.settingsData.getParams().get("ExportDatabank");
        this.exportTrades = (Boolean)this.settingsData.getParams().get("ExportTrades");
        this.saveInHtmlFormat = (Boolean)this.settingsData.getParams().get("SaveInHtmlFormat");
        this.saveInPdfFormat = (Boolean)this.settingsData.getParams().get("SaveInPdfFormat");
        this.saveSourceCode = (Boolean)this.settingsData.getParams().get("SaveSourceCode");
        this.databankSource = (Databank)this.settingsData.getParams().get("DatabankSource");
        this.MNActive = (Boolean)this.settingsData.getParams().get("MNActive");
        this.MNValue = (Integer)this.settingsData.getParams().get("MNValue");
        this.data = (String)this.settingsData.getParams().get("Data");
        this.format = (String)this.settingsData.getParams().get("Format");
        this.useComma = (Boolean)this.settingsData.getParams().get("UseComma");
        this.setNoteActive = (Boolean)this.settingsData.getParams().get("SetNoteActive");
        this.setNoteType = (String)this.settingsData.getParams().get("SetNoteType");
        this.setNoteCustom = (String)this.settingsData.getParams().get("SetNoteCustom");
        this.sourceCodeType = (String)this.settingsData.getParams().get("SourceCodeType");
        if (!this.sourceCodeType.equals("Strategy XML")) {
            this.generator = SourceCodeGenerators.getInstance().getGeneratorFromName(this.sourceCodeType);
            if (this.generator == null) {
                throw new Exception(L.t((String)"Invalid source code generator", (Object[])new Object[]{false}));
            }
        }
        this.sourceCodeFormat = (String)this.settingsData.getParams().get("SourceCodeFormat");
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public void start() throws Exception {
        String targetFilePath;
        this.init();
        this.progressEngine.setLogPrefix(this.taskLogPrefix);
        this.progressEngine.printToLog(L.t((String)"Starting...", (Object[])new Object[0]));
        this.progressEngine.start();
        this.project = ProjectEngine.get((String)this.projectName);
        HashMap<String, String[]> parameterMap = new HashMap<String, String[]>();
        parameterMap.put("useComma", new String[]{this.useComma + ""});
        parameterMap.put("data", new String[]{this.data});
        parameterMap.put("setNoteActive", new String[]{this.setNoteActive + ""});
        parameterMap.put("setNoteType", new String[]{this.setNoteType});
        parameterMap.put("setNoteCustomText", new String[]{this.setNoteCustom});
        int startingStatOrder = 0;
        String firstStatName = L.tsq((String)"Input");
        ArrayList resultNames = this.databankSource.getRecordKeys();
        this.project.setGlobalStats(TaskStat.BAR, this.getCustomName().hashCode(), firstStatName, (long)resultNames.size(), ++startingStatOrder);
        if (this.saveInSqxFormat || this.saveInStrFormat || this.exportTrades || this.saveInHtmlFormat || this.saveInPdfFormat || this.saveSourceCode) {
            if (this.saveInSqxFormat) {
                this.project.setGlobalStats(TaskStat.BAR, this.getCustomName().hashCode(), L.tsq((String)"SQX"), (long)resultNames.size(), ++startingStatOrder, firstStatName);
            }
            if (this.saveInStrFormat) {
                this.project.setGlobalStats(TaskStat.BAR, this.getCustomName().hashCode(), L.tsq((String)"STR"), (long)resultNames.size(), ++startingStatOrder, firstStatName);
            }
            if (this.exportTrades) {
                this.project.setGlobalStats(TaskStat.BAR, this.getCustomName().hashCode(), L.tsq((String)"Trades"), (long)resultNames.size(), ++startingStatOrder, firstStatName);
            }
            if (this.saveInHtmlFormat) {
                this.project.setGlobalStats(TaskStat.BAR, this.getCustomName().hashCode(), L.tsq((String)"HTML"), (long)resultNames.size(), ++startingStatOrder, firstStatName);
            }
            if (this.saveInPdfFormat) {
                this.project.setGlobalStats(TaskStat.BAR, this.getCustomName().hashCode(), L.tsq((String)"PDF"), (long)resultNames.size(), ++startingStatOrder, firstStatName);
            }
            if (this.saveSourceCode) {
                this.project.setGlobalStats(TaskStat.BAR, this.getCustomName().hashCode(), L.tsq((String)"Code"), (long)resultNames.size(), ++startingStatOrder, firstStatName);
            }
            for (int i = resultNames.size() - 1; i >= 0; --i) {
                String strategyName = (String)resultNames.get(i);
                try {
                    ResultsGroup rg = null;
                    try {
                        rg = this.databankSource.getLocked(strategyName, "onSaveToFiles");
                        if (this.saveInSqxFormat) {
                            try {
                                targetFilePath = this.overwriteFiles ? this.destDirectorySqx + "/" + strategyName + ".sqx" : this.generateUniqueName(this.destDirectorySqx, strategyName, ".sqx");
                                this.databankSource.getReportSaver().save(rg, "sqx", targetFilePath, this.MNActive, this.MNValue, parameterMap);
                                this.progressEngine.printToLogDebug(L.t((String)"%s saved in SQX format", (Object[])new Object[]{strategyName}));
                                ++this.savedSqx;
                            }
                            catch (Exception e) {
                                Log.error("Error while saving strategy '" + strategyName + "' to SQX", (Throwable)e);
                            }
                        }
                        if (this.saveInStrFormat) {
                            try {
                                targetFilePath = this.overwriteFiles ? this.destDirectoryStr + "/" + strategyName + ".str" : this.generateUniqueName(this.destDirectoryStr, strategyName, ".str");
                                this.databankSource.getReportSaver().save(rg, "str", targetFilePath, this.MNActive, this.MNValue, parameterMap);
                                this.progressEngine.printToLogDebug(L.t((String)"%s saved in STR (SQ3) format", (Object[])new Object[]{strategyName}));
                                ++this.savedStr;
                            }
                            catch (Exception e) {
                                Log.error("Error while saving strategy '" + strategyName + "' to STR", (Throwable)e);
                            }
                        }
                        if (this.exportTrades) {
                            try {
                                targetFilePath = this.overwriteFiles ? this.destDirectoryTrades + "/" + strategyName + "." + this.format : this.generateUniqueName(this.destDirectoryTrades, strategyName, "." + this.format);
                                this.databankSource.getReportSaver().save(rg, this.format, targetFilePath, this.MNActive, this.MNValue, parameterMap);
                                this.progressEngine.printToLogDebug(L.t((String)"%s saved trades", (Object[])new Object[]{strategyName}));
                                ++this.savedTrades;
                            }
                            catch (Exception e) {
                                Log.error("Error while saving trades of strategy '" + strategyName + "'", (Throwable)e);
                            }
                        }
                        if (this.saveInHtmlFormat) {
                            try {
                                targetFilePath = this.overwriteFiles ? this.destDirectoryHtml + "/" + strategyName + ".html" : this.generateUniqueName(this.destDirectoryHtml, strategyName, ".html");
                                this.databankSource.getReportSaver().save(rg, "html", targetFilePath, this.MNActive, this.MNValue, parameterMap);
                                this.progressEngine.printToLogDebug(L.t((String)"%s saved in HTML format", (Object[])new Object[]{strategyName}));
                                ++this.savedHtml;
                            }
                            catch (Exception e) {
                                Log.error("Error while saving strategy '" + strategyName + "' to HTML", (Throwable)e);
                            }
                        }
                        if (this.saveInPdfFormat) {
                            try {
                                targetFilePath = this.overwriteFiles ? this.destDirectoryPdf + "/" + strategyName + ".pdf" : this.generateUniqueName(this.destDirectoryPdf, strategyName, ".pdf");
                                this.databankSource.getReportSaver().save(rg, "pdf", targetFilePath, this.MNActive, this.MNValue, parameterMap);
                                this.progressEngine.printToLogDebug(L.t((String)"%s saved in PDF format", (Object[])new Object[]{strategyName}));
                                ++this.savedPdf;
                            }
                            catch (Exception e) {
                                Log.error("Error while saving strategy '" + strategyName + "' to PDF", (Throwable)e);
                            }
                        }
                        if (this.saveSourceCode) {
                            try {
                                String ext = null;
                                ext = this.sourceCodeType.equals("Strategy XML") ? "xml" : this.generator.getFileExtension()[1];
                                if (this.sourceCodeFormat != null) {
                                    ext = this.sourceCodeFormat;
                                }
                                targetFilePath = this.overwriteFiles ? this.destDirectorySC + "/" + (ext.contains("java") ? SQUtils.correctClassName((String)strategyName) : strategyName) + "." + ext : this.generateUniqueName(this.destDirectorySC, strategyName, "." + ext);
                                this.databankSource.getReportSaver().save(rg, ext, targetFilePath, this.MNActive, this.MNValue, this.generator, parameterMap, false);
                                this.progressEngine.printToLogDebug(L.t((String)"%s saved Source Code .%s", (Object[])new Object[]{strategyName, ext}));
                                ++this.savedSc;
                            }
                            catch (Exception e) {
                                Log.error("Error while saving strategy '" + strategyName + "' Source Code", (Throwable)e);
                                if (MissingBlockMessage.matches((String)e.getMessage())) {
                                    this.progressEngine.printToLog(L.t((String)"%s - Source Code NOT saved: it uses block '%s', which has no template for this platform", (Object[])new Object[]{strategyName, MissingBlockMessage.blockKey((String)e.getMessage())}));
                                }
                            }
                        }
                    }
                    catch (Exception e) {
                        Log.warn("Strategy '" + strategyName + "' no longer exists (was probably replaced by better strategy with the same fingerprint)");
                        continue;
                    }
                    finally {
                        if (rg != null) {
                            rg.releaseLock("onSaveToFiles");
                        }
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
                    this.progressEngine.printToLog(L.t((String)"%s cannot be saved. Error: %s", (Object[])new Object[]{strategyName, e.getMessage()}));
                    Log.error("Error while saving strategy. Exc.", (Throwable)e);
                }
            }
        }
        if (this.exportDatabank) {
            try {
                targetFilePath = this.overwriteFiles ? this.destDirectoryDatabank + "/DatabankExport." + this.format : this.generateUniqueName(this.destDirectoryDatabank, "DatabankExport", "." + this.format);
                DatabankExport export = new DatabankExport();
                if (targetFilePath.endsWith("xlsx")) {
                    export.toXlsx(this.databankSource, targetFilePath, null, this.useComma, null);
                } else {
                    export.toCsv(this.databankSource, targetFilePath, null, this.useComma, null, ";");
                }
                this.progressEngine.printToLogDebug(L.t((String)"Exported databank contents", (Object[])new Object[0]));
                ++this.savedDatabank;
            }
            catch (Exception e) {
                Log.error("Error while exporting databank contents", (Throwable)e);
            }
        }
        this.progressEngine.finish();
    }

    private String generateUniqueName(String destDirectory, String strategyName, String extension) {
        String targetFilePath = destDirectory + "/" + (extension.contains("java") ? SQUtils.correctClassName((String)strategyName) : strategyName) + extension;
        if (!new File(targetFilePath).exists()) {
            return targetFilePath;
        }
        int count = 1;
        while (new File(targetFilePath = destDirectory + "/" + (extension.contains("java") ? SQUtils.correctClassName((String)(strategyName + "(" + count + ")")) : strategyName + "(" + count + ")") + extension).exists()) {
            ++count;
        }
        return targetFilePath;
    }

    protected int getRunningStatus() {
        return 0;
    }

    public String getPluginFolderName() {
        return "TaskSaveToFiles";
    }

    public int getPreferredPosition() {
        return 10;
    }

    public String getType() {
        return "SaveToFiles";
    }

    public String getName() {
        return L.tsq((String)"Save to files");
    }

    public ISQTask clone(String projectName, ProgressEngine progressEngine) throws Exception {
        SaveToFiles task = new SaveToFiles(projectName, progressEngine);
        task.settingTabPlugins = this.settingTabPlugins;
        return task;
    }

    public String[] getSettings() {
        return new String[]{"SaveToFiles"};
    }

    protected Databank[] getUsedDatabanks() {
        return new Databank[]{this.databankSource};
    }

    protected Databank getOutputDatabank() {
        return null;
    }

    public void logTaskFinished(ProjectGlobalLog log) {
        super.logTaskFinished(log);
        log.print(L.t((String)"Saved strategies in SQX format", (Object[])new Object[0]) + ": " + this.savedSqx);
        log.print(L.t((String)"Saved strategies in STR (SQ3) format", (Object[])new Object[0]) + ": " + this.savedStr);
        log.print(L.t((String)"Exported databank contents", (Object[])new Object[0]) + ": " + this.savedDatabank);
        log.print(L.t((String)"Exported trades", (Object[])new Object[0]) + ": " + this.savedTrades);
        log.print(L.t((String)"Saved strategies in HTML format", (Object[])new Object[0]) + ": " + this.savedHtml);
        log.print(L.t((String)"Saved strategies in PDF format", (Object[])new Object[0]) + ": " + this.savedPdf);
        log.print(L.t((String)"Saved Source Codes", (Object[])new Object[0]) + ": " + this.savedSc);
    }
}

