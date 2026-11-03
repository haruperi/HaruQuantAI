/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.settings.IXMLAble
 *  org.jdom2.Content
 *  org.jdom2.Element
 */
package com.strategyquant.tradinglib.strategy;

import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.settings.IXMLAble;
import com.strategyquant.tradinglib.Order;
import com.strategyquant.tradinglib.SampleTypes;
import java.io.Serializable;
import java.text.ParseException;
import java.util.Arrays;
import java.util.List;
import org.jdom2.Content;
import org.jdom2.Element;

public class OutOfSample
implements IXMLAble,
Serializable {
    private long[] arrDateFrom = null;
    private long[] arrDateTo = null;
    private byte[] arrSampleType = null;
    private boolean hasNoTrade = false;

    public void addRange(Element element) {
        int n;
        long l = this.stringToTime(element.getAttributeValue("dateFrom").trim());
        long l2 = this.stringToTime(element.getAttributeValue("dateTo").trim());
        String string = element.getAttributeValue("type");
        if (string == null) {
            n = 20;
        } else if (string.equals("notrade")) {
            n = 99;
            this.hasNoTrade = true;
        } else {
            n = string.equals("isv") ? 40 : 20;
        }
        this.addRange(l, l2, (byte)n);
    }

    private long stringToTime(String string) {
        return SQTime.parseToMilis((String)string, (String)"dd.MM.yyyy");
    }

    public void addRange(long l, long l2, byte by) {
        if (this.arrDateFrom == null) {
            this.arrDateFrom = new long[1];
            this.arrDateTo = new long[1];
            this.arrSampleType = new byte[1];
        } else {
            long[] lArray = Arrays.copyOf(this.arrDateFrom, this.arrDateFrom.length + 1);
            long[] lArray2 = Arrays.copyOf(this.arrDateTo, this.arrDateTo.length + 1);
            byte[] byArray = Arrays.copyOf(this.arrSampleType, this.arrSampleType.length + 1);
            this.arrDateFrom = lArray;
            this.arrDateTo = lArray2;
            this.arrSampleType = byArray;
        }
        int n = this.arrDateFrom.length - 1;
        this.arrDateFrom[n] = l;
        this.arrDateTo[n] = l2;
        this.arrSampleType[n] = by;
        int n2 = 0;
        int n3 = 0;
        for (int i = 0; i < this.arrSampleType.length - 1; ++i) {
            byte by2 = this.arrSampleType[i];
            if (SampleTypes.isOOS(by2)) {
                ++n2;
            }
            if (!SampleTypes.isISV(by2)) continue;
            ++n3;
        }
        if (SampleTypes.isOOS(by)) {
            this.arrSampleType[n] = OutOfSample.getOOSPart(n2 + 1);
        } else if (SampleTypes.isISV(by)) {
            this.arrSampleType[n] = OutOfSample.getISVPart(n3 + 1);
        }
    }

    public Element getXML() {
        Element element = new Element("OutOfSample");
        if (this.arrDateFrom != null) {
            for (int i = 0; i < this.arrDateFrom.length; ++i) {
                Element element2 = new Element("Range");
                XMLUtil.trySetAttr((Element)element2, (String)"dateFrom", (Object)SQTime.toString((long)this.arrDateFrom[i], (String)"d.M.yyyy"));
                XMLUtil.trySetAttr((Element)element2, (String)"dateTo", (Object)SQTime.toString((long)this.arrDateTo[i], (String)"d.M.yyyy"));
                String string = this.typeToString(this.arrSampleType[i]);
                if (string != null) {
                    XMLUtil.trySetAttr((Element)element2, (String)"type", (Object)string);
                }
                element.addContent((Content)element2);
            }
        }
        return element;
    }

    private String typeToString(byte by) {
        switch (by) {
            case 99: {
                return "notrade";
            }
            case 40: 
            case 41: 
            case 42: 
            case 43: 
            case 44: 
            case 45: 
            case 46: 
            case 47: 
            case 48: 
            case 49: 
            case 50: {
                return "isv";
            }
        }
        return null;
    }

    public void setFromXML(Element element) throws ParseException {
        int n;
        List list = element.getChildren("Range");
        this.hasNoTrade = false;
        if (list == null || list.size() == 0) {
            this.arrDateFrom = null;
            this.arrDateTo = null;
        } else {
            if (this.arrDateFrom == null || this.arrDateFrom.length != list.size()) {
                this.arrDateFrom = new long[list.size()];
                this.arrDateTo = new long[list.size()];
                this.arrSampleType = new byte[list.size()];
            }
            for (n = 0; n < list.size(); ++n) {
                Element element2 = (Element)list.get(n);
                String string = element2.getAttributeValue("dateFrom");
                String string2 = element2.getAttributeValue("dateTo");
                if (string.indexOf(".") > 2) {
                    this.arrDateFrom[n] = SQTime.parseDateToMilis((String)string);
                    this.arrDateTo[n] = SQTime.parseDateToMilis((String)string2);
                    this.arrDateFrom[n] = SQTime.correctDayStart((long)this.arrDateFrom[n]);
                    this.arrDateTo[n] = SQTime.correctDayEnd((long)this.arrDateTo[n]);
                } else {
                    this.arrDateFrom[n] = SQTime.parseToMilis((String)string, (String)"d.M.yyyy");
                    this.arrDateTo[n] = SQTime.parseToMilis((String)string2, (String)"d.M.yyyy");
                }
                String string3 = element2.getAttributeValue("type");
                if (string3 == null) {
                    this.arrSampleType[n] = 20;
                    continue;
                }
                if (string3.equals("notrade")) {
                    this.arrSampleType[n] = 99;
                    this.hasNoTrade = true;
                    continue;
                }
                this.arrSampleType[n] = string3.equals("isv") ? 40 : 20;
            }
        }
        if (this.arrSampleType != null) {
            n = 0;
            int n2 = 0;
            for (int i = 0; i < this.arrSampleType.length; ++i) {
                byte by = this.arrSampleType[i];
                if (by == 40) {
                    this.arrSampleType[i] = OutOfSample.getISVPart(++n2);
                    continue;
                }
                if (by != 20) continue;
                this.arrSampleType[i] = OutOfSample.getOOSPart(++n);
            }
        }
    }

    public void clear() {
        this.arrDateFrom = null;
        this.arrDateTo = null;
    }

    public String toString() {
        StringBuilder stringBuilder = new StringBuilder("");
        if (this.arrDateFrom != null) {
            for (int i = 0; i < this.arrDateFrom.length; ++i) {
                if (i > 0) {
                    stringBuilder.append(", ");
                }
                stringBuilder.append("oos");
                stringBuilder.append(i);
                stringBuilder.append(SQTime.toString((long)this.arrDateFrom[i], (String)"dd.MM.yyyy"));
                stringBuilder.append(" - ");
                stringBuilder.append(SQTime.toString((long)this.arrDateTo[i], (String)"dd.MM.yyyy"));
            }
        }
        return stringBuilder.toString();
    }

    public boolean isEmpty() {
        return this.arrDateFrom == null;
    }

    public long getDateFrom(int n) {
        return this.arrDateFrom != null && n < this.arrDateFrom.length ? this.arrDateFrom[n] : 0L;
    }

    public long getDateTo(int n) {
        return this.arrDateTo != null && n < this.arrDateTo.length ? this.arrDateTo[n] : 0L;
    }

    public byte getSampleType(int n) {
        return this.arrSampleType != null && n < this.arrSampleType.length ? this.arrSampleType[n] : (byte)127;
    }

    public void setDateFrom(int n, long l) {
        if (this.arrDateFrom != null) {
            this.arrDateFrom[n] = l;
        }
    }

    public void setDateTo(int n, long l) {
        if (this.arrDateTo != null) {
            this.arrDateTo[n] = l;
        }
    }

    public static boolean compare(OutOfSample outOfSample, OutOfSample outOfSample2) {
        if (outOfSample.arrDateFrom == null && outOfSample2.arrDateFrom == null) {
            return true;
        }
        if (outOfSample.arrDateFrom != null && outOfSample2.arrDateFrom != null) {
            if (outOfSample.arrDateFrom.length != outOfSample2.arrDateFrom.length) {
                return false;
            }
            for (int i = 0; i < outOfSample.arrDateFrom.length; ++i) {
                if (outOfSample.arrDateFrom[i] != outOfSample2.arrDateFrom[i]) {
                    return false;
                }
                if (outOfSample.arrDateTo[i] == outOfSample2.arrDateTo[i]) continue;
                return false;
            }
            return true;
        }
        return false;
    }

    public int getRangesCount() {
        return this.arrDateFrom == null ? 0 : this.arrDateFrom.length;
    }

    public byte getSampleType(Order order) {
        if (this.arrDateFrom == null) {
            return 11;
        }
        for (int i = 0; i < this.arrDateFrom.length; ++i) {
            if (this.arrDateFrom[i] == 0L || this.arrDateTo[i] == 0L || this.arrDateFrom[i] >= order.OpenTime || order.OpenTime > this.arrDateTo[i]) continue;
            byte by = this.arrSampleType[i];
            return by;
        }
        return 11;
    }

    public static byte getISVPart(int n) {
        switch (n) {
            case 1: {
                return 41;
            }
            case 2: {
                return 42;
            }
            case 3: {
                return 43;
            }
            case 4: {
                return 44;
            }
            case 5: {
                return 45;
            }
            case 6: {
                return 46;
            }
            case 7: {
                return 47;
            }
            case 8: {
                return 48;
            }
            case 9: {
                return 49;
            }
            case 10: {
                return 50;
            }
        }
        return 11;
    }

    public static byte getOOSPart(int n) {
        switch (n) {
            case 1: {
                return 21;
            }
            case 2: {
                return 22;
            }
            case 3: {
                return 23;
            }
            case 4: {
                return 24;
            }
            case 5: {
                return 25;
            }
            case 6: {
                return 26;
            }
            case 7: {
                return 27;
            }
            case 8: {
                return 28;
            }
            case 9: {
                return 29;
            }
            case 10: {
                return 30;
            }
        }
        return 21;
    }

    public boolean hasNoTrade() {
        return this.hasNoTrade;
    }

    public boolean isNoTrade(long l) {
        if (this.arrDateFrom == null) {
            return false;
        }
        for (int i = 0; i < this.arrDateFrom.length; ++i) {
            if (this.arrSampleType[i] != 99 || this.arrDateFrom[i] == 0L || this.arrDateTo[i] == 0L || l < this.arrDateFrom[i] || l > this.arrDateTo[i]) continue;
            return true;
        }
        return false;
    }

    public byte getPartType(int n) {
        if (this.arrSampleType == null || n >= this.arrSampleType.length) {
            return 20;
        }
        return this.arrSampleType[n];
    }

    public int getPartsCount(byte by) {
        if (this.arrSampleType == null) {
            return 0;
        }
        int n = 0;
        for (int i = 0; i < this.arrSampleType.length; ++i) {
            if (by == 40 && SampleTypes.isISV(this.arrSampleType[i])) {
                ++n;
                continue;
            }
            if (by != 20 || !SampleTypes.isOOS(this.arrSampleType[i])) continue;
            ++n;
        }
        return n;
    }
}

