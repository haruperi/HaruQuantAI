/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.ChartDef
 *  com.strategyquant.datalib.DataInfo
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.datalib.data.io.IDataLoader
 *  com.strategyquant.datalib.data.io.VersatileData
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.SQUtils
 *  org.jdom2.JDOMException
 */
package com.strategyquant.tradinglib.stockchart;

import com.strategyquant.datalib.ChartDef;
import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.datalib.data.io.IDataLoader;
import com.strategyquant.datalib.data.io.VersatileData;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.tradinglib.blocks.random.BlockDefinition;
import com.strategyquant.tradinglib.blocks.random.BlocksConfig;
import com.strategyquant.tradinglib.stockchart.ChartKind;
import com.strategyquant.tradinglib.stockchart.Indicator;
import com.strategyquant.tradinglib.stockchart.IndicatorLine;
import com.strategyquant.tradinglib.stockchart.PreviewCaption;
import com.strategyquant.tradinglib.stockchart.StockChartData;
import com.strategyquant.tradinglib.stockchart.StockData;
import com.strategyquant.tradinglib.stockchart.Trade;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.ByteBuffer;
import java.util.HashMap;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;
import java.util.jar.JarEntry;
import java.util.jar.JarFile;
import org.jdom2.JDOMException;

public class StockLoaderForStockPicking {
    private static final String[] COLORS = new String[]{"red", "green", "blue", "brown", "orange"};
    private static final int DEFAULT_DATAWIDTH = 250;
    private StockData data;
    private Map<Long, Long> timestampToIdMap;
    private Map<Long, Long> idToTimestampMap;
    private List<Long> timestamps;
    private List<Long> timeline = new LinkedList<Long>();
    private Long fromTime;
    private Long toTime;
    private Long fromId;
    private Long toId;
    private String path;
    private DataInfo dataInfo;
    private IDataLoader loader;
    private Map<String, Integer> orderCounts = new HashMap<String, Integer>();
    private List<String[]> indicators = new LinkedList<String[]>();
    private int timelineFrom = 0;

    public StockData load(JarFile jarFile, Long l, Long l2, Long l3, boolean bl, boolean bl2, String string, Integer n, String string2) throws Exception {
        this.fromId = l;
        this.toId = l2;
        this.path = "Results/" + this.correctResultKey(string);
        this.prepareStructure(jarFile, string2);
        if (string2 == null) {
            string2 = this.data.getStocks()[0];
        }
        this.data.setCurrentStock(string2);
        Integer n2 = this.orderCounts.get(string2);
        this.data.setTradesCount(n2 == null ? 0L : (long)n2.intValue());
        this.prepareLoader(string2);
        if (l3 != null && this.data.getTradesCount() != 0L) {
            this.setDateFromForTrade(jarFile, l3, l, l2);
            if (this.data.getSelectedTrade() != null) {
                bl2 = true;
            }
        }
        if (bl2) {
            this.findFromToIndexes(n);
        }
        this.correctFromTo();
        this.loadData(jarFile, bl, string2);
        this.loadTrades(jarFile, string2);
        this.cleanup();
        return this.data;
    }

    private void loadTimelines(JarFile jarFile, long l) throws IOException {
        JarEntry jarEntry = jarFile.getJarEntry(this.path + "/timelines.dat");
        InputStream inputStream = jarFile.getInputStream(jarEntry);
        byte[] byArray = this.getBytes(inputStream);
        int n = byArray.length / 8;
        ByteBuffer byteBuffer = ByteBuffer.wrap(byArray);
        for (int i = 0; i < n; ++i) {
            long l2 = byteBuffer.getLong();
            this.timeline.add(l2);
            if (this.timelineFrom != 0 || l2 < l) continue;
            this.timelineFrom = i;
        }
        inputStream.close();
    }

    private void prepareLoader(String string) throws Exception {
        this.dataInfo = DataManager.getDataInfo((String)"History", (String)string);
        if (this.dataInfo == null) {
            throw new Exception("No data info found for symbol '" + string + "'.");
        }
        ChartDef chartDef = new ChartDef("History", string, "D1", 0L, SQTime.toLong((int)2100, (int)1, (int)1), 2.5, "History");
        this.loader = DataManager.getDataLoader((ChartDef)chartDef, (int)1, null);
        this.loader.open();
        this.timestamps = new LinkedList<Long>();
        this.timestampToIdMap = new HashMap<Long, Long>();
        this.idToTimestampMap = new HashMap<Long, Long>();
        VersatileData versatileData = new VersatileData();
        long l = 0L;
        while (this.loader.hasNextTick()) {
            this.loader.getNextTick(versatileData);
            long l2 = versatileData.time;
            this.timestamps.add(l2);
            this.timestampToIdMap.put(l2, l);
            this.idToTimestampMap.put(l, l2);
            ++l;
        }
    }

    private void fillPreview(StockData stockData, long l, IDataLoader iDataLoader) throws Exception {
        double d;
        int n;
        int n2 = 1000;
        if (l < (long)n2) {
            n = (int)l;
            d = 1.0;
        } else {
            d = (double)l / (double)n2;
            n = n2;
        }
        LinkedList<PreviewCaption> linkedList = new LinkedList<PreviewCaption>();
        float[] fArray = new float[n];
        double d2 = 0.0;
        Integer n3 = null;
        VersatileData versatileData = new VersatileData();
        for (int i = 0; d2 < (double)l && i < n; d2 += d, ++i) {
            iDataLoader.seek((int)d2);
            iDataLoader.hasNextTick();
            iDataLoader.getNextTick(versatileData);
            fArray[i] = (float)((double)Math.round(versatileData.close * 10000.0) / 10000.0);
            int n4 = SQTime.getFullYear((long)versatileData.time);
            if (n3 != null && n4 == n3) continue;
            PreviewCaption previewCaption = new PreviewCaption(i, String.valueOf(n4));
            linkedList.add(previewCaption);
            n3 = n4;
        }
        stockData.setPreviewYVals(fArray);
        stockData.setPreviewCaptions(linkedList.toArray(new PreviewCaption[0]));
    }

    private void loadData(JarFile jarFile, boolean bl, String string) throws Exception {
        this.data.setAreaFrom(this.fromId);
        this.data.setAreaTo(this.toId);
        this.loader.seek(this.fromId.intValue());
        long l = this.loader.getTotalRecords();
        this.data.setCount(l);
        StockChartData stockChartData = this.fillStockData(this.data, this.loader, this.dataInfo, string);
        this.loadTimelines(jarFile, stockChartData.getxVals()[0]);
        this.fillIndicators(jarFile, string, stockChartData);
        if (bl) {
            this.fillPreview(this.data, l, this.loader);
        }
    }

    private void fillIndicators(JarFile jarFile, String string, StockChartData stockChartData) throws JDOMException, Exception {
        BlocksConfig blocksConfig = BlocksConfig.getConfig();
        int n = 0;
        LinkedList<Indicator> linkedList = new LinkedList<Indicator>();
        String string2 = this.path + "/indicator_";
        for (String[] stringArray : this.indicators) {
            BlockDefinition blockDefinition = blocksConfig.getBlock("talib_" + stringArray[2]);
            boolean bl = blockDefinition.returnType != 2;
            Indicator indicator = new Indicator();
            indicator.setTitle(stringArray[3].replace("@Chart@", this.data.getCurrentStock() + ","));
            indicator.setSubChart(bl);
            LinkedList<IndicatorLine> linkedList2 = new LinkedList<IndicatorLine>();
            String string3 = string2 + stringArray[1] + ".dat";
            JarEntry jarEntry = jarFile.getJarEntry(string3);
            InputStream inputStream = jarFile.getInputStream(jarEntry);
            int n2 = stockChartData.getClose().size();
            byte[] byArray = this.getBytes(inputStream);
            int n3 = byArray.length / 4;
            ByteBuffer byteBuffer = ByteBuffer.wrap(byArray);
            LinkedList<Float> linkedList3 = new LinkedList<Float>();
            for (int i = 0; i < n3; ++i) {
                linkedList3.add(Float.valueOf(byteBuffer.getFloat()));
            }
            LinkedList<Float> linkedList4 = new LinkedList<Float>();
            for (int i = this.timelineFrom; i < n2 + this.timelineFrom && i < n3; ++i) {
                linkedList4.add((Float)linkedList3.get(i));
            }
            IndicatorLine indicatorLine = new IndicatorLine();
            String string4 = COLORS[n % COLORS.length];
            indicatorLine.setLine(stringArray[4]);
            indicatorLine.setColor(string4);
            indicatorLine.setKind(ChartKind.line);
            indicatorLine.setyValues(linkedList4.toArray(new Float[0]));
            linkedList2.add(indicatorLine);
            ++n;
            if (linkedList2.isEmpty()) continue;
            linkedList.add(indicator);
            indicator.setLines(linkedList2.toArray(new IndicatorLine[0]));
        }
        stockChartData.setIndicators(linkedList.toArray(new Indicator[0]));
    }

    private StockChartData fillStockData(StockData stockData, IDataLoader iDataLoader, DataInfo dataInfo, String string) throws Exception {
        long l = stockData.getAreaTo() - stockData.getAreaFrom();
        int n = 0;
        StockChartData stockChartData = new StockChartData();
        stockChartData.setTitle(string);
        stockChartData.setPrecision(dataInfo.symbolInfo.decimals);
        stockData.setChartData(new StockChartData[1]);
        stockData.getChartData()[0] = stockChartData;
        VersatileData versatileData = new VersatileData();
        stockChartData.setClose(new LinkedList<Double>());
        stockChartData.setLow(new LinkedList<Double>());
        stockChartData.setHigh(new LinkedList<Double>());
        stockChartData.setOpen(new LinkedList<Double>());
        LinkedList<Long> linkedList = new LinkedList<Long>();
        this.fromTime = null;
        while (iDataLoader.hasNextTick()) {
            iDataLoader.getNextTick(versatileData);
            linkedList.add(versatileData.time);
            stockChartData.getClose().add(versatileData.close);
            stockChartData.getOpen().add(versatileData.open);
            stockChartData.getHigh().add(versatileData.high);
            stockChartData.getLow().add(versatileData.low);
            if (this.fromTime == null) {
                this.fromTime = versatileData.time;
            }
            this.toTime = versatileData.time;
            if ((long)n++ != l) continue;
        }
        long[] lArray = new long[linkedList.size()];
        int n2 = 0;
        for (Long l2 : linkedList) {
            lArray[n2++] = l2;
        }
        stockChartData.setxVals(lArray);
        return stockChartData;
    }

    private void setDateFromForTrade(JarFile jarFile, Long l, Long l2, Long l3) throws IOException {
        l2 = this.dataInfo.dateFrom;
        l3 = this.dataInfo.dateTo;
        if (l >= 0L) {
            this.setTradeFromForSpecificTrade(jarFile, l);
        } else if (l == -1L) {
            this.setTradeFromFromFirst(jarFile);
        } else if (l == -2L) {
            this.setTradeFromFromLast(jarFile);
        }
    }

    private String getLastTradeFile(JarFile jarFile) {
        String string;
        JarEntry jarEntry;
        int n = 0;
        String string2 = null;
        while ((jarEntry = jarFile.getJarEntry(string = this.path + "/trades_" + this.data.getCurrentStock() + "_" + n + ".dat")) != null) {
            string2 = string;
            ++n;
        }
        return string2;
    }

    private void setTradeFromFromLast(JarFile jarFile) throws IOException {
        String string = this.getLastTradeFile(jarFile);
        if (string == null) {
            return;
        }
        JarEntry jarEntry = jarFile.getJarEntry(string);
        InputStream inputStream = jarFile.getInputStream(jarEntry);
        byte[] byArray = new byte[16];
        inputStream.read(byArray);
        byte[] byArray2 = this.getBytes(inputStream);
        for (int i = 0; i < byArray2.length; i += 25) {
            long l = ByteBuffer.wrap(byArray2, i, 8).getLong();
            long l2 = ByteBuffer.wrap(byArray2, i += 8, 8).getLong();
            i += 8;
            this.data.setSelectedTrade(l);
            this.fromId = l2;
        }
        inputStream.close();
    }

    private void setTradeFromFromFirst(JarFile jarFile) throws IOException {
        JarEntry jarEntry = jarFile.getJarEntry(this.path + "/trades_" + this.data.getCurrentStock() + "_0.dat");
        if (jarEntry == null) {
            return;
        }
        InputStream inputStream = jarFile.getInputStream(jarEntry);
        byte[] byArray = new byte[16];
        inputStream.read(byArray);
        byte[] byArray2 = this.getBytes(inputStream);
        int n = 0;
        if (n < byArray2.length) {
            long l = ByteBuffer.wrap(byArray2, n, 8).getLong();
            long l2 = ByteBuffer.wrap(byArray2, n += 8, 8).getLong();
            n += 8;
            this.data.setSelectedTrade(l);
            this.fromId = l2;
        }
        inputStream.close();
    }

    private void setTradeFromForSpecificTrade(JarFile jarFile, Long l) throws IOException {
        JarEntry jarEntry;
        int n = 0;
        int n2 = 0;
        while ((jarEntry = jarFile.getJarEntry(this.path + "/trades_" + this.data.getCurrentStock() + "_" + n + ".dat")) != null) {
            InputStream inputStream = jarFile.getInputStream(jarEntry);
            byte[] byArray = new byte[16];
            inputStream.read(byArray);
            byte[] byArray2 = this.getBytes(inputStream);
            int n3 = 0;
            while (n2 < byArray2.length) {
                boolean bl;
                long l2 = ByteBuffer.wrap(byArray2, n2, 8).getLong();
                long l3 = ByteBuffer.wrap(byArray2, n2 += 8, 8).getLong();
                long l4 = ByteBuffer.wrap(byArray2, n2 += 8, 8).getLong();
                double d = ByteBuffer.wrap(byArray2, n2 += 8, 4).getFloat();
                double d2 = ByteBuffer.wrap(byArray2, n2 += 4, 4).getFloat();
                double d3 = ByteBuffer.wrap(byArray2, n2 += 4, 4).getFloat();
                double d4 = ByteBuffer.wrap(byArray2, n2 += 4, 4).getFloat();
                byte by = ByteBuffer.wrap(byArray2, n2 += 4, 1).get();
                ++n2;
                boolean bl2 = bl = by == 1;
                if (l2 == l || (long)n3 == l) {
                    this.fromId = l3;
                    this.data.setSelectedTrade(l2);
                    return;
                }
                ++n3;
            }
            inputStream.close();
            ++n;
        }
    }

    private void findFromToIndexes(Integer n) {
        Long l = this.findNearestTime(this.fromId);
        Long l2 = this.fromId = this.timestampToIdMap.get(l);
        this.fromId = this.fromId - 1L;
        long l3 = n != null ? (long)n.intValue() : 250L;
        this.fromId = this.fromId - l3 / 3L;
        if (this.fromId < 0L) {
            this.fromId = 0L;
        }
        this.toId = this.fromId + l3;
    }

    private void cleanup() {
        this.idToTimestampMap = null;
        this.timestampToIdMap = null;
    }

    private void correctFromTo() throws Exception {
        if (this.fromId == null || this.fromId < 0L || this.fromId > this.toId) {
            this.fromId = 0L;
        }
        if (this.toId == null) {
            this.toId = this.fromId + 250L;
        }
        long l = this.loader.getTotalRecords();
        if (this.toId > l - 1L) {
            long l2 = this.toId - this.fromId;
            this.toId = l - 1L;
            this.fromId = this.toId - l2;
            if (this.fromId < 0L) {
                this.fromId = 0L;
            }
        }
        this.data.setAreaFrom(this.fromId);
        this.data.setAreaTo(this.toId);
    }

    private String correctResultKey(String string) {
        return string.replace("/", "_LOM_");
    }

    private void loadTrades(JarFile jarFile, String string) throws IOException {
        JarEntry jarEntry;
        int n = 0;
        StockChartData stockChartData = this.data.getChartData()[0];
        LinkedList<Trade> linkedList = new LinkedList<Trade>();
        int n2 = 0;
        while ((jarEntry = jarFile.getJarEntry(this.path + "/trades_" + string + "_" + n + ".dat")) != null) {
            InputStream inputStream = jarFile.getInputStream(jarEntry);
            if (this.fitDate(inputStream)) {
                byte[] byArray = this.getBytes(inputStream);
                this.loadTrades(linkedList, byArray, n2);
            }
            inputStream.close();
            ++n;
            n2 += 1000;
        }
        stockChartData.setTrades(linkedList.toArray(new Trade[0]));
    }

    private void loadTrades(List<Trade> list, byte[] byArray, int n) {
        int n2 = 0;
        while (n2 < byArray.length) {
            boolean bl;
            long l = ByteBuffer.wrap(byArray, n2, 8).getLong();
            long l2 = ByteBuffer.wrap(byArray, n2 += 8, 8).getLong();
            long l3 = ByteBuffer.wrap(byArray, n2 += 8, 8).getLong();
            double d = ByteBuffer.wrap(byArray, n2 += 8, 4).getFloat();
            double d2 = ByteBuffer.wrap(byArray, n2 += 4, 4).getFloat();
            double d3 = ByteBuffer.wrap(byArray, n2 += 4, 4).getFloat();
            double d4 = ByteBuffer.wrap(byArray, n2 += 4, 4).getFloat();
            byte by = ByteBuffer.wrap(byArray, n2 += 4, 1).get();
            ++n2;
            boolean bl2 = bl = by == 1;
            if (this.toTime >= l2 && this.fromTime <= l3) {
                Long l4;
                Long l5 = this.timestampToIdMap.get(l2);
                long l6 = l2;
                long l7 = l3;
                if (l5 == null) {
                    l6 = this.findCandleAtOrBefore(l2);
                    l5 = this.timestampToIdMap.get(l6);
                }
                if ((l4 = this.timestampToIdMap.get(l3)) == null) {
                    l7 = this.findCandleAtOrBefore(l3);
                    l4 = this.timestampToIdMap.get(l7);
                }
                Trade trade = new Trade();
                trade.setIndex(n);
                trade.setId(l);
                trade.setOpenTime(l6);
                trade.setOpenValue(d);
                trade.setSLValue(d3);
                trade.setPTValue(d4);
                trade.setCloseTime(l7);
                trade.setCloseValue(d2);
                trade.setShortTrade(bl);
                trade.setRealOpenTime(l2);
                trade.setRealCloseTime(l3);
                list.add(trade);
            }
            ++n;
        }
    }

    private Long findCandleAtOrBefore(long l) {
        int n = this.timestamps.size();
        if (n == 0) {
            return null;
        }
        long l2 = this.timestamps.get(0);
        long l3 = this.timestamps.get(n - 1);
        if (l <= l2) {
            return l2;
        }
        if (l >= l3) {
            return l3;
        }
        int n2 = 0;
        int n3 = n - 1;
        while (n2 < n3) {
            int n4 = n2 + n3 + 1 >>> 1;
            if (this.timestamps.get(n4) <= l) {
                n2 = n4;
                continue;
            }
            n3 = n4 - 1;
        }
        return this.timestamps.get(n2);
    }

    private Long findCandleCloseAtOrAfter(long l) {
        int n = this.timestamps.size();
        if (n == 0) {
            return null;
        }
        long l2 = this.timestamps.get(0);
        long l3 = this.timestamps.get(n - 1);
        if (l <= l2) {
            return l2;
        }
        if (l >= l3) {
            return l3;
        }
        int n2 = 0;
        int n3 = n - 1;
        while (n2 < n3) {
            int n4 = n2 + n3 >>> 1;
            if (this.timestamps.get(n4) < l) {
                n2 = n4 + 1;
                continue;
            }
            n3 = n4;
        }
        return this.timestamps.get(n2);
    }

    private Long findNearestTime(long l) {
        int n = 0;
        int n2 = this.timestamps.size() - 1;
        while (n <= n2) {
            int n3 = (n + n2) / 2;
            Long l2 = this.timestamps.get(n3);
            Long l3 = this.timestamps.get(n2);
            int n4 = n2 - n;
            if (n4 == 0) {
                return l3;
            }
            if (n4 == 1) {
                if (l3 > l) {
                    return this.timestamps.get(n);
                }
                return l3;
            }
            if (l2 > l) {
                n2 = n3;
                continue;
            }
            if (l > l2) {
                n = n3;
                continue;
            }
            if (l2 != l) continue;
            return l2;
        }
        return this.timestamps.get(n2);
    }

    private boolean fitDate(InputStream inputStream) throws IOException {
        byte[] byArray = new byte[16];
        inputStream.read(byArray);
        long l = ByteBuffer.wrap(byArray, 0, 8).getLong();
        long l2 = ByteBuffer.wrap(byArray, 8, 8).getLong();
        boolean bl = this.toTime >= l && this.fromTime <= l2;
        return bl;
    }

    private void prepareStructure(JarFile jarFile, String string) throws Exception {
        this.data = new StockData();
        this.timestampToIdMap = new HashMap<Long, Long>();
        this.idToTimestampMap = new HashMap<Long, Long>();
        JarEntry jarEntry = jarFile.getJarEntry(this.path + "/stock_desc.csv");
        InputStream inputStream = jarFile.getInputStream(jarEntry);
        String string2 = SQUtils.inputStreamToString((InputStream)inputStream);
        String[] stringArray = string2.split("\n");
        LinkedList<String> linkedList = new LinkedList<String>();
        String string3 = null;
        this.data.setChartData(new StockChartData[1]);
        for (int i = 0; i < stringArray.length; ++i) {
            String string4 = stringArray[i];
            String[] stringArray2 = string4.split(";");
            String string5 = stringArray2[0];
            if (string5.equals("S")) {
                string3 = stringArray2[1];
                if (string == null) {
                    string = string3;
                }
                linkedList.add(string3);
                int n = 0;
                try {
                    n = Integer.valueOf(stringArray2[2]);
                }
                catch (Exception exception) {
                    // empty catch block
                }
                this.orderCounts.put(stringArray2[1], n);
                continue;
            }
            if (!string5.equals("I") || !string.equals(string3)) continue;
            this.indicators.add(stringArray2);
        }
        inputStream.close();
        this.data.setStocks(linkedList.toArray(new String[0]));
    }

    private byte[] getBytes(InputStream inputStream) throws IOException {
        int n;
        byte[] byArray = new byte[4096];
        ByteArrayOutputStream byteArrayOutputStream = new ByteArrayOutputStream();
        while ((n = inputStream.read(byArray)) != -1) {
            byteArrayOutputStream.write(byArray, 0, n);
        }
        byteArrayOutputStream.flush();
        return byteArrayOutputStream.toByteArray();
    }
}

