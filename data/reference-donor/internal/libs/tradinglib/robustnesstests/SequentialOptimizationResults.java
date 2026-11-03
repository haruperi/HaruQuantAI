/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.ValuesMap
 *  com.strategyquant.lib.XMLUtil
 *  org.jdom2.Content
 *  org.jdom2.Element
 */
package com.strategyquant.tradinglib.robustnesstests;

import com.strategyquant.lib.ValuesMap;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.tradinglib.Variable;
import com.strategyquant.tradinglib.robustnesstests.FitnessData;
import java.util.ArrayList;
import java.util.List;
import org.jdom2.Content;
import org.jdom2.Element;

public class SequentialOptimizationResults
extends ArrayList<FitnessData> {
    private static final String XML_VALUE_SEPARATOR = ";";
    private ValuesMap paramTypes;
    private boolean applyToStrategy = false;
    private boolean symmetricVariables = false;
    private boolean passed = false;

    public SequentialOptimizationResults() {
    }

    public SequentialOptimizationResults(ValuesMap valuesMap, boolean bl, boolean bl2) {
        this.paramTypes = valuesMap;
        this.symmetricVariables = bl;
        this.applyToStrategy = bl2;
    }

    public Element toXML() {
        Element element = new Element("ChainOptimizationResults");
        element.setAttribute("applyToStrategy", "" + this.applyToStrategy);
        element.setAttribute("symmetricVariables", "" + this.symmetricVariables);
        element.setAttribute("passed", "" + this.passed);
        Element element2 = this.paramTypes.getXML();
        element2.setName("ParamTypes");
        element.addContent((Content)element2);
        Element element3 = new Element("Parameters");
        element.addContent((Content)element3);
        for (int i = 0; i < this.size(); ++i) {
            FitnessData fitnessData = (FitnessData)this.get(i);
            Element element4 = new Element("Parameter");
            element4.setAttribute("originalValue", "" + fitnessData.originalValue);
            Element element5 = new Element("Values");
            Element element6 = new Element("Fitness");
            String string = "";
            String string2 = "";
            for (int j = 0; j < fitnessData.values.length; ++j) {
                string = string + (j > 0 ? XML_VALUE_SEPARATOR : "") + fitnessData.values[j];
                string2 = string2 + (j > 0 ? XML_VALUE_SEPARATOR : "") + fitnessData.fitness[j];
            }
            element5.setText(string);
            element6.setText(string2);
            Element element7 = new Element("Results");
            element7.addContent((Content)new Element("BestAreaStartValue").setText("" + fitnessData.bestAreaStartValue));
            element7.addContent((Content)new Element("BestAreaEndValue").setText("" + fitnessData.bestAreaEndValue));
            element7.addContent((Content)new Element("BestValue").setText("" + fitnessData.bestValue));
            element7.addContent((Content)new Element("StableAreaFound").setText("" + fitnessData.stableAreaFound));
            element4.addContent((Content)fitnessData.variable.getXML().clone());
            element4.addContent((Content)element5);
            element4.addContent((Content)element6);
            element4.addContent((Content)element7);
            element3.addContent((Content)element4);
        }
        return element;
    }

    public SequentialOptimizationResults fromXML(Element element) throws Exception {
        this.clear();
        this.applyToStrategy = XMLUtil.getBooleanAttr((Element)element, (String)"applyToStrategy", (boolean)false);
        this.symmetricVariables = XMLUtil.getBooleanAttr((Element)element, (String)"symmetricVariables", (boolean)false);
        this.passed = XMLUtil.getBooleanAttr((Element)element, (String)"passed", (boolean)false);
        Element element2 = XMLUtil.getChildElem((Element)element, (String)"ParamTypes");
        this.paramTypes = new ValuesMap();
        this.paramTypes.setFromXML(element2);
        Element element3 = XMLUtil.getChildElem((Element)element, (String)"Parameters");
        List list = element3.getChildren("Parameter");
        for (int i = 0; i < list.size(); ++i) {
            Element element4 = (Element)list.get(i);
            FitnessData fitnessData = new FitnessData();
            fitnessData.originalValue = XMLUtil.getDoubleAttr((Element)element4, (String)"originalValue", (double)0.0);
            fitnessData.variable = new Variable(XMLUtil.getChildElem((Element)element4, (String)"variable"));
            fitnessData.values = this.loadXMLValues(XMLUtil.getChildElem((Element)element4, (String)"Values"));
            fitnessData.fitness = this.loadXMLValues(XMLUtil.getChildElem((Element)element4, (String)"Fitness"));
            Element element5 = XMLUtil.getChildElem((Element)element4, (String)"Results");
            fitnessData.bestAreaStartValue = Double.parseDouble(XMLUtil.getNodeValue((Element)element5, (String)"BestAreaStartValue"));
            fitnessData.bestAreaEndValue = Double.parseDouble(XMLUtil.getNodeValue((Element)element5, (String)"BestAreaEndValue"));
            fitnessData.bestValue = Double.parseDouble(XMLUtil.getNodeValue((Element)element5, (String)"BestValue"));
            fitnessData.stableAreaFound = Boolean.parseBoolean(XMLUtil.getNodeValue((Element)element5, (String)"StableAreaFound"));
            this.add(fitnessData);
        }
        return this;
    }

    private double[] loadXMLValues(Element element) {
        String[] stringArray = element.getText().split(XML_VALUE_SEPARATOR);
        double[] dArray = new double[stringArray.length];
        for (int i = 0; i < stringArray.length; ++i) {
            dArray[i] = Double.parseDouble(stringArray[i]);
        }
        return dArray;
    }

    public boolean isApplyToStrategy() {
        return this.applyToStrategy;
    }

    public void setApplyToStrategy(boolean bl) {
        this.applyToStrategy = bl;
    }

    public boolean isSymmetricVariables() {
        return this.symmetricVariables;
    }

    public ValuesMap getParamTypes() {
        return this.paramTypes;
    }

    public boolean isPassed() {
        return this.passed;
    }

    public void setPassed(boolean bl) {
        this.passed = bl;
    }

    public SequentialOptimizationResults getClone() {
        SequentialOptimizationResults sequentialOptimizationResults = new SequentialOptimizationResults();
        sequentialOptimizationResults.paramTypes = this.paramTypes.clone();
        sequentialOptimizationResults.applyToStrategy = this.applyToStrategy;
        sequentialOptimizationResults.symmetricVariables = this.symmetricVariables;
        for (int i = 0; i < this.size(); ++i) {
            sequentialOptimizationResults.add(((FitnessData)this.get(i)).getClone());
        }
        return sequentialOptimizationResults;
    }
}

