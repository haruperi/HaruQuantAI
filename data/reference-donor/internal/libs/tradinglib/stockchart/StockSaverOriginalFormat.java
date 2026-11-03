/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.DataSeries
 *  com.strategyquant.datalib.TradingException
 *  com.strategyquant.lib.app.MainApp
 *  org.apache.commons.lang3.tuple.ImmutablePair
 *  org.apache.commons.lang3.tuple.Pair
 *  org.jdom2.JDOMException
 */
package com.strategyquant.tradinglib.stockchart;

import com.strategyquant.datalib.DataSeries;
import com.strategyquant.datalib.TradingException;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.tradinglib.ChartData;
import com.strategyquant.tradinglib.Order;
import com.strategyquant.tradinglib.OrdersList;
import com.strategyquant.tradinglib.blocks.random.BlockDefinition;
import com.strategyquant.tradinglib.blocks.random.BlocksConfig;
import com.strategyquant.tradinglib.engine.TradingSetup;
import com.strategyquant.tradinglib.indicator.IndicatorBase;
import com.strategyquant.tradinglib.indicator.IndicatorsCache;
import com.strategyquant.tradinglib.stockchart.ChartKind;
import com.strategyquant.tradinglib.stockchart.IndicatorDisplayFormatter;
import com.strategyquant.tradinglib.stockchart.Trade;
import com.strategyquant.tradinglib.strategy.MarketData;
import java.io.BufferedOutputStream;
import java.io.BufferedWriter;
import java.io.IOException;
import java.io.OutputStream;
import java.io.OutputStreamWriter;
import java.nio.ByteBuffer;
import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedList;
import java.util.List;
import java.util.jar.JarEntry;
import java.util.jar.JarOutputStream;
import org.apache.commons.lang3.tuple.ImmutablePair;
import org.apache.commons.lang3.tuple.Pair;
import org.jdom2.JDOMException;

public class StockSaverOriginalFormat {
    private static final String[] COLORS = new String[]{"red", "green", "blue", "brown", "orange"};
    private static final int PREVIEW_SIZE = 1960;
    private static final int MAX_SIZE = 1000;
    public static final int MAX_TRADES = 1000;
    private JarOutputStream jarOutStream;
    private OrdersList orders;
    private MarketData marketData;
    private IndicatorsCache indicatorsCache;
    private int total;
    private String path;

    public void save(JarOutputStream jarOutputStream, TradingSetup tradingSetup, OrdersList ordersList, String string) throws JDOMException, Exception {
        this.jarOutStream = jarOutputStream;
        this.marketData = tradingSetup.getMarketData();
        this.indicatorsCache = tradingSetup.getStrategy().getIndicatorsCache();
        this.orders = ordersList;
        this.path = "Results/" + this.correctResultKey(string);
        this.saveIds();
        this.saveMetadata();
        this.savePreview();
        this.saveStockData();
        this.saveTrades();
    }

    private int getIdsCount() throws TradingException {
        int n = 0;
        int n2 = this.marketData.getChartData().length;
        int[] nArray = new int[n2];
        for (int i = 0; i < n2; ++i) {
            nArray[i] = this.marketData.getChartData()[i].Time.size() - 1;
        }
        block1: while (true) {
            int n3;
            long l = -1L;
            for (n3 = 0; n3 < n2; ++n3) {
                int n4 = nArray[n3];
                if (n4 == -1) continue;
                long l2 = this.marketData.getChartData()[n3].Time.get(n4);
                if (l != -1L && l2 >= l) continue;
                l = l2;
            }
            if (l == -1L) break;
            ++n;
            n3 = 0;
            while (true) {
                long l3;
                if (n3 >= n2) continue block1;
                if (nArray[n3] != -1 && (l3 = this.marketData.getChartData()[n3].Time.get(nArray[n3])) == l) {
                    int n5 = n3;
                    nArray[n5] = nArray[n5] - 1;
                }
                ++n3;
            }
            break;
        }
        return n;
    }

    private void writeIdsToBuffer(ByteBuffer byteBuffer) throws TradingException {
        int n = this.marketData.getChartData().length;
        int[] nArray = new int[n];
        for (int i = 0; i < n; ++i) {
            nArray[i] = this.marketData.getChartData()[i].Time.size() - 1;
        }
        block1: while (true) {
            int n2;
            long l = -1L;
            for (n2 = 0; n2 < n; ++n2) {
                int n3 = nArray[n2];
                if (n3 == -1) continue;
                long l2 = this.marketData.getChartData()[n2].Time.get(n3);
                if (l != -1L && l2 >= l) continue;
                l = l2;
            }
            if (l == -1L) break;
            byteBuffer.putLong(l);
            n2 = 0;
            while (true) {
                long l3;
                if (n2 >= n) continue block1;
                if (nArray[n2] != -1 && (l3 = this.marketData.getChartData()[n2].Time.get(nArray[n2])) == l) {
                    int n4 = n2;
                    nArray[n4] = nArray[n4] - 1;
                }
                ++n2;
            }
            break;
        }
    }

    private void saveIds() throws IOException, TradingException {
        this.total = this.getIdsCount();
        this.createEntry("ids.dat");
        ByteBuffer byteBuffer = ByteBuffer.allocate(8 * this.total);
        this.writeIdsToBuffer(byteBuffer);
        BufferedOutputStream bufferedOutputStream = new BufferedOutputStream(this.jarOutStream);
        bufferedOutputStream.write(byteBuffer.array());
        bufferedOutputStream.flush();
        this.jarOutStream.closeEntry();
    }

    private void createEntry(String string) throws IOException {
        JarEntry jarEntry = new JarEntry(this.path + "/" + string);
        this.jarOutStream.putNextEntry(jarEntry);
    }

    private void saveCount(BufferedWriter bufferedWriter, long l) throws IOException {
        bufferedWriter.write(l + "");
        bufferedWriter.write(System.getProperty("line.separator"));
    }

    private void saveFromTo(ByteBuffer byteBuffer, long l, long l2) throws IOException {
        byteBuffer.putLong(l);
        byteBuffer.putLong(l2);
    }

    private float getFloat(double d) {
        return (float)((double)((float)d) * 10000.0 / 10000.0);
    }

    private void saveMetadata() throws JDOMException, Exception {
        this.createEntry("stock_desc.csv");
        BufferedWriter bufferedWriter = new BufferedWriter(new OutputStreamWriter((OutputStream)this.jarOutStream, "US-ASCII"));
        this.saveCount(bufferedWriter, this.total);
        this.saveCount(bufferedWriter, this.orders.size());
        int n = 0;
        BlocksConfig blocksConfig = BlocksConfig.getConfig();
        for (ChartData chartData : this.marketData.getChartData()) {
            int n2 = chartData.getInstrumentInfo().decimals;
            bufferedWriter.write("S;" + chartData.Symbol + "/" + chartData.Timeframe + ";" + n2 + System.getProperty("line.separator"));
            ArrayList<IndicatorBase> arrayList = this.indicatorsCache.getIndicatorsForThisData(chartData);
            for (IndicatorBase indicatorBase : arrayList) {
                BlockDefinition blockDefinition = blocksConfig.getBlock(indicatorBase.getClass().getSimpleName());
                boolean bl = blockDefinition.returnType != 2;
                String string = IndicatorDisplayFormatter.format(indicatorBase, blockDefinition);
                bufferedWriter.write("I;" + string + ";" + bl + System.getProperty("line.separator"));
                ArrayList<DataSeries> arrayList2 = indicatorBase.getOutputLines();
                for (int i = 0; i < arrayList2.size(); ++i) {
                    DataSeries dataSeries = arrayList2.get(i);
                    String string2 = dataSeries.getColor();
                    if (string2 == null) {
                        string2 = COLORS[n % COLORS.length];
                    }
                    String string3 = arrayList2.get(i).isShowInChart() ? "1" : "0";
                    String string4 = dataSeries.getChartType() != null ? dataSeries.getChartType() : ChartKind.line.name();
                    boolean bl2 = dataSeries.isShowZeroValues();
                    bufferedWriter.write("L;" + arrayList2.get(i).getLineName() + ";" + string2 + ";" + string4 + ";" + string3 + ";" + bl2 + System.getProperty("line.separator"));
                    ++n;
                }
            }
        }
        bufferedWriter.flush();
        this.jarOutStream.closeEntry();
    }

    private void saveStockData() throws IOException, TradingException {
        int n = 0;
        try {
            for (ChartData chartData : this.marketData.getChartData()) {
                ArrayList<IndicatorBase> arrayList = this.indicatorsCache.getIndicatorsForThisData(chartData);
                this.saveChartData(String.valueOf(n), chartData, arrayList);
                ++n;
            }
        }
        catch (IllegalAccessException | IllegalArgumentException exception) {
            throw new TradingException("Cannot create chart data, error; " + exception.getMessage(), exception);
        }
    }

    private void writeChartDataPart(String string, ChartData chartData, ArrayList<IndicatorBase> arrayList, int n, int n2) throws TradingException, IOException, IllegalArgumentException, IllegalAccessException {
        this.createEntry("chartdata_" + string + ".dat");
        BufferedOutputStream bufferedOutputStream = new BufferedOutputStream(this.jarOutStream);
        int n3 = this.getLinesCount(arrayList);
        int n4 = (n2 - n + 1) * ((4 + n3) * 4 + 8) + 16;
        ByteBuffer byteBuffer = ByteBuffer.allocate(n4);
        this.saveFromTo(byteBuffer, chartData.Time.get(n2), chartData.Time.get(n));
        for (int i = n2; i >= n; --i) {
            long l = chartData.Time.get(i);
            byteBuffer.putLong(l);
            double d = chartData.Open.get(i);
            byteBuffer.putFloat(this.getFloat(d));
            double d2 = chartData.Close.get(i);
            byteBuffer.putFloat(this.getFloat(d2));
            double d3 = chartData.Low.get(i);
            byteBuffer.putFloat(this.getFloat(d3));
            double d4 = chartData.High.get(i);
            byteBuffer.putFloat(this.getFloat(d4));
            for (IndicatorBase indicatorBase : arrayList) {
                ArrayList<DataSeries> arrayList2 = indicatorBase.getOutputLines();
                for (int j = 0; j < arrayList2.size(); ++j) {
                    DataSeries dataSeries = arrayList2.get(j);
                    double d5 = 0.0;
                    d5 = i < dataSeries.size() ? dataSeries.get(i) : dataSeries.get(dataSeries.size() - 1);
                    float f = this.getFloat(d5);
                    byteBuffer.putFloat(f);
                }
            }
        }
        bufferedOutputStream.write(byteBuffer.array());
        bufferedOutputStream.flush();
        this.jarOutStream.closeEntry();
    }

    private int getLinesCount(ArrayList<IndicatorBase> arrayList) {
        int n = 0;
        for (IndicatorBase indicatorBase : arrayList) {
            n += indicatorBase.getOutputsCount();
        }
        return n;
    }

    private void saveChartData(String string, ChartData chartData, ArrayList<IndicatorBase> arrayList) throws TradingException, IOException, IllegalArgumentException, IllegalAccessException {
        int n;
        int n2;
        chartData.Time.setShift(0);
        chartData.Open.setShift(0);
        chartData.High.setShift(0);
        chartData.Low.setShift(0);
        chartData.Close.setShift(0);
        chartData.Volume.setShift(0);
        for (IndicatorBase indicatorBase : arrayList) {
            n2 = indicatorBase.getOutputsCount();
            for (n = 0; n < n2; ++n) {
                indicatorBase.setDataShift(n, 0);
            }
        }
        int n3 = chartData.Time.size();
        int n4 = n3 / 1000;
        if (n3 % 1000 != 0) {
            ++n4;
        }
        n2 = n3 - 1;
        for (n = 0; n < n4; ++n) {
            int n5 = n2 - 1000 + 1;
            if (n5 < 0) {
                n5 = 0;
            }
            this.writeChartDataPart(string + "_" + n, chartData, arrayList, n5, n2);
            n2 = n5 - 1;
        }
    }

    private void saveTrades() throws IOException {
        int n = 0;
        String[] stringArray = new String[this.marketData.getChartData().length];
        for (ChartData chartData : this.marketData.getChartData()) {
            this.saveTrades(String.valueOf(n), chartData.Symbol, stringArray);
            stringArray[n] = chartData.Symbol;
            ++n;
        }
    }

    private List<Long> getTradeTimes() {
        LinkedList<Long> linkedList = new LinkedList<Long>();
        if (this.orders == null || this.orders.size() == 0) {
            return linkedList;
        }
        for (int i = 0; i < this.orders.size(); ++i) {
            Order order = this.orders.get(i);
            linkedList.add(order.OpenTime);
            linkedList.add(order.CloseTime);
        }
        return linkedList;
    }

    private boolean skipTrade(Order order, String string, String[] stringArray) {
        if (order.Type != 1 && order.Type != 2) {
            return true;
        }
        if (!string.equals(order.Symbol)) {
            return true;
        }
        for (String string2 : stringArray) {
            if (string2 == null || !string2.equals(order.Symbol)) continue;
            return true;
        }
        return false;
    }

    private boolean shouldShowControlOrders() {
        boolean bl = false;
        try {
            bl = Boolean.parseBoolean(MainApp.settings().get("showControlOrders", "false"));
        }
        catch (Exception exception) {
            // empty catch block
        }
        return bl;
    }

    private void saveTrades(String string, String string2, String[] stringArray) throws IOException {
        if (this.orders == null || this.orders.size() == 0) {
            return;
        }
        boolean bl = this.shouldShowControlOrders();
        int n = 0;
        int n2 = 0;
        while (n2 < this.orders.size()) {
            Object object;
            int n3 = 41016;
            ByteBuffer byteBuffer = ByteBuffer.allocate(n3);
            byteBuffer.position(16);
            int n4 = 0;
            long l = -1L;
            long l2 = -1L;
            while (n4 < 1000 && n2 < this.orders.size()) {
                object = this.orders.get(n2);
                ++n2;
                if (this.skipTrade((Order)object, string2, stringArray) || !bl && !((Order)object).isRealOrder()) continue;
                byte by = ((Order)object).Type;
                boolean bl2 = by != 1;
                byteBuffer.putLong(((Order)object).Ticket);
                byteBuffer.putLong(((Order)object).OpenTime);
                byteBuffer.putLong(((Order)object).CloseTime);
                byteBuffer.putFloat(this.getFloat(((Order)object).OpenPrice));
                byteBuffer.putFloat(this.getFloat(((Order)object).ClosePrice));
                byteBuffer.putFloat(this.getFloat(((Order)object).StopLoss));
                byteBuffer.putFloat(this.getFloat(((Order)object).TakeProfit));
                byteBuffer.put((byte)(bl2 ? 1 : 0));
                if (((Order)object).OpenTime < l || l == -1L) {
                    l = ((Order)object).OpenTime;
                }
                if (((Order)object).CloseTime > l2 || l2 == -1L) {
                    l2 = ((Order)object).CloseTime;
                }
                ++n4;
            }
            if (l2 != -1L && l != -1L) {
                byteBuffer.position(0);
                this.saveFromTo(byteBuffer, l, l2);
                object = string + "_" + n;
                this.createEntry("trades_" + (String)object + ".dat");
                BufferedOutputStream bufferedOutputStream = new BufferedOutputStream(this.jarOutStream);
                bufferedOutputStream.write(byteBuffer.array());
                bufferedOutputStream.flush();
                this.jarOutStream.closeEntry();
            }
            ++n;
        }
    }

    private Pair<Long, Long> getMinMax(Trade[] tradeArray, int n, int n2) {
        Long l = null;
        Long l2 = null;
        for (int i = n; i <= n2; ++i) {
            Trade trade = tradeArray[i];
            if (l == null || l > trade.getOpenTime()) {
                l = trade.getOpenTime();
            }
            if (l2 != null && l2 >= trade.getCloseTime()) continue;
            l2 = trade.getCloseTime();
        }
        return new ImmutablePair(l, l2);
    }

    private void savePreview() throws IOException, TradingException {
        double d;
        double d2;
        int n;
        this.createEntry("preview.dat");
        int n2 = this.marketData.getChartData()[0].Close.size();
        if (n2 < 1960) {
            n = n2;
            d2 = 1.0;
        } else {
            n = 1960;
            d2 = (double)n2 / 1960.0;
        }
        List<Long> list = this.getTradeTimes();
        int n3 = list.size();
        ByteBuffer byteBuffer = ByteBuffer.allocate(4 * n + (1 + n3) * 4);
        byteBuffer.putInt(n3);
        ChartData chartData = this.marketData.getChartData()[0];
        int n4 = chartData.Time.size();
        long l = chartData.Time.get(n4 - 1);
        long l2 = chartData.Time.get(0);
        long l3 = l2 - l;
        double d3 = (double)n / (double)l3;
        for (Long l4 : list) {
            long l5 = l4 - l;
            d = (double)l5 * d3;
            int n5 = (int)d;
            byteBuffer.putInt(n5);
        }
        int n6 = 0;
        LinkedList<Float> linkedList = new LinkedList<Float>();
        ChartData chartData2 = this.marketData.getChartData()[0];
        for (int i = 0; n6 < n2 && i < n; ++i) {
            d = chartData2.Open.get(n6);
            linkedList.add(Float.valueOf(this.getFloat(d)));
            n6 = (int)((double)n6 + d2);
        }
        Collections.reverse(linkedList);
        for (Float object2 : linkedList) {
            byteBuffer.putFloat(this.getFloat(object2.floatValue()));
        }
        BufferedOutputStream bufferedOutputStream = new BufferedOutputStream(this.jarOutStream);
        byte[] byArray = byteBuffer.array();
        bufferedOutputStream.write(byArray);
        bufferedOutputStream.flush();
        this.jarOutStream.closeEntry();
    }

    private String correctResultKey(String string) {
        return string.replace("/", "_LOM_");
    }
}

