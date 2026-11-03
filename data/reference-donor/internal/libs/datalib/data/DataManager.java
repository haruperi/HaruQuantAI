/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.HistoryDataNotAvailableExeption
 *  com.strategyquant.lib.HistoryOHLCData
 *  com.strategyquant.lib.IStopPauseStatus
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.TaskStoppedException
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.lib.constants.SQPaths
 *  com.strategyquant.lib.historyData.HistoryDataChecker
 *  com.strategyquant.lib.historyData.ICryptable
 *  com.strategyquant.lib.hw.OperatingSystem
 *  com.strategyquant.lib.time.SQTimeOld
 *  org.apache.commons.io.FileUtils
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.datalib.data;

import com.strategyquant.datalib.ChartDef;
import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.InstrumentInfo;
import com.strategyquant.datalib.TickEvent;
import com.strategyquant.datalib.TimeframeManager;
import com.strategyquant.datalib.bartype.BarType;
import com.strategyquant.datalib.bartype.BarTypeFactory;
import com.strategyquant.datalib.bartype.BarTypeStatus;
import com.strategyquant.datalib.consts.Precisions;
import com.strategyquant.datalib.data.BatchProgressController;
import com.strategyquant.datalib.data.DataComparator;
import com.strategyquant.datalib.data.DataDb;
import com.strategyquant.datalib.data.DataException;
import com.strategyquant.datalib.data.DataExporter;
import com.strategyquant.datalib.data.DataInfoCache;
import com.strategyquant.datalib.data.SymbolInfo;
import com.strategyquant.datalib.data.io.BinaryDataLoader;
import com.strategyquant.datalib.data.io.IDataLoader;
import com.strategyquant.datalib.data.io.VersatileData;
import com.strategyquant.datalib.data.io.newDataFormat.DataBinWriterNew;
import com.strategyquant.datalib.instrument.InstrumentManager;
import com.strategyquant.datalib.session.Session;
import com.strategyquant.datalib.session.SessionManager;
import com.strategyquant.datalib.session.SessionStatus;
import com.strategyquant.datalib.ticksimulator.DefaultTickSimulator;
import com.strategyquant.lib.HistoryDataNotAvailableExeption;
import com.strategyquant.lib.HistoryOHLCData;
import com.strategyquant.lib.IStopPauseStatus;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.TaskStoppedException;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.lib.constants.SQPaths;
import com.strategyquant.lib.historyData.HistoryDataChecker;
import com.strategyquant.lib.historyData.ICryptable;
import com.strategyquant.lib.hw.OperatingSystem;
import com.strategyquant.lib.time.SQTimeOld;
import java.io.File;
import java.io.IOException;
import java.nio.file.CopyOption;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.attribute.FileAttribute;
import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.Statement;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedList;
import java.util.List;
import org.apache.commons.io.FileUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class DataManager
extends DataDb {
    public static final String SpreadTypePoints = "points";
    public static final String SpreadTypePips = "pips";
    public static final String SpreadTypeReal = "real";
    private static final int BATCH_SIZE = 150;
    public static final String FUTURES_FOLDER = "sq_futures";
    public static final String EQUITY_FOLDER = "sq_equity";
    public static final Logger Log = LoggerFactory.getLogger(DataManager.class);
    private static DataManager instance = null;
    private ArrayList<DataInfo> cachedDataList = new ArrayList();
    private HashMap<String, DataInfo> dataInfoCache = new HashMap();
    private HashMap<String, Boolean> connectionCache = new HashMap();
    private DataComparator dataComparator = new DataComparator();
    private DataInfoCache dataInfoCacheAll = new DataInfoCache();
    private long dataLastTimeUpdated = -1L;
    private List<SymbolInfo> updatedInfos = new LinkedList<SymbolInfo>();
    private HashMap<String, DataInfo> customDataInfoCache = new HashMap();

    public static void init(String string) throws Exception {
        if (instance != null) {
            throw new Exception("DataManager.init() called more than once!");
        }
        instance = new DataManager(string);
        instance.moveDataFromBaseFolder("History");
        if (MainApp.getProduct() != "BACKTESTNODE") {
            DataManager.checkSymbolFiles();
        }
    }

    private DataManager(String string) {
        super(string);
    }

    public static DataManager get() {
        return instance;
    }

    @Override
    public void initDatabase() {
        try {
            String string;
            Class.forName("org.sqlite.JDBC");
            if (!this.tableExists("DATA")) {
                string = "CREATE TABLE DATA (ID INTEGER PRIMARY KEY AUTOINCREMENT,SOURCEDATA_ID INTEGER DEFAULT 0,CONNECTION \tVARCHAR(50)\tNOT NULL, SYMBOL\t\t\tVARCHAR(50)\tNOT NULL, INSTRUMENT \tVARCHAR(20) NOT NULL, TIMEFRAME \t\tVARCHAR(50), TIMEZONE \t\tVARCHAR(100), FILENAME \t\tVARCHAR(100), DATEFROM     \tLONG, DATETO \t\tLONG, DATATYPE \t\tINT, ROWS \t\t\tINT DEFAULT 0, DECIMALS\t\tINT, SOURCE\t\t\tINT)";
                this.sqlCommand(string);
                Log.info("Data table created successfully");
            }
            if (!this.columnExists("DATA", "SECONDS_RECORDS")) {
                string = "ALTER TABLE DATA ADD SECONDS_RECORDS LONG DEFAULT 0";
                this.sqlCommand(string);
            }
            if (!this.columnExists("DATA", "USYMBOL")) {
                this.sqlCommand("ALTER TABLE DATA ADD USYMBOL VARCHAR(50)");
                this.sqlCommand("ALTER TABLE DATA ADD USYMBOLNAME VARCHAR(256)");
            }
            if (!this.columnExists("DATA", "REMOVE_WEEKENDS")) {
                string = "ALTER TABLE DATA ADD REMOVE_WEEKENDS INT DEFAULT 0";
                this.sqlCommand(string);
            }
            if (!this.columnExists("DATA", "SHOW")) {
                string = "ALTER TABLE DATA ADD SHOW INT DEFAULT 1";
                this.sqlCommand(string);
            }
            if (!this.columnExists("DATA", "BASKET_ID")) {
                string = "ALTER TABLE DATA ADD BASKET_ID INT DEFAULT -1";
                this.sqlCommand(string);
            }
            if (!this.columnExists("DATA", "BROKER_ID")) {
                string = "ALTER TABLE DATA ADD BROKER_ID INT DEFAULT -1";
                this.sqlCommand(string);
                String string2 = "UPDATE DATA SET BROKER_ID=(SELECT BROKER_ID FROM INSTRUMENTS WHERE INSTRUMENTS.INSTRUMENT=DATA.INSTRUMENT)";
                this.sqlCommand(string2);
            }
        }
        catch (Exception exception) {
            Log.error("DB error: Cannot create Data table.", (Throwable)exception);
        }
    }

    private static void checkSymbolFiles() {
        try {
            ArrayList<DataInfo> arrayList = DataManager.list();
            for (int i = 0; i < arrayList.size(); ++i) {
                DataInfo dataInfo = arrayList.get(i);
                if (DataManager.isGroupAlias(dataInfo.symbol)) continue;
                String string = DataManager.get()._getDataFileName(dataInfo.connection, dataInfo.symbol, dataInfo.timeframe, "No Session");
                File file = new File(string);
                if (dataInfo.rows <= 0 || Files.exists(file.toPath(), new LinkOption[0])) continue;
                DataManager.updateDataInBatch(dataInfo.connection, dataInfo.symbol, 0L, 0L, 0, 0L, dataInfo.barTimeType, dataInfo.timeframe, null);
                Log.debug("No data files found for symbol '" + dataInfo.symbol + "' (connection '" + dataInfo.connection + "')");
            }
            DataManager.flushUpdatedData();
        }
        catch (Exception exception) {
            Log.error("Cannot check symbol files. ", (Throwable)exception);
        }
    }

    private void moveDataFromBaseFolder(String string) {
        File file = new File(this._getDirectory() + "/" + string);
        if (!Files.exists(file.toPath(), new LinkOption[0])) {
            return;
        }
        File[] fileArray = file.listFiles();
        ArrayList<File> arrayList = new ArrayList<File>();
        if (fileArray.length == 0) {
            return;
        }
        for (File file2 : fileArray) {
            if (file2.isDirectory() || !file2.getName().endsWith(".dat")) continue;
            arrayList.add(file2);
        }
        while (arrayList.size() != 0) {
            File file3 = (File)arrayList.get(0);
            try {
                this.moveFileFromBaseFolder(string, file3);
            }
            catch (Exception exception) {
                exception.printStackTrace();
            }
            arrayList.remove(0);
        }
    }

    private void moveFileFromBaseFolder(String string, File file) throws Exception {
        String string2 = file.getName();
        int n = string2.lastIndexOf(".");
        String string3 = n != -1 ? string2.substring(0, n) : string2;
        int n2 = string2.lastIndexOf("_");
        if (n == -1) {
            throw new Exception("Data file name doesn't have correct format!");
        }
        string3 = string2.substring(0, n2);
        FileUtils.moveFile((File)file, (File)new File(this._getDirectory() + "/" + string + "/" + string3 + "/" + string2));
    }

    private static void deleteFolderExcept(File file, File ... fileArray) {
        if (!Files.exists(file.toPath(), new LinkOption[0])) {
            return;
        }
        File[] fileArray2 = file.listFiles();
        if (fileArray2 != null) {
            for (File file2 : fileArray2) {
                boolean bl = false;
                if (fileArray != null) {
                    for (File file3 : fileArray) {
                        if (!file2.getAbsolutePath().equals(file3.getAbsolutePath())) continue;
                        bl = true;
                        break;
                    }
                }
                if (bl) continue;
                file2.delete();
            }
        }
        file.delete();
    }

    public static ArrayList<DataInfo> list() throws Exception {
        return DataManager.get()._list();
    }

    public static ArrayList<DataInfo> listSafe() throws Exception {
        return DataManager.get()._listSafe();
    }

    public static ArrayList<DataInfo> listForSource(int n) throws Exception {
        return DataManager.get()._listForSource(n);
    }

    public static ArrayList<DataInfo> listCloned(int n) throws Exception {
        return DataManager.get()._listCloned(n);
    }

    public static DataInfo getDataInfo(String string, String string2) {
        String string3 = string + string2;
        if (DataManager.get().customDataInfoCache.containsKey(string3)) {
            return DataManager.get().customDataInfoCache.get(string3);
        }
        return DataManager.get()._getDataInfo(string, string2);
    }

    public static DataInfo getDataInfo(String string, String string2, boolean bl) {
        String string3 = string + string2;
        if (DataManager.get().customDataInfoCache.containsKey(string3)) {
            return DataManager.get().customDataInfoCache.get(string3);
        }
        if (bl) {
            return (DataInfo)DataManager.get().dataInfoCacheAll.get(string3);
        }
        return DataManager.get()._getDataInfo(string, string2);
    }

    public static DataInfo getDataInfo(String string, int n) {
        return DataManager.get()._getDataInfo(string, n);
    }

    public static boolean checkDataExists(String string, String string2) {
        return DataManager.get()._checkDataExists(string, string2);
    }

    public static void addData(String string, String string2, String string3, int n, int n2) throws Exception {
        DataManager.get()._addData(string, string2, string3, n, n2, null, null, -1, -1);
    }

    public static void addData(String string, String string2, String string3, int n, int n2, int n3, int n4) throws Exception {
        DataManager.get()._addData(string, string2, string3, n, n2, null, null, n3, n4);
    }

    public static void addData(String string, String string2, String string3, int n, int n2, String string4, String string5, int n3, int n4) throws Exception {
        DataManager.get()._addData(string, string2, string3, n, n2, string4, string5, n3, n4);
    }

    public static void addData(String string, String string2, String string3, int n, int n2, String string4, String string5) throws Exception {
        DataManager.get()._addData(string, string2, string3, n, n2, string4, string5, -1, -1);
    }

    public static void addDataInBatch(String string, List<DataInfo> list, BatchProgressController batchProgressController) throws Exception {
        DataManager.get()._addDataInBatch(string, list, batchProgressController);
    }

    public static boolean checkConnectionExists(String string) {
        return DataManager.get()._checkConnectionExists(string);
    }

    public static ArrayList<String> getSymbolsForInstrument(String string) throws Exception {
        return DataManager.get()._getSymbolsForInstrument(string);
    }

    public static void clearData(String string, String string2) {
        String string3 = null;
        DataInfo dataInfo = DataManager.getDataInfo(string, string2);
        int n = dataInfo.barTimeType;
        if (dataInfo.source != 1) {
            string3 = dataInfo.timeframe;
        }
        if (dataInfo.source == 5) {
            String string4 = DataManager.getUnadjustedDataFileName(string, string2, string3, "No Session");
            File file = new File(string4);
            try {
                Files.deleteIfExists(file.toPath());
            }
            catch (IOException iOException) {
                Log.error("Unable to delete file " + string4 + ".", (Throwable)iOException);
            }
        }
        DataManager.removeDataFilesWithFolder(string, string2);
        DataManager.updateData(string, string2, 0L, 0L, 0, 0L, n, string3, null);
    }

    public static void clearDataInBatch(String string, String string2) {
        String string3 = null;
        if (DataManager.isLimited(string2)) {
            return;
        }
        DataInfo dataInfo = DataManager.getDataInfo(string, string2);
        int n = dataInfo.barTimeType;
        if (dataInfo.source != 1) {
            string3 = dataInfo.timeframe;
        }
        if (dataInfo.source == 5) {
            String string4 = DataManager.getUnadjustedDataFileName(string, string2, string3, "No Session");
            File file = new File(string4);
            try {
                Files.deleteIfExists(file.toPath());
            }
            catch (IOException iOException) {
                Log.error("Unable to delete file " + string4 + ".", (Throwable)iOException);
            }
        }
        DataManager.removeDataFilesWithFolder(string, string2);
        DataManager.updateDataInBatch(string, string2, 0L, 0L, 0, 0L, n, string3, null);
    }

    public static void deleteData(String string, String string2) {
        DataManager.get()._deleteData(string, string2);
    }

    public static void deleteForGroup(String string, String string2, int n) {
        DataManager.get()._deleteForGroup(string, string2, n);
    }

    private void _deleteForGroup(String string, String string2, int n) {
        try {
            String string3 = "DELETE FROM DATA WHERE BASKET_ID=" + n;
            this.sqlCommand(string3);
            DataInfo dataInfo = this.dataInfoCache.remove(this.getCacheKey(string, string2));
            if (dataInfo != null) {
                this.cachedDataList.remove(dataInfo);
            }
            this.dataLastTimeUpdated = System.currentTimeMillis();
        }
        catch (Exception exception) {
            Log.error("Data DB error:", (Throwable)exception);
        }
    }

    public static void deleteDataInBatch(String[] stringArray, String[] stringArray2, BatchProgressController batchProgressController) throws ClassNotFoundException {
        DataManager.get()._deleteDataInBatch(stringArray, stringArray2, batchProgressController);
    }

    public static void updateInstrument(String string, String string2, String string3) {
        DataManager.get()._updateInstrument(string, string2, string3);
    }

    public static void updateInstrumentSwap(String string, String string2, String string3, String string4) {
        DataManager.get()._updateInstrumentSwap(string, string2, string3, string4);
    }

    public static void updateSecondsRecords(String string, String string2, long l) {
        DataManager.get()._updateSecondsRecords(string, string2, l);
    }

    public static void updateData(String string, String string2, long l, long l2, int n, long l3, int n2, String string3, String string4) {
        DataManager.updateData(string, string2, l, l2, n, l3, n2, string3, string4, -1, false);
    }

    public static void updateDataInBatch(String string, String string2, long l, long l2, int n, long l3, int n2, String string3, String string4) {
        DataManager.updateDataInBatch(string, string2, l, l2, n, l3, n2, string3, string4, -1, false);
    }

    public static void updateData(String string, String string2, long l, long l2, int n, long l3, int n2, String string3, String string4, int n3, boolean bl) {
        DataManager.get()._updateData(string, string2, l, l2, n, l3, n2, string3, string4, n3, bl);
    }

    public static void updateDataInBatch(String string, String string2, long l, long l2, int n, long l3, int n2, String string3, String string4, int n3, boolean bl) {
        DataManager.get()._updateDataInBatch(string, string2, l, l2, n, l3, n2, string3, string4, n3, bl);
    }

    public static void flushUpdatedData() {
        DataManager.get()._flushUpdatedData();
    }

    public static void updateTimeframe(String string, String string2, String string3) {
        DataManager.get()._updateTimeframe(string, string2, string3);
    }

    public static void updateBroker(String string, String string2, int n) {
        DataManager.get()._updateBroker(string, string2, n);
    }

    public static void renameData(String string, String string2, String string3) {
        DataManager.get()._renameData(string, string2, string3);
    }

    public static String renameUnderlayingData(String string, String string2, String string3) {
        return DataManager.get()._renameUnderlayingData(string, string2, string3);
    }

    public static void showData(String string, String string2, boolean bl) {
        DataManager.get()._showData(string, string2, bl);
    }

    public static void updateUnderlyingSymbolName(String string, String string2, String string3) {
        DataManager.get()._updateUnderlyingSymbolName(string, string2, string3);
    }

    public static String getDataFileName(String string, String string2, String string3, String string4) {
        return DataManager.get()._getDataFileName(string, string2, string3, string4);
    }

    public static String getUnadjustedDataFileName(String string, String string2, String string3, String string4) {
        return DataManager.get()._getUnadjustedDataFileName(string, string2, string3, string4);
    }

    public static String getDataFileName(String string, String string2, String string3, String string4, DataInfo dataInfo) {
        return DataManager.get()._getDataFileName(string, string2, string3, string4, dataInfo);
    }

    public static String getUnadjustedDataFileName(String string, String string2, String string3, String string4, DataInfo dataInfo) {
        return DataManager.get()._getUnadjustedDataFileName(string, string2, string3, string4, dataInfo);
    }

    public static synchronized IDataLoader getDataLoader(ChartDef chartDef, int n, IStopPauseStatus iStopPauseStatus) throws Exception {
        return DataManager.get()._getDataLoader(chartDef, n, iStopPauseStatus);
    }

    public static synchronized IDataLoader getDataLoader(ChartDef chartDef, int n) throws Exception {
        return DataManager.get()._getDataLoader(chartDef, n, null);
    }

    private synchronized ArrayList<DataInfo> _listSafe() throws Exception {
        return new ArrayList<DataInfo>(this._list());
    }

    private synchronized ArrayList<DataInfo> _list() throws Exception {
        if (!this.cachedDataList.isEmpty()) {
            return this.cachedDataList;
        }
        ArrayList<DataInfo> arrayList = new ArrayList<DataInfo>();
        Connection connection = null;
        Statement statement = null;
        ResultSet resultSet = null;
        connection = this.getConnection();
        statement = connection.createStatement();
        resultSet = statement.executeQuery("SELECT count(*) FROM DATA");
        if (resultSet.next()) {
            int n = resultSet.getInt(1);
            arrayList.ensureCapacity(n);
            this.cachedDataList.ensureCapacity(n);
        }
        statement = connection.createStatement();
        resultSet = statement.executeQuery("SELECT * FROM DATA");
        while (resultSet.next()) {
            DataInfo dataInfo = new DataInfo();
            dataInfo.id = resultSet.getInt("ID");
            dataInfo.connection = resultSet.getString("CONNECTION");
            dataInfo.symbol = resultSet.getString("SYMBOL");
            dataInfo.instrument = resultSet.getString("INSTRUMENT");
            dataInfo.timeframe = resultSet.getString("TIMEFRAME");
            dataInfo.timezone = resultSet.getString("TIMEZONE");
            dataInfo.filename = resultSet.getString("FILENAME");
            dataInfo.dateFrom = resultSet.getLong("DATEFROM");
            dataInfo.dateTo = resultSet.getLong("DATETO");
            dataInfo.rows = resultSet.getInt("ROWS");
            dataInfo.secondsRecords = resultSet.getLong("SECONDS_RECORDS");
            dataInfo.barTimeType = resultSet.getInt("DATATYPE");
            dataInfo.decimals = resultSet.getInt("DECIMALS");
            dataInfo.source = resultSet.getInt("SOURCE");
            dataInfo.sourceDataId = resultSet.getInt("SOURCEDATA_ID");
            dataInfo.uSymbol = resultSet.getString("USYMBOL");
            dataInfo.uSymbolName = resultSet.getString("USYMBOLNAME");
            dataInfo.show = resultSet.getBoolean("SHOW");
            dataInfo.basketId = resultSet.getInt("BASKET_ID");
            dataInfo.brokerId = resultSet.getInt("BROKER_ID");
            dataInfo.fileHash = this.getFileHash(dataInfo);
            dataInfo.timeframe = dataInfo.timeframe == null || dataInfo.timeframe.equals("null") ? null : dataInfo.timeframe;
            try {
                dataInfo.symbolInfo = InstrumentManager.getInstrumentInfo(dataInfo.instrument);
            }
            catch (Exception exception) {
                Log.error("Error while loading symbolInfo. ", (Throwable)exception);
            }
            arrayList.add(dataInfo);
            this.cachedDataList.add(dataInfo);
            String string = resultSet.getString("CONNECTION");
            String string2 = string + dataInfo.symbol;
            this.dataInfoCache.put(string2, dataInfo);
        }
        this.close(resultSet);
        this.close(statement);
        this.close(connection);
        this.cachedDataList.sort(this.dataComparator);
        arrayList.sort(this.dataComparator);
        return arrayList;
    }

    private synchronized ArrayList<DataInfo> _listForSource(int n) throws Exception {
        ArrayList<DataInfo> arrayList = new ArrayList<DataInfo>();
        Connection connection = null;
        Statement statement = null;
        ResultSet resultSet = null;
        connection = this.getConnection();
        statement = connection.createStatement();
        resultSet = statement.executeQuery("SELECT * FROM DATA where source=" + n);
        while (resultSet.next()) {
            DataInfo dataInfo = new DataInfo();
            dataInfo.id = resultSet.getInt("ID");
            dataInfo.connection = resultSet.getString("CONNECTION");
            dataInfo.symbol = resultSet.getString("SYMBOL");
            dataInfo.instrument = resultSet.getString("INSTRUMENT");
            dataInfo.timeframe = resultSet.getString("TIMEFRAME");
            dataInfo.timezone = resultSet.getString("TIMEZONE");
            dataInfo.filename = resultSet.getString("FILENAME");
            dataInfo.dateFrom = resultSet.getLong("DATEFROM");
            dataInfo.dateTo = resultSet.getLong("DATETO");
            dataInfo.rows = resultSet.getInt("ROWS");
            dataInfo.secondsRecords = resultSet.getLong("SECONDS_RECORDS");
            dataInfo.barTimeType = resultSet.getInt("DATATYPE");
            dataInfo.decimals = resultSet.getInt("DECIMALS");
            dataInfo.source = resultSet.getInt("SOURCE");
            dataInfo.sourceDataId = resultSet.getInt("SOURCEDATA_ID");
            dataInfo.uSymbol = resultSet.getString("USYMBOL");
            dataInfo.uSymbolName = resultSet.getString("USYMBOLNAME");
            dataInfo.show = resultSet.getBoolean("SHOW");
            dataInfo.basketId = resultSet.getInt("BASKET_ID");
            dataInfo.brokerId = resultSet.getInt("BROKER_ID");
            dataInfo.fileHash = this.getFileHash(dataInfo);
            dataInfo.timeframe = dataInfo.timeframe == null || dataInfo.timeframe.equals("null") ? null : dataInfo.timeframe;
            try {
                dataInfo.symbolInfo = InstrumentManager.getInstrumentInfo(dataInfo.instrument);
            }
            catch (Exception exception) {
                Log.error("Error while loading symbolInfo. ", (Throwable)exception);
            }
            arrayList.add(dataInfo);
        }
        this.close(resultSet);
        this.close(statement);
        this.close(connection);
        return arrayList;
    }

    private synchronized ArrayList<DataInfo> _listCloned(int n) throws Exception {
        ArrayList<DataInfo> arrayList = new ArrayList<DataInfo>();
        Connection connection = null;
        Statement statement = null;
        ResultSet resultSet = null;
        connection = this.getConnection();
        statement = connection.createStatement();
        resultSet = statement.executeQuery("SELECT * FROM DATA WHERE SOURCEDATA_ID=" + n);
        while (resultSet.next()) {
            DataInfo dataInfo = new DataInfo();
            dataInfo.id = resultSet.getInt("ID");
            dataInfo.connection = resultSet.getString("CONNECTION");
            dataInfo.symbol = resultSet.getString("SYMBOL");
            dataInfo.instrument = resultSet.getString("INSTRUMENT");
            dataInfo.timeframe = resultSet.getString("TIMEFRAME");
            dataInfo.timezone = resultSet.getString("TIMEZONE");
            dataInfo.filename = resultSet.getString("FILENAME");
            dataInfo.dateFrom = resultSet.getLong("DATEFROM");
            dataInfo.dateTo = resultSet.getLong("DATETO");
            dataInfo.rows = resultSet.getInt("ROWS");
            dataInfo.secondsRecords = resultSet.getLong("SECONDS_RECORDS");
            dataInfo.barTimeType = resultSet.getInt("DATATYPE");
            dataInfo.decimals = resultSet.getInt("DECIMALS");
            dataInfo.source = resultSet.getInt("SOURCE");
            dataInfo.sourceDataId = resultSet.getInt("SOURCEDATA_ID");
            dataInfo.uSymbol = resultSet.getString("USYMBOL");
            dataInfo.uSymbolName = resultSet.getString("USYMBOLNAME");
            dataInfo.removeWeekends = resultSet.getBoolean("REMOVE_WEEKENDS");
            dataInfo.show = resultSet.getBoolean("SHOW");
            dataInfo.basketId = resultSet.getInt("BASKET_ID");
            dataInfo.brokerId = resultSet.getInt("BROKER_ID");
            dataInfo.fileHash = this.getFileHash(dataInfo);
            dataInfo.timeframe = dataInfo.timeframe == null || dataInfo.timeframe.equals("null") ? null : dataInfo.timeframe;
            try {
                dataInfo.symbolInfo = InstrumentManager.getInstrumentInfo(dataInfo.instrument);
            }
            catch (Exception exception) {
                Log.error("Error while loading symbolInfo. ", (Throwable)exception);
            }
            arrayList.add(dataInfo);
        }
        this.close(resultSet);
        this.close(statement);
        this.close(connection);
        return arrayList;
    }

    private String _getDataFileName(String string, String string2, String string3, String string4) {
        String string5 = DataManager.getSymbolFolderName(this._getDirectory(), string, string2);
        if (string4 == null || string4.equals("No Session")) {
            String string6 = string2 + "_" + string3 + ".dat";
            return string5 + "/" + DataManager.fixFilename(string6);
        }
        String string7 = string2 + "_" + string3 + "_" + string4 + ".dat";
        return string5 + "/" + DataManager.fixFilename(string7);
    }

    private String _getUnadjustedDataFileName(String string, String string2, String string3, String string4) {
        String string5 = DataManager.getSymbolFolderName(this._getDirectory(), string, string2);
        if (string4 == null || string4.equals("No Session")) {
            String string6 = string2 + "unadjusted_" + string3 + ".dat";
            return string5 + "/" + DataManager.fixFilename(string6);
        }
        String string7 = string2 + "unadjusted_" + string3 + "_" + string4 + ".dat";
        return string5 + "/" + DataManager.fixFilename(string7);
    }

    private String _getDataFileName(String string, String string2, String string3, String string4, DataInfo dataInfo) {
        String string5 = DataManager.getSymbolFolderName(this._getDirectory(), string, string2, dataInfo);
        if (string4 == null || string4.equals("No Session")) {
            String string6 = string2 + "_" + string3 + ".dat";
            return string5 + "/" + DataManager.fixFilename(string6);
        }
        String string7 = string2 + "_" + string3 + "_" + string4 + ".dat";
        return string5 + "/" + DataManager.fixFilename(string7);
    }

    private String _getUnadjustedDataFileName(String string, String string2, String string3, String string4, DataInfo dataInfo) {
        String string5 = DataManager.getSymbolFolderName(this._getDirectory(), string, string2, dataInfo);
        if (string4 == null || string4.equals("No Session")) {
            String string6 = string2 + "unadjusted_" + string3 + ".dat";
            return string5 + "/" + DataManager.fixFilename(string6);
        }
        String string7 = string2 + "unadjusted_" + string3 + "_" + string4 + ".dat";
        return string5 + "/" + DataManager.fixFilename(string7);
    }

    public static String fixFilename(String string) {
        String string2 = string.replaceAll("[^a-zA-Z0-9\\.\\-@#\\(\\)]", "_");
        if (string2.equalsIgnoreCase("CON") || string2.startsWith("CON.") || string2.equalsIgnoreCase("PRN") || string2.startsWith("PRN.") || string2.equalsIgnoreCase("AUX") || string2.startsWith("AUX.")) {
            string2 = "_" + string2;
        }
        return string2;
    }

    public boolean _isFilenameValid(String string) {
        File file = new File(string);
        try {
            file.getCanonicalPath();
            return true;
        }
        catch (IOException iOException) {
            return false;
        }
    }

    public void _updateInstrumentSwap(String string, String string2, String string3, String string4) {
        try {
            DataInfo dataInfo = this.getRecordFromCache(string, string2);
            InstrumentInfo instrumentInfo = InstrumentManager.getInstrumentInfo(string3);
            instrumentInfo.swap = string4;
            InstrumentManager.updateInstrument(instrumentInfo);
            dataInfo.instrument = string3;
            dataInfo.symbolInfo = InstrumentManager.getInstrumentInfo(string3);
            this.updateCachedDataList(dataInfo);
            this._clearHistoryFolder(string, string2);
        }
        catch (Exception exception) {
            Log.error("Data DB error:", (Throwable)exception);
        }
    }

    public void _updateInstrument(String string, String string2, String string3) {
        try {
            String string4 = "UPDATE DATA SET INSTRUMENT='" + string3 + "'";
            string4 = string4 + " WHERE CONNECTION='" + string + "' AND SYMBOL='" + string2 + "'";
            this.sqlCommand(string4);
            DataInfo dataInfo = this.getRecordFromCache(string, string2);
            dataInfo.instrument = string3;
            dataInfo.symbolInfo = InstrumentManager.getInstrumentInfo(string3);
            this.updateCachedDataList(dataInfo);
            this._clearHistoryFolder(string, string2);
        }
        catch (Exception exception) {
            Log.error("Data DB error:", (Throwable)exception);
        }
    }

    public void _updateSecondsRecords(String string, String string2, long l) {
        try {
            String string3 = "UPDATE DATA SET SECONDS_RECORDS=" + l + "";
            string3 = string3 + " WHERE CONNECTION='" + string + "' AND SYMBOL='" + string2 + "'";
            this.sqlCommand(string3);
            DataInfo dataInfo = this.getRecordFromCache(string, string2);
            dataInfo.secondsRecords = l;
            this.updateCachedDataList(dataInfo);
            this._clearHistoryFolder(string, string2);
        }
        catch (Exception exception) {
            Log.error("Data DB error:", (Throwable)exception);
        }
    }

    private DataInfo getRecordFromCache(String string, String string2) {
        String string3 = this.getCacheKey(string, string2);
        return this.dataInfoCache.get(string3);
    }

    private void updateCachedDataList(DataInfo dataInfo) {
        for (int i = 0; i < this.cachedDataList.size(); ++i) {
            if (!this.cachedDataList.get((int)i).symbol.equals(dataInfo.symbol)) continue;
            this.cachedDataList.set(i, dataInfo);
        }
        this.dataInfoCache.put(this.getCacheKey(dataInfo.connection, dataInfo.symbol), dataInfo);
        this.dataLastTimeUpdated = System.currentTimeMillis();
    }

    private void updateCachedDataList(DataInfo dataInfo, String string) {
        for (int i = 0; i < this.cachedDataList.size(); ++i) {
            if (!this.cachedDataList.get((int)i).symbol.equals(string)) continue;
            this.cachedDataList.set(i, dataInfo);
        }
        this.dataInfoCache.put(this.getCacheKey(dataInfo.connection, dataInfo.symbol), dataInfo);
        this.dataLastTimeUpdated = System.currentTimeMillis();
    }

    public void removeRecordFromCacheForInstrument(String string) {
        ArrayList<String> arrayList = new ArrayList<String>();
        for (String string2 : this.dataInfoCache.keySet()) {
            DataInfo dataInfo = this.dataInfoCache.get(string2);
            if (dataInfo == null || dataInfo.instrument == null || !dataInfo.instrument.equals(string)) continue;
            arrayList.add(string2);
        }
        for (int i = 0; i < arrayList.size(); ++i) {
            this.dataInfoCache.remove(arrayList.get(i));
        }
    }

    private synchronized void _updateDataInBatch(String string, String string2, long l, long l2, int n, long l3, int n2, String string3, String string4, int n3, boolean bl) {
        SymbolInfo symbolInfo = new SymbolInfo();
        symbolInfo.connection = string;
        symbolInfo.symbol = string2;
        symbolInfo.dateFrom = l;
        symbolInfo.dateTo = l2;
        symbolInfo.rows = n;
        symbolInfo.secondsRecords = l3;
        symbolInfo.timeframe = string3;
        symbolInfo.barType = n2;
        symbolInfo.timezone = string4;
        symbolInfo.sourceDataId = n3;
        symbolInfo.removeWeekends = bl;
        this.updatedInfos.add(symbolInfo);
        DataInfo dataInfo = this.getRecordFromCache(string, string2);
        dataInfo.dateFrom = l;
        dataInfo.dateTo = l2;
        dataInfo.rows = n;
        dataInfo.secondsRecords = l3;
        dataInfo.timeframe = string3;
        dataInfo.barTimeType = n2;
        dataInfo.fileHash = this.getFileHash(dataInfo);
        if (string4 != null) {
            dataInfo.timezone = string4;
        }
        if (n3 > 0) {
            dataInfo.sourceDataId = n3;
            dataInfo.removeWeekends = bl;
        }
        if (this.updatedInfos.size() % 150 == 0) {
            this._flushUpdatedData();
        }
    }

    private synchronized void _flushUpdatedData() {
        if (this.updatedInfos.isEmpty()) {
            return;
        }
        try {
            Connection connection = this.getConnection();
            connection.setAutoCommit(false);
            for (SymbolInfo symbolInfo : this.updatedInfos) {
                String string = "UPDATE DATA SET DATEFROM='" + symbolInfo.dateFrom + "',DATETO='" + symbolInfo.dateTo + "',ROWS=" + symbolInfo.rows + ",SECONDS_RECORDS=" + symbolInfo.secondsRecords + ",DATATYPE=" + symbolInfo.barType + ",TIMEFRAME='" + symbolInfo.timeframe + "'";
                if (symbolInfo.timezone != null) {
                    string = string + ",TIMEZONE='" + symbolInfo.timezone + "'";
                }
                if (symbolInfo.sourceDataId > 0) {
                    string = string + ",SOURCEDATA_ID=" + symbolInfo.sourceDataId + ", REMOVE_WEEKENDS=" + (symbolInfo.removeWeekends ? 1 : 0);
                }
                string = string + " WHERE CONNECTION='" + symbolInfo.connection + "' AND SYMBOL='" + symbolInfo.symbol + "'";
                Statement statement = connection.createStatement();
                statement.executeUpdate(string);
                statement.close();
                this._clearHistoryFolder(symbolInfo.connection, symbolInfo.symbol);
            }
            connection.commit();
            connection.close();
        }
        catch (Exception exception) {
            Log.error("Data DB error:", (Throwable)exception);
        }
        this.dataLastTimeUpdated = System.currentTimeMillis();
        this.updatedInfos.clear();
    }

    public void _updateData(String string, String string2, long l, long l2, int n, long l3, int n2, String string3, String string4, int n3, boolean bl) {
        try {
            DataInfo dataInfo = this.getRecordFromCache(string, string2);
            String string5 = "UPDATE DATA SET DATEFROM='" + l + "',DATETO='" + l2 + "',ROWS=" + n + ",SECONDS_RECORDS=" + l3 + ",DATATYPE=" + n2 + ",TIMEFRAME='" + string3 + "'";
            if (string4 != null) {
                string5 = string5 + ",TIMEZONE='" + string4 + "'";
                dataInfo.timezone = string4;
            }
            if (n3 > 0) {
                string5 = string5 + ",SOURCEDATA_ID=" + n3 + ", REMOVE_WEEKENDS=" + (bl ? 1 : 0);
                dataInfo.sourceDataId = n3;
                dataInfo.removeWeekends = bl;
            }
            string5 = string5 + " WHERE CONNECTION='" + string + "' AND SYMBOL='" + string2 + "'";
            this.sqlCommand(string5);
            dataInfo.dateFrom = l;
            dataInfo.dateTo = l2;
            dataInfo.rows = n;
            dataInfo.secondsRecords = l3;
            dataInfo.timeframe = string3;
            dataInfo.barTimeType = n2;
            dataInfo.fileHash = this.getFileHash(dataInfo);
            this.updateCachedDataList(dataInfo);
            this._clearHistoryFolder(string, string2);
        }
        catch (Exception exception) {
            Log.error("Data DB error:", (Throwable)exception);
        }
    }

    private void _updateBroker(String string, String string2, int n) {
        try {
            String string3 = "UPDATE DATA SET BROKER_ID='" + n + "'";
            string3 = string3 + " WHERE CONNECTION='" + string + "' AND SYMBOL='" + string2 + "'";
            this.sqlCommand(string3);
            String string4 = string + string2;
            DataInfo dataInfo = this.dataInfoCache.get(string4);
            dataInfo.brokerId = n;
            this.updateCachedDataList(dataInfo);
            this._clearHistoryFolder(string, string2);
        }
        catch (Exception exception) {
            Log.error("Data DB error:", (Throwable)exception);
        }
    }

    private void _updateTimeframe(String string, String string2, String string3) {
        try {
            String string4 = "UPDATE DATA SET TIMEFRAME='" + string3 + "'";
            string4 = string4 + " WHERE CONNECTION='" + string + "' AND SYMBOL='" + string2 + "'";
            this.sqlCommand(string4);
            String string5 = string + string2;
            DataInfo dataInfo = this.dataInfoCache.get(string5);
            dataInfo.timeframe = string3;
            this.updateCachedDataList(dataInfo);
            this._clearHistoryFolder(string, string2);
        }
        catch (Exception exception) {
            Log.error("Data DB error:", (Throwable)exception);
        }
    }

    private void _updateTimezone(String string, String string2, String string3) {
        try {
            String string4 = "UPDATE DATA SET TIMEZONE='" + string3 + "'";
            string4 = string4 + " WHERE CONNECTION='" + string + "' AND SYMBOL='" + string2 + "'";
            this.sqlCommand(string4);
            String string5 = string + string2;
            DataInfo dataInfo = this.dataInfoCache.get(string5);
            dataInfo.timezone = string3;
            this.updateCachedDataList(dataInfo);
            this._clearHistoryFolder(string, string2);
        }
        catch (Exception exception) {
            Log.error("Data DB error:", (Throwable)exception);
        }
    }

    private void _clearHistoryFolder(String string, String string2) {
        String string3 = DataManager.getSymbolFolderName(this._getDirectory(), string, string2);
        File file = new File(string3);
        if (!Files.exists(file.toPath(), new LinkOption[0])) {
            return;
        }
        DataInfo dataInfo = this._getDataInfo(string, string2);
        if (dataInfo != null) {
            File file2 = new File(this._getDataFileName(string, string2, dataInfo.timeframe, "No Session"));
            File file3 = new File(this._getUnadjustedDataFileName(string, string2, dataInfo.timeframe, "No Session"));
            File file4 = new File(DataManager.getTempFileName(file2.getAbsolutePath()));
            DataManager.deleteFolderExcept(file, file2, file3, file4);
        }
    }

    public synchronized void _renameData(String string, String string2, String string3) {
        try {
            boolean bl;
            if (string2.equals(string3)) {
                throw new RuntimeException("Rename failed - original and new name are the same.");
            }
            boolean bl2 = bl = !string2.equals(string3) && string2.equalsIgnoreCase(string3);
            if (!bl || !new OperatingSystem().isWindows()) {
                DataManager.renameDataFiles(string, string2, string3);
            }
            String string4 = "UPDATE DATA SET SYMBOL='" + string3 + "' WHERE CONNECTION='" + string + "' AND SYMBOL='" + string2 + "'";
            this.sqlCommand(string4);
            DataInfo dataInfo = this.getRecordFromCache(string, string2);
            dataInfo.symbol = string3;
            String string5 = this.getCacheKey(string, string2);
            this.dataInfoCache.remove(string5);
            String string6 = this.getCacheKey(string, string3);
            this.dataInfoCache.put(string6, dataInfo);
            this.updateCachedDataList(dataInfo, string2);
        }
        catch (Exception exception) {
            Log.error("Data DB error:", (Throwable)exception);
        }
    }

    public synchronized String _renameUnderlayingData(String string, String string2, String string3) {
        try {
            if (string2.equals(string3)) {
                throw new RuntimeException("Rename failed - original and new name are the same.");
            }
            String string4 = "UPDATE DATA SET USYMBOL='" + string3 + "' WHERE CONNECTION='" + string + "' AND SYMBOL='" + string2 + "'";
            DataInfo dataInfo = this.getRecordFromCache(string, string2);
            dataInfo.uSymbol = string3;
            this.sqlCommand(string4);
            String string5 = string3;
            while (DataManager.checkDataExists(string, string5)) {
                string5 = DataManager.generateName(string5);
            }
            this._renameData(string, string2, string5);
            return string5;
        }
        catch (Exception exception) {
            Log.error("Data DB error:", (Throwable)exception);
            return null;
        }
    }

    private String getCacheKey(String string, String string2) {
        return string + string2;
    }

    private synchronized void _deleteData(String string, String string2) {
        try {
            String string3 = "DELETE FROM DATA WHERE CONNECTION='" + string + "' AND SYMBOL='" + string2 + "'";
            this.sqlCommand(string3);
            DataManager.removeDataFilesWithFolder(string, string2);
            DataInfo dataInfo = this.dataInfoCache.remove(this.getCacheKey(string, string2));
            if (dataInfo != null) {
                this.cachedDataList.remove(dataInfo);
            }
            this.dataLastTimeUpdated = System.currentTimeMillis();
            this._clearHistoryFolder(string, string2);
        }
        catch (Exception exception) {
            Log.error("Data DB error:", (Throwable)exception);
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private synchronized void _deleteDataInBatch(String[] stringArray, String[] stringArray2, BatchProgressController batchProgressController) throws ClassNotFoundException {
        Class.forName("org.sqlite.JDBC");
        Connection connection = null;
        try {
            connection = this.getConnection();
            connection.setAutoCommit(false);
            int n = stringArray.length;
            int n2 = 0;
            for (int i = 0; i < stringArray.length; ++i) {
                String string = stringArray[i];
                String string2 = stringArray2[i];
                String string3 = "DELETE FROM DATA WHERE CONNECTION='" + string + "' AND SYMBOL='" + string2 + "'";
                try (Object object = connection.createStatement();){
                    object.executeUpdate(string3);
                }
                try {
                    DataManager.removeDataFilesWithFolder(string, string2);
                    this._clearHistoryFolder(string, string2);
                }
                catch (Exception exception) {
                    Log.error("Error while deleting data on filesystem for symbol: " + string2, (Throwable)exception);
                }
                object = this.dataInfoCache.remove(this.getCacheKey(string, string2));
                if (object != null) {
                    this.cachedDataList.remove(object);
                }
                ++n2;
                if (batchProgressController == null) continue;
                if (batchProgressController.isCancel()) break;
                batchProgressController.updateProgress(n2, n, string2);
            }
            this.dataLastTimeUpdated = System.currentTimeMillis();
            connection.commit();
        }
        catch (Exception exception) {
            Log.error("Data DB error:", (Throwable)exception);
        }
        finally {
            this.close(connection);
        }
        if (batchProgressController != null) {
            batchProgressController.finished();
        }
    }

    public static boolean isLimited(String string) {
        return string.endsWith("_limited") || string.endsWith("_limited.D");
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private synchronized boolean _checkConnectionExists(String string) {
        if (this.connectionCache.containsKey(string)) {
            return this.connectionCache.get(string);
        }
        Connection connection = null;
        try {
            connection = this.getConnection();
            boolean bl = this.sqlCheckRecordExists(connection, "SELECT * FROM DATA WHERE CONNECTION='" + string + "'");
            this.connectionCache.put(string, bl);
            boolean bl2 = bl;
            return bl2;
        }
        catch (Exception exception) {
            Log.error("DB Exception", (Throwable)exception);
            boolean bl = false;
            return bl;
        }
        finally {
            this.close(connection);
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     * Enabled aggressive block sorting
     * Enabled unnecessary exception pruning
     * Enabled aggressive exception aggregation
     */
    private synchronized DataInfo _getDataInfo(String string, String string2) {
        ResultSet resultSet;
        Statement statement;
        Connection connection;
        block11: {
            DataInfo dataInfo;
            block10: {
                String string3 = string + string2;
                if (this.dataInfoCache.containsKey(string3)) {
                    return this.dataInfoCache.get(string3);
                }
                connection = null;
                statement = null;
                resultSet = null;
                try {
                    connection = this.getConnection();
                    if (!this._checkDataExists(connection, string, string2)) {
                        DataInfo dataInfo2 = null;
                        return dataInfo2;
                    }
                    String string4 = "SELECT * FROM DATA WHERE SYMBOL='" + string2 + "'";
                    if (string != null) {
                        string4 = string4 + "AND CONNECTION='" + string + "'";
                    }
                    if ((resultSet = (statement = connection.createStatement()).executeQuery(string4)).next()) {
                        DataInfo dataInfo3 = this._dbResultSetToDataInfo(resultSet);
                        this.dataInfoCache.put(string3, dataInfo3);
                        dataInfo = dataInfo3;
                        this.close(resultSet);
                        break block10;
                    }
                    this.close(resultSet);
                    break block11;
                }
                catch (Exception exception) {
                    Log.error("DB Exception", (Throwable)exception);
                    DataInfo dataInfo4 = null;
                    return dataInfo4;
                }
            }
            this.close(statement);
            this.close(connection);
            return dataInfo;
        }
        this.close(statement);
        this.close(connection);
        return null;
        finally {
            this.close(resultSet);
            this.close(statement);
            this.close(connection);
        }
    }

    private DataInfo _dbResultSetToDataInfo(ResultSet resultSet) throws Exception {
        DataInfo dataInfo = new DataInfo();
        dataInfo.id = resultSet.getInt("ID");
        dataInfo.sourceDataId = resultSet.getInt("SOURCEDATA_ID");
        dataInfo.connection = resultSet.getString("CONNECTION");
        dataInfo.symbol = resultSet.getString("SYMBOL");
        dataInfo.instrument = resultSet.getString("INSTRUMENT");
        dataInfo.timeframe = resultSet.getString("TIMEFRAME");
        dataInfo.timezone = resultSet.getString("TIMEZONE");
        dataInfo.filename = resultSet.getString("FILENAME");
        dataInfo.dateFrom = resultSet.getLong("DATEFROM");
        dataInfo.dateTo = resultSet.getLong("DATETO");
        dataInfo.rows = resultSet.getInt("ROWS");
        dataInfo.secondsRecords = resultSet.getLong("SECONDS_RECORDS");
        dataInfo.barTimeType = resultSet.getInt("DATATYPE");
        dataInfo.decimals = resultSet.getInt("DECIMALS");
        dataInfo.source = resultSet.getInt("SOURCE");
        dataInfo.timeframe = dataInfo.timeframe == null || dataInfo.timeframe.equals("null") ? null : dataInfo.timeframe;
        dataInfo.symbolInfo = InstrumentManager.getInstrumentInfo(dataInfo.instrument);
        dataInfo.uSymbol = resultSet.getString("USYMBOL");
        dataInfo.uSymbolName = resultSet.getString("USYMBOLNAME");
        dataInfo.removeWeekends = resultSet.getBoolean("REMOVE_WEEKENDS");
        dataInfo.show = resultSet.getBoolean("SHOW");
        dataInfo.basketId = resultSet.getInt("BASKET_ID");
        dataInfo.brokerId = resultSet.getInt("BROKER_ID");
        dataInfo.fileHash = this.getFileHash(dataInfo);
        return dataInfo;
    }

    private long getFileHash(DataInfo dataInfo) {
        if (dataInfo == null) {
            return 0L;
        }
        boolean bl = dataInfo.source == 6;
        boolean bl2 = dataInfo.source == 5;
        String string = DataManager.fixFilename(dataInfo.symbol);
        String string2 = dataInfo.connection;
        if (bl) {
            string2 = dataInfo.connection + "/" + FUTURES_FOLDER + "/" + string.charAt(0);
        } else if (bl2) {
            string2 = dataInfo.connection + "/" + EQUITY_FOLDER + "/" + string.charAt(0);
        }
        String string3 = this._getDirectory() + "/" + string2 + "/" + string;
        String string4 = dataInfo.symbol + "_" + dataInfo.timeframe + ".dat";
        string4 = string3 + "/" + DataManager.fixFilename(string4);
        File file = new File(string4);
        if (file == null || !Files.exists(file.toPath(), new LinkOption[0])) {
            return 0L;
        }
        return file.lastModified() + file.length();
    }

    public synchronized void refreshDataInfoCache() throws Exception {
        if (this.dataInfoCacheAll.lastTimeUpdated > this.dataLastTimeUpdated) {
            return;
        }
        this.dataInfoCacheAll.clear();
        Connection connection = null;
        Statement statement = null;
        ResultSet resultSet = null;
        try {
            String string = "SELECT * FROM DATA";
            connection = this.getConnection();
            statement = connection.createStatement();
            resultSet = statement.executeQuery(string);
            while (resultSet.next()) {
                DataInfo dataInfo = this._dbResultSetToDataInfo(resultSet);
                String string2 = dataInfo.connection + dataInfo.symbol;
                this.dataInfoCacheAll.put(string2, dataInfo);
            }
            this.dataInfoCacheAll.lastTimeUpdated = System.currentTimeMillis();
        }
        catch (Exception exception) {
            try {
                Log.error("DB Exception", (Throwable)exception);
                throw new Exception("DB Exception, failed to load data info - " + exception.getMessage(), exception);
            }
            catch (Throwable throwable) {
                this.close(resultSet);
                this.close(statement);
                this.close(connection);
                throw throwable;
            }
        }
        this.close(resultSet);
        this.close(statement);
        this.close(connection);
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     * Enabled aggressive block sorting
     * Enabled unnecessary exception pruning
     * Enabled aggressive exception aggregation
     */
    private synchronized DataInfo _getDataInfo(String string, int n) {
        ResultSet resultSet;
        Statement statement;
        Connection connection;
        block8: {
            DataInfo dataInfo;
            block7: {
                connection = null;
                statement = null;
                resultSet = null;
                try {
                    connection = this.getConnection();
                    DataInfo dataInfo2 = new DataInfo();
                    String string2 = "SELECT * FROM DATA WHERE ID=" + n;
                    if (string != null) {
                        string2 = string2 + " AND CONNECTION='" + string + "'";
                    }
                    if ((resultSet = (statement = connection.createStatement()).executeQuery(string2)).next()) {
                        dataInfo2.id = resultSet.getInt("ID");
                        dataInfo2.sourceDataId = resultSet.getInt("SOURCEDATA_ID");
                        dataInfo2.connection = resultSet.getString("CONNECTION");
                        dataInfo2.symbol = resultSet.getString("SYMBOL");
                        dataInfo2.instrument = resultSet.getString("INSTRUMENT");
                        dataInfo2.timeframe = resultSet.getString("TIMEFRAME");
                        dataInfo2.timezone = resultSet.getString("TIMEZONE");
                        dataInfo2.filename = resultSet.getString("FILENAME");
                        dataInfo2.dateFrom = resultSet.getLong("DATEFROM");
                        dataInfo2.dateTo = resultSet.getLong("DATETO");
                        dataInfo2.rows = resultSet.getInt("ROWS");
                        dataInfo2.secondsRecords = resultSet.getLong("SECONDS_RECORDS");
                        dataInfo2.barTimeType = resultSet.getInt("DATATYPE");
                        dataInfo2.decimals = resultSet.getInt("DECIMALS");
                        dataInfo2.source = resultSet.getInt("SOURCE");
                        dataInfo2.timeframe = dataInfo2.timeframe == null || dataInfo2.timeframe.equals("null") ? null : dataInfo2.timeframe;
                        dataInfo2.symbolInfo = InstrumentManager.getInstrumentInfo(dataInfo2.instrument);
                        dataInfo2.uSymbol = resultSet.getString("USYMBOL");
                        dataInfo2.uSymbolName = resultSet.getString("USYMBOLNAME");
                        dataInfo2.removeWeekends = resultSet.getBoolean("REMOVE_WEEKENDS");
                        dataInfo2.show = resultSet.getBoolean("SHOW");
                        dataInfo2.basketId = resultSet.getInt("BASKET_ID");
                        dataInfo2.brokerId = resultSet.getInt("BROKER_ID");
                        dataInfo2.fileHash = this.getFileHash(dataInfo2);
                        dataInfo = dataInfo2;
                        this.close(resultSet);
                        break block7;
                    }
                    this.close(resultSet);
                    break block8;
                }
                catch (Exception exception) {
                    Log.error("DB Exception", (Throwable)exception);
                    DataInfo dataInfo3 = null;
                    return dataInfo3;
                }
            }
            this.close(statement);
            this.close(connection);
            return dataInfo;
        }
        this.close(statement);
        this.close(connection);
        return null;
        finally {
            this.close(resultSet);
            this.close(statement);
            this.close(connection);
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private synchronized boolean _checkDataExists(String string, String string2) {
        String string3 = string + string2;
        if (this.dataInfoCache.containsKey(string3)) {
            return true;
        }
        Connection connection = null;
        try {
            connection = this.getConnection();
            boolean bl = this._checkDataExists(connection, string, string2);
            return bl;
        }
        catch (Exception exception) {
            Log.error("DB Exception", (Throwable)exception);
            boolean bl = false;
            return bl;
        }
        finally {
            this.close(connection);
        }
    }

    private boolean _checkDataExists(Connection connection, String string, String string2) {
        String string3 = "SELECT * FROM DATA WHERE SYMBOL='" + string2 + "'";
        if (string != null) {
            string3 = string3 + " AND CONNECTION='" + string + "'";
        }
        return this.sqlCheckRecordExists(connection, string3);
    }

    public void _addDataInBatch(String string, List<DataInfo> list, BatchProgressController batchProgressController) throws Exception {
        Connection connection = null;
        Class.forName("org.sqlite.JDBC");
        try {
            connection = this.getConnection();
            connection.setAutoCommit(false);
            int n = 0;
            int n2 = list.size();
            for (DataInfo dataInfo : list) {
                int n3;
                this.checkSymbolValid(dataInfo.symbol, -1);
                dataInfo.decimals = n3 = InstrumentManager.getInstrumentInfo((String)dataInfo.instrument).decimals;
                String string2 = "INSERT INTO DATA (CONNECTION, TIMEFRAME, TIMEZONE, SYMBOL, INSTRUMENT, DATATYPE, DECIMALS, SOURCE) VALUES ('" + string + "','" + dataInfo.timeframe + "','" + dataInfo.timezone + "','" + dataInfo.symbol + "','" + dataInfo.instrument + "'," + dataInfo.barTimeType + "," + n3 + "," + dataInfo.source + ")";
                if (dataInfo.uSymbol != null) {
                    dataInfo.uSymbolName = dataInfo.uSymbolName.replace("'", "''");
                    string2 = "INSERT INTO DATA (CONNECTION, TIMEFRAME, TIMEZONE, SYMBOL, INSTRUMENT, DATATYPE, DECIMALS, SOURCE, USYMBOL, USYMBOLNAME) VALUES ('" + string + "','" + dataInfo.timeframe + "','" + dataInfo.timezone + "','" + dataInfo.symbol + "','" + dataInfo.instrument + "'," + dataInfo.barTimeType + "," + n3 + "," + dataInfo.source + ",'" + dataInfo.uSymbol + "','" + dataInfo.uSymbolName + "')";
                }
                int n4 = -1;
                try (Object object = connection.createStatement();){
                    object.executeUpdate(string2);
                    ResultSet resultSet = object.getGeneratedKeys();
                    if (resultSet.next()) {
                        n4 = resultSet.getInt(1);
                    }
                }
                dataInfo.id = n4;
                object = new File(this._getDirectory() + "/" + string);
                if (!Files.exists(((File)object).toPath(), new LinkOption[0])) {
                    Files.createDirectory(((File)object).toPath(), new FileAttribute[0]);
                }
                dataInfo.show = true;
                dataInfo.fileHash = this.getFileHash(dataInfo);
                this.dataInfoCache.put(string + dataInfo.symbol, dataInfo);
                this.cachedDataList.add(dataInfo);
                ++n;
                if (batchProgressController == null) continue;
                if (batchProgressController.isCancel()) {
                    batchProgressController.finished();
                    break;
                }
                batchProgressController.updateProgress(n, n2, dataInfo.symbol);
                if (n != n2) continue;
                batchProgressController.finished();
            }
            this.dataLastTimeUpdated = System.currentTimeMillis();
            connection.commit();
        }
        catch (Exception exception) {
            Log.error("DB Exception", (Throwable)exception);
            throw exception;
        }
        finally {
            this.close(connection);
        }
    }

    private void checkSymbolValid(String string, int n) throws Exception {
        if (n != -1 && string.startsWith("[") && string.endsWith("]")) {
            return;
        }
        if (!string.matches("[\\^\\$a-zA-Z0-9_@.:()-]*")) {
            throw new Exception(String.format("Symbol name '%s' cannot contain any special characters except for ._@$^()", string));
        }
    }

    public void _addData(String string, String string2, String string3, int n, int n2, String string4, String string5, int n3, int n4) throws Exception {
        Connection connection = null;
        try {
            connection = this.getConnection();
            this.checkSymbolValid(string2, n3);
            if (this._checkDataExists(connection, string, string2)) {
                return;
            }
            if (!InstrumentManager.checkInstrumentExists(string3)) {
                throw new DataException(3, "Instrument '" + string3 + "' doesn't exists in instruments database !");
            }
            int n5 = InstrumentManager.getInstrumentInfo((String)string3).decimals;
            String string6 = "INSERT INTO DATA (CONNECTION, SYMBOL, INSTRUMENT, DATATYPE, DECIMALS, SOURCE, BASKET_ID, BROKER_ID) VALUES ('" + string + "','" + string2 + "','" + string3 + "'," + n + "," + n5 + "," + n2 + "," + n3 + "," + n4 + ")";
            if (string4 != null) {
                string5 = string5.replace("'", "''");
                string6 = "INSERT INTO DATA (CONNECTION, SYMBOL, INSTRUMENT, DATATYPE, DECIMALS, SOURCE, USYMBOL, USYMBOLNAME, BROKER_ID) VALUES ('" + string + "','" + string2 + "','" + string3 + "'," + n + "," + n5 + "," + n2 + ",'" + string4 + "','" + string5 + "'," + n4 + ")";
            }
            int n6 = this.sqlInsertReturnAutoId(connection, string6);
            File file = new File(this._getDirectory() + "/" + string);
            if (!Files.exists(file.toPath(), new LinkOption[0])) {
                Files.createDirectory(file.toPath(), new FileAttribute[0]);
            }
            DataInfo dataInfo = new DataInfo();
            dataInfo.id = n6;
            dataInfo.connection = string;
            dataInfo.symbol = string2;
            dataInfo.instrument = string3;
            dataInfo.source = n2;
            dataInfo.decimals = n5;
            dataInfo.barTimeType = n;
            dataInfo.uSymbol = string4;
            dataInfo.uSymbolName = string5;
            dataInfo.show = true;
            dataInfo.basketId = n3;
            dataInfo.brokerId = n4;
            try {
                dataInfo.symbolInfo = InstrumentManager.getInstrumentInfo(dataInfo.instrument);
            }
            catch (Exception exception) {
                Log.error("Error while loading symbolInfo. ", (Throwable)exception);
            }
            this.dataInfoCache.put(string + string2, dataInfo);
            this.cachedDataList.add(dataInfo);
            this.dataLastTimeUpdated = System.currentTimeMillis();
        }
        catch (Exception exception) {
            Log.error("DB Exception - error while inserting data " + string2, (Throwable)exception);
            throw exception;
        }
        finally {
            this.close(connection);
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public ArrayList<String> _getSymbolsForInstrument(String string) throws Exception {
        Log.debug("_getSymbolsForInstrument calling DB");
        ArrayList<String> arrayList = new ArrayList<String>();
        Connection connection = null;
        Statement statement = null;
        ResultSet resultSet = null;
        try {
            String string2 = "SELECT SYMBOL FROM DATA WHERE INSTRUMENT='" + string + "'";
            connection = this.getConnection();
            statement = connection.createStatement();
            resultSet = statement.executeQuery(string2);
            while (resultSet.next()) {
                arrayList.add(resultSet.getString(1));
            }
        }
        catch (Exception exception) {
            ArrayList<String> arrayList2;
            try {
                Log.error("DB Exception", (Throwable)exception);
                arrayList2 = null;
            }
            catch (Throwable throwable) {
                this.close(resultSet);
                this.close(statement);
                this.close(connection);
                throw throwable;
            }
            this.close(resultSet);
            this.close(statement);
            this.close(connection);
            return arrayList2;
        }
        this.close(resultSet);
        this.close(statement);
        this.close(connection);
        return arrayList;
    }

    public IDataLoader _getDataLoader(ChartDef chartDef, int n, IStopPauseStatus iStopPauseStatus) throws Exception {
        IDataLoader iDataLoader = this._getSimpleDataLoader(chartDef.getSymbol());
        if (iDataLoader != null) {
            return iDataLoader;
        }
        String string = chartDef.getConnectionName();
        String string2 = chartDef.getSymbol();
        DataInfo dataInfo = this._getDataInfo(string, string2);
        String string3 = this._getTimeframeToLoad(dataInfo.timeframe, chartDef.getTimeframe(), n);
        BarType barType = BarTypeFactory.getBarType(string3, dataInfo.barTimeType);
        String string4 = this._getDataFileName(string, string2, string3, chartDef.getSession());
        if (!this._dataFileExists(string4)) {
            this._computeData(string3, dataInfo, chartDef.getSession(), iStopPauseStatus);
            if (!this._dataFileExists(string4)) {
                throw new DataException(2, "Data file '" + string4 + "' doesn't exist after computation! ");
            }
        }
        int n2 = barType.isTickBar() ? 2 : 1;
        return new BinaryDataLoader(string4, chartDef, n2, dataInfo);
    }

    public static void renameDataFiles(String string, String string2, String string3) throws Exception {
        File file;
        boolean bl;
        DataInfo dataInfo = DataManager.getDataInfo("History", string2);
        boolean bl2 = bl = dataInfo.source == 6 || dataInfo.source == 5;
        if (bl) {
            for (String string4 : TimeframeManager.getTimeframes()) {
                DataManager.get();
                String string5 = DataManager.getDataFileName(string, string2, string4, null);
                String string6 = DataManager.getDataFileName(string, string3, string4, null, dataInfo);
                file = new File(string5);
                if (Files.exists(file.toPath(), new LinkOption[0])) {
                    try {
                        FileUtils.copyFile((File)new File(string5), (File)new File(string6));
                    }
                    catch (Exception exception) {
                        throw new Exception("Failed to copy data file '" + string5 + "' to '" + string6 + "'.");
                    }
                }
                string5 = DataManager.getUnadjustedDataFileName(string, string2, string4, null);
                string6 = DataManager.getUnadjustedDataFileName(string, string3, string4, null, dataInfo);
                file = new File(string5);
                if (!Files.exists(file.toPath(), new LinkOption[0])) continue;
                try {
                    FileUtils.copyFile((File)new File(string5), (File)new File(string6));
                }
                catch (Exception exception) {
                    throw new Exception("Failed to copy unadjusted data file '" + string5 + "' to '" + string6 + "'.");
                }
            }
        } else {
            for (String string7 : TimeframeManager.getTimeframes()) {
                for (Session session : SessionManager.getSessions()) {
                    String string8 = DataManager.getDataFileName(string, string2, string7, session.getSessionName());
                    String string9 = DataManager.getDataFileName(string, string3, string7, session.getSessionName(), dataInfo);
                    file = new File(string8);
                    if (!Files.exists(file.toPath(), new LinkOption[0])) continue;
                    try {
                        FileUtils.copyFile((File)new File(string8), (File)new File(string9));
                    }
                    catch (Exception exception) {
                        throw new Exception("Failed to copy data file '" + string8 + "' to '" + string9 + "'.");
                    }
                }
            }
        }
        file = new File(DataManager.getSymbolFolderName(SQPaths.dataDirPath, string, string2));
        try {
            FileUtils.deleteDirectory((File)file);
        }
        catch (Exception exception) {
            throw new Exception("Failed to delete orig symbol directory '" + file.getAbsolutePath() + "'");
        }
    }

    public static void removeDataFiles(String string, String string2) {
        for (String string3 : TimeframeManager.getTimeframes()) {
            for (Session session : SessionManager.getSessions()) {
                String string4 = DataManager.getDataFileName(string, string2, string3, session.getSessionName());
                File file = new File(string4);
                try {
                    Files.deleteIfExists(file.toPath());
                }
                catch (IOException iOException) {
                    Log.error("Unable to delete file " + string4 + ".", (Throwable)iOException);
                }
                String string5 = DataManager.getUnadjustedDataFileName(string, string2, string3, session.getSessionName());
                File file2 = new File(string5);
                try {
                    Files.deleteIfExists(file2.toPath());
                }
                catch (IOException iOException) {
                    Log.error("Unable to delete file " + string5 + ".", (Throwable)iOException);
                }
            }
        }
    }

    public static void removeDataFilesWithFolder(String string, String string2) {
        File file = new File(DataManager.getSymbolFolderName(SQPaths.dataDirPath, string, string2));
        try {
            DataManager.deleteFolderExcept(file, new File[0]);
        }
        catch (Exception exception) {
            Log.error("Unable to delete file " + file.getAbsolutePath() + ".", (Throwable)exception);
        }
    }

    public static String getSymbolFolderName(String string, String string2, String string3) {
        DataInfo dataInfo = DataManager.getDataInfo(string2, string3);
        if (dataInfo == null) {
            Log.error("Info of symbol {} was not found for connection {}", (Object)string3, (Object)string2);
            throw new IllegalArgumentException("Symbol was not found: " + string3);
        }
        boolean bl = dataInfo.source == 6;
        boolean bl2 = dataInfo.source == 5;
        String string4 = DataManager.fixFilename(string3);
        String string5 = string2;
        if (bl) {
            string5 = string2 + "/" + FUTURES_FOLDER + "/" + string4.charAt(0);
        } else if (bl2) {
            string5 = string2 + "/" + EQUITY_FOLDER + "/" + string4.charAt(0);
        }
        return string + "/" + string5 + "/" + string4;
    }

    public static String getSymbolFolderName(String string, String string2, String string3, DataInfo dataInfo) {
        boolean bl = dataInfo.source == 6;
        boolean bl2 = dataInfo.source == 5;
        String string4 = DataManager.fixFilename(string3);
        String string5 = string2;
        if (bl) {
            string5 = string2 + "/" + FUTURES_FOLDER + "/" + string4.charAt(0);
        } else if (bl2) {
            string5 = string2 + "/" + EQUITY_FOLDER + "/" + string4.charAt(0);
        }
        return string + "/" + string5 + "/" + string4;
    }

    private boolean _dataFileExists(String string) {
        File file = new File(string);
        boolean bl = Files.exists(file.toPath(), new LinkOption[0]);
        Log.debug("Checking if data file exists: " + string + ". Exists : " + (bl ? "Yes" : "No"));
        return bl;
    }

    String _getTimeframeToLoad(String string, String string2, int n) throws Exception {
        BarType barType;
        String string3;
        String string4 = null;
        if (string == null) {
            throw new Exception("Selected symbol has no base timeframe");
        }
        BarType barType2 = BarTypeFactory.getBarType(string2, 1);
        BarType barType3 = BarTypeFactory.getBarType(string, 1);
        String string5 = barType2.checkCanBeComputedFrom(string);
        if (string5 != null) {
            throw new DataException(2, string5);
        }
        if (n == 3 || n == 4) {
            string3 = barType2.getTickTF();
            barType = BarTypeFactory.getBarType(string3, 1);
            string5 = barType.checkCanBeComputedFrom(string);
            if (string5 == null) {
                string4 = string3;
            } else {
                n = 2;
            }
        }
        if (string4 == null && n == 2) {
            string3 = barType2.getBaseTF();
            barType = BarTypeFactory.getBarType(string3, 1);
            string5 = barType.checkCanBeComputedFrom(string);
            if (string5 == null) {
                string4 = string3;
            } else {
                n = 1;
            }
        }
        if (string4 == null && n == 1) {
            string4 = string2;
        }
        if (string4 == null && n == 5) {
            string4 = string.equals("TICK") ? "TICK" : string2;
        }
        Log.debug("Requested timeframe: " + string2 + ", imported data timeframe: " + string + ", precision: " + Precisions.toString(n) + ", real used timeframe: " + string4);
        return string4;
    }

    private IDataLoader _getSimpleDataLoader(String string) {
        if (string.contains("simpletest1:") || string.contains("simpletest2:")) {
            // empty if block
        }
        return null;
    }

    void _computeData(String string, DataInfo dataInfo, String string2) throws Exception {
        this._computeData(string, dataInfo, string2, null);
    }

    void _computeData(String string, DataInfo dataInfo, String string2, IStopPauseStatus iStopPauseStatus) throws Exception {
        String string3;
        Object object;
        String string4;
        Object object2;
        BinaryDataLoader binaryDataLoader;
        BarType barType = BarTypeFactory.getBarType(string, dataInfo.barTimeType);
        Session session = SessionManager.getSession(string2);
        if (session == null) {
            session = SessionManager.getSession("No Session");
        }
        if ((binaryDataLoader = this._getSourceLoader(dataInfo, string2)) == null) {
            return;
        }
        if (string.equals(dataInfo.timeframe) && this._dataFileExists((String)(object2 = this._getDataFileName(string4 = dataInfo.connection, (String)(object = dataInfo.symbol), string3 = dataInfo.timeframe, string2)))) {
            return;
        }
        binaryDataLoader.open();
        boolean bl = binaryDataLoader.isCrypted();
        object = this._getTargetWriter(barType, string, dataInfo, string2, bl);
        ((DataBinWriterNew)object).open();
        boolean bl2 = false;
        bl2 = barType.isTickBar() ? this.processTickDataTarget(binaryDataLoader, (DataBinWriterNew)object, barType, session, iStopPauseStatus) : this.processOHLCDataTarget(binaryDataLoader, (DataBinWriterNew)object, barType, session, iStopPauseStatus);
        ((DataBinWriterNew)object).close();
        binaryDataLoader.close();
        if (!bl2) {
            object2 = new File(((DataBinWriterNew)object).getFileName());
            if (!((File)object2).delete()) {
                Log.error("Cannot delete data file " + ((File)object2).getAbsolutePath());
            }
            throw new TaskStoppedException();
        }
    }

    private boolean processOHLCDataTarget(BinaryDataLoader binaryDataLoader, DataBinWriterNew dataBinWriterNew, BarType barType, Session session, IStopPauseStatus iStopPauseStatus) throws Exception {
        VersatileData versatileData = new VersatileData();
        TickEvent tickEvent = new TickEvent();
        VersatileData versatileData2 = new VersatileData();
        BarTypeStatus barTypeStatus = new BarTypeStatus();
        String string = barType.getTimeframe();
        barTypeStatus.convertingToHigherTF = true;
        barType = barType.clone(barType.getTimeframe());
        DefaultTickSimulator defaultTickSimulator = new DefaultTickSimulator();
        SessionStatus sessionStatus = new SessionStatus();
        session.clearSessionTempData();
        boolean bl = false;
        long l = 0L;
        long l2 = Long.MIN_VALUE;
        int n = 0;
        while (binaryDataLoader.hasNextTick()) {
            if (iStopPauseStatus != null && iStopPauseStatus.isStopped()) {
                return false;
            }
            ++l;
            binaryDataLoader.getNextTick(versatileData);
            defaultTickSimulator.init(versatileData);
            while (defaultTickSimulator.getNextTick(tickEvent)) {
                if (string.equals("D1") || string.equals("Weekly") || string.equals("Monthly")) {
                    session.fixD1DataTime(tickEvent);
                }
                session.checkTimeIsInSession(tickEvent.getTime(), sessionStatus, string);
                if (!sessionStatus.isInSession) {
                    barTypeStatus.status = 0;
                } else {
                    tickEvent.setSessionStartTime(sessionStatus.sessionStartTime);
                    tickEvent.setSessionEndTime(sessionStatus.sessionEndTime);
                    l2 = sessionStatus.sessionEndTime;
                    barType.processTick(tickEvent, barTypeStatus, 1);
                }
                if (barTypeStatus.status == 0) {
                    if (!bl) continue;
                    if (versatileData2.time > l2 && l2 > Long.MIN_VALUE) {
                        versatileData2.time = l2;
                    }
                    this.writeData(dataBinWriterNew, versatileData2);
                    bl = false;
                    continue;
                }
                if (barTypeStatus.status == 1) {
                    ++n;
                    this.writeData(dataBinWriterNew, versatileData2);
                    this.initBarData(versatileData2, barTypeStatus.barTime, tickEvent.getBid(), tickEvent.getVolume());
                    bl = true;
                    continue;
                }
                this.updateBarData(versatileData2, tickEvent.getBid(), tickEvent.getVolume());
            }
        }
        if (bl) {
            this.writeData(dataBinWriterNew, versatileData2);
        }
        Log.debug("Processed {} ticks, created {} bars", (Object)l, (Object)n);
        return true;
    }

    private void writeData(DataBinWriterNew dataBinWriterNew, VersatileData versatileData) throws Exception {
        if (versatileData.time != Long.MIN_VALUE) {
            versatileData.volume = versatileData.volume > 1.0 ? (double)SQUtils.roundLong((double)versatileData.volume).longValue() : 1.0;
            dataBinWriterNew.writeData(versatileData);
            versatileData.time = Long.MIN_VALUE;
        }
    }

    private void updateBarData(VersatileData versatileData, double d, double d2) {
        if (d > versatileData.high) {
            versatileData.high = d;
        }
        if (d < versatileData.low) {
            versatileData.low = d;
        }
        versatileData.close = d;
        versatileData.volume += d2;
    }

    private void initBarData(VersatileData versatileData, long l, double d, double d2) {
        versatileData.time = l;
        versatileData.open = d;
        versatileData.high = d;
        versatileData.low = d;
        versatileData.close = d;
        versatileData.volume = d2;
    }

    private boolean processTickDataTarget(BinaryDataLoader binaryDataLoader, DataBinWriterNew dataBinWriterNew, BarType barType, Session session, IStopPauseStatus iStopPauseStatus) throws IOException, Exception {
        VersatileData versatileData = new VersatileData();
        while (binaryDataLoader.hasNextTick()) {
            if (iStopPauseStatus != null && iStopPauseStatus.isStopped()) {
                return false;
            }
            binaryDataLoader.getNextTick(versatileData);
            dataBinWriterNew.writeData(versatileData);
        }
        return true;
    }

    private DataBinWriterNew _getTargetWriter(BarType barType, String string, DataInfo dataInfo, String string2, boolean bl) {
        DataBinWriterNew dataBinWriterNew = barType.isTickBar() ? (bl ? DataBinWriterNew.getCryptedInstance(2, this.getDbPath(), dataInfo.symbolInfo) : DataBinWriterNew.getInstance(2, this.getDbPath(), dataInfo.symbolInfo)) : (bl ? DataBinWriterNew.getCryptedInstance(1, this.getDbPath(), dataInfo.symbolInfo) : DataBinWriterNew.getInstance(1, this.getDbPath(), dataInfo.symbolInfo));
        dataBinWriterNew.setFileName(DataManager.getDataFileName(dataInfo.connection, dataInfo.symbol, string, string2));
        return dataBinWriterNew;
    }

    private BinaryDataLoader _getSourceLoader(DataInfo dataInfo, String string) throws DataException {
        Object object;
        Object object2;
        String string2 = dataInfo.connection;
        String string3 = dataInfo.symbol;
        String string4 = dataInfo.timeframe;
        String string5 = this._getDataFileName(string2, string3, string4, string);
        if (!this._dataFileExists(string5)) {
            string5 = this._getDataFileName(string2, string3, string4, "No Session");
            Log.debug("No data file for " + string2 + " / " + string3 + " / " + string4 + " / " + string);
        }
        if (MainApp.getProduct() == "BACKTESTNODE" && !this._dataFileExists(string5)) {
            Log.info("Data not found, copying data file from NFS disk " + string5 + "...");
            object2 = string5;
            Log.debug("Trying to get source data file from NFS disk...");
            String string6 = System.getProperty("NFSDataPath");
            if (string6 == null) {
                throw new DataException(2, "Unable to load data for " + string2 + " / " + string3 + " / " + string4 + " / " + string + " - NFSDataPath property not set");
            }
            object = SQPaths.dataDirPath.replace("\\", "/");
            if (!this._dataFileExists((String)(object2 = ((String)object2).replace("\\", "/").replace((CharSequence)object, string6)))) {
                throw new DataException(2, "Source data file not found on NFS disk (" + (String)object2 + ") - DataPath: " + (String)object + ", NFSDataPath: " + string6);
            }
            try {
                long l = System.currentTimeMillis();
                Log.debug("Copying data file from NFS disk " + (String)object2 + " to " + string5 + "...");
                File file = new File(string5);
                file.getParentFile().mkdirs();
                File file2 = new File((String)object2);
                Files.copy(file2.toPath(), file.toPath(), new CopyOption[0]);
                long l2 = System.currentTimeMillis() - l;
                Log.debug("Copying data took " + l2 + "ms");
                if (file2.length() != file.length()) {
                    throw new Exception(String.format("Error while copying data file from NFS disk. NFS file size %d <> %d copied file size", file2.length(), file.length()));
                }
                Log.debug("Copying data success, file size " + file.length());
            }
            catch (Exception exception) {
                Log.error("Unable to copy file " + (String)object2 + " to " + string5, (Throwable)exception);
                throw new DataException(2, "Unable to copy file " + (String)object2 + " from NFS disk");
            }
        }
        if (!this._dataFileExists(string5)) {
            throw new DataException(2, "There is no source data file for " + string2 + " / " + string3 + " / " + string4 + " / " + string);
        }
        object2 = BarTypeFactory.getBarType(string4, dataInfo.barTimeType);
        int n = ((BarType)object2).isTickBar() ? 2 : 1;
        object = new ChartDef(dataInfo.connection, dataInfo.symbol, dataInfo.timeframe, 0L, SQTimeOld.toLong((int)2100, (int)1, (int)1), 0.0, string);
        return new BinaryDataLoader(string5, (ChartDef)object, n, dataInfo);
    }

    public static void exportTick(String string, long l, long l2, String string2) throws Exception {
        new DataExporter().exportTick(string, l, l2, string2);
    }

    public static void exportM1(String string, long l, long l2, String string2) throws Exception {
        new DataExporter().exportM1(string, l, l2, string2);
    }

    private void updateUnderlyingSymbol(String string, String string2, String string3) {
        try {
            String string4 = "UPDATE DATA SET USYMBOL='" + string3 + "', USYMBOLNAME='" + string3 + "'";
            string4 = string4 + " WHERE CONNECTION='" + string + "' AND SYMBOL='" + string2 + "'";
            this.sqlCommand(string4);
            DataInfo dataInfo = this.getRecordFromCache(string, string2);
            dataInfo.uSymbol = string3;
            this.updateCachedDataList(dataInfo);
        }
        catch (Exception exception) {
            Log.error("Data DB error:", (Throwable)exception);
        }
    }

    private void _updateUnderlyingSymbolName(String string, String string2, String string3) {
        try {
            string3 = string3.replace("'", "''");
            String string4 = "UPDATE DATA SET USYMBOLNAME='" + string3 + "'";
            string4 = string4 + " WHERE CONNECTION='" + string + "' AND SYMBOL='" + string2 + "'";
            this.sqlCommand(string4);
            DataInfo dataInfo = this.getRecordFromCache(string, string2);
            dataInfo.uSymbolName = string3;
            this.updateCachedDataList(dataInfo);
        }
        catch (Exception exception) {
            Log.error("Data DB error:", (Throwable)exception);
        }
    }

    private void _showData(String string, String string2, boolean bl) {
        try {
            String string3 = "UPDATE DATA SET SHOW=" + (bl ? 1 : 0);
            string3 = string3 + " WHERE CONNECTION='" + string + "' AND SYMBOL='" + string2 + "'";
            this.sqlCommand(string3);
            DataInfo dataInfo = this.getRecordFromCache(string, string2);
            dataInfo.show = bl;
            this.updateCachedDataList(dataInfo);
        }
        catch (Exception exception) {
            Log.error("Data DB error:", (Throwable)exception);
        }
    }

    public static void checkData() {
        try {
            ArrayList<DataInfo> arrayList = DataManager.get()._list();
            for (int i = 0; i < arrayList.size(); ++i) {
                DataInfo dataInfo = arrayList.get(i);
                if (dataInfo.rows > 0 && dataInfo.secondsRecords == 0L) {
                    DataManager.updateSecondsRecords(dataInfo);
                }
                if (dataInfo.source != 2 || dataInfo.uSymbol != null) continue;
                DataManager.get().updateUnderlyingSymbol(dataInfo.connection, dataInfo.symbol, dataInfo.instrument);
            }
        }
        catch (Exception exception) {
            Log.error("Error while checking data. Exc.", (Throwable)exception);
        }
    }

    public static void updateSecondsRecords(DataInfo dataInfo) throws Exception {
        long l = 0L;
        l = dataInfo.timeframe.equals("TICK") ? (long)(dataInfo.totalDays * 86400) : (long)(dataInfo.rows * 60);
        DataManager.updateSecondsRecords(dataInfo.connection, dataInfo.symbol, l);
    }

    public static void checkDataExport(ICryptable iCryptable, int n) throws Exception {
        HistoryDataChecker.checkDataExport((ICryptable)iCryptable, (int)n);
    }

    public static String generateName(String string) {
        int n = string.lastIndexOf("(");
        int n2 = string.length() - 1;
        int n3 = 0;
        try {
            String string2 = string.substring(n + 1, n2);
            n3 = Integer.parseInt(string2);
        }
        catch (Exception exception) {
            // empty catch block
        }
        if (n3 > 0) {
            return string.substring(0, n) + "(" + (n3 + 1) + ")";
        }
        n = n < 0 ? string.length() : n;
        return string.substring(0, n) + "(2)";
    }

    public static String getTempFileName(String string) {
        int n = string.lastIndexOf(".");
        String string2 = string.substring(0, string.lastIndexOf("."));
        String string3 = string.substring(n);
        return string2 + "_temp" + string3;
    }

    public static boolean createGroupAlias(String string, int n) throws Exception {
        DataInfo dataInfo = DataManager.getDataInfo("History", string);
        if (dataInfo == null) {
            if (!InstrumentManager.checkInstrumentExists(string)) {
                InstrumentManager.addInstrument(string, string, 1.0, 0.01, 0.01, 0.0, 0.0, "<Method type=\"None\" use=\"true\"><Params/></Method>", (byte)1);
            }
            DataManager.addData("History", string, string, 1, 5, n, -1);
            DataManager.updateData("History", string, 0L, 0L, 1000000, 0L, 1, "D1", "Etc/UCT");
            return true;
        }
        if (dataInfo.rows == 0) {
            DataManager.updateData("History", string, 0L, 0L, 1000000, 0L, 1, "D1", "Etc/UCT");
        }
        return false;
    }

    public static boolean isGroupAlias(String string) {
        if (string == null) {
            return false;
        }
        return string.startsWith("[") && string.endsWith("]");
    }

    public static void deleteGroupAlias(int n, String string) {
        try {
            DataManager.deleteForGroup("History", string, n);
            InstrumentManager.removeInstrument(string);
        }
        catch (Exception exception) {
            Log.error("Data DB error:", (Throwable)exception);
        }
    }

    public static HistoryOHLCData getHistoryData(String string, String string2, long l, long l2, String string3) throws HistoryDataNotAvailableExeption {
        return DataManager.get()._getHistoryData(string, string2, l, l2, string3);
    }

    private synchronized HistoryOHLCData _getHistoryData(String string, String string2, long l, long l2, String string3) throws HistoryDataNotAvailableExeption {
        HistoryOHLCData historyOHLCData = new HistoryOHLCData(string, string2, l, l2, string3);
        DataInfo dataInfo = this._getDataInfo("History", string);
        if (dataInfo == null) {
            throw new HistoryDataNotAvailableExeption(String.format("Symbol '%s' is not recognized!", string));
        }
        try {
            TimeframeManager.getMillis(string2);
        }
        catch (Exception exception) {
            throw new HistoryDataNotAvailableExeption(String.format("Timeframe '%s' for symbol '%s' does not exist!", string2, string));
        }
        try {
            ChartDef chartDef = new ChartDef("History", string, string2, l, l2, 2.5, string3);
            IDataLoader iDataLoader = this._getDataLoader(chartDef, 1, null);
            iDataLoader.open();
            if (iDataLoader.isCrypted()) {
                throw new HistoryDataNotAvailableExeption(String.format("Data for symbol '%s' are protected and cannot be loaded!", string));
            }
            List<VersatileData> list = this._loadHistoryData(iDataLoader, l, l2);
            this._fillHistoryData(historyOHLCData, list);
        }
        catch (Exception exception) {
            Log.error("Error while loading history data", (Throwable)exception);
            throw new HistoryDataNotAvailableExeption("Error while loading data.", exception);
        }
        return historyOHLCData;
    }

    private void _fillHistoryData(HistoryOHLCData historyOHLCData, List<VersatileData> list) {
        historyOHLCData.Open = new float[list.size()];
        historyOHLCData.Close = new float[list.size()];
        historyOHLCData.High = new float[list.size()];
        historyOHLCData.Low = new float[list.size()];
        historyOHLCData.Volume = new float[list.size()];
        historyOHLCData.Time = new long[list.size()];
        for (int i = 0; i < list.size(); ++i) {
            VersatileData versatileData = list.get(i);
            historyOHLCData.Open[i] = (float)versatileData.open;
            historyOHLCData.Close[i] = (float)versatileData.close;
            historyOHLCData.High[i] = (float)versatileData.high;
            historyOHLCData.Low[i] = (float)versatileData.low;
            historyOHLCData.Volume[i] = (float)versatileData.volume;
            historyOHLCData.Time[i] = versatileData.time;
        }
    }

    private List<VersatileData> _loadHistoryData(IDataLoader iDataLoader, long l, long l2) throws Exception {
        LinkedList<VersatileData> linkedList = new LinkedList<VersatileData>();
        while (iDataLoader.hasNextTick()) {
            VersatileData versatileData = new VersatileData();
            iDataLoader.getNextTick(versatileData);
            if (l2 != -1L && versatileData.time > l2) break;
            if (l != -1L && versatileData.time < l) continue;
            linkedList.add(versatileData);
        }
        return linkedList;
    }

    public static DataInfo addCustomData(String string, String string2, int n, String string3) throws Exception {
        String string4 = "SingleAssetCloud";
        if (!InstrumentManager.checkInstrumentExists(string4)) {
            InstrumentManager.addInstrument(string4, string4, 1.0, 0.01, 0.01, 0.0, 0.0, "<Method type=\"None\" use=\"true\"><Params/></Method>", (byte)1);
        }
        InstrumentInfo instrumentInfo = InstrumentManager.getInstrumentInfo(string4);
        DataInfo dataInfo = new DataInfo();
        dataInfo.id = -1;
        dataInfo.symbol = string2;
        dataInfo.connection = string;
        dataInfo.instrument = string4;
        dataInfo.basketId = n;
        dataInfo.symbolInfo = instrumentInfo;
        dataInfo.originalSymbol = string3;
        dataInfo.rows = 100000;
        dataInfo.dateFrom = SQTime.toLong((int)1980, (int)1, (int)1);
        dataInfo.dateTo = System.currentTimeMillis();
        String string5 = string + string2;
        DataManager.get().customDataInfoCache.put(string5, dataInfo);
        return dataInfo;
    }

    public static void cleanHigherTFFiles(String string) {
    }
}

