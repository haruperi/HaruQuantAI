/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.IRandomGenerator
 *  com.strategyquant.lib.SettingsMap
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.gp.strategies;

import com.strategyquant.lib.IRandomGenerator;
import com.strategyquant.lib.SettingsMap;
import com.strategyquant.tradinglib.generator.GenerateException;
import com.strategyquant.tradinglib.gp.AbstractFactory;
import com.strategyquant.tradinglib.gp.IEvolutionaryOperator;
import com.strategyquant.tradinglib.gp.strategies.Node;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class FixNumberOfExitTypes
implements IEvolutionaryOperator<Node> {
    private static final Logger Log = LoggerFactory.getLogger((String)"FixNumberOfExitTypes");
    private final int maxExitTypes;
    private final boolean slRequired;
    private final boolean ptRequired;
    private final boolean exitSymmetry;
    private final ArrayList<String> requiredExitsList;

    public FixNumberOfExitTypes(SettingsMap settingsMap, Element element) throws GenerateException {
        this.maxExitTypes = (Integer)settingsMap.get("MaxExitTypes", (Object)0);
        this.slRequired = (Boolean)settingsMap.get("SLRequired");
        this.ptRequired = (Boolean)settingsMap.get("PTRequired");
        this.exitSymmetry = (Boolean)settingsMap.get("ExitSymmetry");
        this.requiredExitsList = new ArrayList();
        this.analyzeRequiredExits(element, this.requiredExitsList);
    }

    private void analyzeRequiredExits(Element element, ArrayList<String> arrayList) {
        List list = element.getChildren();
        for (Element element2 : list) {
            String string;
            String string2;
            String string3;
            String string4 = element2.getName();
            if (string4.equals("Formula") && (string3 = element2.getAttributeValue("exitMethod")) != null && string3.equals("true") && (string2 = element2.getAttributeValue("probability")) != null && string2.equals("100") && !arrayList.contains(string = element2.getAttributeValue("key"))) {
                arrayList.add(string);
            }
            this.analyzeRequiredExits(element2, arrayList);
        }
    }

    @Override
    public List<Node> apply(List<Node> list, IRandomGenerator iRandomGenerator, AbstractFactory<Node> abstractFactory, int n, int n2) throws Exception {
        for (int i = 0; i < list.size(); ++i) {
            Node node = list.get(i);
            this.fixStrategy(node.getStrategy());
        }
        return list;
    }

    public boolean fixStrategy(Element element) throws GenerateException {
        if (this.maxExitTypes <= 0) {
            return false;
        }
        Element element2 = element.getChild("Strategy");
        Element element3 = element2.getChild("Rules");
        ArrayList<Element> arrayList = new ArrayList<Element>();
        this.findEntryOrders(element3, arrayList);
        boolean bl = false;
        ArrayList<String> arrayList2 = new ArrayList<String>();
        for (int i = 0; i < arrayList.size(); ++i) {
            boolean bl2;
            ArrayList<Element> arrayList3;
            Element element4 = arrayList.get(i);
            int n = this.countAllUsedExitTypes(element4, arrayList3 = new ArrayList<Element>());
            int n2 = n - this.maxExitTypes;
            if (n2 <= 0) continue;
            bl = true;
            if (i == 0) {
                this.removeExits(n2, arrayList3, arrayList2, false);
            } else {
                this.removeExits(n2, arrayList3, arrayList2, this.exitSymmetry);
            }
            arrayList3.clear();
            n = this.countAllUsedExitTypes(element4, arrayList3);
            if (n <= this.maxExitTypes) continue;
            boolean bl3 = bl2 = true;
        }
        return bl;
    }

    private void removeExits(int n, ArrayList<Element> arrayList, ArrayList<String> arrayList2, boolean bl) {
        if (bl) {
            arrayList = this.prepareFromRemovedKeys(arrayList, arrayList2);
        } else {
            Collections.shuffle(arrayList);
        }
        for (int i = 0; i < arrayList.size(); ++i) {
            Element element = arrayList.get(i);
            String string = this.removeOneExit(element);
            if (string != null) {
                --n;
                arrayList2.add(string);
            }
            if (n <= 0) break;
        }
    }

    private ArrayList<Element> prepareFromRemovedKeys(ArrayList<Element> arrayList, ArrayList<String> arrayList2) {
        ArrayList<Element> arrayList3 = new ArrayList<Element>();
        for (int i = 0; i < arrayList.size(); ++i) {
            Element element = arrayList.get(i);
            String string = element.getAttributeValue("key");
            if (!arrayList2.contains(string)) continue;
            arrayList3.add(element);
        }
        return arrayList3;
    }

    private String removeOneExit(Element element) {
        String string;
        String string2 = element.getAttributeValue("key");
        if (this.slRequired && string2.equals("#StopLoss.StopLoss#")) {
            return null;
        }
        if (this.ptRequired && string2.equals("#ProfitTarget.ProfitTarget#")) {
            return null;
        }
        if (this.requiredExitsList.contains(string2)) {
            return null;
        }
        String string3 = element.getAttributeValue("controlType");
        if (string3.equals("jspinnerVar")) {
            element.setText("0");
            return string2;
        }
        Element element2 = element.getChild("Formula");
        if (element2 != null && !(string = element2.getAttributeValue("key")).contains("None") && this.removeFormulaExit(element2)) {
            return string2;
        }
        return null;
    }

    private boolean removeFormulaExit(Element element) {
        String string = element.getAttributeValue("key");
        int n = string.lastIndexOf(".");
        string = string.substring(0, n);
        string = string + ".None";
        element.setAttribute("key", string);
        element.removeContent();
        return true;
    }

    private int countAllUsedExitTypes(Element element, ArrayList<Element> arrayList) {
        boolean bl = false;
        List list = element.getChildren("Param");
        for (int i = 0; i < list.size(); ++i) {
            String string;
            String string2;
            Element element2 = (Element)list.get(i);
            String string3 = element2.getAttributeValue("exitMethod");
            if (string3 == null || !string3.equals("true") || this.isDependentOn(element2)) continue;
            String string4 = element2.getAttributeValue("controlType");
            if (string4.equals("jspinnerVar")) {
                string2 = element2.getText();
                try {
                    int n = Integer.parseInt(string2);
                    if (n <= 0) continue;
                    arrayList.add(element2);
                }
                catch (NumberFormatException numberFormatException) {}
                continue;
            }
            string2 = element2.getChild("Formula");
            if (string2 == null || (string = string2.getAttributeValue("key")).contains("None")) continue;
            arrayList.add(element2);
        }
        return arrayList.size();
    }

    private boolean isDependentOn(Element element) {
        String string = element.getAttributeValue("dependentOn");
        if (string != null) {
            return true;
        }
        String string2 = element.getAttributeValue("key");
        return string2.equals("#MoveSL2BE.SL2BEAddPips#") || string2.equals("#TrailingStop.TrailingActivation#");
    }

    private void findEntryOrders(Element element, ArrayList<Element> arrayList) {
        List list = element.getChildren();
        for (int i = 0; i < list.size(); ++i) {
            String string;
            Element element2 = (Element)list.get(i);
            String string2 = element2.getName();
            if (string2.equals("Item") && (string = element2.getAttributeValue("returnType")) != null && string.equals("order")) {
                arrayList.add(element2);
            }
            this.findEntryOrders(element2, arrayList);
        }
    }
}

