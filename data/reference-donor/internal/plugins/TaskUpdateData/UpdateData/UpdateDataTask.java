/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.DataInfo
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.lib.L
 *  com.strategyquant.pluginlib.annotations.Category
 *  com.strategyquant.pluginlib.annotations.License
 *  com.strategyquant.pluginlib.annotations.Name
 *  com.strategyquant.pluginlib.annotations.ShortDesc
 *  com.strategyquant.pluginlib.program.Program
 *  com.strategyquant.tradinglib.Databank
 *  com.strategyquant.tradinglib.data.download.DownloadDispatcher
 *  com.strategyquant.tradinglib.data.download.NotDownloadableDataException
 *  com.strategyquant.tradinglib.project.ProgressEngine
 *  com.strategyquant.tradinglib.project.ProjectEngine
 *  com.strategyquant.tradinglib.project.ProjectGlobalLog
 *  com.strategyquant.tradinglib.project.SQProject
 *  com.strategyquant.tradinglib.project.websocket.DataManagerDataProgress
 *  com.strategyquant.tradinglib.project.websocket.MultiProgressListener
 *  com.strategyquant.tradinglib.taskImpl.AbstractTask
 *  com.strategyquant.tradinglib.taskImpl.ISQTask
 *  net.xeoh.plugins.base.annotations.PluginImplementation
 *  net.xeoh.plugins.base.annotations.meta.Author
 *  org.jdom2.Element
 *  org.json.JSONObject
 */
package com.strategyquant.plugin.Task.impl.UpdateData;

import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.lib.L;
import com.strategyquant.pluginlib.annotations.Category;
import com.strategyquant.pluginlib.annotations.License;
import com.strategyquant.pluginlib.annotations.Name;
import com.strategyquant.pluginlib.annotations.ShortDesc;
import com.strategyquant.pluginlib.program.Program;
import com.strategyquant.tradinglib.Databank;
import com.strategyquant.tradinglib.data.download.DownloadDispatcher;
import com.strategyquant.tradinglib.data.download.NotDownloadableDataException;
import com.strategyquant.tradinglib.project.ProgressEngine;
import com.strategyquant.tradinglib.project.ProjectEngine;
import com.strategyquant.tradinglib.project.ProjectGlobalLog;
import com.strategyquant.tradinglib.project.SQProject;
import com.strategyquant.tradinglib.project.websocket.DataManagerDataProgress;
import com.strategyquant.tradinglib.project.websocket.MultiProgressListener;
import com.strategyquant.tradinglib.taskImpl.AbstractTask;
import com.strategyquant.tradinglib.taskImpl.ISQTask;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import net.xeoh.plugins.base.annotations.PluginImplementation;
import net.xeoh.plugins.base.annotations.meta.Author;
import org.jdom2.Element;
import org.json.JSONObject;

@Author(name="Tamas Takacs")
@Name(name="Update data")
@Category(name="Task")
@License(text="")
@ShortDesc(text="Short description")
@PluginImplementation
public class UpdateDataTask
extends AbstractTask {
    private String logMessage;
    private List<DataInfo> symbolsToUpdate;
    private String type;

    public UpdateDataTask() throws Exception {
        super(null, null);
    }

    public UpdateDataTask(String projectName, ProgressEngine progressEngine) throws Exception {
        super(projectName, progressEngine);
    }

    public String getType() {
        return "UpdateData";
    }

    public String getName() {
        return L.tsq((String)"Update data");
    }

    public ISQTask clone(String projectName, ProgressEngine progressEngine) throws Exception {
        UpdateDataTask task = new UpdateDataTask(projectName, progressEngine);
        task.settingTabPlugins = this.settingTabPlugins;
        return task;
    }

    private void init() {
        this.type = (String)this.settingsData.getParams().get("Type");
        this.symbolsToUpdate = new ArrayList<DataInfo>();
        if (this.type.equals("project")) {
            try {
                SQProject project = ProjectEngine.get((String)this.projectName);
                Element elConfig = project.getConfig();
                ArrayList tasks = project.getTasks();
                for (int i = 0; i < tasks.size(); ++i) {
                    ISQTask task = (ISQTask)tasks.get(i);
                    this.loadSymbols(task.getConfig());
                }
            }
            catch (Exception e) {
                Log.error("Error while parsing resources.", (Throwable)e);
            }
        } else {
            try {
                ArrayList list = DataManager.list();
                for (int i = 0; i < list.size(); ++i) {
                    try {
                        DataInfo di = (DataInfo)list.get(i);
                        if (di.sourceDataId > 0) continue;
                        DownloadDispatcher.createListener((DataInfo)di);
                        if (this.symbolsToUpdate.contains(di)) continue;
                        this.symbolsToUpdate.add(di);
                        continue;
                    }
                    catch (NotDownloadableDataException notDownloadableDataException) {
                        // empty catch block
                    }
                }
            }
            catch (Exception e) {
                Log.error("Exc.", (Throwable)e);
            }
        }
    }

    private void loadSymbols(Element el) throws Exception {
        Element elResources = el.getChild("Resources");
        if (elResources == null) {
            return;
        }
        Element elSymbols = elResources.getChild("Symbols");
        if (elSymbols == null) {
            return;
        }
        List symbolElems = elSymbols.getChildren("Symbol");
        for (int i = 0; i < symbolElems.size(); ++i) {
            String symbol = ((Element)symbolElems.get(i)).getAttributeValue("name");
            DataInfo di = DataManager.getDataInfo((String)"History", (String)symbol);
            if (di == null) {
                this.progressEngine.printToLog(L.t((String)"Symbol '%s' not found in DataManager.", (Object[])new Object[]{symbol}));
                continue;
            }
            if (di.sourceDataId > 0) {
                di = DataManager.getDataInfo((String)"History", (int)di.sourceDataId);
            }
            if (di == null) continue;
            try {
                DownloadDispatcher.createListener((DataInfo)di);
                if (this.symbolsToUpdate.contains(di)) continue;
                this.symbolsToUpdate.add(di);
                continue;
            }
            catch (NotDownloadableDataException notDownloadableDataException) {
                // empty catch block
            }
        }
    }

    public void start() throws Exception {
        this.progressEngine.setLogPrefix(this.taskLogPrefix);
        this.progressEngine.start();
        this.init();
        if (this.symbolsToUpdate.isEmpty()) {
            String message;
            this.logMessage = message = L.t((String)"No data found to update.", (Object[])new Object[0]);
            this.progressEngine.printToLog(message);
        } else {
            String message = L.t((String)"Updating data...", (Object[])new Object[0]);
            this.progressEngine.printToLog(message);
            this.logMessage = message;
            String symbolsString = "";
            for (int i = 0; i < this.symbolsToUpdate.size(); ++i) {
                DataInfo di = this.symbolsToUpdate.get(i);
                String symbol = di.symbol;
                message = L.t((String)"Updating %s", (Object[])new Object[]{symbol});
                this.progressEngine.printToLog(message);
                this.logMessage = this.logMessage + "\n" + message;
                symbolsString = symbolsString + symbol + ",";
            }
            symbolsString = symbolsString.substring(0, symbolsString.length() - 1);
            HashMap<String, String[]> params = new HashMap<String, String[]>();
            params.put("symbols", new String[]{symbolsString});
            Program.get((String)"DataManagerData").call("updateSelected", new Object[]{params});
            new Thread(){

                @Override
                public void run() {
                    HashMap<String, Boolean> finished = new HashMap<String, Boolean>();
                    while (true) {
                        try {
                            Thread.sleep(5000L);
                        }
                        catch (Exception exception) {
                            // empty catch block
                        }
                        try {
                            String message;
                            for (int i = 0; i < UpdateDataTask.this.symbolsToUpdate.size(); ++i) {
                                JSONObject dataObject;
                                String symbol = ((DataInfo)((UpdateDataTask)UpdateDataTask.this).symbolsToUpdate.get((int)i)).symbol;
                                MultiProgressListener listener = DataManagerDataProgress.get().getListener(symbol);
                                JSONObject jSONObject = dataObject = listener == null ? null : listener.getData();
                                if (listener != null && (dataObject == null || !dataObject.has("pct") || dataObject.getInt("pct") != 100 && dataObject.getInt("pct") >= 0) || finished.containsKey(symbol)) continue;
                                if (listener == null || dataObject != null && dataObject.getInt("pct") == 100) {
                                    message = L.t((String)"%s successfully updated.", (Object[])new Object[]{symbol});
                                    UpdateDataTask.this.progressEngine.printToLog(message);
                                    UpdateDataTask.this.logMessage = UpdateDataTask.this.logMessage + ("\n" + message);
                                    finished.put(symbol, true);
                                    continue;
                                }
                                if (dataObject == null || dataObject.getInt("pct") >= 0 || !dataObject.has("message")) continue;
                                message = L.t((String)"%s update failed - %s.", (Object[])new Object[]{symbol, listener.getData().getString("message")});
                                UpdateDataTask.this.progressEngine.printToLog(message);
                                UpdateDataTask.this.logMessage = UpdateDataTask.this.logMessage + ("\n" + message);
                                finished.put(symbol, false);
                            }
                            MultiProgressListener listener = DataManagerDataProgress.get().getListener("TotalProgressSymbol");
                            JSONObject dataObject = listener.getData();
                            if (finished.size() != UpdateDataTask.this.symbolsToUpdate.size() && (dataObject == null || !dataObject.has("pct") || dataObject.getInt("pct") != 100)) continue;
                            message = L.t((String)"All data updated.", (Object[])new Object[0]);
                            UpdateDataTask.this.progressEngine.printToLog(message);
                            UpdateDataTask.this.logMessage = UpdateDataTask.this.logMessage + ("\n" + message);
                            UpdateDataTask.this.progressEngine.resume();
                            return;
                        }
                        catch (Exception e) {
                            AbstractTask.Log.error("Exc.", (Throwable)e);
                            continue;
                        }
                        break;
                    }
                }
            }.start();
            this.progressEngine.printToLog(L.t((String)"Project was paused until data download is finished.", (Object[])new Object[0]));
            this.progressEngine.pause();
            this.progressEngine.checkPaused();
        }
        this.progressEngine.finish();
    }

    protected int getRunningStatus() {
        return 0;
    }

    public String getPluginFolderName() {
        return "TaskUpdateData";
    }

    public int getPreferredPosition() {
        return 50;
    }

    public String[] getSettings() {
        return new String[]{"UpdateData"};
    }

    protected Databank[] getUsedDatabanks() {
        return null;
    }

    protected Databank getOutputDatabank() {
        return null;
    }

    public void logTaskFinished(ProjectGlobalLog log) {
        super.logTaskFinished(log);
        log.print(this.logMessage);
    }
}

