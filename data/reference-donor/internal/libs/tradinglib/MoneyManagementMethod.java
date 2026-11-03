/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.utils.ISQCloneable
 *  org.jdom2.Content
 *  org.jdom2.Element
 */
package com.strategyquant.tradinglib;

import com.strategyquant.lib.L;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.utils.ISQCloneable;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.moneymanagement.MoneyManagementMethodsList;
import com.strategyquant.tradinglib.propertygrid.ParametersTableItem;
import java.lang.reflect.Constructor;
import java.util.List;
import org.jdom2.Content;
import org.jdom2.Element;

public abstract class MoneyManagementMethod
extends ParametersTableItem
implements ISQCloneable<MoneyManagementMethod> {
    public String name = null;
    private double equity;
    private double initialCapital = 10000.0;
    public static final double defaultInitialCapital = 10000.0;
    protected double weight = 1.0;
    protected double maxPos = 1.0;

    public void setName(String string) {
        this.name = string;
    }

    protected double getEquity() {
        return this.equity;
    }

    public double getInitialCapital() {
        return this.initialCapital;
    }

    public void setInitialCapital(double d) {
        this.initialCapital = d;
    }

    @Override
    public Element getXML() {
        Element element = new Element("MoneyManagement");
        Element element2 = new Element("Method");
        element2.setAttribute("type", this.getClass().getSimpleName());
        element2.setAttribute("use", "true");
        Element element3 = super.getXML();
        element2.addContent((Content)element3);
        Element element4 = new Element("InitialCapital");
        element4.setText(String.valueOf(this.initialCapital));
        element.addContent((Content)element2);
        element.addContent((Content)element4);
        return element;
    }

    @Override
    public void setFromXML(Element element) throws Exception {
        Element element2 = this.getUsedSubelement(element, "Method");
        if (element2 == null) {
            throw new Exception(L.t((String)"Cannot set up MoneyManagement method. Method xml element not found.", (Object[])new Object[0]));
        }
        this.setName(element2.getAttributeValue("type"));
        super.setFromXML(element2);
        Element element3 = element.getChild("InitialCapital");
        if (element3 != null) {
            try {
                this.setInitialCapital(Double.parseDouble(element3.getTextTrim()));
            }
            catch (Exception exception) {
                Log.error("Invalid Initial Capital settings. Using default value - 10000.0");
            }
        } else {
            Log.warn("Initial capital XML element not found");
        }
    }

    public MoneyManagementMethod newInstance() throws Exception {
        Constructor<?> constructor = this.getClass().getConstructor(new Class[0]);
        MoneyManagementMethod moneyManagementMethod = (MoneyManagementMethod)SQUtils.invokeUnchecked(constructor, (Object[])new Object[0]);
        return moneyManagementMethod;
    }

    public double computeTradeSize(StrategyBase strategyBase, String string, byte by, double d, double d2, double d3, double d4, double d5) throws Exception {
        return 0.0;
    }

    public double computeTradeSize(StrategyBase strategyBase, String string, byte by, double d, double d2, double d3, double d4) throws Exception {
        return this.computeTradeSize(strategyBase, string, by, d, d2, d3, d4, 0.0);
    }

    public void setMethodFromXML(Element element) throws Exception {
        for (Element element2 : element.getChild("Params").getChildren("Param")) {
            this.setFromParameterEl(element2);
        }
    }

    @Override
    public void setFromParameterEl(Element element) throws Exception {
        String string = element.getAttributeValue("key");
        string = SQUtils.renameActionParams((String)string);
        string = string.replaceAll("#", "");
        String string2 = element.getTextTrim();
        if (string2 == null || string2.isEmpty()) {
            string2 = element.getAttributeValue("value");
        }
        this.setParameterValue(string, string2);
    }

    public MoneyManagementMethod getClone() throws Exception {
        try {
            List list = MoneyManagementMethodsList.get().getAvailableClasses();
            for (MoneyManagementMethod moneyManagementMethod : list) {
                if (!moneyManagementMethod.getClass().equals(this.getClass())) continue;
                MoneyManagementMethod moneyManagementMethod2 = (MoneyManagementMethod)moneyManagementMethod.getClass().newInstance();
                List<String> list2 = moneyManagementMethod2.getParametersList();
                for (int i = 0; i < list2.size(); ++i) {
                    String string = list2.get(i);
                    moneyManagementMethod2.setParameterValue(string, "" + this.getParameterValue(string));
                }
                return moneyManagementMethod2;
            }
        }
        catch (Exception exception) {
            throw new CloneNotSupportedException("Cloning MoneyManagementMethod " + this.name + " failed. " + exception.getMessage());
        }
        throw new CloneNotSupportedException("Cloning failed. Cannot find MoneyManagementMethod " + this.name);
    }

    public double round(double d, double d2, int n) {
        if (d2 > 0.0) {
            d = Math.floor(d / d2) * d2;
        }
        return SQUtils.round((double)d, (int)n);
    }

    public void setWeight(double d) {
        this.weight = d;
    }

    public void setMaxOpenPositions(double d) {
        this.maxPos = d;
    }
}

