/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.SQUtils
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.stockchart;

import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.tradinglib.stockchart.ChartKind;
import com.strategyquant.tradinglib.stockchart.Indicator;
import com.strategyquant.tradinglib.stockchart.IndicatorLevel;
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
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class StockLoader {
    public static final Logger Log = LoggerFactory.getLogger(StockLoader.class);
    private static final int DEFAULT_DATAWIDTH = 250;
    private StockData data;
    private Map<Long, Long> timestampToIdMap;
    private List<Long> timestamps;
    private Map<Long, Long> idToTimestampMap;
    private Long fromTime;
    private Long toTime;
    private Long fromId;
    private Long toId;
    private String path;

    public StockData load(JarFile jarFile, Long l, Long l2, Long l3, boolean bl, boolean bl2, String string, Integer n) throws Exception {
        this.fromId = l;
        this.toId = l2;
        this.path = "Results/" + this.correctResultKey(string);
        this.prepareStructure(jarFile);
        if (bl) {
            this.loadPreview(jarFile);
        }
        this.loadIds(jarFile, bl);
        if (l3 != null && this.data.getTradesCount() != 0L) {
            if (l3 >= this.data.getTradesCount()) {
                l3 = this.data.getTradesCount() - 1L;
            }
            this.setDateFromForTrade(jarFile, l3, l, l2);
            if (this.data.getSelectedTrade() != null) {
                bl2 = true;
            }
        }
        if (bl2) {
            this.findFromToIndexes(n);
        }
        this.correctFromTo();
        this.data.setAreaFrom(this.fromId);
        this.data.setAreaTo(this.toId);
        this.loadMainData(jarFile);
        this.loadTrades(jarFile);
        this.correctIndicatorNames();
        this.cleanup();
        return this.data;
    }

    private void correctIndicatorNames() {
        for (int i = 0; i < this.data.getChartData().length; ++i) {
            StockChartData stockChartData = this.data.getChartData()[i];
            String string = stockChartData.getTitle();
            for (int j = 0; j < stockChartData.getIndicators().length; ++j) {
                Indicator indicator = stockChartData.getIndicators()[j];
                String string2 = indicator.getTitle();
                string2 = string2.replace("@Chart@)", string + ")");
                string2 = string2.replace("@Chart@", string + ",");
                indicator.setTitle(string2);
            }
        }
    }

    private void setDateFromForTrade(JarFile jarFile, Long l, Long l2, Long l3) throws IOException {
        l2 = this.idToTimestampMap.get(l2);
        l3 = this.idToTimestampMap.get(l3);
        if (l >= 0L) {
            this.setTradeFromForSpecificTrade(jarFile, l);
        } else if (l == -1L) {
            this.setTradeFromFromFirst(jarFile, l3);
        } else if (l == -2L) {
            this.setTradeFromFromLast(jarFile, l2);
        }
    }

    private void setTradeFromFromLast(JarFile jarFile, Long l) throws IOException {
        JarEntry jarEntry;
        int n = 0;
        while ((jarEntry = jarFile.getJarEntry(this.path + "/trades_0_" + n + ".dat")) != null) {
            InputStream inputStream = jarFile.getInputStream(jarEntry);
            byte[] byArray = new byte[16];
            inputStream.read(byArray);
            long l2 = ByteBuffer.wrap(byArray, 0, 8).getLong();
            long l3 = ByteBuffer.wrap(byArray, 8, 8).getLong();
            byte[] byArray2 = this.getBytes(inputStream);
            for (int i = 0; i < byArray2.length; i += 25) {
                long l4 = ByteBuffer.wrap(byArray2, i, 8).getLong();
                long l5 = ByteBuffer.wrap(byArray2, i += 8, 8).getLong();
                i += 8;
                if (l5 > l) {
                    return;
                }
                this.data.setSelectedTrade(l4);
                this.fromId = l5;
            }
            inputStream.close();
        }
        ++n;
    }

    private void setTradeFromFromFirst(JarFile jarFile, Long l) throws IOException {
        JarEntry jarEntry;
        int n = 0;
        while ((jarEntry = jarFile.getJarEntry(this.path + "/trades_0_" + n + ".dat")) != null) {
            InputStream inputStream = jarFile.getInputStream(jarEntry);
            byte[] byArray = new byte[16];
            inputStream.read(byArray);
            long l2 = ByteBuffer.wrap(byArray, 0, 8).getLong();
            long l3 = ByteBuffer.wrap(byArray, 8, 8).getLong();
            if (l3 > l) {
                byte[] byArray2 = this.getBytes(inputStream);
                for (int i = 0; i < byArray2.length; i += 25) {
                    long l4 = ByteBuffer.wrap(byArray2, i, 8).getLong();
                    long l5 = ByteBuffer.wrap(byArray2, i += 8, 8).getLong();
                    i += 8;
                    if (l5 <= l) continue;
                    this.data.setSelectedTrade(l4);
                    this.fromId = l5;
                    return;
                }
            }
            inputStream.close();
            ++n;
        }
    }

    private void setTradeFromForSpecificTrade(JarFile jarFile, Long l) throws IOException {
        int n = (int)(l / 1000L);
        int n2 = 0;
        JarEntry jarEntry = jarFile.getJarEntry(this.path + "/trades_" + n2 + "_" + n + ".dat");
        if (jarEntry == null) {
            return;
        }
        InputStream inputStream = jarFile.getInputStream(jarEntry);
        byte[] byArray = this.getBytes(inputStream);
        inputStream.close();
        int n3 = (int)(l - (long)(n * 1000));
        int n4 = n3 * 41 + 16;
        this.data.setSelectedTrade(ByteBuffer.wrap(byArray, n4, 8).getLong());
        long l2 = ByteBuffer.wrap(byArray, n4 += 8, 8).getLong();
        n4 += 8;
        this.fromId = l2;
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
        this.timestamps = null;
    }

    private void correctFromTo() {
        if (this.fromId == null || this.fromId < 0L || this.fromId > this.toId) {
            this.fromId = 0L;
        }
        if (this.toId == null) {
            this.toId = this.fromId + 250L;
        }
        if (this.toId > (long)(this.timestampToIdMap.size() - 1)) {
            long l = this.toId - this.fromId;
            this.toId = this.timestampToIdMap.size() - 1;
            this.fromId = this.toId - l;
            if (this.fromId < 0L) {
                this.fromId = 0L;
            }
        }
        this.fromTime = this.idToTimestampMap.get(this.fromId);
        this.toTime = this.idToTimestampMap.get(this.toId);
    }

    private String correctResultKey(String string) {
        return string.replace("/", "_LOM_");
    }

    private void loadTrades(JarFile jarFile) throws IOException {
        for (int i = 0; i < this.data.getChartData().length; ++i) {
            this.loadTrades(jarFile, i);
        }
    }

    private void loadTrades(JarFile jarFile, int n) throws IOException {
        JarEntry jarEntry;
        int n2 = 0;
        StockChartData stockChartData = this.data.getChartData()[n];
        LinkedList<Trade> linkedList = new LinkedList<Trade>();
        int n3 = 0;
        while ((jarEntry = jarFile.getJarEntry(this.path + "/trades_" + n + "_" + n2 + ".dat")) != null) {
            InputStream inputStream = jarFile.getInputStream(jarEntry);
            if (this.fitDate(inputStream)) {
                byte[] byArray = this.getBytes(inputStream);
                this.loadTrades(linkedList, byArray, n3);
            }
            inputStream.close();
            ++n2;
            n3 += 1000;
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
                trade.setOpenId(l5);
                trade.setCloseId(l4);
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

    private void loadMainData(JarFile jarFile) throws IOException {
        for (int i = 0; i < this.data.getChartData().length; ++i) {
            this.loadMainData(jarFile, i);
        }
    }

    private boolean fitDate(InputStream inputStream) throws IOException {
        byte[] byArray = new byte[16];
        inputStream.read(byArray);
        long l = ByteBuffer.wrap(byArray, 0, 8).getLong();
        long l2 = ByteBuffer.wrap(byArray, 8, 8).getLong();
        boolean bl = this.toTime >= l && this.fromTime <= l2;
        return bl;
    }

    private int getIndicatorLineCount(StockChartData stockChartData) {
        int n = 0;
        if (stockChartData.getIndicators() == null) {
            return n;
        }
        for (Indicator indicator : stockChartData.getIndicators()) {
            n += indicator.getLines().length;
        }
        return n;
    }

    private void loadMainData(JarFile jarFile, int n) throws IOException {
        JarEntry jarEntry;
        int n2 = 0;
        StockChartData stockChartData = this.data.getChartData()[n];
        int n3 = this.getIndicatorLineCount(stockChartData);
        ChartInfo chartInfo = new ChartInfo(n3);
        while ((jarEntry = jarFile.getJarEntry(this.path + "/chartdata_" + n + "_" + n2 + ".dat")) != null) {
            Indicator[] indicatorArray = jarFile.getInputStream(jarEntry);
            if (this.fitDate((InputStream)indicatorArray)) {
                byte[] byArray = this.getBytes((InputStream)indicatorArray);
                this.loadData(chartInfo, n3, byArray);
            }
            indicatorArray.close();
            ++n2;
        }
        stockChartData.setxVals(chartInfo.getXvalsArray());
        stockChartData.setOpen(chartInfo.getOpen());
        stockChartData.setClose(chartInfo.getClose());
        stockChartData.setLow(chartInfo.getLow());
        stockChartData.setHigh(chartInfo.getHigh());
        if (stockChartData.getIndicators() != null) {
            int n4 = 0;
            for (Indicator indicator : stockChartData.getIndicators()) {
                for (IndicatorLine indicatorLine : indicator.getLines()) {
                    indicatorLine.setyValues(chartInfo.getIndicatorArray(n4++, indicatorLine));
                }
            }
        }
    }

    private void loadData(ChartInfo chartInfo, int n, byte[] byArray) {
        int n2 = 0;
        ByteBuffer byteBuffer = ByteBuffer.wrap(byArray);
        while (n2 < byArray.length) {
            long l = byteBuffer.getLong(n2);
            n2 += 8;
            if (l < this.fromTime) {
                n2 += (4 + n) * 4;
                continue;
            }
            if (l > this.toTime) break;
            chartInfo.getXvals().add(l);
            chartInfo.getOpen().add(Double.valueOf(ByteBuffer.wrap(byArray, n2, 4).getFloat()));
            chartInfo.getClose().add(Double.valueOf(ByteBuffer.wrap(byArray, n2 += 4, 4).getFloat()));
            chartInfo.getLow().add(Double.valueOf(ByteBuffer.wrap(byArray, n2 += 4, 4).getFloat()));
            chartInfo.getHigh().add(Double.valueOf(ByteBuffer.wrap(byArray, n2 += 4, 4).getFloat()));
            n2 += 4;
            for (int i = 0; i < n; ++i) {
                List list = chartInfo.getIndicators()[i];
                list.add(Float.valueOf(byteBuffer.getFloat(n2)));
                n2 += 4;
            }
        }
    }

    private void prepareStructure(JarFile jarFile) throws Exception {
        this.data = new StockData();
        this.timestampToIdMap = new HashMap<Long, Long>();
        this.idToTimestampMap = new HashMap<Long, Long>();
        this.timestamps = new LinkedList<Long>();
        JarEntry jarEntry = jarFile.getJarEntry(this.path + "/stock_desc.csv");
        InputStream inputStream = jarFile.getInputStream(jarEntry);
        String string = SQUtils.inputStreamToString((InputStream)inputStream);
        String[] stringArray = string.split("\n");
        this.data.setCount(Long.parseLong(stringArray[0]));
        this.data.setTradesCount(Long.parseLong(stringArray[1]));
        StockChartData stockChartData = null;
        Indicator indicator = null;
        this.data.setChartData(new StockChartData[this.getChartCounts(stringArray)]);
        int n = 0;
        int n2 = 0;
        int n3 = 0;
        int n4 = 0;
        for (int i = 2; i < stringArray.length; ++i) {
            Object object;
            String[] stringArray2 = stringArray[i].split(";");
            String string2 = stringArray2[0];
            if (string2.equals("S")) {
                stockChartData = new StockChartData();
                stockChartData.setTitle(stringArray2[1]);
                if (stringArray2.length > 2) {
                    try {
                        stockChartData.setPrecision(Integer.parseInt(stringArray2[2]));
                    }
                    catch (Exception exception) {
                        // empty catch block
                    }
                }
                this.data.getChartData()[n] = stockChartData;
                stockChartData.setIndicators(new Indicator[this.getIndicatorsCount(stringArray, i + 1)]);
                ++n;
                n3 = 0;
                continue;
            }
            if (string2.equals("I")) {
                indicator = new Indicator();
                indicator.setTitle(stringArray2[1]);
                indicator.setSubChart(Boolean.parseBoolean(stringArray2[2]));
                indicator.setLines(new IndicatorLine[this.getIndicatorLineCount(stringArray, i + 1)]);
                indicator.setLevels(new IndicatorLevel[this.getLevelCount(stringArray, i + 1)]);
                n2 = 0;
                n4 = 0;
                stockChartData.getIndicators()[n3++] = indicator;
                continue;
            }
            if (string2.equals("L")) {
                object = new IndicatorLine();
                ((IndicatorLine)object).setLine(stringArray2[1]);
                ((IndicatorLine)object).setColor(stringArray2[2]);
                ((IndicatorLine)object).setKind(ChartKind.valueOf(stringArray2[3]));
                if (stringArray2.length > 4) {
                    ((IndicatorLine)object).setShowInChart("1".equals(stringArray2[4]));
                }
                indicator.getLines()[n2++] = object;
                if (stringArray2.length <= 5) continue;
                try {
                    ((IndicatorLine)object).setShowZeroValues(Boolean.valueOf(stringArray2[5]));
                }
                catch (Exception exception) {
                    Log.error("Error while parsin showZeroValues: " + stringArray2[5]);
                }
                continue;
            }
            if (!string2.equals("IL")) continue;
            object = stringArray2[1];
            String string3 = stringArray2[2];
            String string4 = stringArray2[3];
            IndicatorLevel indicatorLevel = new IndicatorLevel();
            indicatorLevel.setColor((String)object);
            indicatorLevel.setPattern(string4);
            indicatorLevel.setValue(Double.parseDouble(string3));
            indicator.getLevels()[n4++] = indicatorLevel;
        }
        inputStream.close();
    }

    private int getIndicatorLineCount(String[] stringArray, int n) {
        int n2 = 0;
        for (int i = n; i < stringArray.length; ++i) {
            String string = stringArray[i];
            if (string.startsWith("L")) {
                ++n2;
                continue;
            }
            if (!string.startsWith("IL")) break;
        }
        return n2;
    }

    private int getLevelCount(String[] stringArray, int n) {
        String string;
        int n2 = 0;
        for (int i = n; i < stringArray.length && (string = stringArray[i]).startsWith("IL;"); ++i) {
            ++n2;
        }
        return n2;
    }

    private int getIndicatorsCount(String[] stringArray, int n) {
        int n2 = 0;
        for (int i = n; i < stringArray.length; ++i) {
            String string = stringArray[i];
            if (string.startsWith("I;")) {
                ++n2;
                continue;
            }
            if (string.startsWith("S;")) break;
        }
        return n2;
    }

    private int getChartCounts(String[] stringArray) {
        int n = 0;
        for (String string : stringArray) {
            if (!string.startsWith("S;")) continue;
            ++n;
        }
        return n;
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

    private void loadIds(JarFile jarFile, boolean bl) throws IOException {
        JarEntry jarEntry = jarFile.getJarEntry(this.path + "/ids.dat");
        InputStream inputStream = jarFile.getInputStream(jarEntry);
        byte[] byArray = this.getBytes(inputStream);
        long l = byArray.length / 8;
        int n = 0;
        Integer n2 = null;
        LinkedList<PreviewCaption> linkedList = new LinkedList<PreviewCaption>();
        for (long i = 0L; i < l; ++i) {
            Long l2 = ByteBuffer.wrap(byArray, n, 8).getLong();
            n += 8;
            if (bl) {
                int n3 = SQTime.getFullYear((long)l2);
                int n4 = this.data.getPreviewYVals().length;
                if (n2 == null || n3 != n2) {
                    int n5 = (int)(i * (long)n4 / l);
                    PreviewCaption previewCaption = new PreviewCaption(n5, String.valueOf(n3));
                    linkedList.add(previewCaption);
                    n2 = n3;
                }
            }
            this.timestamps.add(l2);
            this.timestampToIdMap.put(l2, i);
            this.idToTimestampMap.put(i, l2);
        }
        if (bl) {
            this.data.setPreviewCaptions(linkedList.toArray(new PreviewCaption[0]));
        }
        inputStream.close();
    }

    private void loadPreview(JarFile jarFile) throws IOException {
        int n;
        JarEntry jarEntry = jarFile.getJarEntry(this.path + "/preview.dat");
        InputStream inputStream = jarFile.getInputStream(jarEntry);
        byte[] byArray = this.getBytes(inputStream);
        ByteBuffer.wrap(byArray);
        int n2 = 0;
        int n3 = ByteBuffer.wrap(byArray, n2, 4).getInt();
        n2 = 4;
        int[] nArray = new int[n3];
        for (n = 0; n < n3; ++n) {
            nArray[n] = ByteBuffer.wrap(byArray, n2, 4).getInt();
            n2 += 4;
        }
        this.data.setPreviewTrades(nArray);
        n = (byArray.length - (1 + n3) * 4) / 4;
        float[] fArray = new float[n];
        for (int i = 0; i < n; ++i) {
            fArray[i] = ByteBuffer.wrap(byArray, n2, 4).getFloat();
            n2 += 4;
        }
        this.data.setPreviewYVals(fArray);
        inputStream.close();
    }

    private static class ChartInfo {
        private final List<Long> xvals = new LinkedList<Long>();
        private final List<Double> open = new LinkedList<Double>();
        private final List<Double> close = new LinkedList<Double>();
        private final List<Double> low = new LinkedList<Double>();
        private final List<Double> high = new LinkedList<Double>();
        private final List[] indicators;

        public ChartInfo(int n) {
            this.indicators = new List[n];
            for (int i = 0; i < n; ++i) {
                this.indicators[i] = new LinkedList();
            }
        }

        public long[] getXvalsArray() {
            long[] lArray = new long[this.xvals.size()];
            int n = 0;
            for (Long l : this.xvals) {
                lArray[n++] = l;
            }
            return lArray;
        }

        public List<Long> getXvals() {
            return this.xvals;
        }

        public Float[] getIndicatorArray(int n, IndicatorLine indicatorLine) {
            return this.getSafeFloatArrayFromFloat(this.indicators[n], indicatorLine);
        }

        private Float[] getSafeFloatArrayFromFloat(List<Float> list, IndicatorLine indicatorLine) {
            Float[] floatArray = new Float[list.size()];
            int n = 0;
            for (Float f : list) {
                Float f2;
                if (f.equals(Float.valueOf(Float.NaN))) {
                    f2 = null;
                } else {
                    f2 = f;
                    if ((double)f2.floatValue() == 0.0 && !indicatorLine.isShowZeroValues()) {
                        f2 = null;
                    }
                }
                floatArray[n++] = f2;
            }
            return floatArray;
        }

        public List<Double> getOpen() {
            return this.open;
        }

        public List<Double> getClose() {
            return this.close;
        }

        public List<Double> getLow() {
            return this.low;
        }

        public List<Double> getHigh() {
            return this.high;
        }

        public List[] getIndicators() {
            return this.indicators;
        }
    }
}

