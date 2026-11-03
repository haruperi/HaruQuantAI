/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  net.xeoh.plugins.base.Plugin
 */
package com.strategyquant.pluginlib;

import java.util.Comparator;
import net.xeoh.plugins.base.Plugin;

public interface ISQPlugin
extends Plugin {
    public static final Comparator<ISQPlugin> PositionComparator = new Comparator<ISQPlugin>(){

        @Override
        public int compare(ISQPlugin iSQPlugin, ISQPlugin iSQPlugin2) {
            int n;
            int n2 = iSQPlugin.getPreferredPosition();
            return n2 > (n = iSQPlugin2.getPreferredPosition()) ? 1 : (n2 < n ? -1 : 0);
        }
    };

    public String getProduct();

    public int getPreferredPosition();

    public void initPlugin() throws Exception;

    default public String forEngine() {
        return "*";
    }

    default public boolean disabledForSpecialTrial() {
        return false;
    }
}

