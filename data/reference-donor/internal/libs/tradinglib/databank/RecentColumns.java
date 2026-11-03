/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.constants.SQPaths
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.databank;

import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.constants.SQPaths;
import com.strategyquant.tradinglib.databank.DatabankColumns;
import com.strategyquant.tradinglib.optimization.WalkForwardColumns;
import java.io.File;
import java.io.PrintWriter;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.stream.Collectors;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class RecentColumns {
    private static final Logger Log = LoggerFactory.getLogger(RecentColumns.class);
    private static final String filePath = SQPaths.settingsDirPath + "/RecentRankingCols.txt";
    private static int MAX_COLUMNS = 8;
    private static RecentColumns instance;
    private ArrayList<String> recentCols = new ArrayList();

    private RecentColumns() {
        this.recentCols.clear();
        Log.debug("Loading recently used ranking columns...");
        try {
            File file = new File(filePath);
            if (file.exists()) {
                String string = SQUtils.fileToString((File)file);
                for (String string2 : string.split("\n")) {
                    if ((string2 = string2.trim()).isEmpty()) continue;
                    this.recentCols.add(string2);
                }
            }
        }
        catch (Exception exception) {
            Log.warn("File '" + filePath + "' cannot be loaded.");
        }
        instance = this;
    }

    private static RecentColumns get() {
        if (instance == null) {
            new RecentColumns();
        }
        return instance;
    }

    private void save() {
        block3: {
            PrintWriter printWriter = null;
            try {
                printWriter = new PrintWriter(SQUtils.createFile((String)filePath));
                for (String string : this.recentCols) {
                    if (string == null || string.isEmpty()) continue;
                    printWriter.println(string);
                }
                printWriter.close();
            }
            catch (Exception exception) {
                Log.error("Cannot save recent ranking columns. ", (Throwable)exception);
                if (printWriter == null) break block3;
                printWriter.close();
            }
        }
    }

    private void _updateRecentCols(String[] stringArray) {
        for (String string : stringArray) {
            int n = this.recentCols.indexOf(string = string.trim());
            if (n >= 0) {
                this.recentCols.remove(n);
            }
            this.recentCols.add(0, string);
        }
        if (this.recentCols.size() > MAX_COLUMNS) {
            this.recentCols.subList(MAX_COLUMNS, this.recentCols.size()).clear();
        }
        this.save();
    }

    public static List<String> getRecentCols() {
        List<String> list = Arrays.asList("NetProfit", "NumberOfTrades", "Drawdown", "DrawdownPct", "ReturnDDRatio", "ProfitFactor", "AvgBarsInTrade", "WinningPct");
        ArrayList<String> arrayList = new ArrayList<String>();
        for (String string : RecentColumns.get().recentCols) {
            if (!RecentColumns.checkColumn(string)) continue;
            arrayList.add(string);
        }
        for (String string : list) {
            if (!RecentColumns.checkColumn(string)) continue;
            arrayList.add(string);
        }
        List list2 = arrayList.stream().distinct().collect(Collectors.toList());
        return list2;
    }

    private static boolean checkColumn(String string) {
        try {
            DatabankColumns.get().findClassByName(string);
        }
        catch (Exception exception) {
            try {
                WalkForwardColumns.get().findClassByName(string);
            }
            catch (Exception exception2) {
                return false;
            }
        }
        return true;
    }

    public static void updateRecentCols(String[] stringArray) {
        RecentColumns.get()._updateRecentCols(stringArray);
    }
}

