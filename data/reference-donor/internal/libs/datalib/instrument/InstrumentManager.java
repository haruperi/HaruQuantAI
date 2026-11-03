/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.constants.SQPaths
 *  com.strategyquant.lib.utils.StringComparator
 */
package com.strategyquant.datalib.instrument;

import com.strategyquant.datalib.InstrumentInfo;
import com.strategyquant.datalib.data.DataDb;
import com.strategyquant.datalib.data.DataException;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.datalib.instrument.AliasManager;
import com.strategyquant.datalib.instrument.InstrumentAlias;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.constants.SQPaths;
import com.strategyquant.lib.utils.StringComparator;
import java.io.File;
import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.Statement;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.stream.Collectors;

public class InstrumentManager
extends DataDb {
    private static InstrumentManager instance = null;
    private static final String exchangesFilePath = SQPaths.settingsDirPath + "/exchanges.txt";
    private static final String countriesFilePath = SQPaths.settingsDirPath + "/countries.txt";
    private static final String sectorsFilePath = SQPaths.settingsDirPath + "/sectors.txt";
    private static final String delimiter = "\r\n";
    public static final String defaultCommissionsMethod = "<Method type=\"None\" use=\"true\"><Params/></Method>";
    private ArrayList<String> exchanges = new ArrayList();
    private ArrayList<String> countries = new ArrayList();
    private ArrayList<String> sectors = new ArrayList();
    private InstrumentCache instrumentCache = new InstrumentCache();

    public static void init(String string) throws Exception {
        if (instance != null) {
            throw new Exception("InstrumentManager.init() called more than once!");
        }
        new InstrumentManager(string);
    }

    private InstrumentManager(String string) {
        super(string);
        instance = this;
        File file = new File(exchangesFilePath);
        File file2 = new File(countriesFilePath);
        File file3 = new File(sectorsFilePath);
        if (file.exists()) {
            try {
                SQUtils.fileToArrayList(this.exchanges, (String)exchangesFilePath, (String)delimiter);
            }
            catch (Exception exception) {
                Log.error("Cannot load Exchanges file. ", (Throwable)exception);
            }
        } else {
            Log.warn("Exchanges file doesn't exist.");
        }
        if (file2.exists()) {
            try {
                SQUtils.fileToArrayList(this.countries, (String)countriesFilePath, (String)delimiter);
            }
            catch (Exception exception) {
                Log.error("Cannot load Countries file. ", (Throwable)exception);
            }
        } else {
            Log.warn("Countries file doesn't exist.");
        }
        if (file3.exists()) {
            try {
                SQUtils.fileToArrayList(this.sectors, (String)sectorsFilePath, (String)delimiter);
            }
            catch (Exception exception) {
                Log.error("Cannot load Sectors file. ", (Throwable)exception);
            }
        } else {
            Log.warn("Sectors file doesn't exist.");
        }
    }

    private static InstrumentManager get() {
        return instance;
    }

    @Override
    public void initDatabase() {
        try {
            String string;
            Class.forName("org.sqlite.JDBC");
            if (!this.tableExists("INSTRUMENTS")) {
                string = "CREATE TABLE INSTRUMENTS (INSTRUMENT \tVARCHAR(40) \tPRIMARY KEY NOT NULL, DESCRIPTION\tVARCHAR(255),  POINTVALUE \tDOUBLE \t\t\tNOT NULL, TICKSIZE \t\tDOUBLE \t\t\tNOT NULL, TICKSTEP \t\tDOUBLE \t\t\tNOT NULL, DEFAULTSPREAD \tDOUBLE \t\t\tDEFAULT 0, COMMISSIONS \tTEXT, DATATYPE\t\tINT\t\t\t\tNOT NULL, EXCHANGE\t\tVARCHAR(50), COUNTRY\t\tVARCHAR(50), SECTOR\t\t\tVARCHAR(100), SWAP\t\t\tTEXT, ORDERSIZEMULTIPLIER DOUBLE\t\tDEFAULT 1, ORDERSIZESTEP DOUBLE\t\tDEFAULT 0)";
                this.sqlCommand(string);
                Log.info("Instruments table created successfully");
            }
            if (!this.columnExists("INSTRUMENTS", "DEFAULTSLIPPAGE")) {
                string = "ALTER TABLE INSTRUMENTS ADD DEFAULTSLIPPAGE DOUBLE DEFAULT 0";
                this.sqlCommand(string);
            }
            if (!this.columnExists("INSTRUMENTS", "SWAP")) {
                string = "ALTER TABLE INSTRUMENTS ADD SWAP TEXT DEFAULT NULL";
                this.sqlCommand(string);
            }
            if (!this.columnExists("INSTRUMENTS", "ORDERSIZEMULTIPLIER")) {
                string = "ALTER TABLE INSTRUMENTS ADD ORDERSIZEMULTIPLIER DOUBLE DEFAULT 1";
                this.sqlCommand(string);
            }
            if (!this.columnExists("INSTRUMENTS", "ORDERSIZESTEP")) {
                string = "ALTER TABLE INSTRUMENTS ADD ORDERSIZESTEP DOUBLE DEFAULT 0";
                this.sqlCommand(string);
            }
            if (!this.columnExists("INSTRUMENTS", "BROKER_ID")) {
                string = "ALTER TABLE INSTRUMENTS ADD BROKER_ID INT DEFAULT -1";
                this.sqlCommand(string);
            }
            if (!this.columnExists("INSTRUMENTS", "MIN_DISTANCE")) {
                string = "ALTER TABLE INSTRUMENTS ADD MIN_DISTANCE DOUBLE DEFAULT 0.0";
                this.sqlCommand(string);
            }
        }
        catch (Exception exception) {
            Log.error("DB error: Cannot create Instruments table.", (Throwable)exception);
        }
    }

    public static InstrumentInfo getInstrumentInfo(String string) throws DataException {
        return InstrumentManager.get()._getInstrumentInfo(string);
    }

    public static boolean checkInstrumentExists(String string) {
        return InstrumentManager.get()._checkInstrumentExists(string, false);
    }

    public static boolean checkInstrumentExists(String string, boolean bl) {
        return InstrumentManager.get()._checkInstrumentExists(string, bl);
    }

    public static boolean checkAliasExists(String string) {
        return AliasManager.checkAliasExists(string);
    }

    public static void addInstrumentInBatch(List<InstrumentInfo> list) throws Exception {
        InstrumentManager.get()._addInstrumentInBatch(list);
    }

    public static void addInstrument(String string, String string2, double d, double d2, double d3, double d4, double d5, String string3, byte by) throws Exception {
        InstrumentManager.get()._addInstrument(string, -1, string2, d, d2, d3, d4, d5, 0.0, string3, by, null, null, null, null, 1.0, 0.0);
    }

    public static void addInstrument(String string, String string2, double d, double d2, double d3, double d4, double d5, String string3, byte by, String string4, String string5, String string6, String string7, double d6, double d7) throws Exception {
        InstrumentManager.get()._addInstrument(string, -1, string2, d, d2, d3, d4, d5, 0.0, string3, by, string4, string5, string6, string7, d6, d7);
    }

    public static void addInstrument(String string, int n, String string2, double d, double d2, double d3, double d4, double d5, double d6, String string3, byte by, String string4, String string5, String string6, String string7, double d7, double d8) throws Exception {
        InstrumentManager.get()._addInstrument(string, n, string2, d, d2, d3, d4, d5, d6, string3, by, string4, string5, string6, string7, d7, d8);
    }

    public static void addInstrument(InstrumentInfo instrumentInfo) throws Exception {
        InstrumentManager.get()._addInstrument(instrumentInfo.instrument, instrumentInfo.broker, instrumentInfo.description, instrumentInfo.pointValue, instrumentInfo.tickSize, instrumentInfo.tickStep, instrumentInfo.defaultSpread, instrumentInfo.defaultSlippage, instrumentInfo.minDistance, instrumentInfo.commissions, (byte)instrumentInfo.dataType, instrumentInfo.exchange, instrumentInfo.country, instrumentInfo.sector, instrumentInfo.swap, instrumentInfo.orderSizeMultiplier, instrumentInfo.orderSizeStep);
    }

    public static void updateInstrument(InstrumentInfo instrumentInfo) throws Exception {
        InstrumentManager.get()._updateInstrument(instrumentInfo.instrument, instrumentInfo.description, instrumentInfo.pointValue, instrumentInfo.tickSize, instrumentInfo.tickStep, instrumentInfo.defaultSpread, instrumentInfo.defaultSlippage, instrumentInfo.minDistance, instrumentInfo.commissions, (byte)instrumentInfo.dataType, instrumentInfo.exchange, instrumentInfo.country, instrumentInfo.sector, instrumentInfo.swap, instrumentInfo.orderSizeMultiplier, instrumentInfo.orderSizeStep);
    }

    public static void updateInstrument(String string, String string2, double d, double d2, double d3, double d4, double d5, double d6, String string3, byte by, String string4, String string5, String string6, String string7, double d7, double d8) throws Exception {
        InstrumentManager.get()._updateInstrument(string, string2, d, d2, d3, d4, d5, d6, string3, by, string4, string5, string6, string7, d7, d8);
    }

    public static void removeInstrument(String string) throws Exception {
        InstrumentManager.get()._removeInstrument(string);
    }

    public static void addAlias(String string, String string2, String string3) throws DataException {
        InstrumentManager.get()._addAlias(string, string2, string3);
    }

    public static void updateAlias(String string, String string2, String string3) throws Exception {
        InstrumentManager.get()._updateAlias(string, string2, string3);
    }

    public static void updateDataType(String string, byte by) throws Exception {
        InstrumentManager.get()._updateDataType(string, by);
    }

    private void _updateDataType(String string, byte by) throws Exception {
        if (this._checkInstrumentExists(string, false)) {
            try {
                String string2 = "UPDATE INSTRUMENTS SET DATATYPE='" + by + "'";
                string2 = string2 + " WHERE INSTRUMENT='" + string + "'";
                this.sqlCommand(string2);
                InstrumentInfo instrumentInfo = this.instrumentCache.get(string);
                instrumentInfo.dataType = by;
                this.instrumentCache.store(instrumentInfo);
            }
            catch (Exception exception) {
                Log.error("DB Exception", (Throwable)exception);
                throw new DataException(3, exception.getMessage());
            }
        } else {
            throw new Exception("Instrument '" + string + "' doesn't exist.");
        }
    }

    public static void removeAlias(String string) throws Exception {
        AliasManager.removeAlias(string);
    }

    public static ArrayList<InstrumentInfo> list() throws DataException {
        return InstrumentManager.get()._list();
    }

    public static ArrayList<InstrumentAlias> listAliases() throws DataException {
        return AliasManager.getAliases();
    }

    public static ArrayList<InstrumentAlias> listInstrumentAliases(String string) throws DataException {
        return AliasManager.listInstrumentAliases(string);
    }

    public static void removeInstrumentAliases(String string) throws DataException {
        AliasManager.removeInstrumentAliases(string);
    }

    public static boolean trySaveExchange(String string) throws DataException {
        return InstrumentManager.get()._trySaveExchange(string);
    }

    public static boolean trySaveCountry(String string) throws DataException {
        return InstrumentManager.get()._trySaveCountry(string);
    }

    public static boolean trySaveSector(String string) throws DataException {
        return InstrumentManager.get()._trySaveSector(string);
    }

    public static ArrayList<String> getExchanges() {
        ArrayList<String> arrayList = InstrumentManager.get().exchanges;
        arrayList.sort((Comparator<String>)new StringComparator());
        return arrayList;
    }

    public static ArrayList<String> getCountries() {
        ArrayList<String> arrayList = InstrumentManager.get().countries;
        arrayList.sort((Comparator<String>)new StringComparator());
        return arrayList;
    }

    public static ArrayList<String> getSectors() {
        ArrayList<String> arrayList = InstrumentManager.get().sectors;
        arrayList.sort((Comparator<String>)new StringComparator());
        return arrayList;
    }

    private ArrayList<InstrumentInfo> _list() throws DataException {
        return this.instrumentCache.list();
    }

    private void _addInstrumentInBatch(List<InstrumentInfo> list) throws Exception {
        Connection connection = null;
        try {
            connection = this.getConnection();
            for (InstrumentInfo instrumentInfo : list) {
                String string = "INSERT INTO INSTRUMENTS (INSTRUMENT, DESCRIPTION, POINTVALUE, TICKSIZE, TICKSTEP, DEFAULTSPREAD, DEFAULTSLIPPAGE, COMMISSIONS, DATATYPE, ORDERSIZEMULTIPLIER, ORDERSIZESTEP";
                if (instrumentInfo.exchange != null) {
                    string = string + ", EXCHANGE";
                }
                if (instrumentInfo.country != null) {
                    string = string + ", COUNTRY";
                }
                if (instrumentInfo.sector != null) {
                    string = string + ", SECTOR";
                }
                if (instrumentInfo.swap != null) {
                    string = string + ", SWAP";
                }
                string = string + ") VALUES ('" + instrumentInfo.instrument + "','" + instrumentInfo.description + "'," + instrumentInfo.pointValue + "," + instrumentInfo.tickSize + "," + instrumentInfo.tickStep + "," + instrumentInfo.defaultSpread + "," + instrumentInfo.defaultSlippage + ",'" + instrumentInfo.commissions + "'," + instrumentInfo.dataType + "," + instrumentInfo.orderSizeMultiplier + "," + instrumentInfo.orderSizeStep;
                if (instrumentInfo.exchange != null) {
                    string = string + ", '" + instrumentInfo.exchange + "'";
                }
                if (instrumentInfo.country != null) {
                    string = string + ", '" + instrumentInfo.country + "'";
                }
                if (instrumentInfo.sector != null) {
                    string = string + ", '" + instrumentInfo.sector + "'";
                }
                if (instrumentInfo.swap != null) {
                    string = string + ", '" + instrumentInfo.swap + "'";
                }
                string = string + ")";
                this.sqlCommand(string);
                this.instrumentCache.store(instrumentInfo);
            }
        }
        catch (Exception exception) {
            Log.error("DB Exception", (Throwable)exception);
            throw exception;
        }
        finally {
            this.close(connection);
        }
    }

    private void _addInstrument(String string, int n, String string2, double d, double d2, double d3, double d4, double d5, double d6, String string3, byte by, String string4, String string5, String string6, String string7, double d7, double d8) throws Exception {
        if (!this._checkInstrumentExists(string, false)) {
            try {
                String string8 = "INSERT INTO INSTRUMENTS (INSTRUMENT, BROKER_ID, DESCRIPTION, POINTVALUE, TICKSIZE, TICKSTEP, DEFAULTSPREAD, DEFAULTSLIPPAGE, MIN_DISTANCE, COMMISSIONS, DATATYPE, ORDERSIZEMULTIPLIER, ORDERSIZESTEP";
                if (string4 != null) {
                    string8 = string8 + ", EXCHANGE";
                }
                if (string5 != null) {
                    string8 = string8 + ", COUNTRY";
                }
                if (string6 != null) {
                    string8 = string8 + ", SECTOR";
                }
                if (string7 != null) {
                    string8 = string8 + ", SWAP";
                }
                string8 = string8 + ") VALUES ('" + string + "'," + n + ",'" + string2 + "'," + d + "," + d2 + "," + d3 + "," + d4 + "," + d5 + "," + d6 + ",'" + string3 + "'," + by + "," + d7 + "," + d8;
                if (string4 != null) {
                    string8 = string8 + ", '" + string4 + "'";
                }
                if (string5 != null) {
                    string8 = string8 + ", '" + string5 + "'";
                }
                if (string6 != null) {
                    string8 = string8 + ", '" + string6 + "'";
                }
                if (string7 != null) {
                    string8 = string8 + ", '" + string7 + "'";
                }
                string8 = string8 + ")";
                this.sqlCommand(string8);
                this.instrumentCache.store(string, n, string2, d, d2, d3, d4, d5, d6, string3, by, string4, string5, string6, string7, d7, d8);
            }
            catch (Exception exception) {
                Log.error("DB Exception", (Throwable)exception);
                throw new Exception("Adding instrument '" + string + "' failed.");
            }
        } else {
            throw new Exception("Instrument '" + string + "' already exists.");
        }
    }

    private void _updateInstrument(String string, String string2, double d, double d2, double d3, double d4, double d5, double d6, String string3, byte by, String string4, String string5, String string6, String string7, double d7, double d8) throws Exception {
        if (this._checkInstrumentExists(string, false)) {
            try {
                String string8 = "UPDATE INSTRUMENTS SET DESCRIPTION='" + string2 + "', POINTVALUE=" + d + ", TICKSIZE=" + d2 + ", TICKSTEP=" + d3 + ", DEFAULTSPREAD=" + d4 + ", DEFAULTSLIPPAGE=" + d5 + ", MIN_DISTANCE=" + d6 + ", COMMISSIONS='" + string3 + "', DATATYPE=" + by + ",ORDERSIZEMULTIPLIER=" + d7 + ",ORDERSIZESTEP=" + d8;
                if (string4 != null) {
                    string8 = string8 + ", EXCHANGE='" + string4 + "'";
                }
                if (string5 != null) {
                    string8 = string8 + ", COUNTRY='" + string5 + "'";
                }
                if (string6 != null) {
                    string8 = string8 + ", SECTOR='" + string6 + "'";
                }
                if (string7 != null) {
                    string8 = string8 + ", SWAP='" + string7 + "'";
                }
                string8 = string8 + " WHERE INSTRUMENT='" + string + "'";
                this.sqlCommand(string8);
                this.instrumentCache.store(string, null, string2, d, d2, d3, d4, d5, d6, string3, by, string4, string5, string6, string7, d7, d8);
                DataManager.get().removeRecordFromCacheForInstrument(string);
            }
            catch (Exception exception) {
                Log.error("DB Exception", (Throwable)exception);
                throw new DataException(3, exception.getMessage());
            }
        } else {
            throw new Exception("Instrument '" + string + "' doesn't exist.");
        }
    }

    private void _removeInstrument(String string) throws Exception {
        if (this._checkInstrumentExists(string, false)) {
            try {
                ArrayList<String> arrayList = DataManager.getSymbolsForInstrument(string);
                if (arrayList != null && !arrayList.isEmpty()) {
                    String string2 = "";
                    for (String string3 : arrayList) {
                        string2 = string2 + string3 + ",";
                    }
                    string2 = string2.substring(0, string2.length() - 1);
                    throw new Exception("Cannot delete instrument '" + string + "' as it is currently used by symbols: " + string2);
                }
                String string4 = "DELETE FROM INSTRUMENTS WHERE INSTRUMENT='" + string + "'";
                this.sqlCommand(string4);
                this.instrumentCache.remove(string);
                AliasManager.removeInstrumentAliases(string);
            }
            catch (Exception exception) {
                Log.error("DB Exception", (Throwable)exception);
                throw new DataException(3, exception.getMessage());
            }
        } else {
            throw new Exception("Instrument '" + string + "' doesn't exist.");
        }
    }

    public InstrumentInfo _getInstrumentInfo(String string) throws DataException {
        ResultSet resultSet;
        Statement statement;
        Connection connection;
        block9: {
            InstrumentInfo instrumentInfo;
            InstrumentInfo instrumentInfo2 = this.instrumentCache.get(string);
            if (instrumentInfo2 != null) {
                return instrumentInfo2;
            }
            connection = null;
            statement = null;
            resultSet = null;
            try {
                String string2;
                connection = this.getConnection();
                if (this._checkInstrumentExists(connection, string)) {
                    string2 = string;
                } else if (AliasManager.checkAliasExists(string)) {
                    string2 = AliasManager.getAliasInstrument(string);
                } else {
                    throw new DataException(3, "DB: Instrument or alias '" + string + "' not found.");
                }
                InstrumentInfo instrumentInfo3 = new InstrumentInfo();
                statement = connection.createStatement();
                resultSet = statement.executeQuery("SELECT * FROM INSTRUMENTS WHERE INSTRUMENT='" + string2 + "'");
                if (!resultSet.next()) break block9;
                instrumentInfo3.instrument = string2.intern();
                instrumentInfo3.alias = string.intern();
                instrumentInfo3.description = resultSet.getString("DESCRIPTION").intern();
                instrumentInfo3.broker = resultSet.getInt("BROKER_ID");
                instrumentInfo3.pointValue = resultSet.getDouble("POINTVALUE");
                instrumentInfo3.tickSize = resultSet.getDouble("TICKSIZE");
                instrumentInfo3.tickStep = resultSet.getDouble("TICKSTEP");
                instrumentInfo3.defaultSpread = resultSet.getDouble("DEFAULTSPREAD");
                instrumentInfo3.defaultSlippage = resultSet.getDouble("DEFAULTSLIPPAGE");
                instrumentInfo3.commissions = resultSet.getString("COMMISSIONS");
                instrumentInfo3.swap = resultSet.getString("SWAP");
                instrumentInfo3.dataType = resultSet.getInt("DATATYPE");
                instrumentInfo3.exchange = resultSet.getString("EXCHANGE");
                instrumentInfo3.country = resultSet.getString("COUNTRY");
                instrumentInfo3.sector = resultSet.getString("SECTOR");
                instrumentInfo3.decimals = SQUtils.getDecimalPlaces((double)instrumentInfo3.tickStep);
                instrumentInfo3.orderSizeMultiplier = resultSet.getDouble("ORDERSIZEMULTIPLIER");
                instrumentInfo3.orderSizeStep = resultSet.getDouble("ORDERSIZESTEP");
                instrumentInfo3.minDistance = resultSet.getDouble("MIN_DISTANCE");
                this.instrumentCache.store(instrumentInfo3);
                instrumentInfo = instrumentInfo3;
            }
            catch (Exception exception) {
                try {
                    Log.error("DB Exception", (Throwable)exception);
                    throw new DataException(3, exception.getMessage());
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
            return instrumentInfo;
        }
        this.close(resultSet);
        this.close(statement);
        this.close(connection);
        throw new DataException(3, "DB: Instrument or alias '" + string + "' not found (2).");
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private boolean _checkInstrumentExists(String string, boolean bl) {
        boolean bl2;
        Connection connection;
        block7: {
            block6: {
                connection = null;
                if (!this.instrumentCache.contains(string)) break block6;
                boolean bl3 = true;
                this.close(connection);
                return bl3;
            }
            connection = this.getConnection();
            boolean bl4 = this._checkInstrumentExists(connection, string);
            if (!bl && !bl4) break block7;
            boolean bl5 = bl4;
            this.close(connection);
            return bl5;
        }
        try {
            bl2 = AliasManager.checkAliasExists(string);
        }
        catch (Exception exception) {
            boolean bl6;
            try {
                Log.error("DB Exception", (Throwable)exception);
                bl6 = false;
            }
            catch (Throwable throwable) {
                this.close(connection);
                throw throwable;
            }
            this.close(connection);
            return bl6;
        }
        this.close(connection);
        return bl2;
    }

    private boolean _checkInstrumentExists(Connection connection, String string) {
        return this.sqlCheckRecordExists(connection, "SELECT * FROM INSTRUMENTS WHERE INSTRUMENT='" + string + "'");
    }

    private void _addAlias(String string, String string2, String string3) throws DataException {
        Connection connection = null;
        Statement statement = null;
        ResultSet resultSet = null;
        try {
            connection = this.getConnection();
            statement = connection.createStatement();
            if (!this._checkInstrumentExists(connection, string2)) {
                throw new DataException(3, "DB: Instrument '" + string2 + "' doesn't exist.");
            }
            if (this._checkInstrumentExists(connection, string)) {
                throw new DataException(3, "DB: Alias must not have the same name as an existing instrument.");
            }
            AliasManager.addAlias(string, string2, string3);
        }
        catch (Exception exception) {
            Log.error("DB Exception", (Throwable)exception);
            throw new DataException(3, exception.getMessage());
        }
        finally {
            this.close(resultSet);
            this.close(statement);
            this.close(connection);
        }
    }

    private void _updateAlias(String string, String string2, String string3) throws DataException {
        Connection connection = null;
        Statement statement = null;
        ResultSet resultSet = null;
        try {
            connection = this.getConnection();
            statement = connection.createStatement();
            if (!this._checkInstrumentExists(connection, string)) {
                throw new DataException(3, "DB: Instrument '" + string + "' doesn't exist.");
            }
            if (this._checkInstrumentExists(connection, string2)) {
                throw new DataException(3, "DB: Alias must not have the same name as an existing instrument.");
            }
            AliasManager.updateAlias(string2, string, string3);
        }
        catch (Exception exception) {
            Log.error("DB Exception", (Throwable)exception);
            throw new DataException(3, exception.getMessage());
        }
        finally {
            this.close(resultSet);
            this.close(statement);
            this.close(connection);
        }
    }

    private boolean _trySaveExchange(String string) {
        if (!this.exchanges.contains(string) && !string.isEmpty()) {
            this.exchanges.add(string);
            try {
                SQUtils.arrayListToFile(this.exchanges, (String)exchangesFilePath, (String)delimiter);
            }
            catch (Exception exception) {
                Log.error("Saving exchanges failed. ", (Throwable)exception);
            }
            return true;
        }
        return false;
    }

    private boolean _trySaveCountry(String string) {
        if (!this.countries.contains(string) && !string.isEmpty()) {
            this.countries.add(string);
            try {
                SQUtils.arrayListToFile(this.countries, (String)countriesFilePath, (String)delimiter);
            }
            catch (Exception exception) {
                Log.error("Saving countries failed. ", (Throwable)exception);
            }
            return true;
        }
        return false;
    }

    private boolean _trySaveSector(String string) {
        if (!this.sectors.contains(string) && !string.isEmpty()) {
            this.sectors.add(string);
            try {
                SQUtils.arrayListToFile(this.sectors, (String)sectorsFilePath, (String)delimiter);
            }
            catch (Exception exception) {
                Log.error("Saving sectors failed. ", (Throwable)exception);
            }
            return true;
        }
        return false;
    }

    public static InstrumentInfo findClosestInstrument(String string) throws DataException {
        return InstrumentManager.get()._findClosestInstrument(string);
    }

    private InstrumentInfo _findClosestInstrument(String string) throws DataException {
        ArrayList<InstrumentInfo> arrayList = this._list();
        InstrumentInfo instrumentInfo = null;
        int n = Integer.MAX_VALUE;
        for (int i = 0; i < arrayList.size(); ++i) {
            InstrumentInfo instrumentInfo2 = arrayList.get(i);
            int n2 = SQUtils.levenshteinDistance((CharSequence)string, (CharSequence)instrumentInfo2.instrument);
            if (n2 >= n) continue;
            instrumentInfo = instrumentInfo2;
            n = n2;
        }
        return instrumentInfo;
    }

    private class InstrumentCache {
        private HashMap<String, InstrumentInfo> instrumentInfoCache = new HashMap();
        private boolean cacheReady = false;

        private InstrumentCache() {
        }

        private synchronized void ensureCache() throws DataException {
            if (this.cacheReady) {
                return;
            }
            Connection connection = null;
            Statement statement = null;
            ResultSet resultSet = null;
            ArrayList<InstrumentInfo> arrayList = new ArrayList<InstrumentInfo>();
            try {
                connection = InstrumentManager.this.getConnection();
                statement = connection.createStatement();
                resultSet = statement.executeQuery("SELECT * FROM INSTRUMENTS");
                while (resultSet.next()) {
                    InstrumentInfo instrumentInfo = new InstrumentInfo();
                    instrumentInfo.instrument = resultSet.getString("INSTRUMENT").intern();
                    instrumentInfo.description = resultSet.getString("DESCRIPTION").intern();
                    instrumentInfo.pointValue = resultSet.getDouble("POINTVALUE");
                    instrumentInfo.tickSize = resultSet.getDouble("TICKSIZE");
                    instrumentInfo.tickStep = resultSet.getDouble("TICKSTEP");
                    instrumentInfo.defaultSpread = resultSet.getDouble("DEFAULTSPREAD");
                    instrumentInfo.defaultSlippage = resultSet.getDouble("DEFAULTSLIPPAGE");
                    instrumentInfo.commissions = resultSet.getString("COMMISSIONS");
                    instrumentInfo.dataType = resultSet.getInt("DATATYPE");
                    instrumentInfo.exchange = resultSet.getString("EXCHANGE");
                    instrumentInfo.country = resultSet.getString("COUNTRY");
                    instrumentInfo.sector = resultSet.getString("SECTOR");
                    instrumentInfo.decimals = SQUtils.getDecimalPlaces((double)instrumentInfo.tickStep);
                    instrumentInfo.swap = resultSet.getString("SWAP");
                    instrumentInfo.broker = resultSet.getInt("BROKER_ID");
                    instrumentInfo.minDistance = resultSet.getDouble("MIN_DISTANCE");
                    instrumentInfo.orderSizeMultiplier = resultSet.getDouble("ORDERSIZEMULTIPLIER");
                    instrumentInfo.orderSizeStep = resultSet.getDouble("ORDERSIZESTEP");
                    arrayList.add(instrumentInfo);
                    this.instrumentInfoCache.put(instrumentInfo.instrument, instrumentInfo);
                }
            }
            catch (Exception exception) {
                try {
                    DataDb.Log.error("DB Exception", (Throwable)exception);
                    throw new DataException(3, exception.getMessage());
                }
                catch (Throwable throwable) {
                    InstrumentManager.this.close(resultSet);
                    InstrumentManager.this.close(statement);
                    InstrumentManager.this.close(connection);
                    throw throwable;
                }
            }
            InstrumentManager.this.close(resultSet);
            InstrumentManager.this.close(statement);
            InstrumentManager.this.close(connection);
            this.cacheReady = true;
        }

        public synchronized InstrumentInfo get(String string) throws DataException {
            this.ensureCache();
            return this.instrumentInfoCache.get(string);
        }

        public boolean contains(String string) throws DataException {
            this.ensureCache();
            return this.instrumentInfoCache.containsKey(string);
        }

        public synchronized InstrumentInfo remove(String string) throws DataException {
            this.ensureCache();
            return this.instrumentInfoCache.remove(string);
        }

        public synchronized void store(String string, Integer n, String string2, double d, double d2, double d3, double d4, double d5, double d6, String string3, byte by, String string4, String string5, String string6, String string7, double d7, double d8) throws DataException {
            InstrumentInfo instrumentInfo = this.get(string);
            if (instrumentInfo == null) {
                instrumentInfo = new InstrumentInfo();
                instrumentInfo.instrument = string;
            }
            if (n != null) {
                instrumentInfo.broker = n;
            }
            instrumentInfo.description = string2;
            instrumentInfo.pointValue = d;
            instrumentInfo.tickSize = d2;
            instrumentInfo.tickStep = d3;
            instrumentInfo.defaultSpread = d4;
            instrumentInfo.defaultSlippage = d5;
            instrumentInfo.minDistance = d6;
            instrumentInfo.commissions = string3;
            instrumentInfo.dataType = by;
            instrumentInfo.orderSizeMultiplier = d7;
            instrumentInfo.orderSizeStep = d8;
            instrumentInfo.decimals = SQUtils.getDecimalPlaces((double)instrumentInfo.tickStep);
            if (string4 != null) {
                instrumentInfo.exchange = string4;
            }
            if (string5 != null) {
                instrumentInfo.country = string5;
            }
            if (string6 != null) {
                instrumentInfo.sector = string6;
            }
            if (string7 != null) {
                instrumentInfo.swap = string7;
            }
            this.store(instrumentInfo);
        }

        public synchronized InstrumentInfo store(InstrumentInfo instrumentInfo) throws DataException {
            this.ensureCache();
            instrumentInfo.decimals = SQUtils.getDecimalPlaces((double)instrumentInfo.tickStep);
            return this.instrumentInfoCache.put(instrumentInfo.instrument, instrumentInfo);
        }

        public synchronized ArrayList<InstrumentInfo> list() throws DataException {
            this.ensureCache();
            return new ArrayList<InstrumentInfo>(this.instrumentInfoCache.values().stream().sorted((instrumentInfo, instrumentInfo2) -> instrumentInfo.instrument.compareTo(instrumentInfo2.instrument)).collect(Collectors.toList()));
        }
    }
}

