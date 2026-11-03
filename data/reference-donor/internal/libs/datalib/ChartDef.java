/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.settings.IXMLAble
 *  com.strategyquant.lib.utils.ISQCloneable
 *  org.jdom2.Content
 *  org.jdom2.Element
 */
package com.strategyquant.datalib;

import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.InstrumentInfo;
import com.strategyquant.datalib.bartype.BarType;
import com.strategyquant.datalib.bartype.BarTypeFactory;
import com.strategyquant.datalib.data.DataException;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.datalib.instrument.InstrumentManager;
import com.strategyquant.datalib.session.Session;
import com.strategyquant.datalib.session.SessionElement;
import com.strategyquant.datalib.session.SessionManager;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.settings.IXMLAble;
import com.strategyquant.lib.utils.ISQCloneable;
import java.io.Serializable;
import java.util.ArrayList;
import org.jdom2.Content;
import org.jdom2.Element;

public class ChartDef
implements IXMLAble,
ISQCloneable<ChartDef>,
Serializable {
    protected static final int LIVETRADING = 1;
    protected static final int BACKTEST = 2;
    protected String connectionName;
    protected int connectionNameHash;
    protected String symbol = null;
    protected int symbolHash;
    protected String instrument = null;
    protected String timeframe;
    protected long historyFrom;
    protected long historyTo;
    protected double spread = 0.0;
    protected boolean registered = false;
    protected String session;
    protected DataInfo dataInfo = null;
    protected int type = 0;
    protected long loadedHistoryFrom;
    private int backloadType;
    private long backloadNumber;
    private InstrumentInfo instrumentInfo;
    private double minDistance;
    private boolean realSpread = false;

    public ChartDef() {
    }

    public ChartDef(String string, String string2, String string3, int n, long l, String string4) throws DataException {
        this.type = 1;
        this.connectionName = string;
        this.connectionNameHash = string.hashCode();
        this.symbol = string2;
        this.symbolHash = string2.hashCode();
        this.dataInfo = DataManager.getDataInfo(string, string2);
        if (this.dataInfo == null) {
            throw new DataException(2, "Data for connection '" + string + "' and symbol '" + string2 + "' cannot be found!");
        }
        this.instrumentInfo = InstrumentManager.getInstrumentInfo(this.dataInfo.instrument);
        this.timeframe = string3;
        if (string4.equals("No Session")) {
            // empty if block
        }
        this.session = string4;
        this.backloadType = n;
        this.backloadNumber = l;
        this.minDistance = 0.0;
    }

    public ChartDef(String string, String string2, String string3, long l, long l2, double d, String string4) throws DataException {
        BarTypeFactory.checkTimeframeIsValid(string3);
        this.type = 2;
        this.connectionName = string;
        this.connectionNameHash = string.hashCode();
        this.symbol = string2;
        this.symbolHash = string2.hashCode();
        this.dataInfo = DataManager.getDataInfo(string, string2);
        if (this.dataInfo == null) {
            throw new DataException(2, "Data for connection '" + string + "' and symbol '" + string2 + "' cannot be found!");
        }
        if (this.dataInfo.barTimeType == 1 && string3.startsWith("D")) {
            string4 = "No Session";
        }
        this.instrumentInfo = InstrumentManager.getInstrumentInfo(this.dataInfo.instrument);
        if (l == 0L) {
            l = Long.MIN_VALUE;
        }
        this.timeframe = string3;
        this.historyFrom = l;
        this.historyTo = SQTime.correctDayEnd((long)l2);
        this.loadedHistoryFrom = l;
        this.spread = d;
        if (string4.equals("No Session")) {
            // empty if block
        }
        this.session = string4;
        this.backloadType = 0;
    }

    public ChartDef(ChartDef chartDef) throws DataException {
        this(chartDef.getConnectionName(), chartDef.getSymbol(), chartDef.getTimeframe(), chartDef.getHistoryFrom(), chartDef.getHistoryTo(), chartDef.getSpread(), chartDef.getSession());
        this.loadedHistoryFrom = chartDef.getLoadedHistoryFrom();
    }

    public ChartDef(ChartDef chartDef, String string) throws DataException {
        this(chartDef.getConnectionName(), chartDef.getSymbol(), string, chartDef.getHistoryFrom(), chartDef.getHistoryTo(), chartDef.getSpread(), chartDef.getSession());
        this.loadedHistoryFrom = chartDef.getLoadedHistoryFrom();
    }

    public String getConnectionName() {
        return this.connectionName;
    }

    public boolean isSymbolRecognized() {
        return this.symbol != null;
    }

    public String getTimeframe() {
        return this.timeframe;
    }

    public long getHistoryFrom() {
        return this.historyFrom;
    }

    public void setHistoryFrom(long l) {
        this.historyFrom = l;
    }

    public long getHistoryTo() {
        return this.historyTo;
    }

    public void setHistoryTo(long l) {
        this.historyTo = l;
    }

    public double getSpread() {
        return this.realSpread ? -1.0 : this.spread;
    }

    public void setSpread(double d) {
        this.spread = d;
    }

    public int getConnectionHash() {
        return this.connectionNameHash;
    }

    public void setSymbol(String string) {
        this.symbol = string;
    }

    public String getSymbol() {
        return this.symbol;
    }

    public int getSymbolHash() {
        return this.symbolHash;
    }

    public boolean isRegistered() {
        return this.registered;
    }

    public String getSession() {
        return this.session;
    }

    public void setRegistered() {
        this.registered = true;
    }

    public InstrumentInfo getSymbolInfo() {
        return this.instrumentInfo;
    }

    public String getInstrument() {
        return this.instrument;
    }

    public boolean isBacktestDataDef() {
        return this.type == 2;
    }

    public void setLoadedHistoryFrom(long l) {
        this.loadedHistoryFrom = l;
    }

    public long getLoadedHistoryFrom() {
        return this.loadedHistoryFrom;
    }

    public boolean isSameConnectionSymbol(ChartDef chartDef) {
        if (this.getSymbolHash() != chartDef.getSymbolHash()) {
            return false;
        }
        return this.getConnectionHash() == chartDef.getConnectionHash();
    }

    public int getBackloadType() {
        return this.backloadType;
    }

    public long getBackloadNumber() {
        return this.backloadNumber;
    }

    public Element getXML() {
        Element element = new Element("ChartDef");
        XMLUtil.trySetAttr((Element)element, (String)"connectionName", (Object)this.connectionName);
        XMLUtil.trySetAttr((Element)element, (String)"symbol", (Object)this.symbol);
        XMLUtil.trySetAttr((Element)element, (String)"instrument", (Object)this.instrument);
        XMLUtil.trySetAttr((Element)element, (String)"timeframe", (Object)this.timeframe);
        XMLUtil.trySetAttr((Element)element, (String)"historyFrom", (Object)this.historyFrom);
        XMLUtil.trySetAttr((Element)element, (String)"historyTo", (Object)this.historyTo);
        XMLUtil.trySetAttr((Element)element, (String)"loadedHistoryFrom", (Object)this.loadedHistoryFrom);
        XMLUtil.trySetAttr((Element)element, (String)"spread", (Object)this.spread);
        XMLUtil.trySetAttr((Element)element, (String)"registered", (Object)this.registered);
        XMLUtil.trySetAttr((Element)element, (String)"session", (Object)this.session);
        XMLUtil.trySetAttr((Element)element, (String)"type", (Object)this.type);
        XMLUtil.trySetAttr((Element)element, (String)"backloadType", (Object)this.backloadType);
        XMLUtil.trySetAttr((Element)element, (String)"backloadNumber", (Object)this.backloadNumber);
        if (this.dataInfo != null) {
            Element element2 = this.dataInfo.getXML();
            element.addContent((Content)element2);
        }
        return element;
    }

    public void setFromXML(Element element) {
        this.connectionName = element.getAttributeValue("connectionName");
        this.connectionNameHash = this.connectionName.hashCode();
        this.symbol = element.getAttributeValue("symbol");
        this.symbolHash = this.symbol.hashCode();
        this.instrument = element.getAttributeValue("instrument");
        this.timeframe = element.getAttributeValue("timeframe");
        this.historyFrom = XMLUtil.tryGetLongAttr((Element)element, (String)"historyFrom");
        this.historyTo = SQTime.correctDayEnd((long)XMLUtil.tryGetLongAttr((Element)element, (String)"historyTo"));
        this.loadedHistoryFrom = XMLUtil.tryGetLongAttr((Element)element, (String)"loadedHistoryFrom");
        this.spread = XMLUtil.tryGetDoubleAttr((Element)element, (String)"spread");
        this.registered = XMLUtil.tryGetBoolAttr((Element)element, (String)"registered");
        this.session = element.getAttributeValue("session");
        this.type = XMLUtil.tryGetIntAttr((Element)element, (String)"type");
        this.backloadType = XMLUtil.tryGetIntAttr((Element)element, (String)"backloadType");
        this.backloadNumber = XMLUtil.tryGetLongAttr((Element)element, (String)"backloadNumber");
        Element element2 = element.getChild("DataInfo");
        if (element2 != null) {
            this.dataInfo = new DataInfo();
            this.dataInfo.setFromXML(element2);
        }
    }

    public int getBarTimeType() {
        return this.dataInfo.barTimeType;
    }

    public InstrumentInfo getInstrumentInfo() {
        return this.instrumentInfo;
    }

    public void setMinDistance(double d) {
        this.minDistance = d;
    }

    public double getMinDistance() {
        return this.minDistance;
    }

    public ChartDef getClone() {
        return this.getClone(0L, 0L);
    }

    public ChartDef getClone(long l, long l2) {
        ChartDef chartDef = new ChartDef();
        chartDef.connectionName = this.connectionName;
        chartDef.connectionNameHash = this.connectionNameHash;
        chartDef.symbol = this.symbol;
        chartDef.symbolHash = this.symbolHash;
        chartDef.instrument = this.instrument;
        chartDef.timeframe = this.timeframe;
        chartDef.historyFrom = l > 0L ? l : this.historyFrom;
        chartDef.historyTo = l2 > 0L ? l2 : this.historyTo;
        chartDef.spread = this.spread;
        chartDef.registered = this.registered;
        chartDef.session = this.session;
        chartDef.dataInfo = this.dataInfo != null ? this.dataInfo.clone() : null;
        chartDef.type = this.type;
        chartDef.loadedHistoryFrom = this.loadedHistoryFrom;
        chartDef.backloadType = this.backloadType;
        chartDef.backloadNumber = this.backloadNumber;
        chartDef.instrumentInfo = this.instrumentInfo != null ? this.instrumentInfo.clone() : null;
        chartDef.minDistance = this.minDistance;
        chartDef.realSpread = this.realSpread;
        return chartDef;
    }

    public ChartDef getClone(String string) {
        ChartDef chartDef = new ChartDef();
        chartDef.connectionName = this.connectionName;
        chartDef.connectionNameHash = this.connectionNameHash;
        chartDef.symbol = string;
        chartDef.symbolHash = string.hashCode();
        chartDef.instrument = this.instrument;
        chartDef.timeframe = this.timeframe;
        chartDef.historyFrom = this.historyFrom > 0L ? this.historyFrom : this.historyFrom;
        chartDef.historyTo = this.historyTo > 0L ? this.historyTo : this.historyTo;
        chartDef.spread = this.spread;
        chartDef.registered = this.registered;
        chartDef.session = this.session;
        chartDef.dataInfo = this.dataInfo != null ? this.dataInfo.clone() : null;
        chartDef.type = this.type;
        chartDef.loadedHistoryFrom = this.loadedHistoryFrom;
        chartDef.backloadType = this.backloadType;
        chartDef.backloadNumber = this.backloadNumber;
        chartDef.instrumentInfo = this.instrumentInfo != null ? this.instrumentInfo.clone() : null;
        chartDef.minDistance = this.minDistance;
        chartDef.realSpread = this.realSpread;
        return chartDef;
    }

    public String getChartsHash() {
        StringBuilder stringBuilder = new StringBuilder(this.getSymbol());
        stringBuilder.append(this.getConnectionName());
        stringBuilder.append(this.getHistoryFrom());
        stringBuilder.append(this.getHistoryTo());
        stringBuilder.append(this.getSessionStr(this.getSession()));
        stringBuilder.append(this.getTimeframe());
        stringBuilder.append(this.getDataFileHash());
        return stringBuilder.toString();
    }

    private long getDataFileHash() {
        return this.dataInfo.fileHash;
    }

    private String getSessionStr(String string) {
        Session session = SessionManager.getSession(string);
        if (session == null) {
            return "NULL";
        }
        StringBuilder stringBuilder = new StringBuilder();
        stringBuilder.append(session.getSessionName());
        stringBuilder.append("_");
        ArrayList<SessionElement> arrayList = session.getElements();
        if (arrayList != null) {
            for (int i = 0; i < arrayList.size(); ++i) {
                SessionElement sessionElement = arrayList.get(i);
                try {
                    stringBuilder.append(sessionElement.getDayFromStr());
                }
                catch (Exception exception) {
                    stringBuilder.append("N/A");
                }
                try {
                    stringBuilder.append(sessionElement.getTimeFromStr());
                }
                catch (Exception exception) {
                    stringBuilder.append("N/A");
                }
                try {
                    stringBuilder.append(sessionElement.getDayToStr());
                }
                catch (Exception exception) {
                    stringBuilder.append("N/A");
                }
                try {
                    stringBuilder.append(sessionElement.getTimeToStr());
                }
                catch (Exception exception) {
                    stringBuilder.append("N/A");
                }
                stringBuilder.append(sessionElement.isEOD() ? "Y" : "N");
            }
        } else {
            stringBuilder.append("NONE");
        }
        return stringBuilder.toString();
    }

    public boolean canBeComputedFrom(ChartDef chartDef) throws DataException {
        if (this.getSymbolHash() != chartDef.getSymbolHash()) {
            return false;
        }
        if (this.getConnectionHash() != chartDef.getConnectionHash()) {
            return false;
        }
        BarType barType = BarTypeFactory.getBarType(this.getTimeframe(), this.getBarTimeType());
        return barType.checkCanBeComputedFrom(chartDef.getTimeframe()) == null;
    }

    public void modifySpread(double d) {
        this.spread = d;
    }

    public void setRealSpread(boolean bl) {
        this.realSpread = bl;
    }

    public boolean isSmallerThan(ChartDef chartDef) throws DataException {
        if (this.getSymbolHash() != chartDef.getSymbolHash()) {
            return false;
        }
        if (this.getConnectionHash() != chartDef.getConnectionHash()) {
            return false;
        }
        BarType barType = BarTypeFactory.getBarType(this.getTimeframe(), this.getBarTimeType());
        BarType barType2 = BarTypeFactory.getBarType(chartDef.getTimeframe(), this.getBarTimeType());
        return barType.getPeriodInMS() < barType2.getPeriodInMS();
    }

    public void setSession(String string) {
        this.session = string;
    }
}

