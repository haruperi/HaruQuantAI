/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.InstrumentInfo
 *  com.strategyquant.datalib.session.Session
 *  com.strategyquant.datalib.session.SessionElement
 *  com.strategyquant.lib.XMLUtil
 *  org.jdom2.Element
 *  org.jdom2.JDOMException
 */
package com.strategyquant.plugin.DataManager.impl.Broker;

import com.strategyquant.datalib.InstrumentInfo;
import com.strategyquant.datalib.session.Session;
import com.strategyquant.datalib.session.SessionElement;
import com.strategyquant.lib.XMLUtil;
import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.LinkedList;
import java.util.List;
import org.jdom2.Element;
import org.jdom2.JDOMException;

public class BrokerXmlImporter {
    public List<Session> importSessions(String file, List<String> names) throws JDOMException, IOException, Exception {
        LinkedList<Session> sessions = new LinkedList<Session>();
        Element elements = XMLUtil.fileToXmlElement((File)new File(file));
        List children = elements.getChildren("Session");
        for (Element element : children) {
            String name = element.getAttributeValue("name");
            if (names != null && !names.contains(name)) continue;
            ArrayList<SessionElement> items = new ArrayList<SessionElement>();
            for (Element subElement : element.getChildren("Element")) {
                items.add(new SessionElement(subElement.getAttributeValue("dayFrom"), subElement.getAttributeValue("timeFrom"), subElement.getAttributeValue("dayTo"), subElement.getAttributeValue("timeTo"), Boolean.valueOf(subElement.getAttributeValue("eod")).booleanValue()));
            }
            Session session = new Session(name, items);
            session.setTimeZone(element.getAttributeValue("timeZone"));
            sessions.add(session);
        }
        return sessions;
    }

    public List<InstrumentInfo> importInstruments(String file, List<String> names) throws JDOMException, IOException, Exception {
        LinkedList<InstrumentInfo> instruments = new LinkedList<InstrumentInfo>();
        Element elements = XMLUtil.fileToXmlElement((File)new File(file));
        List children = elements.getChildren("InstrumentInfo");
        for (Element element : children) {
            String name = element.getAttributeValue("instrument");
            if (names != null && !names.contains(name)) continue;
            InstrumentInfo info = new InstrumentInfo(element);
            instruments.add(info);
        }
        return instruments;
    }
}

