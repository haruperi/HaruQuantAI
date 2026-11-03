/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.ChartDef
 *  com.strategyquant.datalib.data.DataException
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.datalib.data.io.IDataLoader
 *  com.strategyquant.datalib.data.io.VersatileData
 *  com.strategyquant.lib.L
 *  com.strategyquant.pluginlib.annotations.Category
 *  com.strategyquant.pluginlib.annotations.HideDatabankChoice
 *  com.strategyquant.pluginlib.annotations.License
 *  com.strategyquant.pluginlib.annotations.Name
 *  com.strategyquant.pluginlib.annotations.ShortDesc
 *  com.strategyquant.tradinglib.OrdersList
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.charts.linechart.series.XYValue
 *  com.strategyquant.tradinglib.equitychart.EquityChart
 *  com.strategyquant.tradinglib.equitychart.EquityChartUtils
 *  com.strategyquant.tradinglib.equitychart.SubChart
 *  com.strategyquant.tradinglib.equitychart.SubChartDataset
 *  com.strategyquant.tradinglib.equitychartnew.addons.IEquityChartAddon
 *  com.strategyquant.tradinglib.results.SpecialValues
 *  it.unimi.dsi.fastutil.objects.ObjectArrayList
 *  net.xeoh.plugins.base.annotations.PluginImplementation
 *  net.xeoh.plugins.base.annotations.meta.Author
 */
package com.strategyquant.plugin.EquityChart.impl.DailyChart;

import com.strategyquant.datalib.ChartDef;
import com.strategyquant.datalib.data.DataException;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.datalib.data.io.IDataLoader;
import com.strategyquant.datalib.data.io.VersatileData;
import com.strategyquant.lib.L;
import com.strategyquant.pluginlib.annotations.Category;
import com.strategyquant.pluginlib.annotations.HideDatabankChoice;
import com.strategyquant.pluginlib.annotations.License;
import com.strategyquant.pluginlib.annotations.Name;
import com.strategyquant.pluginlib.annotations.ShortDesc;
import com.strategyquant.tradinglib.OrdersList;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.charts.linechart.series.XYValue;
import com.strategyquant.tradinglib.equitychart.EquityChart;
import com.strategyquant.tradinglib.equitychart.EquityChartUtils;
import com.strategyquant.tradinglib.equitychart.SubChart;
import com.strategyquant.tradinglib.equitychart.SubChartDataset;
import com.strategyquant.tradinglib.equitychartnew.addons.IEquityChartAddon;
import com.strategyquant.tradinglib.results.SpecialValues;
import it.unimi.dsi.fastutil.objects.ObjectArrayList;
import java.util.Map;
import net.xeoh.plugins.base.annotations.PluginImplementation;
import net.xeoh.plugins.base.annotations.meta.Author;

@Author(name="Tamas Takacs")
@Name(name="Daily chart plugin")
@Category(name="EquityChart")
@License(text="")
@ShortDesc(text="Short description")
@HideDatabankChoice
@PluginImplementation
public class DailyChart
implements IEquityChartAddon {
    public String getProduct() {
        return "SQUANTAlgoWizardBACKTESTNODE";
    }

    public int getPreferredPosition() {
        return 3;
    }

    public void initPlugin() throws Exception {
    }

    public void print(EquityChart chart, ResultsGroup resultsGroup, String resultKey, OrdersList orders, Map<String, String[]> params, String domainAxisType) throws Exception {
        if (!Boolean.parseBoolean(params.get("dailychart")[0])) {
            return;
        }
        if (!domainAxisType.equals("time")) {
            return;
        }
        String symbol = null;
        symbol = resultsGroup.subResult(resultKey).containsKey(SpecialValues.Symbol) ? resultsGroup.subResult(resultKey).getString(SpecialValues.Symbol) : resultsGroup.specialValues().getString(SpecialValues.Symbol, symbol);
        if (symbol == null || symbol.equals("Portfolio") || DataManager.isGroupAlias((String)symbol)) {
            return;
        }
        if (symbol.contains(",")) {
            symbol = symbol.split(",")[0];
        }
        String name = symbol + ", Daily";
        SubChart subChart = new SubChart("DailyChart");
        subChart.name = name;
        subChart.titlePosition = "chartLeftTop";
        chart.addSubChart(subChart);
        try {
            double spread = 2.5;
            String session = "No Session";
            long[] dateRange = EquityChartUtils.dateRange((OrdersList)orders);
            ChartDef chartDef = new ChartDef("History", symbol, "D1", dateRange[0], dateRange[1], spread, session);
            IDataLoader loader = DataManager.getDataLoader((ChartDef)chartDef, (int)1, null);
            loader.open();
            ObjectArrayList list = new ObjectArrayList();
            while (loader.hasNextTick()) {
                VersatileData vd = new VersatileData();
                loader.getNextTick(vd);
                list.add((Object)new XYValue(vd.time, vd.close));
            }
            loader.close();
            SubChartDataset dataset = new SubChartDataset("DailyChart", list.size());
            dataset.setName(name);
            dataset.type = "line";
            dataset.color = "#000000";
            for (int i = 0; i < list.size(); ++i) {
                dataset.addValue(Long.valueOf(((XYValue)list.get((int)i)).x).longValue(), Double.valueOf(((XYValue)list.get((int)i)).y).doubleValue());
            }
            subChart.addDataset(dataset);
        }
        catch (DataException e) {
            subChart.name = subChart.name + " - " + L.t((String)"No data found for symbol '%s'", (Object[])new Object[]{symbol});
            throw e;
        }
        catch (Exception e) {
            subChart.name = subChart.name + " - " + L.t((String)"Error: %s", (Object[])new Object[]{e.getMessage()});
            throw e;
        }
    }

    public String getName() {
        return "Daily chart";
    }
}

