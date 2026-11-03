/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.ChartDef
 *  com.strategyquant.datalib.DataInfo
 *  com.strategyquant.datalib.InstrumentInfo
 *  com.strategyquant.datalib.data.DataException
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.settings.IXMLAble
 *  com.strategyquant.lib.utils.ISQCloneable
 *  org.jdom2.Content
 *  org.jdom2.Element
 */
package com.strategyquant.tradinglib;

import com.strategyquant.datalib.ChartDef;
import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.InstrumentInfo;
import com.strategyquant.datalib.data.DataException;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.settings.IXMLAble;
import com.strategyquant.lib.utils.ISQCloneable;
import com.strategyquant.tradinglib.CommissionsMethod;
import com.strategyquant.tradinglib.connection.Connection;
import com.strategyquant.tradinglib.connection.ConnectionManager;
import java.io.Serializable;
import java.util.ArrayList;
import java.util.HashMap;
import org.jdom2.Content;
import org.jdom2.Element;

public class ChartSetup
implements IXMLAble,
Serializable,
ISQCloneable<ChartSetup> {
    private ArrayList<ChartDef> charts = new ArrayList();
    private boolean used = false;
    private double minDistance;
    private int testPrecision;
    private boolean realSpread = false;
    private CommissionsMethod commissionsMethod;
    private int backtestEngine;

    public ChartSetup() {
    }

    public ChartSetup(String string, String string2, String string3, int n, long l, String string4) throws DataException {
        ChartDef chartDef = new ChartDef(string, string2, string3, n, l, string4);
        this.charts.add(chartDef);
    }

    public ChartSetup(String string, String string2, String string3, long l, long l2, double d, String string4) throws DataException {
        ChartDef chartDef = new ChartDef(string, string2, string3, l, l2, d, string4);
        this.charts.add(chartDef);
    }

    public ChartSetup(String string, String string2, long l, long l2, double d, String string3) throws DataException {
        this("History", string, string2, l, l2, d, string3);
    }

    public ChartDef addChart(String string, String string2, String string3, double d) throws DataException {
        if (this.checkChartExists(string, string2, string3)) {
            throw new DataException(2, "All subcharts must have unique settings.");
        }
        ChartDef chartDef = new ChartDef(string, string2, string3, this.charts.get(0).getHistoryFrom(), this.charts.get(0).getHistoryTo(), d, this.charts.get(0).getSession());
        chartDef.setRealSpread(this.realSpread);
        this.charts.add(chartDef);
        return chartDef;
    }

    public ChartDef addChart(String string, String string2, String string3) throws DataException {
        double d;
        ChartDef chartDef = this.getChartDef(string, string2);
        if (chartDef != null) {
            d = chartDef.getSpread();
            chartDef.setRealSpread(this.realSpread);
        } else {
            d = 0.0;
        }
        return this.addChart(string, string2, string3, d);
    }

    private ChartDef getChartDef(String string, String string2) {
        for (ChartDef chartDef : this.charts) {
            if (!chartDef.getConnectionName().equalsIgnoreCase(string) || !chartDef.getSymbol().equalsIgnoreCase(string2)) continue;
            return chartDef;
        }
        return null;
    }

    public void registerConnectionSymbols(ConnectionManager connectionManager) throws Exception {
        for (ChartDef chartDef : this.charts) {
            connectionManager.registerConnectionAndSymbol(chartDef);
        }
    }

    public void checkConnectionSymbolExist(ConnectionManager connectionManager) throws DataException {
        for (ChartDef chartDef : this.charts) {
            Connection connection = connectionManager.getConnection(chartDef.getConnectionName());
            if (!connection.isDataFeed()) {
                throw new DataException(1, "Connection '" + connection.getConnectionName() + "' is not a datafeed !");
            }
            if (connection.getDataFeed().checkSymbolIsSupported(chartDef.getSymbol())) continue;
            throw new DataException(2, "Data '" + chartDef.getSymbol() + "' is not supported in connection '" + connection.getConnectionName() + "' !");
        }
    }

    public ArrayList<ChartDef> getCharts() {
        return this.charts;
    }

    private boolean checkChartExists(String string, String string2, String string3) {
        for (ChartDef chartDef : this.charts) {
            if (!chartDef.getConnectionName().equalsIgnoreCase(string) || !chartDef.getSymbol().equalsIgnoreCase(string2) || !chartDef.getTimeframe().equalsIgnoreCase(string3)) continue;
            return true;
        }
        return false;
    }

    public void runChecks(ConnectionManager connectionManager) throws Exception {
        this.checkConnectionSymbolExist(connectionManager);
        HashMap<Integer, Double> hashMap = new HashMap<Integer, Double>();
        for (ChartDef object : this.charts) {
            int chartDef = object.getConnectionHash() + object.getSymbolHash();
            if (!hashMap.containsKey(chartDef)) {
                hashMap.put(chartDef, object.getSpread());
                continue;
            }
            double n = (Double)hashMap.get(chartDef);
            if (n == object.getSpread()) continue;
            object.setSpread(n);
        }
        HashMap hashMap2 = new HashMap();
        for (ChartDef chartDef : this.charts) {
            int n = chartDef.getConnectionHash() + chartDef.getSymbolHash();
            if (!hashMap2.containsKey(n)) {
                hashMap2.put(n, chartDef.getSession());
                continue;
            }
            String string = (String)hashMap2.get(n);
            if (string.equals(chartDef.getSession())) continue;
            chartDef.setSession(string);
        }
    }

    public int getChartsCount() {
        return this.charts.size();
    }

    public ChartSetup getClone() {
        ChartSetup chartSetup = new ChartSetup();
        chartSetup.used = false;
        chartSetup.minDistance = this.minDistance;
        chartSetup.testPrecision = this.testPrecision;
        chartSetup.backtestEngine = this.backtestEngine;
        if (this.charts != null) {
            chartSetup.charts = new ArrayList();
            for (ChartDef chartDef : this.charts) {
                chartSetup.charts.add(chartDef.getClone());
            }
        }
        return chartSetup;
    }

    public ChartSetup getClone(long l, long l2) {
        ChartSetup chartSetup = new ChartSetup();
        chartSetup.used = false;
        chartSetup.minDistance = this.minDistance;
        chartSetup.testPrecision = this.testPrecision;
        chartSetup.realSpread = this.realSpread;
        chartSetup.backtestEngine = this.backtestEngine;
        if (this.charts != null) {
            chartSetup.charts = new ArrayList();
            for (ChartDef chartDef : this.charts) {
                chartSetup.charts.add(chartDef.getClone(l, l2));
            }
        }
        return chartSetup;
    }

    public ChartSetup getClone(String string) {
        ChartSetup chartSetup = new ChartSetup();
        chartSetup.used = false;
        chartSetup.minDistance = this.minDistance;
        chartSetup.testPrecision = this.testPrecision;
        chartSetup.realSpread = this.realSpread;
        chartSetup.backtestEngine = this.backtestEngine;
        if (this.charts != null) {
            chartSetup.charts = new ArrayList();
            for (int i = 0; i < this.charts.size(); ++i) {
                ChartDef chartDef = this.charts.get(i);
                if (i == 0) {
                    chartSetup.charts.add(chartDef.getClone(string));
                    continue;
                }
                chartSetup.charts.add(chartDef.getClone());
            }
        }
        return chartSetup;
    }

    public boolean isUsed() {
        return this.used;
    }

    public void setUsed() {
        this.used = true;
    }

    public boolean isCreatedUsingBackload() {
        ChartDef chartDef = this.charts.get(0);
        return chartDef.getBackloadType() != 0;
    }

    public ChartDef getMainChart() {
        return this.charts.get(0);
    }

    public Element getXML() {
        Element element = new Element("ChartSetup");
        element.setAttribute("use", String.valueOf(this.used));
        for (ChartDef chartDef : this.charts) {
            element.addContent((Content)chartDef.getXML());
        }
        return element;
    }

    public void setFromXML(Element element) {
        this.used = XMLUtil.tryGetBoolAttr((Element)element, (String)"use");
        this.charts.clear();
        for (Element element2 : element.getChildren("ChartDef")) {
            ChartDef chartDef = new ChartDef();
            chartDef.setFromXML(element2);
            this.charts.add(chartDef);
        }
    }

    public void setMinDistance(double d) {
        this.minDistance = d;
        if (this.charts.size() > 0) {
            this.getMainChart().setMinDistance(d);
        }
    }

    public void setTestPrecision(int n) {
        this.testPrecision = n;
        this.realSpread = n == 4;
        for (ChartDef chartDef : this.charts) {
            chartDef.setRealSpread(this.realSpread);
        }
    }

    public int getTestPrecision() {
        return this.testPrecision;
    }

    public void addAllCharts(ChartSetup chartSetup) {
        for (int i = 0; i < chartSetup.charts.size(); ++i) {
            ChartDef chartDef = chartSetup.charts.get(i);
            this.addChart(chartDef);
        }
    }

    public void addChart(ChartDef chartDef) {
        for (int i = 0; i < this.charts.size(); ++i) {
            ChartDef chartDef2 = this.charts.get(i);
            if (chartDef.getSymbolHash() != chartDef2.getSymbolHash() || chartDef.getConnectionHash() != chartDef2.getConnectionHash()) continue;
            return;
        }
        this.charts.add(chartDef.getClone());
    }

    public CommissionsMethod getCommissionsMethod() {
        return this.commissionsMethod;
    }

    public void setCommissionsMethod(CommissionsMethod commissionsMethod) {
        this.commissionsMethod = commissionsMethod;
    }

    public int getBacktestEngine() {
        return this.backtestEngine;
    }

    public void setBacktestEngine(int n) {
        this.backtestEngine = n;
    }

    public String getTFsAsString() {
        if (this.charts.size() == 0) {
            return "";
        }
        StringBuilder stringBuilder = new StringBuilder(this.charts.get(0).getTimeframe());
        int n = this.charts.get(0).getSymbolHash();
        for (int i = 1; i < this.charts.size(); ++i) {
            ChartDef chartDef = this.charts.get(i);
            if (chartDef.getSymbolHash() != n) continue;
            stringBuilder.append(", ");
            stringBuilder.append(chartDef.getTimeframe());
        }
        return stringBuilder.toString();
    }

    public String getSymbol() {
        ChartDef chartDef = this.getMainChart();
        StringBuilder stringBuilder = new StringBuilder(chartDef.getSymbol());
        if (this.charts.size() > 1) {
            for (int i = 1; i < this.charts.size(); ++i) {
                chartDef = this.charts.get(i);
                boolean bl = false;
                for (int j = 0; j < i; ++j) {
                    ChartDef chartDef2 = this.charts.get(j);
                    if (!chartDef2.getSymbol().equals(chartDef.getSymbol())) continue;
                    bl = true;
                    break;
                }
                if (bl) continue;
                stringBuilder.append(",");
                stringBuilder.append(chartDef.getSymbol());
            }
        }
        return stringBuilder.toString();
    }

    public String getTimeframe() {
        ChartDef chartDef = this.getMainChart();
        StringBuilder stringBuilder = new StringBuilder(chartDef.getTimeframe());
        if (this.charts.size() > 1) {
            for (int i = 1; i < this.charts.size(); ++i) {
                chartDef = this.charts.get(i);
                boolean bl = false;
                for (int j = 0; j < i; ++j) {
                    ChartDef chartDef2 = this.charts.get(j);
                    if (!chartDef2.getTimeframe().equals(chartDef.getTimeframe())) continue;
                    bl = true;
                    break;
                }
                if (bl) continue;
                stringBuilder.append(",");
                stringBuilder.append(chartDef.getTimeframe());
            }
        }
        return stringBuilder.toString();
    }

    public static ChartSetup createFirstAvailableData() throws Exception {
        ArrayList arrayList = DataManager.list();
        if (arrayList == null || arrayList.size() == 0) {
            return null;
        }
        DataInfo dataInfo = (DataInfo)arrayList.get(0);
        InstrumentInfo instrumentInfo = dataInfo.symbolInfo;
        return new ChartSetup(dataInfo.symbol, dataInfo.timeframe, dataInfo.dateFrom, dataInfo.dateTo, instrumentInfo.defaultSpread, "No Session");
    }
}

