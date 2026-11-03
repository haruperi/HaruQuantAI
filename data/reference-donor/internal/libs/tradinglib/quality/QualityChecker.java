/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.ChartDef
 *  com.strategyquant.datalib.DataInfo
 *  com.strategyquant.datalib.TimeframeManager
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.datalib.data.io.IDataLoader
 *  com.strategyquant.datalib.data.io.VersatileData
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.time.SQTimeOld
 *  com.strategyquant.lib.utils.JsonCreator
 *  org.joda.time.format.DateTimeFormat
 *  org.joda.time.format.DateTimeFormatter
 */
package com.strategyquant.tradinglib.quality;

import com.strategyquant.datalib.ChartDef;
import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.TimeframeManager;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.datalib.data.io.IDataLoader;
import com.strategyquant.datalib.data.io.VersatileData;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.time.SQTimeOld;
import com.strategyquant.lib.utils.JsonCreator;
import com.strategyquant.tradinglib.quality.DataProblemEvaluator;
import org.joda.time.format.DateTimeFormat;
import org.joda.time.format.DateTimeFormatter;

public class QualityChecker {
    private static final int TIME_CHECK_PERIOD = 20;
    private static final DateTimeFormatter formaterDateMinute = DateTimeFormat.forPattern((String)"yyyy.MM.dd HH:mm");
    private DataProblemEvaluator evaluator = new DataProblemEvaluator();
    private int minHour;
    private int maxHour;

    private void analyseDataKind(IDataLoader iDataLoader) throws Exception {
        int n = 0;
        int n2 = -1;
        int n3 = -1;
        int n4 = -1;
        long l = -1L;
        while (iDataLoader.hasNextTick() && n < 20) {
            VersatileData versatileData = new VersatileData();
            iDataLoader.getNextTick(versatileData);
            int n5 = SQTime.getDay((long)versatileData.time);
            if (n5 != n2) {
                ++n;
                int n6 = SQTime.getHour((long)versatileData.time);
                if (n3 == -1 || n3 > n6) {
                    n3 = n6;
                }
                if (l != -1L) {
                    int n7 = SQTime.getHour((long)l);
                    if (n4 == -1 || n4 < n7) {
                        n4 = n7;
                    }
                }
                n2 = n5;
            }
            l = versatileData.time;
        }
        iDataLoader.seek(0);
        this.minHour = n3;
        this.maxHour = n4;
        this.evaluator.setMinMaxHour(n3, n4);
    }

    private void writeEndYear(JsonCreator jsonCreator, int n, long l) {
        if (n != -1) {
            jsonCreator.endArray(true);
            jsonCreator.put("end", (Object)formaterDateMinute.print(l), false);
            jsonCreator.endObject(false);
        }
    }

    private void writeProblem(JsonCreator jsonCreator, long l, long l2, boolean bl) {
        if (l != -1L) {
            if (!bl) {
                jsonCreator.separator();
            }
            jsonCreator.beginObject();
            jsonCreator.put("from", (Object)formaterDateMinute.print(l), true);
            jsonCreator.put("to", (Object)formaterDateMinute.print(l2), false);
            jsonCreator.endObject(false);
        }
    }

    public String getSummary(String string, String string2, String string3) throws Exception {
        this.evaluator.setTimeframe(string);
        long l = TimeframeManager.getMillis((String)string) - 1L;
        IDataLoader iDataLoader = this.getLoader(string2, string, string3);
        this.analyseDataKind(iDataLoader);
        DataInfo dataInfo = DataManager.getDataInfo((String)"History", (String)string2);
        int n = dataInfo.decimals;
        JsonCreator jsonCreator = new JsonCreator();
        jsonCreator.beginObject();
        int n2 = 0;
        int n3 = -1;
        long l2 = -1L;
        long l3 = -1L;
        jsonCreator.putBeginArray("problems");
        long l4 = 0L;
        long l5 = 0L;
        long l6 = 0L;
        long l7 = 0L;
        boolean bl = false;
        while (iDataLoader.hasNextTick()) {
            DataProblemEvaluator.ProblemKind problemKind;
            ++l7;
            VersatileData versatileData = new VersatileData();
            iDataLoader.getNextTick(versatileData);
            versatileData.open = SQUtils.round((double)versatileData.open, (int)n);
            versatileData.high = SQUtils.round((double)versatileData.high, (int)n);
            versatileData.low = SQUtils.round((double)versatileData.low, (int)n);
            versatileData.close = SQUtils.round((double)versatileData.close, (int)n);
            int n4 = 1900 + SQTime.getYear((long)versatileData.time);
            if (n4 != n3) {
                this.writeProblem(jsonCreator, l3, l2 + l, bl);
                this.writeEndYear(jsonCreator, n3, l2);
                if (n3 != -1) {
                    jsonCreator.separator();
                }
                jsonCreator.beginObject();
                jsonCreator.put("year", (Object)n4, true);
                jsonCreator.put("start", (Object)formaterDateMinute.print(versatileData.time), true);
                jsonCreator.putBeginArray("problems");
                n3 = n4;
                l3 = -1L;
                bl = true;
            }
            if ((problemKind = this.evaluator.evalProblemKind(versatileData, false)) == DataProblemEvaluator.ProblemKind.GAP) {
                long l8 = this.evaluator.getBeginGap();
                long l9 = this.evaluator.getEndGap();
                ++l4;
                ++n2;
                if (l3 == -1L) {
                    l3 = l8;
                }
                l2 = l9;
                problemKind = this.evaluator.evalProblemKind(versatileData, true);
            }
            if (problemKind != null) {
                ++n2;
                if (l3 == -1L) {
                    l3 = versatileData.time;
                }
                switch (problemKind) {
                    case SPIKE: {
                        ++l5;
                        break;
                    }
                    case HIGH_PROBLEM: 
                    case LOW_PROBLEM: {
                        ++l6;
                    }
                }
            } else if (l3 != -1L) {
                this.writeProblem(jsonCreator, l3, l2 + l, bl);
                bl = false;
                l3 = -1L;
            }
            l2 = versatileData.time;
        }
        this.writeProblem(jsonCreator, l3, l2 + l, bl);
        this.writeEndYear(jsonCreator, n3, l2 + l);
        jsonCreator.endArray(true);
        jsonCreator.put("pointOpacity", (Object)this.getPointOpacity(string), true);
        jsonCreator.put("minHour", (Object)this.minHour, true);
        jsonCreator.put("maxHour", (Object)this.maxHour, true);
        jsonCreator.put("totalErrors", (Object)n2, true);
        jsonCreator.putBeginObject("gap");
        jsonCreator.put("count", (Object)l4, true);
        jsonCreator.put("percent", (Object)this.getPercent(l4, l7), false);
        jsonCreator.endObject(true);
        jsonCreator.putBeginObject("ohlc");
        jsonCreator.put("count", (Object)l6, true);
        jsonCreator.put("percent", (Object)this.getPercent(l6, l7), false);
        jsonCreator.endObject(true);
        jsonCreator.putBeginObject("spike");
        jsonCreator.put("count", (Object)l5, true);
        jsonCreator.put("percent", (Object)this.getPercent(l5, l7), false);
        jsonCreator.endObject(false);
        jsonCreator.endObject(false);
        iDataLoader.close();
        return jsonCreator.toJson();
    }

    private String getPointOpacity(String string) {
        return "ff";
    }

    private double getPercent(long l, long l2) {
        double d = (double)l * 100.0 / (double)l2;
        int n = (int)(d * 1000.0);
        return (double)n / 1000.0;
    }

    private IDataLoader getLoader(String string, String string2, String string3) throws Exception {
        DataInfo dataInfo;
        DataInfo dataInfo2 = DataManager.getDataInfo((String)"History", (String)string);
        int n = dataInfo2.sourceDataId;
        if (n != 0 && (dataInfo = DataManager.getDataInfo((String)"History", (int)n)) != null) {
            string = dataInfo.symbol;
        }
        dataInfo = new ChartDef("History", string, string2, 0L, SQTimeOld.toLong((int)2100, (int)1, (int)1), 2.5, string3);
        IDataLoader iDataLoader = DataManager.getDataLoader((ChartDef)dataInfo, (int)1);
        iDataLoader.open();
        return iDataLoader;
    }

    private String getTimeframe(String string) {
        DataInfo dataInfo = DataManager.getDataInfo((String)"History", (String)string);
        String string2 = dataInfo.timeframe;
        String string3 = string2;
        if (string3 == "TICK") {
            string3 = "M1";
        }
        return string3;
    }

    public String getDetails(String string, String string2, String string3, int n, int n2) throws Exception {
        JsonCreator jsonCreator = new JsonCreator();
        jsonCreator.beginArray();
        this.evaluator.setTimeframe(string);
        IDataLoader iDataLoader = this.getLoader(string2, string, string3);
        this.analyseDataKind(iDataLoader);
        DataInfo dataInfo = DataManager.getDataInfo((String)"History", (String)string2);
        int n3 = dataInfo.decimals;
        int n4 = 0;
        int n5 = 0;
        while (iDataLoader.hasNextTick()) {
            VersatileData versatileData = new VersatileData();
            iDataLoader.getNextTick(versatileData);
            versatileData.open = SQUtils.round((double)versatileData.open, (int)n3);
            versatileData.high = SQUtils.round((double)versatileData.high, (int)n3);
            versatileData.low = SQUtils.round((double)versatileData.low, (int)n3);
            versatileData.close = SQUtils.round((double)versatileData.close, (int)n3);
            DataProblemEvaluator.ProblemKind problemKind = this.evaluator.evalProblemKind(versatileData, false);
            if (problemKind == DataProblemEvaluator.ProblemKind.GAP) {
                long l = this.evaluator.getBeginGap();
                long l2 = this.evaluator.getEndGap();
                long l3 = this.evaluator.getMilisForTimeframe();
                while (l <= l2) {
                    if (n4 >= n && n4 < n2) {
                        if (n5 != 0) {
                            jsonCreator.separator();
                        }
                        jsonCreator.beginObject();
                        jsonCreator.put("data");
                        jsonCreator.beginArray();
                        jsonCreator.setValue((Object)SQTime.toFullDateMinuteString((long)l), true);
                        jsonCreator.setValue((Object)"missing", true);
                        jsonCreator.setValue((Object)"missing", true);
                        jsonCreator.setValue((Object)"missing", true);
                        jsonCreator.setValue((Object)"missing", true);
                        jsonCreator.setValue((Object)"missing", true);
                        jsonCreator.setValue((Object)problemKind.getDesc(), false);
                        jsonCreator.endArray(true);
                        jsonCreator.put("id", (Object)("r" + n4), false);
                        jsonCreator.endObject(false);
                        ++n5;
                    }
                    l += l3;
                    ++n4;
                }
                problemKind = this.evaluator.evalProblemKind(versatileData, true);
            }
            if (problemKind == null) continue;
            if (n4 >= n && n4 < n2) {
                if (n5 != 0) {
                    jsonCreator.separator();
                }
                jsonCreator.beginObject();
                jsonCreator.put("data");
                jsonCreator.beginArray();
                jsonCreator.setValue((Object)SQTime.toFullDateMinuteString((long)versatileData.time), true);
                jsonCreator.setValue((Object)versatileData.open, true);
                jsonCreator.setValue((Object)versatileData.high, true);
                jsonCreator.setValue((Object)versatileData.low, true);
                jsonCreator.setValue((Object)versatileData.close, true);
                jsonCreator.setValue((Object)versatileData.volume, true);
                jsonCreator.setValue((Object)problemKind.getDesc(), false);
                jsonCreator.endArray(true);
                jsonCreator.put("id", (Object)("r" + n4), false);
                jsonCreator.endObject(false);
                ++n5;
            }
            ++n4;
        }
        iDataLoader.close();
        jsonCreator.endArray(false);
        return jsonCreator.toJson();
    }
}

