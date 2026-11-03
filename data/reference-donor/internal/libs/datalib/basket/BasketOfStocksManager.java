/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.lib.constants.SQPaths
 *  org.apache.commons.io.IOUtils
 *  org.apache.http.client.methods.CloseableHttpResponse
 *  org.apache.http.client.methods.HttpGet
 *  org.apache.http.client.methods.HttpUriRequest
 *  org.apache.http.impl.client.CloseableHttpClient
 *  org.apache.http.impl.client.HttpClientBuilder
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.datalib.basket;

import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.basket.BasketBrokerDev;
import com.strategyquant.datalib.basket.BasketDto;
import com.strategyquant.datalib.basket.StockDto;
import com.strategyquant.datalib.data.DataDb;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.lib.constants.SQPaths;
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
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;
import org.apache.commons.io.IOUtils;
import org.apache.http.client.methods.CloseableHttpResponse;
import org.apache.http.client.methods.HttpGet;
import org.apache.http.client.methods.HttpUriRequest;
import org.apache.http.impl.client.CloseableHttpClient;
import org.apache.http.impl.client.HttpClientBuilder;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class BasketOfStocksManager
extends DataDb {
    private static final Logger Log = LoggerFactory.getLogger(BasketOfStocksManager.class);
    private static final String GROUP_OF_STOCKS_VERSION = "group_of_stocks.version";
    private static final String version = "v2";
    public static final String LimitedGroupName = "[[S&P 100 limited]]";
    private static BasketOfStocksManager instance = null;
    private static final String insertBasketSQL = "INSERT INTO STOCK_GROUP (NAME, DESC, SYSTEM)values(?,?, ?)";
    private static final String updateBasketSQL = "UPDATE STOCK_GROUP set NAME=?, DESC=? where ID=?";
    private static final String insertStockSql = "INSERT INTO STOCK (BASKET_ID, TICKER, DATE_FROM, DATE_TO) values(?,?,?,?)";
    private Map<String, StockDto> quickStockMap = new HashMap<String, StockDto>();
    private Map<String, Set<Integer>> groupsForStocks = new HashMap<String, Set<Integer>>();
    private Map<Integer, List<StockDto>> stocksOfGroup;
    private LinkedHashMap<Integer, BasketDto> groupsMap;
    private Map<Integer, List<StockDto>> customStocksOfGroup = new HashMap<Integer, List<StockDto>>();
    private LinkedHashMap<Integer, BasketDto> customGroupsMap = new LinkedHashMap();
    private String url;
    private String version_url;
    private boolean devel = false;

    public static void init(String string) throws Exception {
        if (instance != null) {
            throw new Exception("BasketOfStocksManager.init() called more than once!");
        }
        instance = new BasketOfStocksManager(string);
    }

    private void checkDevelMode() {
        File file = new File(MainApp.getDataPath() + "/usenewdata.txt");
        if (file.exists()) {
            Log.info("Using development mode for downloading data. So it means that test data will be downloaded instead of real one!!!!!!!!!!");
            this.devel = true;
        }
    }

    public void synhronizeAsync(final Runnable runnable) {
        boolean bl;
        boolean bl2 = bl = MainApp.runInConsole() && !MainApp.CLIWebServeActive;
        if (bl) {
            return;
        }
        new Thread(new Runnable(){
            final /* synthetic */ BasketOfStocksManager this$0;
            {
                this.this$0 = basketOfStocksManager;
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

    private BasketOfStocksManager(String string) {
        super(string);
        String string2 = BasketBrokerDev.getInstance().isDev() ? "_dev" : "";
        this.url = "http://autoupdate.strategyquant.com/stockgroups_v2" + string2 + "/stocks.zip";
        this.version_url = "http://autoupdate.strategyquant.com/stockgroups_v2" + string2 + "/stocks.version";
        this.checkDevelMode();
        if (this.devel) {
            this.url = "http://autoupdate.strategyquant.com/stockgroups_dev/stocks.zip";
            this.version_url = "http://autoupdate.strategyquant.com/stockgroups_dev/stocks.version";
        }
    }

    public static BasketOfStocksManager getInstance() {
        return instance;
    }

    public void sync(Runnable runnable) throws Exception {
        Log.info("Syncing stockgroup starting");
        long l = System.currentTimeMillis();
        String string = this.getNewAvailableVersion();
        if (string != null) {
            byte[] byArray = this.download(this.url);
            Map<String, String> map = this.unzip(byArray);
            Map<String, BasketDto> map2 = this.getSystemGroupsByName();
            for (String object : map.keySet()) {
                try {
                    Log.debug("Syncing group: {}", (Object)object);
                    String string2 = map.get(object);
                    BasketDto basketDto = map2.get(object);
                    Integer n = null;
                    if (basketDto != null) {
                        n = basketDto.getId();
                        map2.remove(object);
                    }
                    this.importFromCsv(string2, n, object);
                }
                catch (Exception exception) {
                    Log.error("Syncing group: " + object + " failed", (Throwable)exception);
                }
            }
            for (BasketDto basketDto : map2.values()) {
                this.deleteGroup(basketDto.getId());
            }
            this.saveLatestVersion(string);
            this.performLoadGroups();
            if (runnable != null) {
                runnable.run();
            }
        }
        this.checkDataAliases();
        if (string == null) {
            this.updateGroupsOfSymbols();
        }
        long l2 = System.currentTimeMillis() - l;
        Log.info("Syncing stockgroup finished in {}ms", (Object)l2);
    }

    private void saveLatestVersion(String string) throws IOException {
        Log.debug("Updating data version file");
        File file = null;
        file = this.devel ? new File(SQPaths.dataDirPath, "group_of_stocks_dev.version") : new File(SQPaths.dataDirPath, GROUP_OF_STOCKS_VERSION);
        Files.write(file.toPath(), string.getBytes(), StandardOpenOption.CREATE);
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private Map<String, String> unzip(byte[] byArray) throws IOException {
        HashMap<String, String> hashMap = new HashMap<String, String>();
        byte[] byArray2 = new byte[4096];
        ZipInputStream zipInputStream = new ZipInputStream(new ByteArrayInputStream(byArray));
        try {
            Object object;
            ZipEntry zipEntry = zipInputStream.getNextEntry();
            while (zipEntry != null) {
                object = zipEntry.getName();
                if (((String)object).endsWith(".csv")) {
                    int n;
                    ByteArrayOutputStream byteArrayOutputStream = new ByteArrayOutputStream();
                    while ((n = zipInputStream.read(byArray2)) > 0) {
                        byteArrayOutputStream.write(byArray2, 0, n);
                    }
                    byteArrayOutputStream.close();
                    byte[] byArray3 = byteArrayOutputStream.toByteArray();
                    String string = ((String)object).substring(0, ((String)object).length() - 4);
                    hashMap.put(string, new String(byArray3));
                }
                zipEntry = zipInputStream.getNextEntry();
            }
            object = hashMap;
            return object;
        }
        finally {
            zipInputStream.closeEntry();
            zipInputStream.close();
        }
    }

    private String getCurrentDownloadedVersion() throws IOException {
        File file = null;
        file = this.devel ? new File(SQPaths.dataDirPath, "group_of_stocks_dev.version") : new File(SQPaths.dataDirPath, GROUP_OF_STOCKS_VERSION);
        if (!file.exists()) {
            return null;
        }
        return new String(Files.readAllBytes(file.toPath()));
    }

    private String getNewAvailableVersion() throws IOException {
        String string = this.getCurrentDownloadedVersion();
        Log.debug("Current version: {}", (Object)string);
        byte[] byArray = this.download(this.version_url + "?time=" + new Date().getTime());
        if (byArray == null) {
            return null;
        }
        String string2 = new String(byArray);
        Log.debug("Available version: {}", (Object)string2);
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

    public List<StockDto> readStocksFromCsv(String string, String string2) throws Exception {
        String[] stringArray = string.split("\n");
        ArrayList<StockDto> arrayList = new ArrayList<StockDto>(stringArray.length);
        for (String string3 : stringArray) {
            if ((string3 = string3.trim()).isEmpty()) continue;
            String[] stringArray2 = string3.split(";");
            StockDto stockDto = new StockDto();
            stockDto.setTicker(string2 + stringArray2[0]);
            if (stringArray2.length > 1 && !stringArray2[1].isBlank()) {
                stockDto.setDateFrom(this.parseDate(stringArray2[1]));
            } else {
                stockDto.setDateFrom(-1L);
            }
            if (stringArray2.length > 2 && !stringArray2[2].isBlank()) {
                stockDto.setDateTo(this.parseDate(stringArray2[2]));
            } else {
                stockDto.setDateTo(-1L);
            }
            arrayList.add(stockDto);
        }
        if (arrayList.isEmpty()) {
            throw new Exception("No stocks recognized.");
        }
        return arrayList;
    }

    private long parseDate(String string) {
        try {
            string = string.trim();
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
        this.importFromCsv(string, n, string2, "");
    }

    public void importFromCsv(String string, Integer n, String string2, String string3) throws Exception {
        BasketDto basketDto;
        List<StockDto> list = this.readStocksFromCsv(string, string3);
        if (n == null) {
            basketDto = this.getSystemBasket(string2);
            if (basketDto == null) {
                basketDto = new BasketDto();
                basketDto.setSystem(true);
                basketDto.setName(string2);
                this.saveGroup(basketDto);
            }
            n = basketDto.getId();
        }
        if ((basketDto = this.getBasket(n)) == null) {
            throw new Exception("Stockgroup was not found.");
        }
        DataManager.createGroupAlias(basketDto.getName(), n);
        this.saveStocks(n, list);
        this.updateCount(basketDto);
    }

    public List<StockDto> updateStocksFromStr(String string, Integer n, String string2) throws Exception {
        List<StockDto> list = this.readStocksFromCsv(string, string2);
        BasketDto basketDto = this.getBasket(n);
        if (basketDto == null) {
            throw new Exception("Stockgroup was not found.");
        }
        this.saveStocks(n, list);
        this.updateCount(basketDto);
        return list;
    }

    private void updateCount(BasketDto basketDto) {
        List<StockDto> list = this.stocksOfGroup.get(basketDto.getId());
        long l = list == null ? 0L : list.stream().filter(stockDto -> stockDto.isActive()).count();
        basketDto.setCount((int)l);
        basketDto.setTotal(list.size());
    }

    @Override
    public void initDatabase() {
        try {
            String string;
            if (!this.tableExists("STOCK_GROUP")) {
                string = "CREATE TABLE STOCK_GROUP (ID INTEGER PRIMARY KEY AUTOINCREMENT, NAME VARCHAR(50) NOT NULL,SYSTEM BOOLEAN NOT NULL,DESC VARCHAR(250))";
                this.sqlCommand(string);
                Log.debug("Stockgroup table created successfully");
            }
            if (!this.tableExists("STOCK")) {
                string = "CREATE TABLE STOCK (ID INTEGER PRIMARY KEY AUTOINCREMENT, TICKER VARCHAR(50) NOT NULL,BASKET_ID INTEGER NOT NULL,DATE_FROM LONG NOT NULL,DATE_TO LONG,FOREIGN KEY(BASKET_ID) REFERENCES STOCK_GROUP(ID))";
                this.sqlCommand(string);
                Log.debug("Stock table created successfully");
            }
        }
        catch (Exception exception) {
            Log.error("DB error: Cannot create baskets table.", (Throwable)exception);
        }
    }

    /*
     * Unable to fully structure code
     */
    public synchronized void saveGroup(BasketDto var1_1) throws Exception {
        v0 = var2_2 = var1_1.getId() == null;
        if (var1_1.getName() == null) {
            throw new IllegalArgumentException("Group's name must be set");
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
                if (!var1_1.isSystem() && this.getBasket(var3_3) != null) {
                    throw new IllegalArgumentException("Name must be unique");
                }
                var5_5 = var4_4.prepareStatement("INSERT INTO STOCK_GROUP (NAME, DESC, SYSTEM)values(?,?, ?)", 1);
                try {
                    var5_5.setString(1, var3_3);
                    if (var1_1.getDesc() == null) {
                        var5_5.setNull(2, 12);
                    } else {
                        var5_5.setString(2, var1_1.getDesc());
                    }
                    var5_5.setBoolean(3, var1_1.isSystem());
                    var5_5.execute();
                    var6_8 = var5_5.getGeneratedKeys();
                    if (!var6_8.next()) ** GOTO lbl55
                    var7_12 = var6_8.getInt(1);
                    var1_1.setId(var7_12);
                }
                finally {
                    if (var5_5 != null) {
                        var5_5.close();
                    }
                }
            } else {
                var5_6 = this.getBasket(var3_3);
                if (var5_6 != null && !var5_6.getId().equals(var1_1.getId())) {
                    throw new IllegalArgumentException("Name must be unique");
                }
                var6_10 = var4_4.prepareStatement("UPDATE STOCK_GROUP set NAME=?, DESC=? where ID=?");
                try {
                    var7_14 = this.getBasket(var1_1.getId());
                    var6_10.setString(1, var3_3);
                    if (var1_1.getDesc() == null) {
                        var6_10.setNull(2, 12);
                    } else {
                        var6_10.setString(2, var1_1.getDesc());
                    }
                    var6_10.setInt(3, var1_1.getId());
                    var6_10.execute();
                    var1_1.setCount(var7_14.getCount());
                    var1_1.setTotal(var7_14.getTotal());
                }
                finally {
                    if (var6_10 != null) {
                        var6_10.close();
                    }
                }
            }
            this.groupsMap.put(var1_1.getId(), var1_1);
            DataManager.createGroupAlias(var3_3, var1_1.getId());
        }
        finally {
            if (var4_4 != null) {
                var4_4.close();
            }
        }
    }

    /*
     * Enabled aggressive block sorting
     * Enabled unnecessary exception pruning
     * Enabled aggressive exception aggregation
     */
    public BasketDto getBasket(String string) {
        try (Connection connection = this.getConnection();){
            try (PreparedStatement preparedStatement = connection.prepareStatement("SELECT * FROM STOCK_GROUP where NAME=?");){
                preparedStatement.setString(1, string);
                ResultSet resultSet = preparedStatement.executeQuery();
                if (resultSet.next()) {
                    BasketDto basketDto = this.toGroupDto(resultSet);
                    return basketDto;
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

    public Set<Integer> getGroupsForStock(String string) {
        return this.groupsForStocks.get(string);
    }

    public Set<String> updateGroupsOfSymbols() {
        Object object;
        Object object2;
        Object object3;
        Log.info("Updating stockgroup's from-to dates");
        HashMap<Integer, MinMax> hashMap = new HashMap<Integer, MinMax>();
        String[] stringArray = this.getAllSymbolsArray();
        Object object4 = this.stocksOfGroup.keySet().iterator();
        while (object4.hasNext()) {
            int n = object4.next();
            hashMap.put(n, new MinMax());
        }
        object4 = new HashSet();
        Map<String, DataInfo> map = this.getDataInfosMap();
        for (int i = 0; i < stringArray.length; ++i) {
            Object object5 = stringArray[i];
            object3 = map.get(object5);
            if (object3 == null || (object2 = this.getGroupsForStock((String)object5)) == null || ((DataInfo)object3).dateFrom == 0L) continue;
            object = object2.iterator();
            while (object.hasNext()) {
                long l;
                StockDto stockDto;
                Integer n = (Integer)object.next();
                BasketDto basketDto = this.groupsMap.get(n);
                if (basketDto == null) {
                    Log.error("Stockgroup: " + n + " was not found!");
                    continue;
                }
                DataInfo dataInfo = DataManager.getDataInfo("History", basketDto.getName());
                if (dataInfo == null) continue;
                MinMax minMax = (MinMax)hashMap.get(basketDto.getId());
                if (minMax == null) {
                    minMax = new MinMax();
                    hashMap.put(basketDto.getId(), minMax);
                }
                if ((stockDto = this.quickStockMap.get(n + "_" + (String)object5)) == null) continue;
                long l2 = Math.max(((DataInfo)object3).dateFrom, stockDto.getDateFrom());
                long l3 = l = stockDto.getDateTo() == -1L ? ((DataInfo)object3).dateTo : Math.min(((DataInfo)object3).dateTo, stockDto.getDateTo());
                if (minMax.min == 0L || minMax.min > l2) {
                    minMax.min = l2;
                }
                if (minMax.max != 0L && minMax.max >= l) continue;
                minMax.max = l;
            }
        }
        for (Object object5 : hashMap.keySet()) {
            object3 = this.groupsMap.get(object5);
            object2 = DataManager.getDataInfo("History", ((BasketDto)object3).getName());
            Log.debug("Evaluating min/max dates of stock group range: {}", (Object)((DataInfo)object2).symbol);
            object = (MinMax)hashMap.get(object5);
            if (((MinMax)object).min == ((DataInfo)object2).dateFrom && ((MinMax)object).max == ((DataInfo)object2).dateTo) continue;
            Log.debug("Updating stock group {} range: {} - {}", new Object[]{((DataInfo)object2).symbol, SQTime.formatDate((long)((MinMax)object).min), SQTime.formatDate((long)((MinMax)object).max)});
            DataManager.updateData("History", ((DataInfo)object2).symbol, ((MinMax)object).min, ((MinMax)object).max, 1000000, 0L, 1, "D1", "Etc/UCT");
            object4.add(((DataInfo)object2).symbol);
        }
        return object4;
    }

    private Map<String, DataInfo> getDataInfosMap() {
        try {
            DataManager.get();
            ArrayList<DataInfo> arrayList = DataManager.listSafe();
            HashMap<String, DataInfo> hashMap = new HashMap<String, DataInfo>();
            for (DataInfo dataInfo : arrayList) {
                if (dataInfo.symbol == null) continue;
                hashMap.put(dataInfo.symbol, dataInfo);
            }
            return hashMap;
        }
        catch (Exception exception) {
            throw new RuntimeException(L.t((String)"Error while getting datainfos", (Object[])new Object[0]), exception);
        }
    }

    private String[] getAllSymbolsArray() {
        try {
            DataManager.get();
            ArrayList<DataInfo> arrayList = DataManager.listSafe();
            return arrayList.stream().map(dataInfo -> dataInfo.symbol).collect(Collectors.toList()).toArray(new String[0]);
        }
        catch (Exception exception) {
            throw new RuntimeException(L.t((String)"Error while getting datainfos", (Object[])new Object[0]), exception);
        }
    }

    public void updateGroupRange(Integer n) {
        BasketDto basketDto = this.getBasket(n);
        DataInfo dataInfo = DataManager.getDataInfo("History", basketDto.getName());
        if (dataInfo == null) {
            Log.warn("Stock's group alias symbol {} doesn't exist", (Object)basketDto.getName());
            return;
        }
        LinkedList<StockDto> linkedList = new LinkedList<StockDto>(this.getStocks(n));
        long l = 0L;
        long l2 = 0L;
        try {
            Map<String, DataInfo> map = this.getDataInfosMap();
            for (StockDto stockDto : linkedList) {
                long l3;
                String string = stockDto.getTicker();
                DataInfo dataInfo2 = map.get(string);
                StockDto stockDto2 = this.quickStockMap.get(n + "_" + string);
                if (stockDto2 == null || dataInfo2 == null) continue;
                long l4 = Math.max(dataInfo2.dateFrom, stockDto2.getDateFrom());
                long l5 = l3 = stockDto2.getDateTo() == -1L ? dataInfo2.dateTo : Math.min(dataInfo2.dateTo, stockDto2.getDateTo());
                if (l == 0L || l > l4) {
                    l = l4;
                }
                if (l2 != 0L && l2 >= l3) continue;
                l2 = l3;
            }
            if (l != dataInfo.dateFrom || l2 != dataInfo.dateTo) {
                Log.debug("Updating stock group {} range: {} - {}", new Object[]{basketDto.getName(), SQTime.formatDate((long)l), SQTime.formatDate((long)l2)});
                DataManager.updateData("History", basketDto.getName(), l, l2, 1000000, 0L, 1, "D1", "Etc/UCT");
            }
        }
        catch (Exception exception) {
            Log.error("Error while updating group range", (Throwable)exception);
        }
    }

    public void saveCustomStocks(int n, List<StockDto> list) {
        this.customStocksOfGroup.put(n, list);
    }

    public void saveStocks(int n, List<StockDto> list) {
        try (Connection connection = this.getConnection();){
            try {
                connection.setAutoCommit(false);
                try (PreparedStatement preparedStatement = connection.prepareStatement("delete from stock where basket_id=?");){
                    preparedStatement.setInt(1, n);
                    preparedStatement.executeUpdate();
                    this.stocksOfGroup.put(n, new LinkedList());
                    for (StockDto stockDto : list) {
                        PreparedStatement preparedStatement2 = connection.prepareStatement(insertStockSql);
                        try {
                            preparedStatement2.setInt(1, n);
                            preparedStatement2.setString(2, stockDto.getTicker());
                            preparedStatement2.setLong(3, stockDto.getDateFrom() == null ? -1L : stockDto.getDateFrom());
                            preparedStatement2.setLong(4, stockDto.getDateTo() == null ? -1L : stockDto.getDateTo());
                            preparedStatement2.executeUpdate();
                            this.stocksOfGroup.get(n).add(stockDto);
                            this.quickStockMap.put(n + "_" + stockDto.getTicker(), stockDto);
                            String string = stockDto.getTicker();
                            Set<Integer> set = this.groupsForStocks.get(string);
                            if (set == null) {
                                set = new HashSet<Integer>();
                                this.groupsForStocks.put(string, set);
                            }
                            set.add(n);
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
        this.updateGroupRange(n);
    }

    public List<StockDto> getStocks(int n) {
        LinkedList linkedList;
        if (n < 0) {
            return this.customStocksOfGroup.get(n);
        }
        if (this.stocksOfGroup == null) {
            this.performLoadGroups();
        }
        return (linkedList = this.stocksOfGroup.get(n)) == null ? new LinkedList() : linkedList;
    }

    public List<StockDto> getStocks(int n, List<String> list) {
        List<StockDto> list2 = this.getStocks(n);
        if (list == null) {
            return list2;
        }
        LinkedList<StockDto> linkedList = new LinkedList<StockDto>();
        for (StockDto stockDto : list2) {
            if (!list.contains(stockDto.getTicker())) continue;
            linkedList.add(stockDto);
        }
        return linkedList;
    }

    public synchronized BasketDto deleteGroup(int n) throws Exception {
        BasketDto basketDto = this.getBasket(n);
        if (basketDto == null) {
            throw new RuntimeException(L.t((String)"Group was not found.", (Object[])new Object[0]));
        }
        this.sqlCommand("delete from stock where basket_id=" + n);
        this.sqlCommand("DELETE FROM STOCK_GROUP WHERE ID=" + n);
        DataManager.deleteGroupAlias(n, basketDto.getName());
        this.groupsMap.remove(n);
        this.stocksOfGroup.remove(n);
        return basketDto;
    }

    private Map<String, BasketDto> getSystemGroupsByName() {
        return this.getGroups().stream().filter(basketDto -> basketDto.isSystem()).collect(Collectors.toMap(BasketDto::getName, basketDto -> basketDto));
    }

    private synchronized void performLoadGroups() {
        try (Connection connection = this.getConnection();){
            Object object;
            this.groupsMap = new LinkedHashMap();
            this.stocksOfGroup = new HashMap<Integer, List<StockDto>>();
            this.groupsForStocks = new HashMap<String, Set<Integer>>();
            this.quickStockMap = new HashMap<String, StockDto>();
            try (Object object3 = connection.createStatement();
                 ResultSet object22 = object3.executeQuery("SELECT * FROM STOCK_GROUP ORDER BY NAME");){
                while (object22.next()) {
                    BasketDto n = this.toGroupDto(object22);
                    this.groupsMap.put(n.getId(), n);
                }
            }
            object3 = connection.createStatement();
            try (ResultSet resultSet = object3.executeQuery("SELECT * FROM STOCK");){
                while (resultSet.next()) {
                    int list = resultSet.getInt("BASKET_ID");
                    List<StockDto> list2 = this.stocksOfGroup.get(list);
                    if (list2 == null) {
                        list2 = new LinkedList<StockDto>();
                        this.stocksOfGroup.put(list, list2);
                    }
                    StockDto stockDto2 = this.toStockDto(resultSet);
                    list2.add(stockDto2);
                    this.quickStockMap.put(list + "_" + stockDto2.getTicker(), stockDto2);
                    object = stockDto2.getTicker();
                    Set<Integer> set = this.groupsForStocks.get(object);
                    if (set == null) {
                        set = new HashSet<Integer>();
                        this.groupsForStocks.put((String)object, set);
                    }
                    set.add(list);
                }
            }
            finally {
                if (object3 != null) {
                    object3.close();
                }
            }
            for (Integer n : this.stocksOfGroup.keySet()) {
                List<StockDto> list = this.stocksOfGroup.get(n);
                long l = list.stream().filter(stockDto -> stockDto.isActive()).count();
                object = this.groupsMap.get(n);
                ((BasketDto)object).setCount((int)l);
                this.groupsMap.get(n).setTotal(list.size());
            }
        }
        catch (Exception exception) {
            Log.error("", (Throwable)exception);
            throw new RuntimeException(L.t((String)"Error while reading data", (Object[])new Object[0]));
        }
    }

    public synchronized List<BasketDto> getGroups() {
        if (this.groupsMap == null) {
            this.performLoadGroups();
        }
        return this.groupsMap.values().stream().collect(Collectors.toList());
    }

    /*
     * Enabled aggressive block sorting
     * Enabled unnecessary exception pruning
     * Enabled aggressive exception aggregation
     */
    public BasketDto getSystemBasket(String string) {
        try (Connection connection = this.getConnection();){
            try (PreparedStatement preparedStatement = connection.prepareStatement("SELECT * FROM STOCK_GROUP where NAME=? AND SYSTEM=?");){
                preparedStatement.setString(1, string);
                preparedStatement.setBoolean(2, true);
                ResultSet resultSet = preparedStatement.executeQuery();
                if (resultSet.next()) {
                    BasketDto basketDto = new BasketDto();
                    basketDto.setId(resultSet.getInt("ID"));
                    basketDto.setName(resultSet.getString("NAME"));
                    basketDto.setDesc(resultSet.getString("DESC"));
                    basketDto.setSystem(resultSet.getBoolean("SYSTEM"));
                    BasketDto basketDto2 = basketDto;
                    return basketDto2;
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

    public BasketDto getBasket(Integer n) {
        if (n < 0) {
            return this.customGroupsMap.get(n);
        }
        if (this.groupsMap == null) {
            this.performLoadGroups();
        }
        return this.groupsMap.get(n);
    }

    private BasketDto toGroupDto(ResultSet resultSet) throws SQLException {
        BasketDto basketDto = new BasketDto();
        basketDto.setId(resultSet.getInt("ID"));
        basketDto.setName(resultSet.getString("NAME"));
        basketDto.setDesc(resultSet.getString("DESC"));
        basketDto.setSystem(resultSet.getBoolean("SYSTEM"));
        basketDto.setCount(0);
        return basketDto;
    }

    private StockDto toStockDto(ResultSet resultSet) throws SQLException {
        StockDto stockDto = new StockDto();
        stockDto.setId(resultSet.getInt("ID"));
        stockDto.setTicker(resultSet.getString("TICKER"));
        stockDto.setDateFrom(resultSet.getLong("DATE_FROM"));
        stockDto.setDateTo(resultSet.getLong("DATE_TO"));
        return stockDto;
    }

    private void checkDataAliases() {
        try {
            List<BasketDto> list = BasketOfStocksManager.getInstance().getGroups();
            for (int i = 0; i < list.size(); ++i) {
                BasketDto basketDto = list.get(i);
                DataManager.createGroupAlias(basketDto.getName(), basketDto.getId());
            }
        }
        catch (Exception exception) {
            Log.error("Error while checking Data aliases", (Throwable)exception);
        }
    }

    public BasketDto createCustomGroup(String string, int n, String string2, boolean bl, String string3) throws Exception {
        try {
            ArrayList<StockDto> arrayList;
            if (string3 == null) {
                string3 = "local";
            }
            BasketDto basketDto = new BasketDto();
            basketDto.setId(n);
            basketDto.setName("group=" + string);
            basketDto.setDesc(String.format("userID=%s, symbols=%s", string3, string2));
            if (bl) {
                arrayList = new ArrayList();
                StockDto stockDto = new StockDto();
                stockDto.setId(0);
                stockDto.setTicker(string2);
                stockDto.setDateFrom(-1L);
                stockDto.setDateTo(-1L);
                arrayList.add(stockDto);
            } else {
                arrayList = BasketOfStocksManager.getInstance().readStocksFromCsv(string2, "");
            }
            BasketOfStocksManager.getInstance().saveCustomStocks(basketDto.getId(), arrayList);
            this.customGroupsMap.put(n, basketDto);
            return basketDto;
        }
        catch (Exception exception) {
            throw new Exception("Faile to create custom group - " + exception.getMessage(), exception);
        }
    }

    public static int getNumberOfSymbolsInGroup(Set<String> set, BasketDto basketDto) {
        List<StockDto> list = BasketOfStocksManager.getInstance().getStocks(basketDto.getId());
        int n = 0;
        for (StockDto stockDto : list) {
            String string = stockDto.getTicker();
            if (!set.contains(string) && !set.contains(stockDto.getTicker())) continue;
            ++n;
        }
        return n;
    }

    public static int getDownloaded(Map<String, DataInfo> map, Integer n) {
        List<StockDto> list = BasketOfStocksManager.getInstance().getStocks(n);
        int n2 = 0;
        for (StockDto stockDto : list) {
            String string = stockDto.getTicker();
            DataInfo dataInfo = map.get(string);
            if (dataInfo == null) {
                dataInfo = map.get(stockDto.getTicker());
            }
            if (dataInfo == null || dataInfo.dateTo <= 0L) continue;
            ++n2;
        }
        return n2;
    }

    public static boolean isReadyForUse(int n, int n2) {
        return n >= n2 - 3;
    }

    private class MinMax {
        public long min;
        public long max;

        private MinMax() {
        }
    }
}

