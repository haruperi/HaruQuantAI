/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQTime
 *  it.unimi.dsi.fastutil.longs.Long2DoubleOpenHashMap
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.equitychart;

import com.strategyquant.lib.SQTime;
import com.strategyquant.tradinglib.Order;
import com.strategyquant.tradinglib.OrdersList;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.equitychart.MainChartDataset;
import com.strategyquant.tradinglib.results.stats.comparator.OrderComparatorByCloseTime;
import it.unimi.dsi.fastutil.longs.Long2DoubleOpenHashMap;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Random;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class EquityChartUtils {
    private static final Comparator<Order> comparatorByCloseTime = new OrderComparatorByCloseTime();
    private static final String[] colors = new String[]{"#3366CC", "#980048", "#ff9062", "#007a38", "#a89f00", "#64ff88", "#ffdd6f", "#4400ae", "#415fff", "#ff4969", "#ff30ba", "#63ffba", "#884ffe", "#6d0055", "#d8a200", "#eb5200", "#56ee38", "#fff872", "#df6697", "#0243e8", "#5a7008", "#00318b", "#d7ff5b", "#dd87d7", "#d800c4", "#b3b700", "#01ba6b", "#9120d6", "#899936", "#cf0040", "#cd9eff", "#b763ff", "#00e39c", "#e6ff86", "#4f0659", "#7e9e00", "#6ed000", "#01cfa3", "#ffa84d", "#c90023", "#6a2978", "#9ae691", "#868500", "#0032ab", "#398f00", "#dac05e", "#322fd5", "#971d00", "#ff615b", "#ffdd3d", "#4c0084", "#fb73ff", "#9c4d00", "#756dc6", "#980077", "#ff487b", "#aeffa4", "#005cd2", "#ff7b36", "#02c93f", "#92c000", "#b584ff"};
    private static final String[] colors_dark = new String[]{"#556EE6", "#980048", "#ff9062", "#007a38", "#a89f00", "#64ff88", "#ffdd6f", "#4400ae", "#415fff", "#ff4969", "#ff30ba", "#63ffba", "#884ffe", "#6d0055", "#d8a200", "#eb5200", "#56ee38", "#fff872", "#df6697", "#0243e8", "#5a7008", "#00318b", "#d7ff5b", "#dd87d7", "#d800c4", "#b3b700", "#01ba6b", "#9120d6", "#899936", "#cf0040", "#cd9eff", "#b763ff", "#00e39c", "#e6ff86", "#4f0659", "#7e9e00", "#6ed000", "#01cfa3", "#ffa84d", "#c90023", "#6a2978", "#9ae691", "#868500", "#0032ab", "#398f00", "#dac05e", "#322fd5", "#971d00", "#ff615b", "#ffdd3d", "#4c0084", "#fb73ff", "#9c4d00", "#756dc6", "#980077", "#ff487b", "#aeffa4", "#005cd2", "#ff7b36", "#02c93f", "#92c000", "#b584ff"};
    public static final Logger Log = LoggerFactory.getLogger(EquityChartUtils.class);

    public static MainChartDataset generateDataset(OrdersList ordersList, String string) {
        if (string.equals("time")) {
            long[] lArray = EquityChartUtils.dateRange(ordersList);
            return EquityChartUtils.generateDailyDataset(ordersList, lArray[0], lArray[1]);
        }
        return EquityChartUtils.generateTradeDataset(ordersList);
    }

    public static MainChartDataset generateTradeDataset(OrdersList ordersList) {
        MainChartDataset mainChartDataset = new MainChartDataset("main", ordersList.size());
        double d = 0.0;
        ordersList.sort(comparatorByCloseTime);
        for (int i = 0; i < ordersList.size(); ++i) {
            mainChartDataset.addValue(i, d += (double)ordersList.get((int)i).PL);
        }
        return mainChartDataset;
    }

    private static MainChartDataset generateDailyDataset(OrdersList ordersList, long l, long l2) {
        long l3;
        MainChartDataset mainChartDataset = new MainChartDataset("main", ordersList.isEmpty() ? 0 : EquityChartUtils.getDaysBetween(l, l2));
        if (ordersList.isEmpty()) {
            return mainChartDataset;
        }
        Long2DoubleOpenHashMap long2DoubleOpenHashMap = new Long2DoubleOpenHashMap();
        for (int i = 0; i < ordersList.size(); ++i) {
            Order order = ordersList.get(i);
            l3 = SQTime.getDateInMs((long)order.CloseTime);
            if (long2DoubleOpenHashMap.containsKey(l3)) {
                long2DoubleOpenHashMap.put(l3, long2DoubleOpenHashMap.get(l3) + (double)order.PL);
                continue;
            }
            long2DoubleOpenHashMap.put(l3, (double)order.PL);
        }
        l3 = SQTime.getDateInMs((long)l);
        double d = 0.0;
        do {
            if (long2DoubleOpenHashMap.containsKey(l3)) {
                d += long2DoubleOpenHashMap.get(l3);
            }
            mainChartDataset.addValue(l3, d);
        } while ((l3 = SQTime.addDays((long)l3, (int)1)) <= l2);
        return mainChartDataset;
    }

    public static int getDaysBetween(long l, long l2) {
        int n = 0;
        long l3 = SQTime.getDateInMs((long)l);
        do {
            ++n;
        } while ((l3 = SQTime.addDays((long)l3, (int)1)) <= l2);
        return n;
    }

    public static List<MainChartDataset> generatePorfolioDatasets(ResultsGroup resultsGroup, byte by, byte by2, String string, String string2) throws Exception {
        Object object;
        ArrayList<MainChartDataset> arrayList = new ArrayList<MainChartDataset>();
        OrdersList ordersList = resultsGroup.orders().filter("Portfolio", by, by2, true);
        if (string == null || string.equals("Portfolio only")) {
            object = EquityChartUtils.generateDataset(ordersList, string2);
            ((MainChartDataset)object).name = "Portfolio";
            ((MainChartDataset)object).title = "Portfolio";
            arrayList.add((MainChartDataset)object);
        }
        if (string == null || string.equals("Portfolio parts only")) {
            object = resultsGroup.getMainResultKey();
            ordersList = resultsGroup.orders().filter((String)object, by, by2, true);
            MainChartDataset mainChartDataset = EquityChartUtils.generateDataset(ordersList, string2);
            mainChartDataset.name = object;
            mainChartDataset.title = object;
            arrayList.add(mainChartDataset);
            for (String string3 : resultsGroup.getResultKeys()) {
                if (string3.equals("Portfolio") || string3.equals(object) || string3.startsWith("WF:") || string3.startsWith("CrossCheck_")) continue;
                ordersList = resultsGroup.orders().filter(string3, by, by2, true);
                mainChartDataset = EquityChartUtils.generateDataset(ordersList, string2);
                mainChartDataset.name = string3;
                mainChartDataset.title = string3;
                arrayList.add(mainChartDataset);
            }
        }
        return arrayList;
    }

    public static String getColor(int n, boolean bl) {
        if (bl) {
            return n < colors_dark.length ? colors_dark[n] : EquityChartUtils.randomColor(n);
        }
        return n < colors.length ? colors[n] : EquityChartUtils.randomColor(n);
    }

    public static long[] dateRange(OrdersList ordersList) {
        return EquityChartUtils.dateRange(ordersList, false);
    }

    public static long[] dateRange(OrdersList ordersList, boolean bl) {
        long[] lArray = new long[]{0L, 0L};
        if (ordersList.isEmpty()) {
            return lArray;
        }
        long l = -1L;
        long l2 = -1L;
        for (int i = 0; i < ordersList.size(); ++i) {
            long l3;
            Order order = ordersList.get(i);
            long l4 = l3 = bl ? order.OpenTime : order.CloseTime;
            if (l == -1L || l > l3) {
                l = l3;
            }
            if (l2 >= order.CloseTime) continue;
            l2 = order.CloseTime;
        }
        lArray[0] = l;
        lArray[1] = l2;
        return lArray;
    }

    public static String randomColor(int n) {
        Random random = new Random(n);
        int n2 = random.nextInt(0x1000000);
        return String.format("#%06x", n2);
    }
}

