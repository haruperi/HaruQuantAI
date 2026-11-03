/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.lib.constants.SQPaths
 *  com.strategyquant.pluginlib.program.IProgram
 *  com.strategyquant.pluginlib.program.Program
 *  org.jdom2.Element
 *  org.json.JSONArray
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib;

import com.strategyquant.lib.L;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.lib.constants.SQPaths;
import com.strategyquant.pluginlib.program.IProgram;
import com.strategyquant.pluginlib.program.Program;
import com.strategyquant.tradinglib.DatabankSyncTypes;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.databank.DatabankRecords;
import com.strategyquant.tradinglib.databank.DatabankTableView;
import com.strategyquant.tradinglib.databank.DatabankViewsManager;
import com.strategyquant.tradinglib.databank.IDatabankFilter;
import com.strategyquant.tradinglib.databank.IDatabankListener;
import com.strategyquant.tradinglib.databank.IProgressListener;
import com.strategyquant.tradinglib.databank.RecordNotFoundException;
import com.strategyquant.tradinglib.gp.FitnessCollectionData;
import com.strategyquant.tradinglib.project.ProjectEngine;
import com.strategyquant.tradinglib.project.StrategiesSaver;
import com.strategyquant.tradinglib.project.StrategySaver;
import java.io.File;
import java.io.Serializable;
import java.util.ArrayList;
import java.util.concurrent.locks.StampedLock;
import org.jdom2.Element;
import org.json.JSONArray;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class Databank
implements Serializable {
    public static final Logger Log = LoggerFactory.getLogger(Databank.class);
    public static final String ACTION_RESULT_ADDED = "added";
    public static final String ACTION_RESULT_REMOVED = "removed";
    public static final String ACTION_CLEARED = "cleared";
    public static final String ACTION_UPDATED = "updated";
    public static final String DefaultMainViewName = "Default - Main data";
    public static final String DefaultPortfolioViewName = "Default - Portfolio";
    public static final int TIMER_TICKS_FREQUENCY = 5000;
    private String name;
    private String projectName;
    private String databankFolder;
    private int position;
    private boolean loading = false;
    private boolean loaded = false;
    private double percentLoaded = 0.0;
    private DatabankTableView view;
    private DatabankRecords databankRecords = new DatabankRecords(this);
    private StrategySaver reportSaver = new StrategySaver();
    private ArrayList<IDatabankListener> listeners = new ArrayList();
    private IDatabankFilter filter;
    private String syncType;
    private boolean fileBased = false;
    private boolean syncAllowed = true;
    private Thread dbSyncThread = null;
    private StampedLock progressLock = new StampedLock();

    public Databank(String string, String string2, String string3) {
        this.projectName = string;
        this.name = string2;
        this.databankFolder = string3 + "/" + this.name;
        try {
            this.view = DatabankViewsManager.getInstance().getView(DefaultMainViewName);
        }
        catch (Exception exception) {
            Log.debug("Cannot find databank view 'Default - Main data'", (Throwable)exception);
            this.view = DatabankViewsManager.getInstance().createDefaultView(DefaultMainViewName, "main");
        }
    }

    public String getProject() {
        return this.projectName;
    }

    public void addListener(IDatabankListener iDatabankListener) {
        this.listeners.add(iDatabankListener);
    }

    public void removeListener(IDatabankListener iDatabankListener) {
        this.listeners.remove(iDatabankListener);
    }

    public void loadStrategies(final IProgressListener iProgressListener) throws Exception {
        if (this.databankFolder == null) {
            this.loading = false;
            throw new Exception(L.t((String)"Databank folder not set", (Object[])new Object[0]));
        }
        if (this.loading) {
            throw new Exception(L.t((String)"Loading is already in progress", (Object[])new Object[0]));
        }
        this.loaded = false;
        final File file = new File(this.databankFolder);
        if (file.exists()) {
            this.loading = true;
            Thread thread = new Thread(this){
                final /* synthetic */ Databank this$0;
                {
                    this.this$0 = databank;
                }

                /*
                 * WARNING - Removed try catching itself - possible behaviour change.
                 */
                @Override
                public void run() {
                    try {
                        File[] fileArray = file.listFiles();
                        int n = 0;
                        IProgram iProgram = null;
                        try {
                            iProgram = Program.get((String)"Loader");
                        }
                        catch (Exception exception) {
                            Log.error("Loader not initialized", (Throwable)exception);
                        }
                        for (int i = 0; i < fileArray.length; ++i) {
                            block14: {
                                File file2 = fileArray[i];
                                try {
                                    ResultsGroup resultsGroup = (ResultsGroup)iProgram.call("loadFile", new Object[]{file2.getAbsolutePath()});
                                    this.this$0.add(this.this$0, resultsGroup);
                                }
                                catch (Exception exception) {
                                    Log.error("Cannot load strategy from file '" + file2.getAbsolutePath() + "'. ", (Throwable)exception);
                                    if (iProgressListener == null) break block14;
                                    iProgressListener.onError(this.this$0.percentLoaded, "Cannot load strategy from file '" + file2.getAbsolutePath() + "'. " + exception.getMessage());
                                }
                                catch (OutOfMemoryError outOfMemoryError) {
                                    if (iProgressListener == null) break;
                                    iProgressListener.onError(this.this$0.percentLoaded, "Cannot load strategy from file '" + file2.getAbsolutePath() + ". " + outOfMemoryError.getMessage());
                                    break;
                                }
                            }
                            this.this$0.setPercentLoaded(fileArray.length != 0 ? (double)(++n) / (double)fileArray.length * 100.0 : 100.0);
                            if (iProgressListener == null) continue;
                            iProgressListener.onProgress(this.this$0.percentLoaded);
                        }
                        this.this$0.refreshGrid();
                        this.this$0.updateBestResults();
                    }
                    catch (Error | Exception throwable) {
                        Log.error("Databank '" + this.this$0.getProject() + "/" + this.this$0.getName() + "', error while loading strategies - " + throwable.getMessage(), throwable);
                    }
                    finally {
                        if (this.this$0.percentLoaded != 100.0) {
                            this.this$0.setPercentLoaded(100.0);
                            if (iProgressListener != null) {
                                iProgressListener.onProgress(this.this$0.percentLoaded);
                            }
                        }
                        this.this$0.loading = false;
                        this.this$0.loaded = true;
                        if (iProgressListener != null) {
                            iProgressListener.onDone();
                        }
                    }
                }
            };
            thread.start();
            if (MainApp.runInConsoleWithoutActiveWebserver()) {
                thread.join();
            }
        } else {
            file.mkdirs();
            if (iProgressListener != null) {
                this.setPercentLoaded(100.0);
                iProgressListener.onProgress(this.percentLoaded);
                iProgressListener.onDone();
            }
            this.loading = false;
            this.loaded = true;
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private void setPercentLoaded(double d) {
        long l = this.progressLock.writeLock();
        try {
            this.percentLoaded = d;
        }
        finally {
            this.progressLock.unlock(l);
        }
    }

    protected void add(Databank databank, ResultsGroup resultsGroup) throws Exception {
        databank.add(resultsGroup, false);
    }

    public void add(StrategyBase strategyBase) throws Exception {
        ResultsGroup resultsGroup = new ResultsGroup(strategyBase.getStrategyName());
        resultsGroup.portfolio().addStrategy(strategyBase);
        this.add(resultsGroup, true);
    }

    public boolean add(ResultsGroup resultsGroup, boolean bl) throws Exception {
        return this.add(resultsGroup, bl, true);
    }

    public boolean add(ResultsGroup resultsGroup, boolean bl, boolean bl2) throws Exception {
        return this.databankRecords.add(resultsGroup, bl, bl2);
    }

    public void remove(String string, boolean bl, boolean bl2, boolean bl3, boolean bl4, String string2) throws Exception {
        this.databankRecords.remove(string, bl, bl2, bl3, bl4, string2);
    }

    public void remove(String string, boolean bl, boolean bl2, boolean bl3, boolean bl4, boolean bl5, String string2) throws Exception {
        this.databankRecords.remove(string, bl, bl2, bl3, bl4, bl5, string2);
    }

    public void removeNoLock(String string, boolean bl, boolean bl2, boolean bl3, String string2) throws Exception {
        this.databankRecords.removeNoLock(string, bl, bl2, bl3, string2);
    }

    public void removeNoLockNoException(String string, boolean bl, boolean bl2, boolean bl3, String string2) throws Exception {
        try {
            this.databankRecords.removeNoLock(string, bl, bl2, bl3, string2);
        }
        catch (RecordNotFoundException recordNotFoundException) {
            // empty catch block
        }
    }

    public void update(String string, ResultsGroup resultsGroup, boolean bl, String string2) throws Exception {
        this.databankRecords.update(string, resultsGroup, bl, string2);
    }

    public void updateAllResults() throws Exception {
        this.databankRecords.updateAllResults();
    }

    public void updateBestResults() {
        this.databankRecords.updateBestResults();
    }

    public void updateBestResults(ResultsGroup resultsGroup) {
        this.databankRecords.updateBestResults(resultsGroup);
    }

    public ResultsGroup getLocked(String string, String string2) throws Exception {
        return this.databankRecords.get(string, string2);
    }

    public boolean contains(String string) {
        return this.databankRecords.contains(string);
    }

    public ArrayList<ResultsGroup> getRecords() {
        return this.databankRecords.getRecords();
    }

    public int getRecordsSizeNoLock() {
        return this.databankRecords.getRecordsSizeNoLock();
    }

    public ArrayList<String> getRecordKeys() {
        return this.databankRecords.getRecordKeys();
    }

    public ArrayList<String> getRecordKeysNoLock() {
        return this.databankRecords.getRecordKeysNoLock();
    }

    public ArrayList<String> getRecordKeysNoLock(String string) {
        return this.databankRecords.getRecordKeysNoLock(string);
    }

    public ArrayList<String> getRecordKeys(String string) {
        return this.databankRecords.getRecordKeys(string);
    }

    public void onResultChange(ResultsGroup resultsGroup) throws Exception {
        this.databankRecords.sendUpdate(resultsGroup, true);
    }

    public String getResultsFilePath(ResultsGroup resultsGroup) {
        return this.databankFolder + "/" + resultsGroup.getName() + ".sqx";
    }

    public void deleteResultsFile(ResultsGroup resultsGroup) throws Exception {
        String string = this.getResultsFilePath(resultsGroup);
        File file = new File(string);
        if (file.exists()) {
            if (!file.delete()) {
                throw new Exception(L.t((String)"File '%s' wasn't removed.", (Object[])new Object[]{file.getName()}));
            }
        } else {
            throw new Exception(L.t((String)"File '%s' doesn't exist.", (Object[])new Object[]{file.getName()}));
        }
    }

    public Element getConfig() {
        Element element = new Element("Databank");
        element.setAttribute("name", this.name);
        element.setAttribute("view", this.view.name.equals("?") ? DefaultMainViewName : this.view.name);
        element.setAttribute("syncType", this.syncType != null ? this.syncType : Databank.getDefaultSyncType());
        element.setAttribute("position", String.valueOf(this.position));
        return element;
    }

    public static Element getDefaultConfig() {
        Element element = new Element("Databank");
        element.setAttribute("name", "Results");
        element.setAttribute("view", DefaultMainViewName);
        element.setAttribute("syncType", "Auto-sync never");
        element.setAttribute("position", "10");
        return element;
    }

    public void setView(DatabankTableView databankTableView) {
        this.view = databankTableView;
    }

    public DatabankTableView getView() {
        return this.view;
    }

    public ArrayList<Object[]> getBufferData(boolean bl) {
        return this.databankRecords.getBufferData(bl);
    }

    public void removeAll(boolean bl, String string) throws Exception {
        this.clearRecords(bl, true, string);
        if (this.isFileBased()) {
            File file = new File(this.databankFolder);
            File[] fileArray = file.listFiles();
            boolean bl2 = true;
            for (int i = 0; i < fileArray.length; ++i) {
                File file2 = fileArray[i];
                if (file2.delete()) {
                    Log.info("File " + file2.getName() + " deleted.");
                    continue;
                }
                Log.error("Unable to delete file " + file2.getName());
                bl2 = false;
            }
            if (!bl2) {
                throw new Exception(L.t((String)"Some databank files were not deleted.", (Object[])new Object[0]));
            }
        }
    }

    public void clearRecords(boolean bl, boolean bl2, String string) throws Exception {
        this.databankRecords.clearRecords(bl);
        if (bl2) {
            this.synchronizeNow(string);
        }
    }

    public boolean setViewByName(String string) {
        try {
            DatabankTableView databankTableView;
            if (string.equals("Default")) {
                string = DefaultMainViewName;
            }
            this.view = databankTableView = DatabankViewsManager.getInstance().getView(string);
            return true;
        }
        catch (Exception exception) {
            Log.debug("Cannot find databank view '" + string + "'");
            try {
                DatabankViewsManager.getInstance().getView(DefaultMainViewName);
            }
            catch (Exception exception2) {
                Log.error("Cannot get default databank view");
            }
            return false;
        }
    }

    public boolean noActionRunning() {
        return this.dbSyncThread == null || !this.dbSyncThread.isAlive();
    }

    public String getName() {
        return this.name;
    }

    public boolean isLoading() {
        return this.loading;
    }

    public boolean isLoaded() {
        return this.loaded;
    }

    public int size() {
        return this.databankRecords.size();
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public double getPercentLoaded() {
        long l = this.progressLock.readLock();
        try {
            double d = this.percentLoaded;
            return d;
        }
        finally {
            this.progressLock.unlock(l);
        }
    }

    public void notifyListeners(String string) {
        for (int i = 0; i < this.listeners.size(); ++i) {
            IDatabankListener iDatabankListener = this.listeners.get(i);
            iDatabankListener.databankChanged(this);
        }
    }

    public void applyFilter(IDatabankFilter iDatabankFilter) throws Exception {
        this.filter = iDatabankFilter;
        iDatabankFilter.init(this);
    }

    public void applyFilter(IDatabankFilter iDatabankFilter, IProgressListener iProgressListener) throws Exception {
        this.filter = iDatabankFilter;
        iDatabankFilter.init(this, iProgressListener);
    }

    public void removeFilter() {
        if (this.filter != null) {
            this.filter.destroy();
            this.filter = null;
        }
    }

    public IDatabankFilter getFilter() {
        return this.filter;
    }

    public double getWorstFitness() {
        if (this.filter != null) {
            return this.filter.getWorstFitness();
        }
        return 0.0;
    }

    public JSONArray getChanges() {
        return this.databankRecords.getChanges();
    }

    public StrategySaver getReportSaver() {
        return this.reportSaver;
    }

    public String getDatabankFolder() {
        return this.databankFolder;
    }

    public void addExtraDatabankChange(String string, String string2) {
        this.databankRecords.addExtraChange(string, string2);
    }

    public ResultsGroup[] getTopResults() {
        return this.databankRecords.getTopResults();
    }

    public FitnessCollectionData getFitnessData() {
        return this.databankRecords.getFitnessData();
    }

    public boolean isFileBased() {
        return this.fileBased;
    }

    public String getSyncType() {
        return this.syncType != null ? this.syncType : Databank.getDefaultSyncType();
    }

    public void setSyncType(String string) {
        if (this.name.equals("Last generation")) {
            this.syncType = "Auto-sync never";
            this.fileBased = false;
            return;
        }
        this.syncType = string != null ? string : Databank.getDefaultSyncType();
        this.fileBased = this.syncType.equals("Immediately (not recommended, very slow)");
        try {
            final int n = DatabankSyncTypes.getTimeout(this.syncType);
            if (this.dbSyncThread != null && this.dbSyncThread.isAlive()) {
                this.dbSyncThread.interrupt();
            }
            if (this.fileBased) {
                this.synchronize(false, String.format("Periodical sync of databank %s/%s - %s", this.projectName, this.name, this.syncType));
                return;
            }
            if (n > 0 && !this.isFileBased()) {
                this.dbSyncThread = new Thread(this){
                    final /* synthetic */ Databank this$0;
                    {
                        this.this$0 = databank;
                    }

                    @Override
                    public void run() {
                        while (true) {
                            try {
                                Thread.sleep(n);
                            }
                            catch (InterruptedException interruptedException) {
                                break;
                            }
                            if (!MainApp.AppLoaded) continue;
                            if (MainApp.isExiting()) break;
                            if (this.this$0.loading || !this.this$0.syncAllowed) continue;
                            this.this$0.synchronize(false, String.format("Periodical sync of databank %s/%s - %s", this.this$0.projectName, this.this$0.name, this.this$0.syncType));
                        }
                    }
                };
                this.dbSyncThread.start();
            }
        }
        catch (Exception exception) {
            Log.error("Initializing databank synchronization failed", (Throwable)exception);
        }
    }

    public void synchronizeNow(String string) {
        this.synchronizeNow(false, string);
    }

    public void synchronizeNow(boolean bl, final String string) {
        if (this.isFileBased()) {
            return;
        }
        if (this.dbSyncThread != null && this.dbSyncThread.isAlive()) {
            this.dbSyncThread.interrupt();
        }
        if (MainApp.runInConsoleWithoutActiveWebserver()) {
            this.synchronize(false, string);
            this.setSyncType(this.syncType);
        } else {
            Thread thread = new Thread(this){
                final /* synthetic */ Databank this$0;
                {
                    this.this$0 = databank;
                }

                @Override
                public void run() {
                    this.this$0.synchronize(true, string);
                    this.this$0.setSyncType(this.this$0.syncType);
                    Log.debug("Synchronization finished2.");
                }
            };
            thread.start();
            if (bl) {
                try {
                    thread.join();
                }
                catch (Exception exception) {
                    Log.error("Error while joining databank synchronization thread", (Throwable)exception);
                }
            }
        }
    }

    private void synchronize(boolean bl, String string) {
        if (ProjectEngine.loading) {
            return;
        }
        StrategiesSaver.syncDatabank(this, bl, string);
    }

    public static String getDefaultSyncType() {
        return MainApp.settings().get("databankSyncType", "Auto-sync every 1 hour");
    }

    public void refreshGrid() {
        this.addExtraDatabankChange("remove", "refreshGrid");
    }

    public void setProjectName(String string) {
        this.projectName = string;
        this.databankFolder = SQPaths.projectsDirPath + "/" + string + "/databanks/" + this.name;
    }

    public int getPosition() {
        return this.position;
    }

    public void setPosition(int n) {
        this.position = n;
    }

    public boolean isDefault() {
        return Databank.isDefault(this.name);
    }

    public static boolean isDefault(String string) {
        switch (string) {
            case "Results": 
            case "Strategies to improve": 
            case "Initial population": 
            case "Strategies to optimize": 
            case "Last generation": 
            case "Existing portfolio": 
            case "Simple strategies": {
                return true;
            }
        }
        return false;
    }

    public void rename(String string) {
        File file = new File(this.databankFolder);
        File file2 = file.getParentFile();
        this.databankFolder = file2.getAbsolutePath() + "/" + string;
        file.renameTo(new File(this.databankFolder));
        this.name = string;
    }

    public void destroyTimers() {
        if (this.dbSyncThread != null && this.dbSyncThread.isAlive()) {
            this.dbSyncThread.interrupt();
        }
    }

    public long getLastChangeTime() {
        return this.databankRecords.getLastChangeTime();
    }

    public void disableSynchronization() {
        this.syncAllowed = false;
    }

    public void enableSynchronization() {
        this.syncAllowed = true;
    }

    public void clearResultsData() {
        this.databankRecords.clearResultsData();
    }

    public void clearResultsData(ArrayList<String> arrayList) {
        this.databankRecords.clearResultsData(arrayList);
    }
}

