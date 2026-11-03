/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQTime
 *  org.jdom2.Element
 */
package com.strategyquant.plugin.Task.impl.Optimize;

import com.strategyquant.lib.SQTime;
import java.text.ParseException;
import java.util.ArrayList;
import org.jdom2.Element;

public class ConfigVerifier {
    public ArrayList<String> verifyConfig(Element taskConfig) {
        ArrayList<String> errors = new ArrayList<String>();
        Element settingsElem = taskConfig.getChild("Settings");
        if (settingsElem == null) {
            errors.add("Invalid XML configuration.");
        } else {
            this.checkDataConfig(errors, settingsElem);
        }
        return errors;
    }

    private void checkDataConfig(ArrayList<String> errors, Element settingsElem) {
        Element elData = settingsElem.getChild("Data");
        if (elData == null) {
            errors.add("Cannot find Data settings.");
            return;
        }
        Element elSetups = elData.getChild("Setups");
        if (elSetups == null) {
            errors.add("Cannot find Data.Setups settings.");
            return;
        }
        if (elSetups.getChildren("Setup").size() == 0) {
            errors.add("You have to choose at least one backtest!");
            return;
        }
        int i = 0;
        for (Element elSetup : elSetups.getChildren("Setup")) {
            ++i;
            int j = 0;
            for (Element elChart : elSetup.getChildren("Chart")) {
                this.checkChart(elChart, i, ++j, errors);
            }
            if (!this.checkDate(elSetup.getAttributeValue("dateFrom"), "Date From", i, errors) || !this.checkDate(elSetup.getAttributeValue("dateTo"), "Date To", i, errors)) break;
            if (elSetup.getAttributeValue("slippage") == null || elSetup.getAttributeValue("slippage").equals("") || elSetup.getAttributeValue("slippage").equals("undefined")) {
                errors.add(String.format("Slippage in %s is undefined!", i, this.getBacktestLabel(i)));
                return;
            }
            if (elSetup.getAttributeValue("minDist") == null || elSetup.getAttributeValue("minDist").equals("") || elSetup.getAttributeValue("minDist").equals("undefined")) {
                errors.add(String.format("Min Distance in %s is undefined!", i, this.getBacktestLabel(i)));
                return;
            }
            if (elSetup.getAttributeValue("commission") != null && !elSetup.getAttributeValue("commission").equals("") && !elSetup.getAttributeValue("commission").equals("undefined")) continue;
            errors.add(String.format("Commission in %s is undefined!", i, this.getBacktestLabel(i)));
            return;
        }
    }

    private void checkChart(Element elChart, int backtestIndex, int chartIndex, ArrayList<String> errors) {
        if (elChart.getAttributeValue("symbol") == null || elChart.getAttributeValue("symbol").equals("") || elChart.getAttributeValue("symbol").equals("undefined")) {
            errors.add(String.format("Symbol in Chart %d in %s is undefined!", chartIndex, this.getBacktestLabel(backtestIndex)));
            return;
        }
        if (elChart.getAttributeValue("timeframe") == null || elChart.getAttributeValue("timeframe").equals("") || elChart.getAttributeValue("timeframe").equals("undefined")) {
            errors.add(String.format("Timeframe in Chart %d in %s is undefined!", chartIndex, this.getBacktestLabel(backtestIndex)));
            return;
        }
        if (elChart.getAttributeValue("spread") == null || elChart.getAttributeValue("spread").equals("") || elChart.getAttributeValue("spread").equals("undefined")) {
            errors.add(String.format("Spread in Chart %d in %s is undefined!", chartIndex, this.getBacktestLabel(backtestIndex)));
            return;
        }
    }

    private boolean checkDate(String value, String label, int index, ArrayList<String> errors) {
        if (value == null || value.equals("") || value.equals("undefined")) {
            errors.add(String.format("%s in %s is undefined!", label, this.getBacktestLabel(index)));
            return false;
        }
        try {
            long l = SQTime.parseDateToMilis((String)value);
        }
        catch (ParseException e) {
            errors.add(String.format("%s in %s has incorrect value'%s'!", label, this.getBacktestLabel(index), value));
            return false;
        }
        return true;
    }

    private String getBacktestLabel(int index) {
        if (index == 1) {
            return "Main backtest";
        }
        return String.format("Backtest %d", index);
    }
}

