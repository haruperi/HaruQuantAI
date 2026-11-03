/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.constants.SQPaths
 *  org.jdom2.Content
 *  org.jdom2.Element
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.datalib.customData;

import com.strategyquant.datalib.customData.CustomDataDb;
import com.strategyquant.datalib.customData.CustomDataInfo;
import com.strategyquant.datalib.customData.CustomDataTypes;
import com.strategyquant.datalib.customData.ct.CTCustomIndicators;
import com.strategyquant.datalib.indicators.SCustomIndicator;
import com.strategyquant.datalib.indicators.SParameter;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.constants.SQPaths;
import java.io.File;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.Statement;
import java.util.ArrayList;
import java.util.Collection;
import java.util.HashMap;
import org.jdom2.Content;
import org.jdom2.Element;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class CustomDataManager
extends CustomDataDb {
    public static final Logger Log = LoggerFactory.getLogger(CustomDataManager.class);
    private static CustomDataManager instance = null;
    private HashMap<String, CustomDataInfo> dataInfoCache = new HashMap();

    public static void init(String string) throws Exception {
        if (instance != null) {
            return;
        }
        instance = new CustomDataManager(string);
        instance._list();
        if (!CustomDataManager.configFileExists()) {
            instance._updateConfigFileLock();
        }
    }

    private CustomDataManager(String string) {
        super(string);
    }

    static CustomDataManager get() {
        return instance;
    }

    @Override
    public void initDatabase() {
        try {
            Class.forName("org.sqlite.JDBC");
            if (!this.tableExists("DATA")) {
                String string = "CREATE TABLE DATA (ID INTEGER PRIMARY KEY AUTOINCREMENT, NAME\t\t\tVARCHAR(50)\tNOT NULL, VALUESOBJECT\tVARCHAR(1024), DATATYPE \t\tINT, TIMEFRAME \t\tVARCHAR(50), FILENAME \t\tVARCHAR(100), DATEFROM     \tLONG, DATETO \t\tLONG, ROWS \t\t\tINT DEFAULT 0)";
                this.sqlCommand(string);
                Log.info("Custom Data table created successfully");
            }
        }
        catch (Exception exception) {
            Log.error("DB error: Cannot create Custom Data table.", (Throwable)exception);
        }
    }

    public static Collection<CustomDataInfo> list() throws Exception {
        return CustomDataManager.get()._list();
    }

    public static void add(CustomDataInfo customDataInfo) throws Exception {
        CustomDataManager.add(customDataInfo.name, customDataInfo.valuesObject.toString(), customDataInfo.dataType);
    }

    public static void add(String string, String string2, int n) throws Exception {
        CustomDataManager.get()._add(string, string2, n);
    }

    public static void update(CustomDataInfo customDataInfo) throws Exception {
        CustomDataManager.update(customDataInfo.name, customDataInfo.name, customDataInfo.valuesObject.toString(), customDataInfo.dataType);
    }

    public static void update(String string, String string2, String string3, int n) throws Exception {
        CustomDataManager.get()._update(string, string2, string3, n);
    }

    public static void updateData(String string, long l, long l2, int n, String string2) throws Exception {
        CustomDataManager.get()._updateData(string, l, l2, n, string2);
    }

    public static boolean checkDataExists(String string) {
        return CustomDataManager.get()._checkDataExists(string);
    }

    public static CustomDataInfo getDataInfo(String string) {
        return CustomDataManager.get()._getDataInfo(string);
    }

    public static void delete(String string) {
        CustomDataManager.get()._delete(string);
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private void _delete(String string) {
        try {
            String string2 = "DELETE FROM DATA WHERE NAME='" + string + "'";
            this.sqlCommand(string2);
            CustomDataManager.removeDataFile(string);
            HashMap<String, CustomDataInfo> hashMap = this.dataInfoCache;
            synchronized (hashMap) {
                this.dataInfoCache.remove(string);
                this._updateConfigFile();
            }
        }
        catch (Exception exception) {
            Log.error("Custom Data DB error:", (Throwable)exception);
        }
    }

    public static void clear(String string) throws Exception {
        CustomDataManager.removeDataFile(string);
        CustomDataManager.updateData(string, 0L, 0L, 0, null);
    }

    public static void removeDataFile(String string) {
        String string2 = CustomDataManager.getDataFileName(string);
        File file = new File(string2);
        if (file.exists() && !file.delete()) {
            Log.error("Unable to delete file " + string2 + ".");
        }
    }

    private synchronized Collection<CustomDataInfo> _list() throws Exception {
        if (!this.dataInfoCache.isEmpty()) {
            return this.dataInfoCache.values();
        }
        ArrayList<CustomDataInfo> arrayList = new ArrayList<CustomDataInfo>();
        Connection connection = null;
        Statement statement = null;
        ResultSet resultSet = null;
        connection = this.getConnection();
        statement = connection.createStatement();
        resultSet = statement.executeQuery("SELECT * FROM DATA");
        while (resultSet.next()) {
            try {
                CustomDataInfo customDataInfo = new CustomDataInfo();
                customDataInfo.id = resultSet.getInt("ID");
                customDataInfo.name = resultSet.getString("NAME");
                customDataInfo.setValues(resultSet.getString("VALUESOBJECT"));
                customDataInfo.dataType = resultSet.getInt("DATATYPE");
                customDataInfo.timeframe = resultSet.getString("TIMEFRAME");
                customDataInfo.filename = resultSet.getString("FILENAME");
                customDataInfo.dateFrom = resultSet.getLong("DATEFROM");
                customDataInfo.dateTo = resultSet.getLong("DATETO");
                customDataInfo.rows = resultSet.getInt("ROWS");
                arrayList.add(customDataInfo);
                this.dataInfoCache.put(customDataInfo.name, customDataInfo);
            }
            catch (Exception exception) {
                Log.error("Error while loading External indicator. Exc.", (Throwable)exception);
            }
        }
        this.close(resultSet);
        this.close(statement);
        this.close(connection);
        return arrayList;
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public void _add(String string, String string2, int n) throws Exception {
        Connection connection = null;
        try {
            connection = this.getConnection();
            if (this._checkDataExists(connection, string)) {
                throw new Exception(String.format("Indicator with name '%s' already exists.", string));
            }
            try {
                new JSONArray(string2);
            }
            catch (Exception exception) {
                throw new Exception("Invalid values object.", exception);
            }
            PreparedStatement preparedStatement = connection.prepareStatement("INSERT INTO DATA (NAME, VALUESOBJECT, DATATYPE) VALUES (?,?,?)", 1);
            preparedStatement.setString(1, string);
            preparedStatement.setString(2, string2);
            preparedStatement.setInt(3, n);
            int n2 = this.sqlInsertReturnAutoId(connection, preparedStatement);
            CustomDataInfo customDataInfo = new CustomDataInfo();
            customDataInfo.id = n2;
            customDataInfo.name = string;
            customDataInfo.setValues(string2);
            customDataInfo.dataType = n;
            HashMap<String, CustomDataInfo> hashMap = this.dataInfoCache;
            synchronized (hashMap) {
                this.dataInfoCache.put(string, customDataInfo);
                this._updateConfigFile();
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

    public static void updateConfigFile() {
        CustomDataManager.get()._updateConfigFileLock();
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private void _updateConfigFileLock() {
        HashMap<String, CustomDataInfo> hashMap = this.dataInfoCache;
        synchronized (hashMap) {
            this._updateConfigFile();
        }
    }

    private void _updateConfigFile() {
        try {
            Element element = new Element("CustomDataIndys");
            for (CustomDataInfo customDataInfo : this.dataInfoCache.values()) {
                if (customDataInfo.values <= 0) continue;
                Element element2 = new Element("Item");
                element2.setAttribute("key", "CDataIndy_" + customDataInfo.name);
                try {
                    element2.setAttribute("returnType", CustomDataTypes.translateDataType((byte)customDataInfo.dataType));
                    if (customDataInfo.dataType == 10) {
                        element2.setAttribute("categoryType", "simpleRules");
                    } else {
                        element2.setAttribute("categoryType", "indicator");
                    }
                }
                catch (Exception exception) {
                    Log.error("Error setting custom indocator return type! DataType=" + customDataInfo.dataType, (Throwable)exception);
                }
                Element element3 = new Element("Param");
                element3.setAttribute("key", "#Shift#");
                element3.setAttribute("controlType", "jspinnerVar");
                element3.setAttribute("type", "int");
                element3.setText("0");
                element2.addContent((Content)element3);
                element3 = new Element("Param");
                element3.setAttribute("key", "#Value#");
                element3.setAttribute("controlType", "combo");
                element3.setAttribute("type", "int");
                String string = CustomDataManager.createCDataValues(customDataInfo.values, customDataInfo);
                element3.setAttribute("values", string);
                element3.setText("0");
                element2.addContent((Content)element3);
                element.addContent((Content)element2);
            }
            String string = XMLUtil.elementToString((Element)element);
            SQUtils.stringToFile((String)SQPaths.algoWizardCustomDataIndysPath, (String)string);
        }
        catch (Exception exception) {
            Log.error("Cannot save custom data indicators config!");
        }
    }

    public static boolean configFileExists() {
        File file = new File(SQPaths.algoWizardCustomDataIndysPath);
        return file.exists();
    }

    public static String createCDataValues(int n, CustomDataInfo customDataInfo) throws Exception {
        try {
            StringBuilder stringBuilder = new StringBuilder();
            for (int i = 0; i < n; ++i) {
                if (i > 0) {
                    stringBuilder.append(",");
                }
                stringBuilder.append(customDataInfo.getValue(i, "name"));
                stringBuilder.append("=");
                stringBuilder.append(i);
            }
            return stringBuilder.toString();
        }
        catch (Exception exception) {
            throw new Exception("Cannot init Custom Data Indicators", exception);
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public void _update(String string, String string2, String string3, int n) throws Exception {
        Connection connection = null;
        try {
            CustomDataInfo customDataInfo = this.getRecordFromCache(string);
            try {
                new JSONArray(string3);
            }
            catch (Exception exception) {
                throw new Exception("Invalid values object.", exception);
            }
            connection = this.getConnection();
            PreparedStatement preparedStatement = connection.prepareStatement("UPDATE DATA SET NAME = ?, VALUESOBJECT = ?, DATATYPE = ? WHERE NAME = ?");
            preparedStatement.setString(1, string2);
            preparedStatement.setString(2, string3);
            preparedStatement.setInt(3, n);
            preparedStatement.setString(4, string);
            this.sqlCommand(connection, preparedStatement);
            customDataInfo.name = string2;
            customDataInfo.setValues(string3);
            customDataInfo.dataType = n;
            HashMap<String, CustomDataInfo> hashMap = this.dataInfoCache;
            synchronized (hashMap) {
                this.dataInfoCache.remove(string);
                this.dataInfoCache.put(string2, customDataInfo);
                this._updateConfigFile();
            }
        }
        catch (Exception exception) {
            try {
                Log.error("Custom Data DB error:", (Throwable)exception);
                throw exception;
            }
            catch (Throwable throwable) {
                this.close(connection);
                throw throwable;
            }
        }
        this.close(connection);
    }

    public void _updateData(String string, long l, long l2, int n, String string2) throws Exception {
        try {
            CustomDataInfo customDataInfo = this.getRecordFromCache(string);
            String string3 = "UPDATE DATA SET DATEFROM='" + l + "',DATETO='" + l2 + "',ROWS=" + n + ",TIMEFRAME='" + string2 + "' WHERE NAME ='" + string + "'";
            if (string2 == null) {
                string3 = "UPDATE DATA SET DATEFROM='" + l + "',DATETO='" + l2 + "',ROWS=" + n + ",TIMEFRAME=NULL WHERE NAME ='" + string + "'";
            }
            this.sqlCommand(string3);
            customDataInfo.dateFrom = l;
            customDataInfo.dateTo = l2;
            customDataInfo.rows = n;
            customDataInfo.timeframe = string2;
        }
        catch (Exception exception) {
            Log.error("Custom Data DB error:", (Throwable)exception);
            throw exception;
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private boolean _checkDataExists(String string) {
        HashMap<String, CustomDataInfo> hashMap = this.dataInfoCache;
        synchronized (hashMap) {
            boolean bl;
            String string2 = string;
            if (this.dataInfoCache.containsKey(string2)) {
                return true;
            }
            Connection connection = null;
            try {
                connection = this.getConnection();
                bl = this._checkDataExists(connection, string);
            }
            catch (Exception exception) {
                boolean bl2;
                try {
                    Log.error("DB Exception", (Throwable)exception);
                    bl2 = false;
                }
                catch (Throwable throwable) {
                    this.close(connection);
                    throw throwable;
                }
                this.close(connection);
                return bl2;
            }
            this.close(connection);
            return bl;
        }
    }

    private boolean _checkDataExists(Connection connection, String string) {
        String string2 = "SELECT * FROM DATA WHERE NAME='" + string + "'";
        return this.sqlCheckRecordExists(connection, string2);
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     * Enabled force condition propagation
     * Lifted jumps to return sites
     */
    private synchronized CustomDataInfo _getDataInfo(String string) {
        HashMap<String, CustomDataInfo> hashMap = this.dataInfoCache;
        synchronized (hashMap) {
            ResultSet resultSet;
            Statement statement;
            Connection connection;
            block14: {
                CustomDataInfo customDataInfo;
                block13: {
                    if (this.dataInfoCache.containsKey(string)) {
                        return this.dataInfoCache.get(string);
                    }
                    connection = null;
                    statement = null;
                    resultSet = null;
                    connection = this.getConnection();
                    if (this._checkDataExists(connection, string)) break block13;
                    CustomDataInfo customDataInfo2 = null;
                    this.close(resultSet);
                    this.close(statement);
                    this.close(connection);
                    return customDataInfo2;
                }
                try {
                    CustomDataInfo customDataInfo3 = new CustomDataInfo();
                    String string2 = "SELECT * FROM DATA WHERE NAME='" + string + "'";
                    statement = connection.createStatement();
                    resultSet = statement.executeQuery(string2);
                    if (!resultSet.next()) break block14;
                    customDataInfo3.id = resultSet.getInt("ID");
                    customDataInfo3.name = resultSet.getString("NAME");
                    customDataInfo3.setValues(resultSet.getString("VALUESOBJECT"));
                    customDataInfo3.dataType = resultSet.getInt("DATATYPE");
                    customDataInfo3.timeframe = resultSet.getString("TIMEFRAME");
                    customDataInfo3.filename = resultSet.getString("FILENAME");
                    customDataInfo3.dateFrom = resultSet.getLong("DATEFROM");
                    customDataInfo3.dateTo = resultSet.getLong("DATETO");
                    customDataInfo3.rows = resultSet.getInt("ROWS");
                    this.dataInfoCache.put(string, customDataInfo3);
                    customDataInfo = customDataInfo3;
                }
                catch (Exception exception) {
                    CustomDataInfo customDataInfo4;
                    try {
                        Log.error("DB Exception", (Throwable)exception);
                        customDataInfo4 = null;
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
                    return customDataInfo4;
                }
                this.close(resultSet);
                this.close(statement);
                this.close(connection);
                return customDataInfo;
            }
            this.close(resultSet);
            this.close(statement);
            this.close(connection);
            return null;
        }
    }

    private CustomDataInfo getRecordFromCache(String string) {
        return this.dataInfoCache.get(string);
    }

    public static String getDataFileName(String string) {
        return CustomDataManager.get()._getDataFileName(string);
    }

    private String _getDataFileName(String string) {
        String string2 = string + ".dat";
        return this._getDirectory() + "/" + CustomDataManager.fixFilename(string2);
    }

    public static String fixFilename(String string) {
        return string.replaceAll("[^a-zA-Z0-9.-@#()]", "_");
    }

    public static void addCDataIndySourceCodes(Element element) throws Exception {
        CTCustomIndicators cTCustomIndicators = null;
        Element element2 = element.getChild("Strategy").getChild("CustomIndicators");
        if (element2 != null && !element2.getChildren().isEmpty()) {
            cTCustomIndicators = new CTCustomIndicators(element2);
        }
        CustomDataManager.get()._addCDataIndySourceCodes(element, cTCustomIndicators);
    }

    private void _addCDataIndySourceCodes(Element element, CTCustomIndicators cTCustomIndicators) throws Exception {
        String string;
        Object object;
        if (element.getName().equals("Item") && (object = element.getAttributeValue("key")) != null && ((String)object).startsWith("CDataIndy") && (string = CustomDataManager.getCDataIndyId((String)object)) != null) {
            if (cTCustomIndicators == null) {
                this._addSourceCodesToItem(element, string);
            } else {
                cTCustomIndicators.addSourceCodesToItem(element, string);
            }
        }
        if ((object = element.getChildren()) != null && object.size() > 0) {
            for (int i = 0; i < object.size(); ++i) {
                Element element2 = (Element)object.get(i);
                if (element2.getName().equals("CustomIndicators")) continue;
                this._addCDataIndySourceCodes(element2, cTCustomIndicators);
            }
        }
    }

    public static String getCDataIndyId(String string) {
        if (string.length() <= 10) {
            return null;
        }
        return string.substring(10);
    }

    private void _addSourceCodesToItem(Element element, String string) {
        String string2;
        element.setAttribute("cdataIndyName", string);
        CustomDataInfo customDataInfo = CustomDataManager.getDataInfo(string);
        if (customDataInfo == null) {
            Log.debug("Cannot load data info for CustomIndicator {}", (Object)string);
            element.setAttribute("mt4", "");
            element.setAttribute("mt5", "");
            element.setAttribute("el", "");
            element.setAttribute("jf", "");
            return;
        }
        int n = 0;
        Element element2 = XMLUtil.findFirstWithKey((Element)element, (String)"Param", (String)"#Value#");
        if (element2 != null && (string2 = element2.getText()) != null && !string2.equals("")) {
            n = Integer.parseInt(string2);
        }
        try {
            String string3 = customDataInfo.getValue(n, "mt4");
            if (string3 == null) {
                string3 = "";
            }
            element.setAttribute("mt4", string3);
            string3 = customDataInfo.getValue(n, "mt5");
            if (string3 == null) {
                string3 = "";
            }
            element.setAttribute("mt5", string3);
            string3 = customDataInfo.getValue(n, "el");
            if (string3 == null) {
                string3 = "";
            }
            element.setAttribute("el", string3);
        }
        catch (Exception exception) {
            Log.error("Cannot load Src value", (Throwable)exception);
        }
    }

    public static void add(SCustomIndicator sCustomIndicator) throws Exception {
        String string = sCustomIndicator.shortName;
        JSONArray jSONArray = new JSONArray();
        for (int i = 0; i < 3; ++i) {
            Object object;
            String string2 = null;
            String string3 = null;
            String string4 = null;
            String string5 = null;
            try {
                string2 = sCustomIndicator.outputList.get(i);
                object = "";
                for (int j = 0; j < sCustomIndicator.parameterList.size(); ++j) {
                    SParameter sParameter = sCustomIndicator.parameterList.get(j);
                    object = sParameter.type.equals("string") || sParameter.type.equals("color") ? (String)object + "\\\"" + sParameter.value + "\\\"" : (String)object + sParameter.value;
                    if (j >= sCustomIndicator.parameterList.size() - 1) continue;
                    object = (String)object + ",";
                }
                string4 = String.format("iCustom(NULL, 0, \"%s\",%s %d, #Shift#)", string, ((String)object).isBlank() ? "" : (String)object + ",", i);
                string5 = String.format("iCustom(NULL, 0, \"%s\",%s)", string, object, i);
                string3 = String.format("%s.%s[#Shift#]", string, string2.equals(string) ? "Main" : string2);
            }
            catch (Exception exception) {
                // empty catch block
            }
            object = new JSONObject();
            object.put("name", string2 == null ? JSONObject.NULL : string2);
            object.put("el", string3 == null ? JSONObject.NULL : string3);
            object.put("mt4", string4 == null ? JSONObject.NULL : string4);
            object.put("mt5", string5 == null ? JSONObject.NULL : string5);
            jSONArray.put(object);
        }
        CustomDataManager.add(string, jSONArray.toString(), sCustomIndicator.returnType);
    }

    public static void checkData() {
        try {
            Collection<CustomDataInfo> collection = CustomDataManager.get()._list();
            for (CustomDataInfo customDataInfo : collection) {
                File file;
                if (customDataInfo.rows <= 0 || (file = new File(CustomDataManager.getDataFileName(customDataInfo.name))).exists() && file.length() != 0L) continue;
                CustomDataManager.clear(customDataInfo.name);
            }
        }
        catch (Exception exception) {
            Log.error("Error while checking Custom data.", (Throwable)exception);
        }
    }
}

