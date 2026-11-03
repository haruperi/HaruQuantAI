/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.TimePeriod
 */
package com.strategyquant.tradinglib.equitychart;

import com.strategyquant.lib.TimePeriod;
import com.strategyquant.tradinglib.SampleTypes;
import com.strategyquant.tradinglib.equitychart.AreaFill;
import com.strategyquant.tradinglib.equitychart.EquityChart;
import java.util.List;

public class SampleMarkers {
    public void print(EquityChart equityChart, List<TimePeriod> list, boolean bl) {
        for (TimePeriod timePeriod : list) {
            AreaFill areaFill;
            if (timePeriod.name.contains("OOS")) {
                areaFill = new AreaFill();
                if (bl) {
                    areaFill.text = SampleTypes.typeToFullString(timePeriod.type);
                }
                areaFill.color = "#89c284";
                areaFill.xFrom = timePeriod.from;
                areaFill.xTo = timePeriod.to;
                equityChart.addArea(areaFill);
                continue;
            }
            if (!timePeriod.name.contains("ISV")) continue;
            areaFill = new AreaFill();
            if (bl) {
                areaFill.text = SampleTypes.typeToFullString(timePeriod.type);
            }
            areaFill.color = "#88a9bf";
            areaFill.xFrom = timePeriod.from;
            areaFill.xTo = timePeriod.to;
            equityChart.addArea(areaFill);
        }
    }
}

