/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.lib.constants.SQPaths
 *  com.strategyquant.lib.utils.Pair
 *  org.apache.commons.io.IOUtils
 *  org.apache.http.client.methods.CloseableHttpResponse
 *  org.apache.http.client.methods.HttpGet
 *  org.apache.http.client.methods.HttpUriRequest
 *  org.apache.http.impl.client.CloseableHttpClient
 *  org.apache.http.impl.client.HttpClientBuilder
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.datalib.broker;

import com.strategyquant.datalib.basket.BasketBrokerDev;
import com.strategyquant.datalib.broker.BrokerDto;
import com.strategyquant.datalib.broker.BrokerStockDto;
import com.strategyquant.datalib.data.DataDb;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.lib.constants.SQPaths;
import com.strategyquant.lib.utils.Pair;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.StandardOpenOption;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.Date;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;
import org.apache.commons.io.IOUtils;
import org.apache.http.client.methods.CloseableHttpResponse;
import org.apache.http.client.methods.HttpGet;
import org.apache.http.client.methods.HttpUriRequest;
import org.apache.http.impl.client.CloseableHttpClient;
import org.apache.http.impl.client.HttpClientBuilder;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class BrokerManager
extends DataDb {
    public static final String DEFAULT_BROKER = "SQ default";
    private static final Logger Log = LoggerFactory.getLogger(BrokerManager.class);
    public static final String NO_BROKER = "No filter";
    private static final String BROKERS_VERSION = "brokers.version";
    private static final String version = "v2";
    private static final String insertBrokerSQL = "INSERT INTO BROKER (NAME, DESC, SYSTEM, MT_USE, MT_TIMEZONE, POSTFIX, STOCKPICKER_USE)values(?,?,?,?,?,?,?)";
    private static final String updateBrokerSQL = "UPDATE BROKER set NAME=?, DESC=?, MT_USE=?, MT_TIMEZONE=?, POSTFIX=?, STOCKPICKER_USE=? where ID=?";
    private static final String insertStockSql = "INSERT INTO BROKER_STOCK (BROKER_ID, TICKER) values(?,?)";
    private LinkedHashMap<Integer, BrokerDto> brokerMap;
    private Map<Integer, List<String>> stocksOfBroker;
    private static BrokerManager instance = null;
    private static String url;
    private static String version_url;

    public static void init(String string) throws Exception {
        String string2;
        if (instance != null) {
            throw new Exception("BrokerManager.init() called more than once!");
        }
        instance = new BrokerManager(string);
        String string3 = string2 = BasketBrokerDev.getInstance().isDev() ? "_dev" : "";
        if (MainApp.isBrazilianEdition()) {
            url = "http://autoupdate.strategyquant.com/brokers_br_v2" + string2 + "/brokers.zip";
            version_url = "http://autoupdate.strategyquant.com/brokers_br_v2" + string2 + "/brokers.version";
        } else {
            url = "http://autoupdate.strategyquant.com/brokers_v2" + string2 + "/brokers.zip";
            version_url = "http://autoupdate.strategyquant.com/brokers_v2" + string2 + "/brokers.version";
        }
    }

    public void synhronizeAsync(final Runnable runnable) {
        boolean bl;
        boolean bl2 = bl = MainApp.runInConsole() && !MainApp.CLIWebServeActive;
        if (bl) {
            return;
        }
        new Thread(new Runnable(){
            final /* synthetic */ BrokerManager this$0;
            {
                this.this$0 = brokerManager;
            }

            @Override
            public void run() {
                try {
                    instance.sync(runnable);
                }
                catch (Throwable throwable) {
                    Log.error("Error while sync stock group definition", throwable);
                }
            }
        }).start();
    }

    private BrokerManager(String string) {
        super(string);
    }

    public static BrokerManager getInstance() {
        return instance;
    }

    private void sync(Runnable runnable) throws Exception {
        long l = System.currentTimeMillis();
        String string = this.getNewAvailableVersion();
        if (string != null) {
            byte[] byArray = this.download(url);
            Pair pair = this.unzip(byArray);
            String string2 = (String)pair.getA();
            if (string2 == null) {
                return;
            }
            List<BrokerDto> list = this.parse(string2);
            Map map = (Map)pair.getB();
            Map<String, BrokerDto> map2 = this.getSystemBrokersByName();
            for (BrokerDto brokerDto : list) {
                try {
                    Log.debug("Syncing broker: {}", (Object)brokerDto.getName());
                    if (!brokerDto.isMtUse() && MainApp.checkProduct((String)"QDM")) {
                        Log.info("Skipping broker: {}", (Object)brokerDto.getName());
                        continue;
                    }
                    String string3 = (String)map.get(brokerDto.getName());
                    BrokerDto brokerDto2 = map2.get(brokerDto.getName());
                    if (brokerDto2 != null) {
                        brokerDto.setId(brokerDto2.getId());
                    } else {
                        brokerDto.setSystem(true);
                    }
                    this.saveBroker(brokerDto);
                    if (string3 != null) {
                        this.importFromCsv(string3, brokerDto.getId(), "");
                        continue;
                    }
                    this.saveStocks(brokerDto.getId(), new LinkedList<BrokerStockDto>());
                }
                catch (Exception exception) {
                    Log.error("Syncing broker: " + brokerDto.getName() + " failed", (Throwable)exception);
                }
            }
            this.saveLatestVersion(string);
            this.performLoadBrokers();
            if (runnable != null) {
                runnable.run();
            }
        }
        long l2 = System.currentTimeMillis() - l;
        Log.info("Syncing brokers finished in {}ms", (Object)l2);
    }

    private List<BrokerDto> parse(String string) {
        JSONArray jSONArray = new JSONArray(string);
        LinkedList<BrokerDto> linkedList = new LinkedList<BrokerDto>();
        for (int i = 0; i < jSONArray.length(); ++i) {
            JSONObject jSONObject = jSONArray.getJSONObject(i);
            BrokerDto brokerDto = new BrokerDto();
            linkedList.add(brokerDto);
            brokerDto.setName(jSONObject.getString("name"));
            brokerDto.setDesc(jSONObject.getString("description"));
            brokerDto.setStockPickerUse(jSONObject.getBoolean("spUse"));
            brokerDto.setMtUse(jSONObject.getBoolean("mtUse"));
            if (!brokerDto.isMtUse()) continue;
            brokerDto.setPostfix(jSONObject.getString("postfix"));
            brokerDto.setMtTimezone(jSONObject.getString("timezone"));
        }
        return linkedList;
    }

    private void saveLatestVersion(String string) throws IOException {
        Log.debug("Updating data version file");
        File file = new File(SQPaths.dataDirPath, BROKERS_VERSION);
        Files.write(file.toPath(), string.getBytes(), StandardOpenOption.CREATE);
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private Pair unzip(byte[] byArray) throws IOException {
        HashMap<String, String> hashMap = new HashMap<String, String>();
        String string = null;
        byte[] byArray2 = new byte[4096];
        ZipInputStream zipInputStream = new ZipInputStream(new ByteArrayInputStream(byArray));
        try {
            String string2;
            ZipEntry zipEntry = zipInputStream.getNextEntry();
            while (zipEntry != null) {
                byte[] byArray3;
                int n;
                ByteArrayOutputStream byteArrayOutputStream;
                string2 = zipEntry.getName();
                if (string2.endsWith(".csv")) {
                    byteArrayOutputStream = new ByteArrayOutputStream();
                    while ((n = zipInputStream.read(byArray2)) > 0) {
                        byteArrayOutputStream.write(byArray2, 0, n);
                    }
                    byteArrayOutputStream.close();
                    byArray3 = byteArrayOutputStream.toByteArray();
                    String string3 = string2.substring(0, string2.length() - 4);
                    hashMap.put(string3, new String(byArray3));
                } else if (string2.equals("config.json")) {
                    byteArrayOutputStream = new ByteArrayOutputStream();
                    while ((n = zipInputStream.read(byArray2)) > 0) {
                        byteArrayOutputStream.write(byArray2, 0, n);
                    }
                    byteArrayOutputStream.close();
                    byArray3 = byteArrayOutputStream.toByteArray();
                    string = new String(byArray3);
                }
                zipEntry = zipInputStream.getNextEntry();
            }
            string2 = new Pair(string, hashMap);
            return string2;
        }
        finally {
            zipInputStream.closeEntry();
            zipInputStream.close();
        }
    }

    private String getCurrentDownloadedVersion() throws IOException {
        File file = new File(SQPaths.dataDirPath, BROKERS_VERSION);
        if (!file.exists()) {
            return null;
        }
        return new String(Files.readAllBytes(file.toPath()));
    }

    private String getNewAvailableVersion() throws IOException {
        String string = this.getCurrentDownloadedVersion();
        Log.debug("Current version file: {}", (Object)string);
        byte[] byArray = this.download(version_url + "?time=" + new Date().getTime());
        if (byArray == null) {
            return null;
        }
        String string2 = new String(byArray);
        Log.debug("Available version file: {}", (Object)string2);
        if (string == null || string.compareTo(string2) < 0) {
            return string2;
        }
        return null;
    }

    private byte[] download(String string) throws IOException {
        try (CloseableHttpClient closeableHttpClient = HttpClientBuilder.create().build();){
            byte[] byArray;
            CloseableHttpResponse closeableHttpResponse = closeableHttpClient.execute((HttpUriRequest)new HttpGet(string));
            int n = closeableHttpResponse.getStatusLine().getStatusCode();
            if (n != 200) {
                Log.error("Http result: {} for url: {}", (Object)n, (Object)string);
                byte[] byArray2 = null;
                return byArray2;
            }
            InputStream inputStream = closeableHttpResponse.getEntity().getContent();
            byte[] byArray3 = byArray = IOUtils.toByteArray((InputStream)inputStream);
            return byArray3;
        }
    }

    public List<BrokerStockDto> readStocksFromCsv(String string, String string2) throws Exception {
        String[] stringArray = string.split("\n");
        ArrayList<BrokerStockDto> arrayList = new ArrayList<BrokerStockDto>(stringArray.length);
        for (String string3 : stringArray) {
            if ((string3 = string3.trim()).isEmpty()) continue;
            String[] stringArray2 = string3.split(";");
            BrokerStockDto brokerStockDto = new BrokerStockDto();
            brokerStockDto.setTicker(string2 + stringArray2[0]);
            arrayList.add(brokerStockDto);
        }
        return arrayList;
    }

    private long parseDate(String string) {
        try {
            return SQTime.parseToMilis((String)string, (String)"dd.MM.yyyy");
        }
        catch (Exception exception) {
            try {
                return SQTime.parseToMilis((String)string, (String)"yyyy.MM.dd");
            }
            catch (Exception exception2) {
                Log.error("Error while parsing date: " + string);
                return -1L;
            }
        }
    }

    public void importFromCsv(String string, Integer n, String string2) throws Exception {
        List<BrokerStockDto> list = this.readStocksFromCsv(string, string2);
        BrokerDto brokerDto = this.getBroker(n);
        if (brokerDto == null) {
            throw new Exception("Broker was not found.");
        }
        this.saveStocks(n, list);
    }

    public List<BrokerStockDto> updateStocksFromStr(String string, Integer n, String string2) throws Exception {
        List<BrokerStockDto> list = this.readStocksFromCsv(string, string2);
        BrokerDto brokerDto = this.getBroker(n);
        if (brokerDto == null) {
            throw new Exception("Broker was not found.");
        }
        this.saveStocks(n, list);
        List<String> list2 = this.stocksOfBroker.get(brokerDto.getId());
        long l = list2 == null ? 0L : (long)list2.size();
        brokerDto.setCustomizedStocks((int)l);
        return list;
    }

    @Override
    public void initDatabase() {
        try {
            String string;
            if (!this.tableExists("BROKER")) {
                string = "CREATE TABLE BROKER (ID INTEGER PRIMARY KEY AUTOINCREMENT, NAME VARCHAR(50) NOT NULL,SYSTEM BOOLEAN NOT NULL,DESC VARCHAR(250))";
                this.sqlCommand(string);
                Log.debug("Broker table created successfully");
            }
            if (!this.tableExists("BROKER_STOCK")) {
                string = "CREATE TABLE BROKER_STOCK (ID INTEGER PRIMARY KEY AUTOINCREMENT, TICKER VARCHAR(50) NOT NULL,BROKER_ID INTEGER NOT NULL,FOREIGN KEY(BROKER_ID) REFERENCES BROKER(ID))";
                this.sqlCommand(string);
                Log.debug("Broker's stock table created successfully");
            }
            if (!this.columnExists("BROKER", "STOCKPICKER_USE")) {
                string = "ALTER TABLE BROKER ADD STOCKPICKER_USE INTEGER DEFAULT 0";
                this.sqlCommand(string);
            }
            if (!this.columnExists("BROKER", "MT_USE")) {
                string = "ALTER TABLE BROKER ADD MT_USE INTEGER DEFAULT 0";
                this.sqlCommand(string);
            }
            if (!this.columnExists("BROKER", "MT_TIMEZONE")) {
                string = "ALTER TABLE BROKER ADD MT_TIMEZONE VARCHAR(100)";
                this.sqlCommand(string);
            }
            if (!this.columnExists("BROKER", "POSTFIX")) {
                string = "ALTER TABLE BROKER ADD POSTFIX VARCHAR(100)";
                this.sqlCommand(string);
            }
        }
        catch (Exception exception) {
            Log.error("DB error: Cannot create baskets table.", (Throwable)exception);
        }
    }

    /*
     * Enabled aggressive block sorting
     * Enabled unnecessary exception pruning
     * Enabled aggressive exception aggregation
     */
    public BrokerDto getBroker(String string) {
        try (Connection connection = this.getConnection();){
            try (PreparedStatement preparedStatement = connection.prepareStatement("SELECT * FROM BROKER where NAME=?");){
                preparedStatement.setString(1, string);
                ResultSet resultSet = preparedStatement.executeQuery();
                if (resultSet.next()) {
                    BrokerDto brokerDto = this.toBrokerDto(resultSet);
                    return brokerDto;
                }
            }
            preparedStatement = null;
            return preparedStatement;
        }
        catch (Exception exception) {
            Log.error("", (Throwable)exception);
            throw new RuntimeException(L.t((String)"Error while reading data", (Object[])new Object[0]));
        }
    }

    /*
     * Unable to fully structure code
     */
    public synchronized void saveBroker(BrokerDto var1_1) throws Exception {
        v0 = var2_2 = var1_1.getId() == null;
        if (var1_1.getName() == null) {
            throw new IllegalArgumentException("Broker's name must be set");
        }
        var3_3 = var1_1.getName().trim();
        if (!var3_3.startsWith("[")) {
            var3_3 = "[" + var3_3;
        }
        if (!var3_3.endsWith("]")) {
            var3_3 = var3_3 + "]";
        }
        var1_1.setName(var3_3);
        var4_4 = this.getConnection();
        try {
            if (var2_2) {
                if (!var1_1.isSystem() && this.getBroker(var3_3) != null) {
                    throw new IllegalArgumentException("Name must be unique");
                }
                var5_5 = var4_4.prepareStatement("INSERT INTO BROKER (NAME, DESC, SYSTEM, MT_USE, MT_TIMEZONE, POSTFIX, STOCKPICKER_USE)values(?,?,?,?,?,?,?)", 1);
                try {
                    var5_5.setString(1, var3_3);
                    if (var1_1.getDesc() == null) {
                        var5_5.setNull(2, 12);
                    } else {
                        var5_5.setString(2, var1_1.getDesc());
                    }
                    var5_5.setBoolean(3, var1_1.isSystem());
                    var5_5.setInt(4, var1_1.isMtUse() != false ? 1 : 0);
                    var5_5.setString(5, var1_1.getMtTimezone());
                    var5_5.setString(6, var1_1.getPostfix());
                    var5_5.setInt(7, var1_1.isStockPickerUse() != false ? 1 : 0);
                    var5_5.execute();
                    var6_8 = var5_5.getGeneratedKeys();
                    if (!var6_8.next()) ** GOTO lbl60
                    var7_12 = var6_8.getInt(1);
                    var1_1.setId(var7_12);
                }
                finally {
                    if (var5_5 != null) {
                        var5_5.close();
                    }
                }
            } else {
                var5_6 = this.getBroker(var3_3);
                if (var5_6 != null && !var5_6.getId().equals(var1_1.getId())) {
                    throw new IllegalArgumentException("Name must be unique");
                }
                var6_10 = var4_4.prepareStatement("UPDATE BROKER set NAME=?, DESC=?, MT_USE=?, MT_TIMEZONE=?, POSTFIX=?, STOCKPICKER_USE=? where ID=?");
                try {
                    var6_10.setString(1, var3_3);
                    if (var1_1.getDesc() == null) {
                        var6_10.setNull(2, 12);
                    } else {
                        var6_10.setString(2, var1_1.getDesc());
                    }
                    var6_10.setInt(3, var1_1.isMtUse() != false ? 1 : 0);
                    var6_10.setString(4, var1_1.getMtTimezone());
                    var6_10.setString(5, var1_1.getPostfix());
                    var6_10.setInt(6, var1_1.isStockPickerUse() != false ? 1 : 0);
                    var6_10.setInt(7, var1_1.getId());
                    var6_10.execute();
                }
                finally {
                    if (var6_10 != null) {
                        var6_10.close();
                    }
                }
            }
            this.brokerMap.put(var1_1.getId(), var1_1);
        }
        finally {
            if (var4_4 != null) {
                var4_4.close();
            }
        }
        this.refresh();
    }

    public void saveStocks(int n, List<BrokerStockDto> list) {
        try (Connection connection = this.getConnection();){
            try {
                connection.setAutoCommit(false);
                try (PreparedStatement preparedStatement = connection.prepareStatement("delete from broker_stock where broker_id=?");){
                    preparedStatement.setInt(1, n);
                    preparedStatement.executeUpdate();
                    this.stocksOfBroker.put(n, new LinkedList());
                    for (BrokerStockDto brokerStockDto : list) {
                        PreparedStatement preparedStatement2 = connection.prepareStatement(insertStockSql);
                        try {
                            preparedStatement2.setInt(1, n);
                            preparedStatement2.setString(2, brokerStockDto.getTicker());
                            preparedStatement2.executeUpdate();
                            this.stocksOfBroker.get(n).add(brokerStockDto.getTicker());
                        }
                        finally {
                            if (preparedStatement2 == null) continue;
                            preparedStatement2.close();
                        }
                    }
                }
                connection.commit();
            }
            catch (Exception exception) {
                connection.rollback();
                throw exception;
            }
        }
        catch (Exception exception) {
            Log.error("", (Throwable)exception);
            throw new RuntimeException(L.t((String)"Error while saving data", (Object[])new Object[0]));
        }
    }

    public List<String> getStocks(int n) {
        LinkedList linkedList;
        if (this.stocksOfBroker == null) {
            this.performLoadBrokers();
        }
        return (linkedList = this.stocksOfBroker.get(n)) == null ? new LinkedList() : linkedList;
    }

    public synchronized BrokerDto deleteBroker(int n, boolean bl) throws Exception {
        BrokerDto brokerDto = this.getBroker(n);
        if (brokerDto == null) {
            throw new RuntimeException(L.t((String)"Broker was not found.", (Object[])new Object[0]));
        }
        if (!bl && this.isUsedByMt(n)) {
            throw new RuntimeException(L.t((String)"Broker is used and can't be deleted.", (Object[])new Object[0]));
        }
        this.sqlCommand("delete from broker_stock where broker_id=" + n);
        this.sqlCommand("DELETE FROM broker WHERE ID=" + n);
        this.brokerMap.remove(n);
        this.stocksOfBroker.remove(n);
        return brokerDto;
    }

    public boolean isUsedByMt(int n) throws SQLException {
        try (Connection connection = this.getConnection();){
            ResultSet resultSet;
            try (PreparedStatement preparedStatement = connection.prepareStatement("SELECT * FROM instruments where broker_id=?");){
                preparedStatement.setInt(1, n);
                resultSet = preparedStatement.executeQuery();
                try {
                    if (resultSet.next()) {
                        boolean bl = true;
                        return bl;
                    }
                }
                finally {
                    if (resultSet != null) {
                        resultSet.close();
                    }
                }
            }
            preparedStatement = connection.prepareStatement("SELECT * FROM sessions where broker_id=?");
            try {
                preparedStatement.setInt(1, n);
                resultSet = preparedStatement.executeQuery();
                try {
                    if (resultSet.next()) {
                        boolean bl = true;
                        return bl;
                    }
                }
                finally {
                    if (resultSet != null) {
                        resultSet.close();
                    }
                }
            }
            finally {
                if (preparedStatement != null) {
                    preparedStatement.close();
                }
            }
        }
        return false;
    }

    private Map<String, BrokerDto> getSystemBrokersByName() {
        return this.getAllBrokers().stream().filter(brokerDto -> brokerDto.isSystem()).collect(Collectors.toMap(BrokerDto::getName, brokerDto -> brokerDto));
    }

    public void refresh() {
        this.performLoadBrokers();
    }

    private synchronized void performLoadBrokers() {
        try (Connection connection = this.getConnection();){
            Object object;
            this.brokerMap = new LinkedHashMap();
            this.stocksOfBroker = new HashMap<Integer, List<String>>();
            try (Object object3 = connection.createStatement();
                 ResultSet object22 = object3.executeQuery("SELECT * FROM BROKER ORDER BY NAME");){
                while (object22.next()) {
                    BrokerDto brokerDto = this.toBrokerDto(object22);
                    this.brokerMap.put(brokerDto.getId(), brokerDto);
                }
            }
            object3 = connection.createStatement();
            try (ResultSet resultSet = object3.executeQuery("SELECT * FROM BROKER_STOCK");){
                while (resultSet.next()) {
                    int n = resultSet.getInt("BROKER_ID");
                    List<String> list = this.stocksOfBroker.get(n);
                    if (list == null) {
                        list = new LinkedList<String>();
                        this.stocksOfBroker.put(n, list);
                    }
                    object = this.toStockDto(resultSet);
                    list.add(((BrokerStockDto)object).getTicker());
                }
            }
            finally {
                if (object3 != null) {
                    object3.close();
                }
            }
            for (Integer n : this.stocksOfBroker.keySet()) {
                List<String> list = this.stocksOfBroker.get(n);
                this.brokerMap.get(n).setCustomizedStocks(list.size());
            }
            object3 = connection.createStatement();
            try (ResultSet resultSet = object3.executeQuery("SELECT BROKER_ID, count(*) as CNT FROM instruments where broker_id<>-1 group by broker_id");){
                while (resultSet.next()) {
                    int n = resultSet.getInt("BROKER_ID");
                    int n2 = resultSet.getInt("CNT");
                    object = this.brokerMap.get(n);
                    if (object == null) continue;
                    ((BrokerDto)object).setCustomizedInstruments(n2);
                }
            }
            finally {
                if (object3 != null) {
                    object3.close();
                }
            }
            object3 = connection.createStatement();
            try (ResultSet resultSet = object3.executeQuery("SELECT BROKER_ID, count(*) as CNT FROM sessions where broker_id<>-1 group by broker_id");){
                while (resultSet.next()) {
                    int n = resultSet.getInt("BROKER_ID");
                    int n3 = resultSet.getInt("CNT");
                    object = this.brokerMap.get(n);
                    if (object == null) continue;
                    ((BrokerDto)object).setCustomizedSessions(n3);
                }
            }
            finally {
                if (object3 != null) {
                    object3.close();
                }
            }
        }
        catch (Exception exception) {
            Log.error("", (Throwable)exception);
            throw new RuntimeException(L.t((String)"Error while reading data", (Object[])new Object[0]));
        }
    }

    public synchronized List<BrokerDto> getAllBrokers() {
        if (this.brokerMap == null) {
            this.performLoadBrokers();
        }
        return this.brokerMap.values().stream().collect(Collectors.toList());
    }

    /*
     * Enabled aggressive block sorting
     * Enabled unnecessary exception pruning
     * Enabled aggressive exception aggregation
     */
    public BrokerDto getSystemBroker(String string) {
        try (Connection connection = this.getConnection();){
            try (PreparedStatement preparedStatement = connection.prepareStatement("SELECT * FROM STOCK_GROUP where NAME=? AND SYSTEM=?");){
                preparedStatement.setString(1, string);
                preparedStatement.setBoolean(2, true);
                ResultSet resultSet = preparedStatement.executeQuery();
                if (resultSet.next()) {
                    BrokerDto brokerDto = new BrokerDto();
                    brokerDto.setId(resultSet.getInt("ID"));
                    brokerDto.setName(resultSet.getString("NAME"));
                    brokerDto.setDesc(resultSet.getString("DESC"));
                    brokerDto.setSystem(resultSet.getBoolean("SYSTEM"));
                    BrokerDto brokerDto2 = brokerDto;
                    return brokerDto2;
                }
            }
            preparedStatement = null;
            return preparedStatement;
        }
        catch (Exception exception) {
            Log.error("", (Throwable)exception);
            throw new RuntimeException(L.t((String)"Error while reading data", (Object[])new Object[0]));
        }
    }

    public synchronized BrokerDto getBroker(Integer n) {
        if (this.brokerMap == null) {
            this.performLoadBrokers();
        }
        if (n.equals(-1)) {
            return this.getDefaultBroker();
        }
        BrokerDto brokerDto = this.brokerMap.get(n);
        return brokerDto;
    }

    public BrokerDto getDefaultBroker() {
        BrokerDto brokerDto = new BrokerDto();
        brokerDto.setId(-1);
        brokerDto.setName(DEFAULT_BROKER);
        brokerDto.setPostfix("");
        return brokerDto;
    }

    public String getBrokerName(int n) {
        BrokerDto brokerDto = BrokerManager.getInstance().getBroker(n);
        return brokerDto == null ? DEFAULT_BROKER : brokerDto.getName();
    }

    private BrokerDto toBrokerDto(ResultSet resultSet) throws SQLException {
        BrokerDto brokerDto = new BrokerDto();
        brokerDto.setId(resultSet.getInt("ID"));
        brokerDto.setName(resultSet.getString("NAME"));
        brokerDto.setDesc(resultSet.getString("DESC"));
        brokerDto.setSystem(resultSet.getBoolean("SYSTEM"));
        brokerDto.setMtTimezone(resultSet.getString("MT_TIMEZONE"));
        brokerDto.setMtUse(resultSet.getInt("MT_USE") == 1);
        brokerDto.setStockPickerUse(resultSet.getInt("STOCKPICKER_USE") == 1);
        brokerDto.setPostfix(resultSet.getString("POSTFIX"));
        return brokerDto;
    }

    private BrokerStockDto toStockDto(ResultSet resultSet) throws SQLException {
        BrokerStockDto brokerStockDto = new BrokerStockDto();
        brokerStockDto.setId(resultSet.getInt("ID"));
        brokerStockDto.setTicker(resultSet.getString("TICKER"));
        return brokerStockDto;
    }

    public String getBrokerDependantName(String string, int n) {
        if (n != -1) {
            BrokerDto brokerDto = BrokerManager.getInstance().getBroker(n);
            if (brokerDto == null) {
                throw new RuntimeException(L.t((String)"Selected broker doesn't exists", (Object[])new Object[0]));
            }
            string = string + brokerDto.getPostfix();
        }
        return string;
    }

    public boolean checkBrokerExists(String string) {
        if (this.brokerMap == null) {
            this.performLoadBrokers();
        }
        for (BrokerDto brokerDto : this.brokerMap.values()) {
            if (!brokerDto.getName().equals(string)) continue;
            return true;
        }
        return false;
    }
}

