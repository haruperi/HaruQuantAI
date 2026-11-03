/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.settings.IXMLAble
 *  org.jdom2.Content
 *  org.jdom2.Element
 */
package com.strategyquant.tradinglib.propertygrid;

import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.settings.IXMLAble;
import com.strategyquant.tradinglib.ClassConfig;
import com.strategyquant.tradinglib.Description;
import com.strategyquant.tradinglib.ForEngine;
import com.strategyquant.tradinglib.Help;
import com.strategyquant.tradinglib.propertygrid.IPGParameter;
import com.strategyquant.tradinglib.propertygrid.ParametersTableItemProperties;
import java.lang.reflect.Constructor;
import java.util.ArrayList;
import java.util.Iterator;
import org.jdom2.Content;
import org.jdom2.Element;

public abstract class ParametersTableItem<T extends ParametersTableItemProperties>
extends ParametersTableItemProperties
implements IXMLAble {
    private boolean used = false;
    public String _text = null;
    public boolean editable = true;
    public String name = null;

    public boolean isUsed() {
        return this.used;
    }

    public void setUsed(boolean bl) {
        this.used = bl;
    }

    public void setEditable(boolean bl) {
        this.editable = bl;
    }

    public boolean isEditable() {
        return this.editable;
    }

    public String getName() {
        ClassConfig classConfig = this.getConfig();
        if (classConfig != null) {
            return classConfig.name();
        }
        return "Unknown";
    }

    public String getNote() {
        Help help = this.getClass().getAnnotation(Help.class);
        if (help != null) {
            return help.value();
        }
        return "";
    }

    public String getDescription() {
        Description description = this.getClass().getAnnotation(Description.class);
        if (description != null) {
            return description.value();
        }
        return "";
    }

    public String getFormatedName() {
        ClassConfig classConfig = this.getConfig();
        if (classConfig != null) {
            return classConfig.display();
        }
        return "Unknown";
    }

    public String printFormatedName() {
        String string = this.getFormatedName();
        ArrayList<IPGParameter> arrayList = this.getParams();
        for (IPGParameter iPGParameter : arrayList) {
            string = string.replace("#" + iPGParameter.getKey() + "#", iPGParameter.print());
        }
        return string;
    }

    public String getEngine() {
        ForEngine forEngine = this.getClass().getAnnotation(ForEngine.class);
        if (forEngine != null) {
            return forEngine.value();
        }
        return "*";
    }

    public boolean checkEngine(String string) {
        String string2 = this.getEngine();
        if (string == null || string2.isEmpty()) {
            return true;
        }
        return SQUtils.checkEngine((String)string, (String)string2);
    }

    private ClassConfig getConfig() {
        ClassConfig classConfig = this.getClass().getAnnotation(ClassConfig.class);
        return classConfig;
    }

    public T newInstance(Object[] objectArray) throws Exception {
        Constructor<?> constructor = this.getClass().getConstructor(new Class[0]);
        ParametersTableItemProperties parametersTableItemProperties = (ParametersTableItemProperties)SQUtils.invokeUnchecked(constructor, (Object[])new Object[0]);
        parametersTableItemProperties.applyParameters(objectArray);
        return (T)parametersTableItemProperties;
    }

    public T getClone() throws Exception {
        Constructor<?> constructor = this.getClass().getConstructor(new Class[0]);
        ParametersTableItemProperties parametersTableItemProperties = (ParametersTableItemProperties)SQUtils.invokeUnchecked(constructor, (Object[])new Object[0]);
        parametersTableItemProperties.applyParameters(this.getParams());
        return (T)parametersTableItemProperties;
    }

    public Element getXML() {
        String string = this.getClass().getSimpleName();
        Element element = new Element("Params");
        ArrayList<IPGParameter> arrayList = this.getParams();
        for (int i = 0; i < arrayList.size(); ++i) {
            IPGParameter iPGParameter = arrayList.get(i);
            try {
                String string2 = iPGParameter.getEngine();
                Element element2 = iPGParameter.getXML().setAttribute("className", string).setAttribute("category", iPGParameter.getCategory()).setAttribute("engine", string2 == null ? "*" : string2);
                element.addContent((Content)element2);
                continue;
            }
            catch (Exception exception) {
                Log.error("Parameter '" + iPGParameter.getKey() + "' wasn't found", (Throwable)exception);
            }
        }
        return element;
    }

    public void setFromXML(Element element) throws Exception {
        Element element2 = element.getChild("Params");
        if (element2 != null) {
            for (Element element3 : element2.getChildren("Param")) {
                this.setFromParameterEl(element3);
            }
        }
    }

    public void setFromParameterEl(Element element) throws Exception {
        String string = element.getAttributeValue("key");
        String string2 = element.getTextTrim();
        if (string2.isEmpty()) {
            string2 = element.getAttributeValue("value");
        }
        this.setParameterValue(string, string2);
    }

    public boolean equals(Object object) {
        try {
            ParametersTableItemProperties parametersTableItemProperties = (ParametersTableItemProperties)object;
            for (String string : this.getParametersList()) {
                boolean bl = false;
                for (String string2 : parametersTableItemProperties.getParametersList()) {
                    if (!string.equals(string2) || !this.getParameterValue(string).equals(parametersTableItemProperties.getParameterValue(string))) continue;
                    bl = true;
                    break;
                }
                if (bl) continue;
                return false;
            }
        }
        catch (Exception exception) {
            // empty catch block
        }
        return true;
    }

    protected Element getUsedSubelement(Element element, String string) {
        Element element2;
        boolean bl = false;
        int n = 0;
        Iterator iterator = element.getChildren(string).iterator();
        while (iterator.hasNext()) {
            element2 = (Element)iterator.next();
            ++n;
            String string2 = element2.getAttributeValue("use");
            if (string2 == null) continue;
            bl = true;
            if (!string2.equals("true")) continue;
            return element2;
        }
        if (n == 1 && !bl && (iterator = element.getChildren(string).iterator()).hasNext()) {
            element2 = (Element)iterator.next();
            return element2;
        }
        return null;
    }
}

