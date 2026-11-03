/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.jdom2.Element
 */
package com.strategyquant.tradinglib.blocks.random;

import com.strategyquant.tradinglib.blocks.random.ReplacementChartConfig;
import com.strategyquant.tradinglib.generator.GenerateException;
import java.util.ArrayList;
import org.jdom2.Element;

public class ReplacementChartsConfig
extends ArrayList<ReplacementChartConfig> {
    public ReplacementChartsConfig(Element element, double d) throws GenerateException {
        int n = 0;
        for (Element element2 : element.getChildren()) {
            this.add(new ReplacementChartConfig(n, element2, d));
            ++n;
        }
    }
}

