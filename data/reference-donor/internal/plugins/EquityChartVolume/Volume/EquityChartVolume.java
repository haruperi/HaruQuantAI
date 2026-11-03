/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.InstrumentInfo
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.pluginlib.annotations.Category
 *  com.strategyquant.pluginlib.annotations.HideDatabankChoice
 *  com.strategyquant.pluginlib.annotations.License
 *  com.strategyquant.pluginlib.annotations.Name
 *  com.strategyquant.pluginlib.annotations.ShortDesc
 *  com.strategyquant.tradinglib.Order
 *  com.strategyquant.tradinglib.OrdersList
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.equitychart.EquityChart
 *  com.strategyquant.tradinglib.equitychart.SubChart
 *  com.strategyquant.tradinglib.equitychart.SubChartDataset
 *  com.strategyquant.tradinglib.equitychartnew.addons.IEquityChartAddon
 *  com.strategyquant.tradinglib.results.SymbolInfo
 *  it.unimi.dsi.fastutil.longs.Long2DoubleAVLTreeMap
 *  it.unimi.dsi.fastutil.longs.Long2DoubleMap$Entry
 *  net.xeoh.plugins.base.annotations.PluginImplementation
 *  net.xeoh.plugins.base.annotations.meta.Author
 */
package com.strategyquant.plugin.EquityChart.impl.Volume;

import com.strategyquant.datalib.InstrumentInfo;
import com.strategyquant.lib.SQTime;
import com.strategyquant.pluginlib.annotations.Category;
import com.strategyquant.pluginlib.annotations.HideDatabankChoice;
import com.strategyquant.pluginlib.annotations.License;
import com.strategyquant.pluginlib.annotations.Name;
import com.strategyquant.pluginlib.annotations.ShortDesc;
import com.strategyquant.tradinglib.Order;
import com.strategyquant.tradinglib.OrdersList;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.equitychart.EquityChart;
import com.strategyquant.tradinglib.equitychart.SubChart;
import com.strategyquant.tradinglib.equitychart.SubChartDataset;
import com.strategyquant.tradinglib.equitychartnew.addons.IEquityChartAddon;
import com.strategyquant.tradinglib.results.SymbolInfo;
import it.unimi.dsi.fastutil.longs.Long2DoubleAVLTreeMap;
import it.unimi.dsi.fastutil.longs.Long2DoubleMap;
import java.util.Map;
import net.xeoh.plugins.base.annotations.PluginImplementation;
import net.xeoh.plugins.base.annotations.meta.Author;

@Author(name="Tamas Takacs")
@Name(name="Equity Chart Volume plugin")
@Category(name="EquityChart")
@License(text="")
@ShortDesc(text="Short description")
@HideDatabankChoice
@PluginImplementation
public class EquityChartVolume
implements IEquityChartAddon {
    private static byte Auto = (byte)5;
    private static byte Size = (byte)2;
    private static byte Money = 1;
    private static byte Off = 0;

    public String getProduct() {
        return "SQUANTAlgoWizardBACKTESTNODE";
    }

    public int getPreferredPosition() {
        return 1;
    }

    public void initPlugin() throws Exception {
    }

    public void print(EquityChart chart, ResultsGroup resultsGroup, String resultKey, OrdersList orders, Map<String, String[]> params, String domainAxisType) throws Exception {
        SubChartDataset dataset;
        byte type = Byte.parseByte(params.get("volume")[0]);
        if (type == Off) {
            return;
        }
        byte t = this.getVolumeType(resultsGroup, type);
        String datasetName = t == Size ? "Volume" : "Volume ($)";
        double firstSize = -11111.0;
        boolean differentVolume = false;
        if (domainAxisType.equals("time")) {
            long date;
            double size;
            Long2DoubleAVLTreeMap map = new Long2DoubleAVLTreeMap();
            for (int i = 0; i < orders.size(); ++i) {
                Order order = orders.get(i);
                size = this.getVolume(resultsGroup, order, type);
                date = SQTime.getDateInMs((long)order.CloseTime);
                if (map.containsKey(date)) {
                    map.put(date, map.get(date) + size);
                    continue;
                }
                map.put(date, size);
            }
            dataset = new SubChartDataset(datasetName, map.size());
            for (Long2DoubleMap.Entry item : map.long2DoubleEntrySet()) {
                size = item.getDoubleValue();
                date = item.getLongKey();
                if (firstSize == -11111.0) {
                    firstSize = size;
                } else if (firstSize != size) {
                    differentVolume = true;
                }
                dataset.addValue(date, size);
            }
        } else {
            dataset = new SubChartDataset(datasetName, orders.size());
            for (int i = 0; i < orders.size(); ++i) {
                Order order = orders.get(i);
                double size = this.getVolume(resultsGroup, order, type);
                if (firstSize == -11111.0) {
                    firstSize = size;
                } else if (firstSize != size) {
                    differentVolume = true;
                }
                dataset.addValue((long)i, size);
            }
        }
        if (type != Auto || type == Auto && differentVolume) {
            dataset.d3Format();
            dataset.setName(datasetName);
            dataset.type = "bar";
            dataset.color = "#61a8ff";
            SubChart subChart = new SubChart(datasetName);
            subChart.forceStartYFromZero = true;
            subChart.name = datasetName;
            subChart.titlePosition = "chartLeftTop";
            subChart.addDataset(dataset);
            chart.addSubChart(subChart);
        }
    }

    private double getVolume(ResultsGroup resultsGroup, Order order, byte type) throws Exception {
        byte t = this.getVolumeType(resultsGroup, type);
        if (t == Size) {
            return order.Size;
        }
        InstrumentInfo instrumentInfo = this.getInstrumentInfo(resultsGroup, order);
        return (double)(order.Size * order.OpenPrice) * instrumentInfo.pointValue;
    }

    private byte getVolumeType(ResultsGroup resultsGroup, byte type) {
        if (type == Auto) {
            return resultsGroup.isStockpickerStrategy() ? Money : Size;
        }
        return type;
    }

    private InstrumentInfo getInstrumentInfo(ResultsGroup rg, Order order) throws Exception {
        InstrumentInfo instrumentInfo = null;
        SymbolInfo si = rg.symbols().get(order.Symbol);
        if (si != null) {
            instrumentInfo = si.InstrumentInfo();
        }
        if (instrumentInfo == null) {
            instrumentInfo = rg.symbols().getDefaultInstrumentInfo();
        }
        if (instrumentInfo == null) {
            throw new Exception(String.format("Instrument info not found for %s / %s", rg.getName(), order.Symbol));
        }
        return instrumentInfo;
    }

    public String getName() {
        return "Volume";
    }
}

