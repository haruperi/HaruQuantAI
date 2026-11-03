/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.memory.MemoryUsageChecker
 *  org.json.JSONArray
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.databank;

import com.strategyquant.lib.L;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.memory.MemoryUsageChecker;
import com.strategyquant.tradinglib.CustomCellFormat;
import com.strategyquant.tradinglib.Databank;
import com.strategyquant.tradinglib.DatabankColumn;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.WalkForwardResult;
import com.strategyquant.tradinglib.databank.DatabankChange;
import com.strategyquant.tradinglib.databank.DatabankColumns;
import com.strategyquant.tradinglib.databank.DatabankTableColumnEntry;
import com.strategyquant.tradinglib.databank.DatabankTableView;
import com.strategyquant.tradinglib.databank.IDatabankFilter;
import com.strategyquant.tradinglib.databank.RecordNotFoundException;
import com.strategyquant.tradinglib.databank.TopStrategiesData;
import com.strategyquant.tradinglib.gp.FitnessCollectionData;
import com.strategyquant.tradinglib.miniequitychart.MiniEquityChartComputer;
import com.strategyquant.tradinglib.optimization.OptimizationProfile;
import com.strategyquant.tradinglib.optimization.WalkForwardMatrixResult;
import com.strategyquant.tradinglib.project.SQProject;
import com.strategyquant.tradinglib.project.websocket.ProjectFeeds;
import java.io.File;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.concurrent.locks.StampedLock;
import org.json.JSONArray;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class DatabankRecords {
    public static final int MaxColumns = 500;
    public static final Logger Log = LoggerFactory.getLogger(DatabankRecords.class);
    private static final int CHANGES_BUFFER_SIZE_INCREMENT = 20;
    private static final int DATABANK_FIRSTLOAD_COUNT = 1000;
    private Databank databank;
    private HashMap<String, Integer> indexes = new HashMap();
    private ArrayList<ResultsGroup> records = new ArrayList();
    private boolean containsRefreshChange = false;
    private StampedLock recordsLock = new StampedLock();
    private StampedLock changesLock = new StampedLock();
    private FitnessCollectionData databankFitness = new FitnessCollectionData(0);
    private TopStrategiesData topStrategiesData = new TopStrategiesData();
    private DatabankChange[] changes = new DatabankChange[100];
    private Object[] rowDataTemp = new Object[500];
    private int changesLastIndex = -1;
    private long lastChangeTime = 0L;

    public DatabankRecords(Databank databank) {
        this.databank = databank;
        this.databankFitness.reset();
        this.topStrategiesData.reset();
        for (int i = 0; i < this.changes.length; ++i) {
            this.changes[i] = new DatabankChange();
        }
        this.changesLastIndex = -1;
    }

    public boolean add(ResultsGroup resultsGroup, boolean bl, boolean bl2) throws Exception {
        if (this.databank.isLoading() || SQProject.isMemoryProtectionUsed()) {
            MemoryUsageChecker.checkAvailableMemory();
        }
        IDatabankFilter iDatabankFilter = this.databank.getFilter();
        if (this.databank.isLoading() || iDatabankFilter == null) {
            return this.addRecord(resultsGroup, bl, bl2);
        }
        return this.checkAndAddRecord(iDatabankFilter, resultsGroup, bl, bl2);
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private boolean checkAndAddRecord(IDatabankFilter iDatabankFilter, ResultsGroup resultsGroup, boolean bl, boolean bl2) {
        String string;
        boolean bl3;
        boolean bl4 = iDatabankFilter.checkShouldAdd(resultsGroup);
        if (!bl4) {
            return false;
        }
        long l = this.recordsLock.writeLock();
        boolean bl5 = false;
        try {
            bl3 = iDatabankFilter.onAdd(resultsGroup);
            if (!bl3) {
                boolean bl6 = false;
                return bl6;
            }
            string = this.findUniqueName(resultsGroup);
            resultsGroup.setDatabank(this.databank);
            resultsGroup.setName(string);
            this.records.add(resultsGroup);
            this.indexes.put(string, this.records.size() - 1);
            if (!this.databank.isLoading()) {
                resultsGroup.trySaveToFile();
            }
            bl5 = true;
        }
        finally {
            this.recordsLock.unlock(l);
        }
        if (bl5) {
            OptimizationProfile optimizationProfile;
            this.computeMiniEquityCharts(resultsGroup);
            bl3 = resultsGroup.specialValues().containsKey("DontComputeOP");
            if (!bl3 && (optimizationProfile = resultsGroup.getOptimizationProfile()) != null) {
                optimizationProfile.compute(bl2, true);
            }
            if (this.contains(string)) {
                this.addChange("add", string, resultsGroup, bl);
            }
            this.databank.notifyListeners("added");
            this.databank.refreshGrid();
        }
        return bl5;
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private boolean addRecord(ResultsGroup resultsGroup, boolean bl, boolean bl2) {
        String string;
        long l = this.recordsLock.writeLock();
        boolean bl3 = false;
        try {
            string = this.findUniqueName(resultsGroup);
            resultsGroup.setDatabank(this.databank);
            resultsGroup.setName(string);
            this.records.add(resultsGroup);
            this.indexes.put(string, this.records.size() - 1);
            if (!this.databank.isLoading()) {
                resultsGroup.trySaveToFile();
            }
            bl3 = true;
        }
        finally {
            this.recordsLock.unlock(l);
        }
        if (bl3) {
            OptimizationProfile optimizationProfile;
            this.computeMiniEquityCharts(resultsGroup);
            boolean bl4 = resultsGroup.specialValues().containsKey("DontComputeOP");
            if (!bl4 && (optimizationProfile = resultsGroup.getOptimizationProfile()) != null) {
                optimizationProfile.compute(bl2, true);
            }
            if (this.contains(string)) {
                this.addChange("add", string, resultsGroup, bl);
            }
            this.databank.notifyListeners("added");
            this.databank.refreshGrid();
        }
        return bl3;
    }

    private void computeMiniEquityCharts(ResultsGroup resultsGroup) {
        try {
            List<String> list = resultsGroup.getResultKeys();
            String string = resultsGroup.getMainResultKey();
            for (int i = 0; i < list.size(); ++i) {
                String string2 = list.get(i);
                if (!string2.equals(string) && !string2.equals("Portfolio") && !string2.contains("Walk-Forward")) continue;
                MiniEquityChartComputer.computeForResult(resultsGroup, string2);
            }
        }
        catch (Exception exception) {
            Log.error("Cannot compute mini equity chart values for strategy '" + resultsGroup.getName() + "'", (Throwable)exception);
        }
    }

    private String findUniqueName(ResultsGroup resultsGroup) {
        String string = resultsGroup.getName();
        if (!this.indexes.containsKey(string)) {
            return string;
        }
        String string2 = string;
        int n = 1;
        while (true) {
            StringBuilder stringBuilder = new StringBuilder(string);
            stringBuilder.append("(");
            stringBuilder.append(n);
            stringBuilder.append(")");
            string2 = stringBuilder.toString();
            if (!this.indexes.containsKey(string2)) {
                return string2;
            }
            ++n;
        }
    }

    public void remove(String string, boolean bl, boolean bl2, boolean bl3, boolean bl4, String string2) throws Exception {
        this.remove(string, bl, bl2, true, bl3, bl4, string2);
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public void remove(String string, boolean bl, boolean bl2, boolean bl3, boolean bl4, boolean bl5, String string2) throws Exception {
        long l = this.recordsLock.writeLock();
        try {
            this.removeNoLock(string, bl, bl4, bl5, string2);
            IDatabankFilter iDatabankFilter = this.databank.getFilter();
            if (iDatabankFilter != null) {
                iDatabankFilter.onRemove(string);
            }
        }
        finally {
            this.recordsLock.unlock(l);
        }
        if (bl2) {
            this.databank.notifyListeners("removed");
        }
    }

    public void removeNoLock(String string, boolean bl, boolean bl2, boolean bl3, String string2) throws Exception {
        this.removeNoLock(string, bl, true, bl2, bl3, string2);
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public void removeNoLock(String string, boolean bl, boolean bl2, boolean bl3, boolean bl4, String string2) throws Exception {
        block12: {
            Object object;
            if (this.databank.isLoading()) {
                throw new Exception(L.t((String)"Cannot remove results while loading", (Object[])new Object[0]));
            }
            if (!this.indexes.containsKey(string)) {
                return;
            }
            if (Log.isDebugEnabled()) {
                Log.debug(String.format("Report with the name '%s' was removed from databank '%s'.", string, this.databank.getName()));
            }
            int n = this.indexes.remove(string);
            ResultsGroup resultsGroup = this.records.remove(n);
            if (bl2) {
                this.addChange("remove", string, null, bl3);
            }
            for (int i = n; i < this.records.size(); ++i) {
                object = this.records.get(i).getName();
                this.indexes.put((String)object, i);
            }
            if (bl) {
                resultsGroup.destroy(bl4);
            }
            if (this.databank.isFileBased()) {
                resultsGroup.lockRecord(string2);
                try {
                    String string3 = this.databank.getResultsFilePath(resultsGroup);
                    object = new File(string3);
                    if (!((File)object).exists()) break block12;
                    if (((File)object).delete()) {
                        if (Log.isDebugEnabled()) {
                            Log.debug("File " + string3 + " deleted.");
                        }
                        break block12;
                    }
                    Log.error("Unable to delete file " + string3);
                    throw new Exception(L.t((String)"Unable to delete %s.sqx file", (Object[])new Object[]{resultsGroup.getName()}));
                }
                finally {
                    resultsGroup.releaseLock(string2);
                }
            }
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public void update(String string, ResultsGroup resultsGroup, boolean bl, String string2) throws Exception {
        ResultsGroup resultsGroup2 = null;
        try {
            resultsGroup2 = this.databank.getLocked(string, string2);
            if (resultsGroup2 != resultsGroup) {
                OptimizationProfile optimizationProfile;
                resultsGroup2.updateResults(resultsGroup, true);
                boolean bl2 = resultsGroup.specialValues().containsKey("DontComputeOP");
                if (!bl2 && (optimizationProfile = resultsGroup2.getOptimizationProfile()) != null) {
                    optimizationProfile.compute(true, true);
                }
            }
        }
        finally {
            if (resultsGroup2 != null) {
                resultsGroup2.releaseLock(string2);
            }
        }
        long l = this.recordsLock.writeLock();
        try {
            resultsGroup.trySaveToFile();
            this.sendUpdateNoLock(resultsGroup, bl);
        }
        finally {
            this.recordsLock.unlock(l);
        }
        this.databank.notifyListeners("updated");
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public void updateAllResults() throws Exception {
        long l = this.recordsLock.writeLock();
        try {
            for (int i = 0; i < this.records.size(); ++i) {
                ResultsGroup resultsGroup = this.records.get(i);
                this.addChange("update", resultsGroup.getName(), resultsGroup, true);
            }
        }
        finally {
            this.recordsLock.unlock(l);
        }
        this.updateBestResults();
        if (this.databank.getFilter() != null) {
            this.databank.getFilter().init(this.databank);
        }
        this.databank.notifyListeners("updated");
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public void clearRecords(boolean bl) {
        long l = this.recordsLock.writeLock();
        try {
            this.topStrategiesData.reset();
            this.databankFitness.reset();
            for (int i = 0; i < this.records.size(); ++i) {
                ResultsGroup resultsGroup = this.records.get(i);
                if (bl) {
                    resultsGroup.clear();
                }
                if (this.databank.getFilter() == null) continue;
                this.databank.getFilter().onRemove(resultsGroup.getName());
            }
            this.records.clear();
            this.indexes.clear();
        }
        finally {
            this.recordsLock.unlock(l);
        }
        this.databank.notifyListeners("cleared");
        this.addChange("clearAll", null, null, true);
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public ResultsGroup get(String string, String string2) throws Exception {
        ResultsGroup resultsGroup = null;
        long l = this.recordsLock.tryOptimisticRead();
        if (this.recordsLock.validate(l)) {
            if (this.indexes.containsKey(string)) {
                resultsGroup = this.records.get(this.indexes.get(string));
            }
        } else {
            l = this.recordsLock.readLock();
            try {
                if (this.indexes.containsKey(string)) {
                    resultsGroup = this.records.get(this.indexes.get(string));
                }
            }
            finally {
                this.recordsLock.unlockRead(l);
            }
        }
        if (resultsGroup == null) {
            throw new RecordNotFoundException("RecordNotFoundException - " + L.t((String)"Report with the name '%s' was not found in databank '%s'(2).", (Object[])new Object[]{string, this.databank.getName()}));
        }
        return resultsGroup.lockRecord(string2);
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public ArrayList<ResultsGroup> getRecords() {
        long l = this.recordsLock.readLock();
        try {
            ArrayList<ResultsGroup> arrayList = this.records;
            return arrayList;
        }
        finally {
            this.recordsLock.unlock(l);
        }
    }

    public int getRecordsSizeNoLock() {
        return this.records.size();
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public ArrayList<String> getRecordKeys() {
        long l = this.recordsLock.readLock();
        try {
            ArrayList<String> arrayList = new ArrayList<String>(this.indexes.keySet());
            return arrayList;
        }
        finally {
            this.recordsLock.unlock(l);
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public ArrayList<String> getRecordKeys(String string) {
        long l = this.recordsLock.readLock();
        try {
            ArrayList<String> arrayList = new ArrayList<String>();
            for (String string2 : this.indexes.keySet()) {
                if (!string2.startsWith(string) || !string2.contains(" - Optimiz")) continue;
                arrayList.add(string2);
            }
            ArrayList<String> arrayList2 = arrayList;
            return arrayList2;
        }
        finally {
            this.recordsLock.unlock(l);
        }
    }

    public ArrayList<String> getRecordKeysNoLock() {
        return new ArrayList<String>(this.indexes.keySet());
    }

    public ArrayList<String> getRecordKeysNoLock(String string) {
        ArrayList<String> arrayList = new ArrayList<String>();
        for (String string2 : this.indexes.keySet()) {
            if (!string2.startsWith(string) || !string2.contains(" - Optimiz")) continue;
            arrayList.add(string2);
        }
        return arrayList;
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public int size() {
        long l = this.recordsLock.tryOptimisticRead();
        int n = this.records.size();
        if (!this.recordsLock.validate(l)) {
            l = this.recordsLock.readLock();
            try {
                n = this.records.size();
            }
            finally {
                this.recordsLock.unlockRead(l);
            }
        }
        return n;
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public ArrayList<Object[]> getBufferData(boolean bl) {
        ArrayList<Object[]> arrayList = new ArrayList<Object[]>();
        long l = this.recordsLock.readLock();
        try {
            for (int i = 0; i < this.records.size(); ++i) {
                ResultsGroup resultsGroup = this.records.get(i);
                arrayList.add(this.getRecordData(resultsGroup, true));
                if (!bl || i < 999) continue;
                break;
            }
        }
        finally {
            this.recordsLock.unlockRead(l);
        }
        return arrayList;
    }

    private synchronized Object[] getRecordData(ResultsGroup resultsGroup, boolean bl) {
        Object object;
        Object object2;
        Object object3;
        int n;
        int n2;
        DatabankTableView databankTableView = this.databank.getView();
        int n3 = databankTableView.columns.size();
        int n4 = 1;
        boolean bl2 = !this.databank.getProject().equals("Builder") && !this.databank.getProject().equals("PortfolioMaster");
        boolean bl3 = this.databank.getProject().equals("Optimizer");
        if (bl2) {
            ++n4;
        }
        if (bl3) {
            n4 += 2;
        }
        if ((n2 = n3 + n4 + 1) > this.rowDataTemp.length) {
            this.rowDataTemp = new Object[n2];
        } else {
            for (n = n2; n < this.rowDataTemp.length; ++n) {
                this.rowDataTemp[n] = null;
            }
        }
        this.rowDataTemp[0] = resultsGroup.getName();
        if (bl2) {
            try {
                DatabankColumn databankColumn = (DatabankColumn)DatabankColumns.get().findClassByName("FiltersResult");
                object3 = databankColumn.getValue(resultsGroup, null, (byte)0, (byte)10, (byte)127);
                if (!((String)object3).equals("N/A")) {
                    object2 = databankColumn.getCustomFormat((byte)0, (byte)10, (byte)127, (String)object3, resultsGroup);
                    object3 = ((CustomCellFormat)object2).getHtmlContent(object3);
                }
                this.rowDataTemp[1] = object3;
            }
            catch (Exception exception) {
                this.rowDataTemp[1] = "N/A";
            }
        }
        if (bl3) {
            String string = null;
            object3 = null;
            try {
                object2 = (WalkForwardMatrixResult)resultsGroup.mainResult().get("WalkForwardResult");
                object = ((WalkForwardMatrixResult)object2).getWFResult(resultsGroup.getBestWFResultKey(), true);
                string = ((WalkForwardResult)object).testParams;
                object3 = ((WalkForwardResult)object).toString(((WalkForwardMatrixResult)object2).periodType);
            }
            catch (Exception exception) {
                // empty catch block
            }
            try {
                string = resultsGroup.getParams();
            }
            catch (Exception exception) {
                // empty catch block
            }
            this.rowDataTemp[bl2 ? 2 : 1] = string != null ? string : "N/A";
            this.rowDataTemp[bl2 ? 3 : 2] = object3 != null ? object3 : "N/A";
        }
        for (n = 0; n < databankTableView.columns.size(); ++n) {
            object3 = databankTableView.columns.get(n);
            object2 = ((DatabankTableColumnEntry)object3).getValue(resultsGroup);
            try {
                if (!((String)object2).equals("N/A")) {
                    if (((DatabankTableColumnEntry)object3).tableColumn.getType().equals("Integer")) {
                        try {
                            double d = Double.parseDouble((String)object2);
                            if (!Double.isNaN(d)) {
                                object2 = Integer.toString((int)d);
                            }
                        }
                        catch (Exception exception) {
                            // empty catch block
                        }
                    }
                    object = ((DatabankTableColumnEntry)object3).tableColumn.getCustomFormat(((DatabankTableColumnEntry)object3).direction, ((DatabankTableColumnEntry)object3).plType, ((DatabankTableColumnEntry)object3).sampleType, (String)object2, resultsGroup);
                    object2 = ((CustomCellFormat)object).getHtmlContent(object2);
                }
                this.rowDataTemp[n + n4] = object2;
            }
            catch (Exception exception) {
                this.rowDataTemp[n + n4] = "N/A";
            }
            this.rowDataTemp[n3 + n4] = resultsGroup.specialValues().getInt("StrategyProblems", 0);
        }
        if (!bl) {
            return this.rowDataTemp;
        }
        Object[] objectArray = new Object[n2];
        for (int i = 0; i < n2; ++i) {
            objectArray[i] = this.rowDataTemp[i];
        }
        return objectArray;
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private void addChange(String string, String string2, ResultsGroup resultsGroup, boolean bl) {
        this.lastChangeTime = System.currentTimeMillis();
        if (ProjectFeeds.isSubscribed(this.databank.getProject(), "databanks-channel")) {
            long l = this.changesLock.writeLock();
            try {
                Object[] objectArray;
                Object[] objectArray2 = objectArray = resultsGroup != null ? this.getRecordData(resultsGroup, false) : null;
                String string3 = this.records.size() == 0 ? "DatabankEmpty" : (bl ? "refreshGrid" : null);
                this.setNextChange(string, string2, objectArray, string3);
            }
            finally {
                this.changesLock.unlock(l);
            }
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public void addExtraChange(String string, String string2) {
        if (string2 == null) {
            return;
        }
        if (ProjectFeeds.isSubscribed(this.databank.getProject(), "databanks-channel")) {
            long l = this.changesLock.writeLock();
            try {
                boolean bl = string2.equals("refreshGrid");
                if (!bl || !this.containsRefreshChange) {
                    this.setNextChange(string, null, null, string2);
                }
            }
            finally {
                this.changesLock.unlock(l);
            }
        }
    }

    private void setNextChange(String string, String string2, Object[] objectArray, String string3) {
        if (this.changesLastIndex >= this.changes.length - 1) {
            Log.debug("Maximum changes capacity reached");
            int n = this.changes.length;
            int n2 = n + 20;
            this.changes = Arrays.copyOf(this.changes, n2);
            for (int i = n; i < n2; ++i) {
                this.changes[i] = new DatabankChange();
            }
        }
        ++this.changesLastIndex;
        DatabankChange databankChange = this.changes[this.changesLastIndex];
        databankChange.update(string, string2, objectArray);
        databankChange.setExtraValue(string3);
        this.containsRefreshChange = this.containsRefreshChange || string3 != null && string3.equals("refreshGrid");
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public JSONArray getChanges() {
        long l = this.changesLock.writeLock();
        try {
            if (this.changesLastIndex < 0) {
                JSONArray jSONArray = null;
                return jSONArray;
            }
            JSONArray jSONArray = new JSONArray();
            boolean bl = false;
            String string = null;
            for (int i = 0; i <= this.changesLastIndex; ++i) {
                DatabankChange databankChange = this.changes[i];
                if (databankChange.type == "remove" && bl && databankChange.id != null && string != null && databankChange.id.equals(string)) {
                    jSONArray.remove(jSONArray.length() - 1);
                    bl = false;
                    continue;
                }
                if (databankChange.type == "add") {
                    bl = true;
                    string = databankChange.id;
                } else {
                    bl = false;
                }
                jSONArray.put((Object)databankChange.toJSON());
            }
            this.changesLastIndex = -1;
            this.containsRefreshChange = false;
            JSONArray jSONArray2 = jSONArray;
            return jSONArray2;
        }
        finally {
            this.changesLock.unlock(l);
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public void sendUpdate(ResultsGroup resultsGroup, boolean bl) {
        long l = this.recordsLock.readLock();
        try {
            this.sendUpdateNoLock(resultsGroup, bl);
        }
        finally {
            this.recordsLock.unlock(l);
        }
    }

    private void sendUpdateNoLock(ResultsGroup resultsGroup, boolean bl) {
        String string = resultsGroup.getName();
        this.addChange("update", string, resultsGroup, bl);
        if (this.databank.getFilter() != null) {
            this.databank.getFilter().onUpdate(resultsGroup);
        }
    }

    public boolean contains(String string) {
        return this.indexes.containsKey(string);
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public ResultsGroup[] getTopResults() {
        long l = this.recordsLock.readLock();
        try {
            ResultsGroup[] resultsGroupArray = this.topStrategiesData.getTopResults();
            return resultsGroupArray;
        }
        finally {
            this.recordsLock.unlock(l);
        }
    }

    public FitnessCollectionData getFitnessData() {
        return this.databankFitness;
    }

    public void updateBestResults(ResultsGroup resultsGroup) {
        this.topStrategiesData.updateWith(resultsGroup);
        this.topStrategiesData.updateDatabankFitnesses(this.databankFitness);
    }

    private String fitnessesToString(ResultsGroup resultsGroup) {
        StringBuilder stringBuilder = new StringBuilder();
        stringBuilder.append("BST IS:");
        stringBuilder.append(this.getFitness(resultsGroup, (byte)10));
        stringBuilder.append(", ISV:");
        stringBuilder.append(this.getFitness(resultsGroup, (byte)40));
        stringBuilder.append(", IST:");
        stringBuilder.append(this.getFitness(resultsGroup, (byte)11));
        stringBuilder.append(", OOS:");
        stringBuilder.append(this.getFitness(resultsGroup, (byte)20));
        stringBuilder.append(", FS:");
        stringBuilder.append(this.getFitness(resultsGroup, (byte)127));
        stringBuilder.append("\n");
        stringBuilder.append("-----------------------------------");
        return stringBuilder.toString();
    }

    private double getFitness(ResultsGroup resultsGroup, byte by) {
        try {
            double d = SQUtils.round2((double)resultsGroup.portfolio().getFitness(by));
            return d > 0.0 ? d : 0.0;
        }
        catch (Exception exception) {
            return 0.0;
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public void updateBestResults() {
        long l = this.recordsLock.readLock();
        try {
            this.topStrategiesData.reset();
            this.databankFitness.reset();
            for (int i = 0; i < this.records.size(); ++i) {
                ResultsGroup resultsGroup = this.records.get(i);
                this.topStrategiesData.updateWith(resultsGroup);
            }
            this.topStrategiesData.updateDatabankFitnesses(this.databankFitness);
        }
        finally {
            this.recordsLock.unlock(l);
        }
    }

    public long getLastChangeTime() {
        return this.lastChangeTime;
    }

    public void clearResultsData() {
        this.clearResultsData(null);
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public void clearResultsData(ArrayList<String> arrayList) {
        ArrayList<String> arrayList2 = null;
        if (arrayList != null) {
            arrayList2 = new ArrayList<String>(arrayList);
        }
        long l = this.recordsLock.readLock();
        try {
            this.topStrategiesData.reset();
            this.databankFitness.reset();
            for (int i = 0; i < this.records.size(); ++i) {
                ResultsGroup resultsGroup = this.records.get(i);
                String string = resultsGroup.getName();
                if (arrayList2 != null && !arrayList2.contains(string)) continue;
                resultsGroup.clear();
                if (arrayList2 != null) {
                    arrayList2.remove(string);
                }
                this.addChange("reset", string, null, true);
            }
        }
        finally {
            this.recordsLock.unlock(l);
        }
        if (arrayList2 == null) {
            this.addChange("reset", null, null, true);
        }
    }
}

