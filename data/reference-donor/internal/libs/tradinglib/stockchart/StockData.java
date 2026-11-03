/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.utils.JsonCreator
 *  org.joda.time.format.DateTimeFormat
 *  org.joda.time.format.DateTimeFormatter
 */
package com.strategyquant.tradinglib.stockchart;

import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.utils.JsonCreator;
import com.strategyquant.tradinglib.stockchart.Indicator;
import com.strategyquant.tradinglib.stockchart.IndicatorLevel;
import com.strategyquant.tradinglib.stockchart.IndicatorLine;
import com.strategyquant.tradinglib.stockchart.PreviewCaption;
import com.strategyquant.tradinglib.stockchart.StockChartData;
import com.strategyquant.tradinglib.stockchart.Trade;
import java.util.List;
import java.util.stream.Stream;
import org.joda.time.format.DateTimeFormat;
import org.joda.time.format.DateTimeFormatter;

public class StockData {
    private static final DateTimeFormatter formatter = DateTimeFormat.forPattern((String)"yyyy-MM-dd HH:mm:ss");
    private StockChartData[] chartData;
    private float[] previewYVals;
    private PreviewCaption[] previewCaptions;
    private int[] previewTrades;
    private String[] stocks;
    private String currentStock;
    private long count;
    private long areaFrom;
    private long areaTo;
    private Double pipValue;
    private long tradesCount;
    private Long selectedTrade;

    public long getAreaFrom() {
        return this.areaFrom;
    }

    public void setAreaFrom(long l) {
        this.areaFrom = l;
    }

    public long getAreaTo() {
        return this.areaTo;
    }

    public void setAreaTo(long l) {
        this.areaTo = l;
    }

    public StockChartData[] getChartData() {
        return this.chartData;
    }

    public void setChartData(StockChartData[] stockChartDataArray) {
        this.chartData = stockChartDataArray;
    }

    public float[] getPreviewYVals() {
        return this.previewYVals;
    }

    public void setPreviewYVals(float[] fArray) {
        this.previewYVals = fArray;
    }

    public long getCount() {
        return this.count;
    }

    public void setCount(long l) {
        this.count = l;
    }

    private String getTimestampStr(long l) {
        return formatter.print(l);
    }

    public String toJSON() {
        int n;
        StockChartData stockChartData;
        int n2;
        int n3;
        JsonCreator jsonCreator = new JsonCreator();
        jsonCreator.beginObject();
        jsonCreator.put("count", (Object)this.count, true);
        jsonCreator.put("selectedTradeId", (Object)this.selectedTrade, true);
        jsonCreator.put("totalTrades", (Object)this.tradesCount, true);
        jsonCreator.put("pipValue", (Object)this.pipValue, true);
        jsonCreator.put("area_from", (Object)this.areaFrom, true);
        jsonCreator.put("area_to", (Object)this.areaTo, true);
        jsonCreator.put("stocks");
        jsonCreator.beginArray();
        if (this.stocks != null) {
            for (n3 = 0; n3 < this.stocks.length; ++n3) {
                jsonCreator.setValue((Object)this.stocks[n3], n3 < this.stocks.length - 1);
            }
        }
        jsonCreator.endArray(true);
        jsonCreator.put("currentStock", (Object)this.currentStock, true);
        jsonCreator.putBeginObject("preview");
        if (this.previewCaptions != null) {
            jsonCreator.putBeginArray("captions");
            for (n3 = 0; n3 < this.previewCaptions.length; ++n3) {
                PreviewCaption previewCaption = this.previewCaptions[n3];
                jsonCreator.beginObject();
                jsonCreator.put("index", (Object)previewCaption.getIndex(), true);
                jsonCreator.put("caption", (Object)previewCaption.getCaption(), false);
                jsonCreator.endObject(n3 != this.previewCaptions.length - 1);
            }
            jsonCreator.endArray(true);
        }
        jsonCreator.put("yVals", (Object)this.previewYVals, true);
        jsonCreator.put("trades");
        jsonCreator.beginArray();
        if (this.previewTrades != null) {
            n3 = 0;
            while (n3 < this.previewTrades.length) {
                jsonCreator.beginObject();
                jsonCreator.put("from", (Object)this.previewTrades[n3], true);
                jsonCreator.put("to", (Object)this.previewTrades[++n3], false);
                jsonCreator.endObject(++n3 < this.previewTrades.length);
            }
        }
        jsonCreator.endArray(false);
        jsonCreator.endObject(true);
        jsonCreator.putBeginArray("indicators");
        n3 = 0;
        for (n2 = 0; n2 < this.chartData.length; ++n2) {
            stockChartData = this.chartData[n2];
            if (stockChartData.getIndicators() == null) continue;
            for (n = 0; n < stockChartData.getIndicators().length; ++n) {
                if (n3 != 0) {
                    jsonCreator.separator();
                }
                Indicator indicator = stockChartData.getIndicators()[n];
                jsonCreator.beginObject();
                jsonCreator.put("id", (Object)("indicator" + n3), true);
                jsonCreator.put("title", (Object)indicator.getTitle(), true);
                jsonCreator.put("displayOn", (Object)(indicator.isSubChart() ? "subchart" : "chart"), true);
                jsonCreator.put("subchartID", (Object)String.valueOf(n2), indicator.getLevels() != null);
                if (indicator.getLevels() != null) {
                    jsonCreator.putBeginArray("levels");
                    for (int i = 0; i < indicator.getLevels().length; ++i) {
                        IndicatorLevel indicatorLevel = indicator.getLevels()[i];
                        jsonCreator.beginObject();
                        jsonCreator.put("color", (Object)indicatorLevel.getColor(), true);
                        boolean bl = indicatorLevel.getPattern() != null && !indicatorLevel.getPattern().isEmpty();
                        jsonCreator.put("value", (Object)indicatorLevel.getValue(), bl);
                        if (bl) {
                            String[] stringArray = indicatorLevel.getPattern().split(",");
                            int[] nArray = new int[stringArray.length];
                            for (int j = 0; j < stringArray.length; ++j) {
                                nArray[j] = Integer.parseInt(stringArray[j]);
                            }
                            jsonCreator.put("pattern", (Object)nArray, false);
                        }
                        jsonCreator.endObject(i != indicator.getLevels().length - 1);
                    }
                    jsonCreator.endArray(false);
                }
                jsonCreator.separator();
                jsonCreator.putBeginArray("datasets");
                if (indicator.getLines() != null) {
                    List<IndicatorLine> list = Stream.of(indicator.getLines()).filter(indicatorLine -> indicatorLine.isShowInChart()).toList();
                    for (int i = 0; i < list.size(); ++i) {
                        IndicatorLine indicatorLine2 = list.get(i);
                        jsonCreator.beginObject();
                        jsonCreator.put("line", (Object)indicatorLine2.getLine(), true);
                        jsonCreator.put("color", (Object)indicatorLine2.getColor(), true);
                        jsonCreator.put("type", (Object)indicatorLine2.getKind().name(), true);
                        jsonCreator.put("yVals", (Object)indicatorLine2.getyValues(), false);
                        jsonCreator.endObject(i != list.size() - 1);
                    }
                }
                jsonCreator.endArray(false);
                jsonCreator.endObject(false);
                ++n3;
            }
        }
        jsonCreator.endArray(true);
        jsonCreator.putBeginArray("charts");
        for (n2 = 0; n2 < this.chartData.length; ++n2) {
            int n4;
            stockChartData = this.chartData[n2];
            jsonCreator.beginObject();
            jsonCreator.put("id", (Object)String.valueOf(n2), true);
            jsonCreator.put("title", (Object)stockChartData.getTitle(), true);
            jsonCreator.put("precision", (Object)stockChartData.getPrecision(), true);
            n = n2 == 0 ? 2 : 1;
            jsonCreator.put("weight", (Object)n, true);
            jsonCreator.putBeginArray("xVals");
            if (stockChartData.getxVals() != null) {
                for (n4 = 0; n4 < stockChartData.getxVals().length; ++n4) {
                    jsonCreator.setValue((Object)this.getTimestampStr(stockChartData.getxVals()[n4]), n4 < stockChartData.getxVals().length - 1);
                }
            }
            jsonCreator.endArray(true);
            jsonCreator.putBeginArray("yVals");
            if (stockChartData.getxVals() != null) {
                for (n4 = 0; n4 < stockChartData.getxVals().length; ++n4) {
                    jsonCreator.beginObject();
                    jsonCreator.put("open", (Object)SQUtils.round((double)stockChartData.getOpen().get(n4), (int)stockChartData.getPrecision()), true);
                    jsonCreator.put("close", (Object)SQUtils.round((double)stockChartData.getClose().get(n4), (int)stockChartData.getPrecision()), true);
                    jsonCreator.put("low", (Object)SQUtils.round((double)stockChartData.getLow().get(n4), (int)stockChartData.getPrecision()), true);
                    jsonCreator.put("high", (Object)SQUtils.round((double)stockChartData.getHigh().get(n4), (int)stockChartData.getPrecision()), false);
                    jsonCreator.endObject(n4 != stockChartData.getxVals().length - 1);
                }
            }
            jsonCreator.endArray(true);
            jsonCreator.putBeginArray("tradeMarkers");
            if (stockChartData.getTrades() != null) {
                for (n4 = 0; n4 < stockChartData.getTrades().length; ++n4) {
                    Trade trade = stockChartData.getTrades()[n4];
                    jsonCreator.beginObject();
                    jsonCreator.put("id", (Object)String.valueOf(trade.getId()), true);
                    jsonCreator.put("open", (Object)this.getTimestampStr(trade.getOpenTime()), true);
                    jsonCreator.put("close", (Object)this.getTimestampStr(trade.getCloseTime()), true);
                    jsonCreator.put("openValue", (Object)SQUtils.round((double)trade.getOpenValue(), (int)stockChartData.getPrecision()), true);
                    jsonCreator.put("closeValue", (Object)SQUtils.round((double)trade.getCloseValue(), (int)stockChartData.getPrecision()), true);
                    jsonCreator.put("slValue", (Object)SQUtils.round((double)trade.getSLValue(), (int)stockChartData.getPrecision()), true);
                    jsonCreator.put("ptValue", (Object)SQUtils.round((double)trade.getPTValue(), (int)stockChartData.getPrecision()), true);
                    jsonCreator.put("realOpen", (Object)this.getTimestampStr(trade.getRealOpenTime()), true);
                    jsonCreator.put("realClose", (Object)this.getTimestampStr(trade.getRealCloseTime()), true);
                    jsonCreator.put("long", (Object)(!trade.isShortTrade() ? 1 : 0), true);
                    jsonCreator.put("index", (Object)trade.getIndex(), false);
                    jsonCreator.endObject(n4 != stockChartData.getTrades().length - 1);
                }
            }
            jsonCreator.endArray(false);
            jsonCreator.endObject(n2 != this.chartData.length - 1);
        }
        jsonCreator.endArray(false);
        jsonCreator.endObject(false);
        return jsonCreator.toJson();
    }

    public PreviewCaption[] getPreviewCaptions() {
        return this.previewCaptions;
    }

    public void setPreviewCaptions(PreviewCaption[] previewCaptionArray) {
        this.previewCaptions = previewCaptionArray;
    }

    public Double getPipValue() {
        return this.pipValue;
    }

    public void setPipValue(Double d) {
        this.pipValue = d;
    }

    public int[] getPreviewTrades() {
        return this.previewTrades;
    }

    public void setPreviewTrades(int[] nArray) {
        this.previewTrades = nArray;
    }

    public long getTradesCount() {
        return this.tradesCount;
    }

    public void setTradesCount(long l) {
        this.tradesCount = l;
    }

    public Long getSelectedTrade() {
        return this.selectedTrade;
    }

    public void setSelectedTrade(Long l) {
        this.selectedTrade = l;
    }

    public String[] getStocks() {
        return this.stocks;
    }

    public void setStocks(String[] stringArray) {
        this.stocks = stringArray;
    }

    public String getCurrentStock() {
        return this.currentStock;
    }

    public void setCurrentStock(String string) {
        this.currentStock = string;
    }
}

