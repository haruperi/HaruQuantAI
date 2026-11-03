/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.snippets.CustomClasses
 */
package com.strategyquant.tradinglib.enginecharts;

import com.strategyquant.lib.snippets.CustomClasses;
import com.strategyquant.tradinglib.EngineChart;
import java.util.ArrayList;
import java.util.List;

public class EngineChartsList
extends CustomClasses<EngineChart> {
    private static EngineChartsList instance;
    public ArrayList<EngineChart> globalCharts = new ArrayList();

    public static EngineChartsList getInstance() {
        if (instance == null) {
            instance = new EngineChartsList();
        }
        return instance;
    }

    private EngineChartsList() {
        this.setDirName("EngineCharts");
        this.setExpectedClassType(EngineChart.class);
        this.loadAvailableClasses();
        this.initGlobalCharts();
    }

    private void initGlobalCharts() {
        List list = this.getAvailableClasses();
        for (int i = 0; i < list.size(); ++i) {
            EngineChart engineChart = (EngineChart)list.get(i);
            if (engineChart.getType() != 10) continue;
            EngineChart engineChart2 = (EngineChart)this.createNew(engineChart.getClassName());
            this.globalCharts.add(engineChart2);
        }
    }
}

