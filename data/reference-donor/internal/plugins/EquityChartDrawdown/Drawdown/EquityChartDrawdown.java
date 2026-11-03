/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.SettingsMap
 *  com.strategyquant.pluginlib.annotations.Category
 *  com.strategyquant.pluginlib.annotations.HideDatabankChoice
 *  com.strategyquant.pluginlib.annotations.License
 *  com.strategyquant.pluginlib.annotations.Name
 *  com.strategyquant.pluginlib.annotations.ShortDesc
 *  com.strategyquant.tradinglib.Order
 *  com.strategyquant.tradinglib.OrdersList
 *  com.strategyquant.tradinglib.PlTypes
 *  com.strategyquant.tradinglib.Result
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.equitychart.EquityChart
 *  com.strategyquant.tradinglib.equitychart.EquityChartUtils
 *  com.strategyquant.tradinglib.equitychart.SubChart
 *  com.strategyquant.tradinglib.equitychart.SubChartDataset
 *  com.strategyquant.tradinglib.equitychartnew.addons.IEquityChartAddon
 *  it.unimi.dsi.fastutil.longs.Long2DoubleAVLTreeMap
 *  it.unimi.dsi.fastutil.longs.Long2FloatMap$Entry
 *  it.unimi.dsi.fastutil.longs.Long2FloatRBTreeMap
 *  net.xeoh.plugins.base.annotations.PluginImplementation
 *  net.xeoh.plugins.base.annotations.meta.Author
 */
package com.strategyquant.plugin.EquityChart.impl.Drawdown;

import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.SettingsMap;
import com.strategyquant.pluginlib.annotations.Category;
import com.strategyquant.pluginlib.annotations.HideDatabankChoice;
import com.strategyquant.pluginlib.annotations.License;
import com.strategyquant.pluginlib.annotations.Name;
import com.strategyquant.pluginlib.annotations.ShortDesc;
import com.strategyquant.tradinglib.Order;
import com.strategyquant.tradinglib.OrdersList;
import com.strategyquant.tradinglib.PlTypes;
import com.strategyquant.tradinglib.Result;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.equitychart.EquityChart;
import com.strategyquant.tradinglib.equitychart.EquityChartUtils;
import com.strategyquant.tradinglib.equitychart.SubChart;
import com.strategyquant.tradinglib.equitychart.SubChartDataset;
import com.strategyquant.tradinglib.equitychartnew.addons.IEquityChartAddon;
import it.unimi.dsi.fastutil.longs.Long2DoubleAVLTreeMap;
import it.unimi.dsi.fastutil.longs.Long2FloatMap;
import it.unimi.dsi.fastutil.longs.Long2FloatRBTreeMap;
import java.util.Map;
import net.xeoh.plugins.base.annotations.PluginImplementation;
import net.xeoh.plugins.base.annotations.meta.Author;

@Author(name="Tamas Takacs")
@Name(name="Equity Chart DD plugin")
@Category(name="EquityChart")
@License(text="")
@ShortDesc(text="Short description")
@HideDatabankChoice
@PluginImplementation
public class EquityChartDrawdown
implements IEquityChartAddon {
    public String getProduct() {
        return "SQUANTAlgoWizardBACKTESTNODE";
    }

    public int getPreferredPosition() {
        return 2;
    }

    public void initPlugin() throws Exception {
    }

    public void print(EquityChart chart, ResultsGroup resultsGroup, String resultKey, OrdersList orders, Map<String, String[]> params, String domainAxisType) throws Exception {
        long date;
        boolean dailyDDPctInitialized;
        double initialCapital;
        byte type = Byte.parseByte(params.get("drawdown")[0]);
        if (type == 0) {
            return;
        }
        SubChart subChart = new SubChart("Drawdown");
        subChart.name = "Drawdown (" + PlTypes.print((byte)type) + ")";
        subChart.titlePosition = "chartLeftTop";
        if (type == 111) {
            subChart.hideYTitle = true;
            type = 1;
        }
        SubChartDataset dataset = new SubChartDataset("Drawdown", orders.size());
        double dd = 0.0;
        Result result = resultsGroup.subResult(resultKey);
        Long2FloatRBTreeMap dailyDD = result.getMaxDailyDD();
        Long2FloatRBTreeMap dailyDDPct = result.getMaxDailyDDPct();
        Long2DoubleAVLTreeMap dailyDDMap = new Long2DoubleAVLTreeMap();
        SettingsMap settings = result.getSettings();
        double peakEquity = initialCapital = settings.getDouble("MoneyManagement.InitialCapital", 10000.0);
        double equity = initialCapital;
        boolean dailyDDInitialized = dailyDD != null && !dailyDD.isEmpty();
        boolean bl = dailyDDPctInitialized = dailyDDPct != null && !dailyDDPct.isEmpty();
        if (domainAxisType.equals("time") && type == 40 && dailyDDInitialized) {
            for (Long2FloatMap.Entry item : dailyDD.long2FloatEntrySet()) {
                date = item.getLongKey();
                dd = item.getFloatValue();
                dailyDDMap.put(date, dd);
            }
        } else if (domainAxisType.equals("time") && type == 50 && dailyDDPctInitialized) {
            for (Long2FloatMap.Entry item : dailyDDPct.long2FloatEntrySet()) {
                date = item.getLongKey();
                dd = item.getFloatValue();
                dailyDDMap.put(date, dd);
            }
        } else {
            double maeEquity = 0.0;
            for (int i = 0; i < orders.size(); ++i) {
                Order order = orders.get(i);
                if (type == 30) {
                    dd = EquityChartDrawdown.specialSubtraction(peakEquity, equity += (double)order.PipsPL);
                } else if (type == 20) {
                    dd = EquityChartDrawdown.specialSubtraction(peakEquity, equity += (double)order.PL);
                    dd = this.getPercentageDD(dd, peakEquity);
                } else if (type == 40) {
                    maeEquity = equity - (double)order.MAE;
                    equity += (double)order.PL;
                    dd = EquityChartDrawdown.specialSubtraction(peakEquity, maeEquity);
                    if (equity > peakEquity) {
                        peakEquity = equity;
                    }
                } else if (type == 50) {
                    maeEquity = equity - (double)order.MAE;
                    equity += (double)order.PL;
                    dd = EquityChartDrawdown.specialSubtraction(peakEquity, maeEquity);
                    dd = this.getPercentageDD(dd, peakEquity);
                    if (equity > peakEquity) {
                        peakEquity = equity;
                    }
                } else {
                    dd = EquityChartDrawdown.specialSubtraction(peakEquity, equity += (double)order.PL);
                }
                if (domainAxisType.equals("time")) {
                    date = SQTime.getDateInMs((long)order.CloseTime);
                    if (!dailyDDMap.containsKey(date) || dailyDDMap.get(date) > dd) {
                        dailyDDMap.put(date, dd);
                    }
                } else {
                    dataset.addValue((long)i, dd);
                }
                if (!(equity > peakEquity)) continue;
                peakEquity = equity;
            }
        }
        if (domainAxisType.equals("time")) {
            dataset = new SubChartDataset("Drawdown", dailyDDMap.size());
            for (Long2FloatMap.Entry item : dailyDDMap.long2DoubleEntrySet()) {
                dataset.addValue(item.getLongKey(), item.getDoubleValue());
            }
        }
        dataset.setName("Drawdown");
        dataset.type = "bar";
        dataset.color = "#ff6961";
        subChart.addDataset(dataset);
        chart.addSubChart(subChart);
    }

    private Long2DoubleAVLTreeMap generateDailyEquityMap(OrdersList orders) {
        long time;
        Long2DoubleAVLTreeMap dailyEquityMap = new Long2DoubleAVLTreeMap();
        long[] date = EquityChartUtils.dateRange((OrdersList)orders);
        long msFrom = date[0];
        long msTo = date[1];
        if (orders.isEmpty()) {
            return dailyEquityMap;
        }
        for (int i = 0; i < orders.size(); ++i) {
            Order order = orders.get(i);
            time = SQTime.getDateInMs((long)order.CloseTime);
            if (dailyEquityMap.containsKey(time)) {
                dailyEquityMap.put(time, dailyEquityMap.get(time) + (double)order.PL);
                continue;
            }
            dailyEquityMap.put(time, (double)order.PL);
        }
        time = SQTime.getDateInMs((long)msFrom);
        double equity = 0.0;
        do {
            if (dailyEquityMap.containsKey(time)) {
                equity += dailyEquityMap.get(time);
                continue;
            }
            dailyEquityMap.put(time, equity);
        } while ((time = SQTime.addDays((long)time, (int)1)) <= msTo);
        return dailyEquityMap;
    }

    private static double specialSubtraction(double peak, double equity) {
        double dd = peak - equity;
        if (dd < 0.0) {
            dd = 0.0;
        }
        return -1.0 * dd;
    }

    private double getPercentageDD(double pl, double equity) {
        if (equity <= 0.0 || pl > equity) {
            return -1.0;
        }
        return pl / (equity / 100.0);
    }

    public String getName() {
        return "Drawdown";
    }
}

