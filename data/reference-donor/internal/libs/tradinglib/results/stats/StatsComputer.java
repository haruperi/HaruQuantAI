/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.SettingsMap
 *  com.strategyquant.lib.snippets.NonexistingCustomClassException
 *  com.strategyquant.lib.utils.ISQCloneable
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.results.stats;

import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.SettingsMap;
import com.strategyquant.lib.snippets.NonexistingCustomClassException;
import com.strategyquant.lib.utils.ISQCloneable;
import com.strategyquant.tradinglib.DatabankColumn;
import com.strategyquant.tradinglib.Order;
import com.strategyquant.tradinglib.OrdersList;
import com.strategyquant.tradinglib.Result;
import com.strategyquant.tradinglib.SQStats;
import com.strategyquant.tradinglib.StatsTypeCombination;
import com.strategyquant.tradinglib.databank.DatabankColumns;
import com.strategyquant.tradinglib.results.SymbolsMap;
import com.strategyquant.tradinglib.results.stats.comparator.OrderComparatorByCloseTime;
import com.strategyquant.tradinglib.results.stats.computer.IOrderComputer;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.ListIterator;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class StatsComputer
implements ISQCloneable {
    public static final Logger Log = LoggerFactory.getLogger((String)"StatsComputer");
    private static final String ConstantAll = "*";
    private static final ArrayList<DatabankColumn> globalStatValues = new ArrayList();
    private static final ArrayList<IOrderComputer> globalOrderComputers = new ArrayList();
    private ArrayList<DatabankColumn> statValues;
    private static boolean dependenciesComputed = false;
    private boolean filtered = false;
    private OrdersList originalOrdersList;
    private OrdersList filteredOL;
    private SettingsMap rgSpecialValues = null;
    private final Comparator<Order> comparatorByCloseTime = new OrderComparatorByCloseTime();

    public StatsComputer() {
        this.statValues = globalStatValues;
    }

    public StatsComputer(ArrayList<DatabankColumn> arrayList) {
        this.statValues = arrayList;
    }

    public static void clearGlobalStatsValues() {
        globalStatValues.clear();
    }

    public static void registerDatabankColumn(DatabankColumn databankColumn) {
        globalStatValues.add(databankColumn);
    }

    public static void registerOrderComputer(IOrderComputer iOrderComputer) {
        globalOrderComputers.add(iOrderComputer);
    }

    public static void createDependencyGraph() throws Exception {
        StatsComputer.createDependencyGraph(globalStatValues);
        dependenciesComputed = true;
    }

    public static void createDependencyGraph(ArrayList<DatabankColumn> arrayList) throws Exception {
        ArrayList<DatabankColumn> arrayList2 = new ArrayList<DatabankColumn>();
        arrayList2.addAll(arrayList);
        ArrayList<DatabankColumn> arrayList3 = new ArrayList<DatabankColumn>();
        for (int i = 0; i < arrayList.size(); ++i) {
            boolean bl = false;
            ListIterator listIterator = arrayList2.listIterator();
            while (listIterator.hasNext()) {
                DatabankColumn databankColumn = (DatabankColumn)listIterator.next();
                if (!StatsComputer.checkColumnDependsOnExistingColumn(databankColumn, arrayList3)) continue;
                arrayList3.add(databankColumn);
                listIterator.remove();
                bl = true;
            }
            if (arrayList2.size() == 0) break;
            if (bl) continue;
            throw new Exception("Unsolved dependency detected. Missing values required by some other snippet:\n\nThe problem could be either circular dependency (A depends on B, B depends on C, C depends on A)\nor missing / uncompiled stats value snippet. Check if all the StatValues snippets were successfuly compiled.");
        }
        arrayList.clear();
        arrayList.addAll(arrayList3);
    }

    private static boolean checkColumnDependsOnExistingColumn(DatabankColumn databankColumn, ArrayList<DatabankColumn> arrayList) {
        String[] stringArray = databankColumn.getDependencies();
        if (stringArray == null) {
            return true;
        }
        for (String string : stringArray) {
            boolean bl = false;
            for (int i = 0; i < arrayList.size(); ++i) {
                if (!string.equals(arrayList.get(i).getClass().getSimpleName())) continue;
                bl = true;
                break;
            }
            if (bl) continue;
            return false;
        }
        return true;
    }

    public static ArrayList<DatabankColumn> getAllDependentStatValues(ArrayList<DatabankColumn> arrayList) throws NonexistingCustomClassException {
        while (true) {
            ArrayList<DatabankColumn> arrayList2 = null;
            for (int i = 0; i < arrayList.size(); ++i) {
                DatabankColumn databankColumn = arrayList.get(i);
                if (StatsComputer.checkColumnDependsOnExistingColumn(databankColumn, arrayList)) continue;
                if (arrayList2 == null) {
                    arrayList2 = new ArrayList<DatabankColumn>();
                }
                arrayList2.addAll(StatsComputer.getDependOnColumns(databankColumn));
            }
            if (arrayList2 == null) break;
            arrayList.addAll(arrayList2);
        }
        return arrayList;
    }

    private static ArrayList<DatabankColumn> getDependOnColumns(DatabankColumn databankColumn) throws NonexistingCustomClassException {
        String[] stringArray = databankColumn.getDependencies();
        if (stringArray == null) {
            return null;
        }
        ArrayList<DatabankColumn> arrayList = new ArrayList<DatabankColumn>();
        for (String string : stringArray) {
            arrayList.add((DatabankColumn)DatabankColumns.get().findClassByName(string));
        }
        return arrayList;
    }

    public void initializeWithOrders(OrdersList ordersList) {
        this.initializeWithOrders(ordersList, false);
    }

    public void initializeWithOrders(OrdersList ordersList, boolean bl) {
        this.filteredOL = this.originalOrdersList = ordersList;
        this.filtered = bl;
    }

    public void filterBy(String string, byte by, byte by2) {
        this.filteredOL = this.originalOrdersList.filter(string, by, by2);
        this.filtered = true;
    }

    public void sortAndComputeOrderValues(SettingsMap settingsMap, SymbolsMap symbolsMap) throws Exception {
        if (!this.filtered) {
            throw new Exception("You have to call StatsComputer.filterBy() before calling sortAndComputeOrderValues()");
        }
        this.filteredOL.sort(this.comparatorByCloseTime);
        for (int i = 0; i < globalOrderComputers.size(); ++i) {
            globalOrderComputers.get(i).compute(this.filteredOL, settingsMap, symbolsMap);
        }
    }

    public SQStats computeStats(Result result, StatsTypeCombination statsTypeCombination, SettingsMap settingsMap) throws Exception {
        if (!this.filtered) {
            throw new Exception("You have to call StatsComputer.filterBy() before calling computeStats()");
        }
        int n = statsTypeCombination.getKey();
        try {
            SQStats sQStats = new SQStats();
            SQStats sQStats2 = null;
            SQStats sQStats3 = null;
            if (result != null) {
                if (statsTypeCombination.getPLType() != 10) {
                    SQStats sQStats4 = result.stats((byte)1, (byte)10, statsTypeCombination.getSampleType());
                    sQStats.copyValuesFrom(sQStats4);
                }
                if (statsTypeCombination.getDirection() == 0) {
                    sQStats2 = result.stats((byte)1, statsTypeCombination.getPLType(), statsTypeCombination.getSampleType());
                    sQStats3 = result.stats((byte)-1, statsTypeCombination.getPLType(), statsTypeCombination.getSampleType());
                }
            }
            long l = System.currentTimeMillis();
            this.computeStatValues(sQStats, statsTypeCombination, this.filteredOL, settingsMap, sQStats2, sQStats3, result);
            return sQStats;
        }
        catch (Exception exception) {
            Log.error("Failed to compute stats for combination: " + statsTypeCombination.getKeyAsStr() + ", message: " + exception.getMessage(), (Throwable)exception);
            throw new Exception("Failed to compute stats for combination: " + statsTypeCombination.getKeyAsStr() + ", message: " + exception.getMessage(), exception);
        }
    }

    private void computeStatValues(SQStats sQStats, StatsTypeCombination statsTypeCombination, OrdersList ordersList, SettingsMap settingsMap, SQStats sQStats2, SQStats sQStats3, Result result) throws Exception {
        for (int i = 0; i < this.statValues.size(); ++i) {
            byte[] byArray;
            DatabankColumn databankColumn = this.statValues.get(i);
            String string = databankColumn.getClassName();
            boolean bl = true;
            byte[] byArray2 = databankColumn.getPLTypeRestrictions();
            if (byArray2 != null && !SQUtils.isInByteArray((byte)statsTypeCombination.getPLType(), (byte[])byArray2)) {
                bl = false;
            }
            if (!bl || (byArray = databankColumn.getDirectionRestrictions()) == null || !SQUtils.isInByteArray((byte)statsTypeCombination.getDirection(), (byte[])byArray)) {
                // empty if block
            }
            if (bl) {
                try {
                    double d = databankColumn.compute(sQStats, statsTypeCombination, ordersList, settingsMap, sQStats2, sQStats3, result, this.rgSpecialValues);
                    sQStats.set(string, d);
                }
                catch (Exception exception) {
                    Log.error("Exception computing databank column {}", (Object)string, (Object)exception);
                    sQStats.set(string, -1);
                }
                continue;
            }
            if (sQStats.containsKey(string)) continue;
            sQStats.set(string, 0);
        }
    }

    public OrdersList getFilteredOrders() throws Exception {
        if (!this.filtered) {
            throw new Exception("You have to call StatsComputer.filterBy() before calling getFilteredOrders()");
        }
        return this.filteredOL;
    }

    public int checkStrategyProblems(String string, int n) {
        if (this.filteredOL.size() == 0) {
            return n;
        }
        double d = 0.0;
        double d2 = 0.0;
        double d3 = 0.0;
        int n2 = 0;
        for (int i = 0; i < this.filteredOL.size(); ++i) {
            Order order = this.filteredOL.get(i);
            if (order.isBalanceOrder()) continue;
            double d4 = order.PL;
            if (d4 > d) {
                d3 = d2;
                d2 = d;
                d = d4;
            } else if (d4 > d2) {
                d3 = d2;
                d2 = d4;
            } else if (d4 > d3) {
                d3 = d4;
            }
            ++n2;
        }
        if (n2 > 2 && d > 2.0 * (d2 + d3)) {
            n |= 0x200;
        }
        return n;
    }

    public void setRGSpecialValues(SettingsMap settingsMap) {
        this.rgSpecialValues = settingsMap;
    }

    public StatsComputer getClone() {
        StatsComputer statsComputer = new StatsComputer();
        statsComputer.statValues = this.statValues;
        return statsComputer;
    }

    public SQStats computeZeroStats() {
        SQStats sQStats = new SQStats();
        for (int i = 0; i < this.statValues.size(); ++i) {
            DatabankColumn databankColumn = this.statValues.get(i);
            String string = databankColumn.getClassName();
            sQStats.set(string, 0);
        }
        return sQStats;
    }
}

