/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.gui;

import com.strategyquant.tradinglib.gui.IInitAfterGUILoad;
import java.util.ArrayList;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class InitAfterGUILoad {
    public static final Logger Log = LoggerFactory.getLogger(InitAfterGUILoad.class);
    public static List<IInitAfterGUILoad> listeners = new ArrayList<IInitAfterGUILoad>();

    public static void register(IInitAfterGUILoad iInitAfterGUILoad) {
        listeners.add(iInitAfterGUILoad);
    }

    public static void notifyAllListeners() {
        for (int i = 0; i < listeners.size(); ++i) {
            try {
                listeners.get(i).callAfterGUILoaded();
                continue;
            }
            catch (Exception exception) {
                Log.error("Exc.", (Throwable)exception);
            }
        }
    }
}

