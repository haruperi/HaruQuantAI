/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.settings.IXMLAble
 *  org.jdom2.Content
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.datalib.session;

import com.strategyquant.datalib.TickEvent;
import com.strategyquant.datalib.data.io.VersatileData;
import com.strategyquant.datalib.session.MonthlyRangeCalculator;
import com.strategyquant.datalib.session.SessionElement;
import com.strategyquant.datalib.session.SessionStatus;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.settings.IXMLAble;
import java.io.Serializable;
import java.util.ArrayList;
import java.util.List;
import org.jdom2.Content;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class Session
implements Serializable,
IXMLAble {
    public static final Logger Log = LoggerFactory.getLogger((String)"Session");
    public static final long WEEK_MILLIS = 604800000L;
    public static final String NoSession = "No Session";
    public static final String Forex_247 = "Forex_247";
    public static final String Forex_245 = "Forex_245";
    public static final String US_Index_Futures = "US_Index_Futures";
    public static final String US_Stocks = "US_Stocks";
    private String sessionName;
    private int broker = -1;
    private ArrayList<SessionElement> sessionElements;
    private long lastTimeChecked = -1L;
    private SessionStatus lastSessionStatus = new SessionStatus();

    public Session() {
    }

    public Session(String string, ArrayList<SessionElement> arrayList) {
        this.sessionName = string;
        this.sessionElements = arrayList;
    }

    public String getSessionName() {
        return this.sessionName;
    }

    public ArrayList<SessionElement> getElements() {
        return this.sessionElements;
    }

    public void checkTimeIsInSession(long l, SessionStatus sessionStatus, String string) {
        if (this.sessionElements == null) {
            sessionStatus.isInSession = true;
            sessionStatus.sessionStartTime = Long.MIN_VALUE;
            sessionStatus.sessionEndTime = Long.MIN_VALUE;
            return;
        }
        if (this.lastTimeChecked == l) {
            sessionStatus.isInSession = this.lastSessionStatus.isInSession;
            sessionStatus.sessionStartTime = this.lastSessionStatus.sessionStartTime;
            sessionStatus.sessionEndTime = this.lastSessionStatus.sessionEndTime;
            return;
        }
        sessionStatus.isInSession = false;
        SessionElement sessionElement = null;
        int n = -1;
        for (int i = 0; i < this.sessionElements.size(); ++i) {
            SessionElement sessionElement2 = this.sessionElements.get(i);
            if (!sessionElement2.includesTime(l)) continue;
            sessionElement = sessionElement2;
            n = i;
        }
        if (sessionElement != null) {
            sessionStatus.isInSession = true;
            String string2 = string = string != null ? string : "H1";
            if (string.equals("Weekly")) {
                sessionStatus.sessionStartTime = this.sessionElements.get(0).getStartTime();
                sessionStatus.sessionEndTime = this.sessionElements.get(this.sessionElements.size() - 1).getEndTime();
                if (sessionStatus.sessionStartTime > sessionStatus.sessionEndTime) {
                    sessionStatus.sessionStartTime -= 604800000L;
                }
                if (sessionStatus.sessionEndTime < l) {
                    sessionStatus.sessionStartTime += 604800000L;
                    sessionStatus.sessionEndTime += 604800000L;
                }
            } else if (string.equals("Monthly")) {
                sessionStatus.sessionStartTime = MonthlyRangeCalculator.getSessionStartTime(l, this.sessionElements.get(0).getStartTime(), this.sessionElements.get(this.sessionElements.size() - 1).getEndTime());
                sessionStatus.sessionEndTime = MonthlyRangeCalculator.getSessionEndTime(l, this.sessionElements.get(0).getStartTime(), this.sessionElements.get(this.sessionElements.size() - 1).getEndTime());
            } else if (string.equals("D1")) {
                sessionStatus.sessionStartTime = this.findStartElement(n).getStartTime();
                sessionStatus.sessionEndTime = this.findEndElement(n).getEndTime();
                if (sessionStatus.sessionStartTime > sessionStatus.sessionEndTime) {
                    sessionStatus.sessionStartTime -= 604800000L;
                }
                if (sessionStatus.sessionEndTime < l) {
                    sessionStatus.sessionStartTime += 604800000L;
                    sessionStatus.sessionEndTime += 604800000L;
                }
            } else {
                sessionStatus.sessionStartTime = sessionElement.getStartTime();
                sessionStatus.sessionEndTime = sessionElement.getEndTime();
                if (sessionStatus.sessionStartTime > sessionStatus.sessionEndTime) {
                    long l2 = sessionStatus.sessionStartTime;
                    sessionStatus.sessionStartTime = sessionStatus.sessionEndTime;
                    sessionStatus.sessionEndTime = l2;
                }
            }
            this.lastTimeChecked = l;
            this.lastSessionStatus.isInSession = sessionStatus.isInSession;
            this.lastSessionStatus.sessionStartTime = sessionStatus.sessionStartTime;
            this.lastSessionStatus.sessionEndTime = sessionStatus.sessionEndTime;
        }
    }

    private SessionElement findStartElement(int n) {
        int n2 = 50;
        int n3 = n;
        SessionElement sessionElement = null;
        for (int i = 0; i < n2; ++i) {
            if (--n3 < 0) {
                n3 = this.sessionElements.size() - 1;
            }
            if (!this.sessionElements.get(n3).isEOD()) continue;
            int n4 = n3 + 1;
            if (n4 == this.sessionElements.size()) {
                n4 = 0;
            }
            sessionElement = this.sessionElements.get(n4);
            break;
        }
        if (sessionElement == null) {
            Log.error("Session start element not found");
            return this.sessionElements.get(n);
        }
        return sessionElement;
    }

    private SessionElement findEndElement(int n) {
        int n2 = 50;
        int n3 = n;
        SessionElement sessionElement = null;
        for (int i = 0; i < n2; ++i) {
            if (n3 >= this.sessionElements.size()) {
                n3 = 0;
            }
            if (this.sessionElements.get(n3).isEOD()) {
                sessionElement = this.sessionElements.get(n3);
                break;
            }
            ++n3;
        }
        if (sessionElement == null) {
            Log.error("Session start element not found");
            return this.sessionElements.get(n);
        }
        return sessionElement;
    }

    public Session clone() {
        return new Session(this.sessionName, this.cloneElements());
    }

    public void clearSessionTempData() {
        if (this.sessionElements == null) {
            return;
        }
        for (int i = 0; i < this.sessionElements.size(); ++i) {
            SessionElement sessionElement = this.sessionElements.get(i);
            sessionElement.clearSessionTempData();
        }
    }

    public ArrayList<SessionElement> cloneElements() {
        if (this.sessionElements == null) {
            return null;
        }
        ArrayList<SessionElement> arrayList = new ArrayList<SessionElement>();
        for (SessionElement sessionElement : this.sessionElements) {
            arrayList.add(sessionElement.clone());
        }
        return arrayList;
    }

    public void fixD1DataTime(VersatileData versatileData) {
        if (this.sessionElements == null || this.sessionElements.size() == 0) {
            return;
        }
        SessionElement sessionElement = null;
        for (int i = 0; i < this.sessionElements.size(); ++i) {
            SessionElement sessionElement2 = this.sessionElements.get(i);
            if (!sessionElement2.includesTime(versatileData.time)) continue;
            sessionElement = sessionElement2;
        }
        if (sessionElement != null) {
            sessionElement.fixD1DataTime(versatileData);
        }
    }

    public void fixD1DataTime(TickEvent tickEvent) {
        if (this.sessionElements == null || this.sessionElements.size() == 0) {
            return;
        }
        SessionElement sessionElement = null;
        for (int i = 0; i < this.sessionElements.size(); ++i) {
            SessionElement sessionElement2 = this.sessionElements.get(i);
            if (!sessionElement2.includesTime(tickEvent.getTime())) continue;
            sessionElement = sessionElement2;
        }
        if (sessionElement != null) {
            sessionElement.fixD1DataTime(tickEvent);
        }
    }

    public Element getXML() {
        try {
            Element element = new Element("Session");
            element.setAttribute("name", this.sessionName);
            ArrayList<SessionElement> arrayList = this.getElements();
            for (int i = 0; i < arrayList.size(); ++i) {
                SessionElement sessionElement = arrayList.get(i);
                Element element2 = new Element("Element");
                element2.setAttribute("dayFrom", sessionElement.getDayFromStr());
                element2.setAttribute("dayTo", sessionElement.getDayToStr());
                element2.setAttribute("timeFrom", sessionElement.getTimeFromStr());
                element2.setAttribute("timeTo", sessionElement.getTimeToStr());
                element2.setAttribute("eod", String.valueOf(sessionElement.isEOD()));
                element.addContent((Content)element2);
            }
            return element;
        }
        catch (Exception exception) {
            Log.error("Cannot get xml. Exc.", (Throwable)exception);
            return null;
        }
    }

    public void setFromXML(Element element) throws Exception {
        this.sessionName = element.getAttributeValue("name");
        this.sessionElements = new ArrayList();
        List list = element.getChildren("Element");
        for (int i = 0; i < list.size(); ++i) {
            Element element2 = (Element)list.get(i);
            String string = element2.getAttributeValue("dayFrom");
            String string2 = element2.getAttributeValue("dayTo");
            String string3 = element2.getAttributeValue("timeFrom");
            String string4 = element2.getAttributeValue("timeTo");
            boolean bl = Boolean.parseBoolean(element2.getAttributeValue("eod"));
            this.sessionElements.add(new SessionElement(string, string3, string2, string4, bl));
        }
    }

    public String toText() {
        Element element = this.getXML();
        if (element == null) {
            return this.sessionName;
        }
        return XMLUtil.elementToString((Element)element);
    }

    public int getBroker() {
        return this.broker;
    }

    public void setBroker(int n) {
        this.broker = n;
    }
}

