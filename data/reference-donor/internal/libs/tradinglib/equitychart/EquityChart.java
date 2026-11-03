/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.utils.JsonCreator
 *  org.json.JSONObject
 */
package com.strategyquant.tradinglib.equitychart;

import com.strategyquant.lib.L;
import com.strategyquant.lib.utils.JsonCreator;
import com.strategyquant.tradinglib.PlTypes;
import com.strategyquant.tradinglib.equitychart.AreaFill;
import com.strategyquant.tradinglib.equitychart.BenchmarkTable;
import com.strategyquant.tradinglib.equitychart.ChartDataset;
import com.strategyquant.tradinglib.equitychart.EquityChartUtils;
import com.strategyquant.tradinglib.equitychart.MainChartDataset;
import com.strategyquant.tradinglib.equitychart.Marker;
import com.strategyquant.tradinglib.equitychart.SubChart;
import com.strategyquant.tradinglib.equitychart.Text;
import com.strategyquant.tradinglib.equitychart.Zoom;
import java.util.ArrayList;
import org.json.JSONObject;

public class EquityChart {
    public static final String PORTFOLIO_ONLY = "Portfolio only";
    public static final String PORTFOLIO_PARTS_ONLY = "Portfolio parts only";
    private byte plType = (byte)10;
    private String domainAxisType = "trade";
    private boolean hideYTitle = false;
    public static final String EQUITY_AREA_FILL_COLOR = "#DAF5FF";
    public static final String EQUITY_AREA_FILL_NEGATIVE_COLOR = "#F49C9C";
    public static final String EQUITY_AREA_FILL_COLOR_DARK = "#333C63";
    private ArrayList<MainChartDataset> mainChartDatasets = new ArrayList();
    private ArrayList<SubChart> subCharts = new ArrayList();
    private ArrayList<AreaFill> areas = new ArrayList();
    private ArrayList<Marker> markers = new ArrayList();
    private ArrayList<Text> texts = new ArrayList();
    private Zoom zoom = new Zoom();
    public BenchmarkTable benchmark = new BenchmarkTable();
    private String cornerCaption = null;

    public void zoom(boolean bl, int n, long l, long l2) {
        this.zoom.active = bl;
        this.zoom.width = n;
        this.zoom.minX = l;
        this.zoom.maxX = l2;
    }

    public void hideYTitle(boolean bl) {
        this.hideYTitle = bl;
    }

    public void setPLType(byte by) {
        this.plType = by;
    }

    public void setDomainAxisType(String string) {
        this.domainAxisType = string;
    }

    public void addMainChartDataset(MainChartDataset mainChartDataset) {
        this.setColor(mainChartDataset, this.mainChartDatasets.size());
        this.mainChartDatasets.add(mainChartDataset);
    }

    public ArrayList<MainChartDataset> getMainChartDatasets() {
        return this.mainChartDatasets;
    }

    public SubChart findSubChartByName(String string) {
        for (int i = 0; i < this.subCharts.size(); ++i) {
            SubChart subChart = this.subCharts.get(i);
            if (!subChart.name.equals(string)) continue;
            return subChart;
        }
        return null;
    }

    public SubChart findSubChartByKey(String string) {
        for (int i = 0; i < this.subCharts.size(); ++i) {
            SubChart subChart = this.subCharts.get(i);
            if (!subChart.key.equals(string)) continue;
            return subChart;
        }
        return null;
    }

    public void addSubChart(SubChart subChart) {
        this.subCharts.add(subChart);
    }

    public void addArea(AreaFill areaFill) {
        this.areas.add(areaFill);
    }

    public void addMarker(Marker marker) {
        this.markers.add(marker);
    }

    private void setColor(ChartDataset chartDataset, int n) {
        if (chartDataset.color == null) {
            chartDataset.color = EquityChartUtils.getColor(n, false);
        }
        if (chartDataset.colorDark == null) {
            chartDataset.colorDark = EquityChartUtils.getColor(n, true);
        }
    }

    public void reset() {
        this.mainChartDatasets.clear();
        this.subCharts.clear();
        this.areas.clear();
        this.markers.clear();
        this.texts.clear();
        this.zoom.reset();
        this.benchmark.clear();
    }

    public void fillJSON(JsonCreator jsonCreator) {
        Object object;
        int n;
        jsonCreator.put("domainAxisType", (Object)(this.domainAxisType.equals("time") ? "time" : "number"), true);
        if (this.zoom == null || this.zoom.minX <= 0L || !this.zoom.active) {
            jsonCreator.putRaw("zoom", null, true);
        } else {
            jsonCreator.putBeginObject("zoom");
            jsonCreator.put("startZoomX", (Object)this.zoom.minX, true);
            jsonCreator.put("currentZoomX", (Object)this.zoom.maxX, false);
            jsonCreator.endObject(true);
        }
        jsonCreator.putBeginObject("mainCharts");
        String string = String.format(L.tsq((String)"Equity (%s)"), PlTypes.print(this.plType));
        jsonCreator.put("title", (Object)string, true);
        jsonCreator.put("weight", (Object)60, true);
        if (this.cornerCaption != null) {
            jsonCreator.put("cornerCaption", (Object)this.cornerCaption, true);
        }
        jsonCreator.put("hideYTitle", (Object)this.hideYTitle, true);
        jsonCreator.putBeginArray("datasets");
        for (n = 0; n < this.mainChartDatasets.size(); ++n) {
            jsonCreator.beginObject();
            object = this.mainChartDatasets.get(n);
            ((ChartDataset)object).fillJSON(jsonCreator, this.zoom, this.domainAxisType.equals("time"));
            jsonCreator.endObject(n < this.mainChartDatasets.size() - 1);
        }
        jsonCreator.endArray(true);
        jsonCreator.putBeginArray("markers");
        for (n = 0; n < this.markers.size(); ++n) {
            object = this.markers.get(n);
            jsonCreator.beginObject();
            ((Marker)object).fillJSON(jsonCreator);
            jsonCreator.endObject(n < this.markers.size() - 1);
        }
        jsonCreator.endArray(true);
        jsonCreator.putBeginArray("texts");
        for (n = 0; n < this.texts.size(); ++n) {
            object = this.texts.get(n);
            jsonCreator.beginObject();
            ((Text)object).fillJSON(jsonCreator);
            jsonCreator.endObject(n < this.texts.size() - 1);
        }
        jsonCreator.endArray(true);
        jsonCreator.putBeginArray("areaFill");
        for (n = 0; n < this.areas.size(); ++n) {
            object = this.areas.get(n);
            jsonCreator.beginObject();
            ((AreaFill)object).fillJSON(jsonCreator);
            jsonCreator.endObject(n < this.areas.size() - 1);
        }
        jsonCreator.endArray(false);
        jsonCreator.endObject(true);
        jsonCreator.putBeginObject("subCharts");
        jsonCreator.putBeginArray("charts");
        for (n = 0; n < this.subCharts.size(); ++n) {
            object = this.subCharts.get(n);
            jsonCreator.beginObject();
            ((SubChart)object).fillJSON(jsonCreator, this.zoom, this.domainAxisType.equals("time"));
            jsonCreator.endObject(n < this.subCharts.size() - 1);
        }
        jsonCreator.endArray(false);
        jsonCreator.endObject(true);
        jsonCreator.putBeginObject("benchmark");
        jsonCreator.putRaw("data", (Object)this.benchmark.toJSON(), false);
        jsonCreator.endObject(false);
    }

    public JSONObject toJSON() {
        JsonCreator jsonCreator = new JsonCreator();
        jsonCreator.beginObject();
        this.fillJSON(jsonCreator);
        jsonCreator.endObject(false);
        JSONObject jSONObject = new JSONObject(jsonCreator.toJson());
        return jSONObject;
    }

    public String getCornerCaption() {
        return this.cornerCaption;
    }

    public void setCornerCaption(String string) {
        this.cornerCaption = string;
    }

    public void drawText(String string, String string2, String string3, int n, int n2) {
        this.texts.add(new Text(string, string2, string3, n, n2));
    }
}

