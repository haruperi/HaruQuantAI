/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.utils.ISQCloneable
 *  org.jdom2.Content
 *  org.jdom2.Element
 */
package com.strategyquant.tradinglib;

import com.strategyquant.lib.utils.ISQCloneable;
import com.strategyquant.tradinglib.ILiveOrder;
import com.strategyquant.tradinglib.Trader;
import com.strategyquant.tradinglib.propertygrid.ParametersTableItem;
import com.strategyquant.tradinglib.riskmanagement.RiskManagementMethodsList;
import java.util.List;
import org.jdom2.Content;
import org.jdom2.Element;

public abstract class RiskManagementMethod
extends ParametersTableItem
implements ISQCloneable<RiskManagementMethod> {
    private double equity;
    private int decimals;

    public void setName(String string) {
        this.name = string;
    }

    protected double getEquity() {
        return this.equity;
    }

    protected int getDecimals() {
        return this.decimals;
    }

    @Override
    public Element getXML() {
        Element element = new Element("Method");
        element.setAttribute("type", this.getClass().getSimpleName());
        Element element2 = super.getXML();
        element.addContent((Content)element2);
        return element;
    }

    @Override
    public void setFromXML(Element element) throws Exception {
        Element element2 = this.getUsedSubelement(element, "Method");
        if (element2 == null) {
            throw new Exception("Error while loading Risk Management xml config. XML element Method was not found.");
        }
        super.setFromXML(element.getChild("Method"));
    }

    public abstract void verifyOrder(Trader var1, ILiveOrder var2);

    public RiskManagementMethod getClone() throws Exception {
        try {
            List list = RiskManagementMethodsList.get().getAvailableClasses();
            for (RiskManagementMethod riskManagementMethod : list) {
                if (!riskManagementMethod.getClass().equals(this.getClass())) continue;
                RiskManagementMethod riskManagementMethod2 = (RiskManagementMethod)riskManagementMethod.getClass().newInstance();
                List<String> list2 = riskManagementMethod2.getParametersList();
                for (int i = 0; i < list2.size(); ++i) {
                    String string = list2.get(i);
                    riskManagementMethod2.setParameterValue(string, "" + this.getParameterValue(string));
                }
                return riskManagementMethod2;
            }
        }
        catch (Exception exception) {
            throw new CloneNotSupportedException("Cloning RiskManagementMethod " + this.name + " failed. " + exception.getMessage());
        }
        throw new CloneNotSupportedException("Cloning failed. Cannot find RiskManagementMethod " + this.name);
    }
}

