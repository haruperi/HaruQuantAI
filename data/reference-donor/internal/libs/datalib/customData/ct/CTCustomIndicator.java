/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.XMLUtil
 *  org.jdom2.Element
 */
package com.strategyquant.datalib.customData.ct;

import com.strategyquant.datalib.customData.ct.CTCustomIndicatorOutput;
import com.strategyquant.datalib.customData.ct.CTCustomIndicatorParam;
import com.strategyquant.lib.XMLUtil;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.jdom2.Element;

public class CTCustomIndicator {
    public String fileName;
    public String shortName;
    public String longName;
    public String returnType;
    public List<CTCustomIndicatorParam> params = new ArrayList<CTCustomIndicatorParam>();
    public Map<String, CTCustomIndicatorOutput> outputs = new HashMap<String, CTCustomIndicatorOutput>();

    public CTCustomIndicator(Element element) throws Exception {
        CTCustomIndicatorParam cTCustomIndicatorParam;
        Object object2;
        this.fileName = XMLUtil.getAttr((Element)element, (String)"fileName");
        this.shortName = XMLUtil.getAttr((Element)element, (String)"shortName");
        this.longName = XMLUtil.getAttr((Element)element, (String)"longName");
        this.returnType = XMLUtil.getAttr((Element)element, (String)"returnType");
        List list = element.getChildren("Param");
        for (Object object2 : list) {
            cTCustomIndicatorParam = new CTCustomIndicatorParam((Element)object2);
            this.params.add(cTCustomIndicatorParam);
        }
        List list2 = element.getChildren("Output");
        object2 = list2.iterator();
        while (object2.hasNext()) {
            cTCustomIndicatorParam = (Element)object2.next();
            CTCustomIndicatorOutput cTCustomIndicatorOutput = new CTCustomIndicatorOutput((Element)cTCustomIndicatorParam);
            this.outputs.put(cTCustomIndicatorOutput.name, cTCustomIndicatorOutput);
        }
    }
}

