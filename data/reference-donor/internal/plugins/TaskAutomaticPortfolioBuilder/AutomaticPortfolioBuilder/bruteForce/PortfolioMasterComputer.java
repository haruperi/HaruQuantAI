/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.tradinglib.Order
 *  com.strategyquant.tradinglib.OrdersList
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.conditions.Condition
 *  com.strategyquant.tradinglib.conditions.ConditionsChecker
 *  com.strategyquant.tradinglib.conditions.DismissStruct
 *  com.strategyquant.tradinglib.databank.IDatabankFilter
 *  com.strategyquant.tradinglib.databank.IProgressListener
 *  com.strategyquant.tradinglib.portfolioMaster.PortfolioMasterSettings
 *  com.strategyquant.tradinglib.project.ProgressEngine
 *  com.strategyquant.tradinglib.project.SQProject
 *  com.strategyquant.tradinglib.results.SpecialValues
 *  it.unimi.dsi.fastutil.objects.ObjectListIterator
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Task.impl.AutomaticPortfolioBuilder.bruteForce;

import com.strategyquant.lib.L;
import com.strategyquant.lib.SQTime;
import com.strategyquant.plugin.Task.impl.AutomaticPortfolioBuilder.bruteForce.PMDatabankFilter;
import com.strategyquant.tradinglib.Order;
import com.strategyquant.tradinglib.OrdersList;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.conditions.Condition;
import com.strategyquant.tradinglib.conditions.ConditionsChecker;
import com.strategyquant.tradinglib.conditions.DismissStruct;
import com.strategyquant.tradinglib.databank.IDatabankFilter;
import com.strategyquant.tradinglib.databank.IProgressListener;
import com.strategyquant.tradinglib.portfolioMaster.PortfolioMasterSettings;
import com.strategyquant.tradinglib.project.ProgressEngine;
import com.strategyquant.tradinglib.project.SQProject;
import com.strategyquant.tradinglib.results.SpecialValues;
import it.unimi.dsi.fastutil.objects.ObjectListIterator;
import java.util.ArrayList;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public abstract class PortfolioMasterComputer {
    public static final Logger Log = LoggerFactory.getLogger((String)"PortfolioMasterComputer");
    protected ArrayList<ResultsGroup> originalResults;
    protected ConditionsChecker conditionsChecker = new ConditionsChecker();
    protected PortfolioMasterSettings settings;
    protected ProgressEngine progressEngine;
    protected SQProject project;
    protected int portfolioIndex = 0;

    public abstract void execute() throws Exception;

    private String indexesToString(int[] indexes) {
        String str = "[";
        for (int i = 0; i < indexes.length; ++i) {
            str = str + indexes[i] + ",";
        }
        str = str.substring(0, str.length() - 1);
        str = str + "]";
        return str;
    }

    public String getPortfolioIndexes(int[] indexes) {
        return "Portfolio " + this.indexesToString(indexes);
    }

    public String getPortfolioName(int index) {
        return "Portfolio " + index;
    }

    public abstract void computePortfolio(int[] var1) throws Exception;

    public synchronized ArrayList<ResultsGroup> getResults(int[] indexes) throws Exception {
        ArrayList<ResultsGroup> results = new ArrayList<ResultsGroup>();
        for (int i : indexes) {
            results.add(this.originalResults.get(i));
        }
        return results;
    }

    public void beforeStart() throws Exception {
        this.limitMaxStrategiesInDatabank();
        boolean limitDateRange = this.settings.limitDateRange;
        if (limitDateRange) {
            long dateFrom = this.settings.dateRangeFrom;
            long dateTo = this.settings.dateRangeTo;
            this.limitDataRange(this.originalResults, dateFrom, dateTo);
        }
        this.setSampleParts(this.originalResults);
        for (int i = 0; i < this.originalResults.size(); ++i) {
            ResultsGroup rg = this.originalResults.get(i);
            rg.specialValues().set("result_index", (Object)i);
        }
        for (ResultsGroup result : this.originalResults) {
            String sector = result.getNote();
            if (sector != null) {
                sector = sector.trim();
                sector = sector.toLowerCase();
            }
            result.specialValues().setString(SpecialValues.Sector, sector);
        }
    }

    private void limitMaxStrategiesInDatabank() throws Exception {
        try {
            PMDatabankFilter filter = new PMDatabankFilter(this.settings.maxStrategiesInDatabank, false, this.settings.fitnessSampleType);
            this.settings.databankTarget.applyFilter((IDatabankFilter)filter, new IProgressListener(){

                public void onProgress(double percentDone) {
                    PortfolioMasterComputer.this.project.getProgress().update("max-strategies-change", percentDone, null);
                }

                public void onError(double percentDone, String error) {
                    PortfolioMasterComputer.this.project.getProgress().update("max-strategies-change", percentDone, error);
                }

                public void onDone() {
                    PortfolioMasterComputer.this.settings.databankTarget.removeFilter();
                }
            });
        }
        catch (Exception e) {
            throw new Exception("Error while setting maximum portfolios in databank - " + e.getMessage(), e);
        }
    }

    protected synchronized DismissStruct checkCustomConditions(ResultsGroup result) {
        int dismissalReasonPrefix = 200000;
        ArrayList conditions = this.settings.conditions;
        if (conditions != null && conditions.size() > 0) {
            for (int i = 0; i < conditions.size(); ++i) {
                try {
                    boolean met;
                    Condition condition = (Condition)conditions.get(i);
                    if (!condition.isUsed() || (met = this.conditionsChecker.check(result, condition))) continue;
                    return new DismissStruct(dismissalReasonPrefix + i, this.conditionsChecker.dismissalMessage);
                }
                catch (Exception e) {
                    Log.error("Error while checking condition", (Throwable)e);
                    return new DismissStruct(10003, L.t((String)"Error while evaluating conditions: %s", (Object[])new Object[]{e.getMessage()}));
                }
            }
        }
        return null;
    }

    public void limitDataRange(ArrayList<ResultsGroup> selectedStrategies, long dateFrom, long dateTo) throws Exception {
        try {
            for (int i = 0; i < selectedStrategies.size(); ++i) {
                ResultsGroup rg = selectedStrategies.get(i);
                OrdersList orders = rg.orders();
                ObjectListIterator it = orders.listIterator();
                while (it.hasNext()) {
                    Order order = (Order)it.next();
                    if (order.OpenTime > dateFrom && order.CloseTime < dateTo) continue;
                    it.remove();
                }
                long historyFrom = orders.isEmpty() ? 0L : orders.get((int)0).OpenTime;
                long historyTo = orders.isEmpty() ? 0L : orders.get((int)(orders.size() - 1)).CloseTime;
                rg.specialValues().set(SpecialValues.HistoryFrom, (Object)historyFrom);
                rg.specialValues().set(SpecialValues.HistoryTo, (Object)historyTo);
            }
        }
        catch (Exception e) {
            throw new Exception("Error while limiting Data range - " + e.getMessage(), e);
        }
    }

    public void setSampleParts(ArrayList<ResultsGroup> selectedStrategies) throws Exception {
        try {
            long dateMin = 0L;
            long dateMax = 0L;
            for (int i = 0; i < selectedStrategies.size(); ++i) {
                ResultsGroup rg = selectedStrategies.get(i);
                long dateFrom = rg.specialValues().getLong(SpecialValues.HistoryFrom, Long.MAX_VALUE);
                long dateTo = rg.specialValues().getLong(SpecialValues.HistoryTo, Long.MIN_VALUE);
                if (dateMin == 0L || dateFrom < dateMin) {
                    dateMin = dateFrom;
                }
                if (dateTo <= dateMax) continue;
                dateMax = dateTo;
            }
            Log.info(String.format("Data range %s - %s", SQTime.toDateString((long)dateMin), SQTime.toDateString((long)dateMax)));
            double days = SQTime.getDaysBetween((long)dateMin, (long)dateMax);
            Double isDays = days / 100.0 * (double)this.settings.IsPct;
            long oosFrom = SQTime.addDays((long)dateMin, (int)isDays.intValue());
            for (int i = 0; i < selectedStrategies.size(); ++i) {
                ResultsGroup rg = selectedStrategies.get(i);
                this.setSampleParts(rg, oosFrom);
            }
        }
        catch (Exception e) {
            throw new Exception("Error while setting Sample parts - " + e.getMessage(), e);
        }
    }

    private void setSampleParts(ResultsGroup rg, long oosFrom) throws Exception {
        OrdersList orders = rg.orders();
        for (int i = 0; i < orders.size(); ++i) {
            Order order = orders.get(i);
            if (this.settings.reverseSample) {
                if (order.OpenTime >= oosFrom) {
                    order.SampleType = (byte)11;
                    continue;
                }
                order.SampleType = (byte)21;
                continue;
            }
            order.SampleType = order.OpenTime >= oosFrom ? (byte)21 : (byte)11;
        }
    }

    protected abstract boolean isStopped();
}

