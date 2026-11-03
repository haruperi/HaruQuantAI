/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  it.unimi.dsi.fastutil.longs.Long2ObjectOpenHashMap
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.datalib.bartype;

import com.strategyquant.datalib.TimeframeManager;
import com.strategyquant.datalib.bartype.BarType;
import com.strategyquant.datalib.bartype.TimeframeNotSupportedException;
import com.strategyquant.datalib.bartype.impl.FuturesIntradayBar;
import com.strategyquant.datalib.bartype.impl.FuturesTimeBar;
import com.strategyquant.datalib.bartype.impl.FxIntradayBar;
import com.strategyquant.datalib.bartype.impl.FxTimeBar;
import com.strategyquant.datalib.data.DataException;
import it.unimi.dsi.fastutil.longs.Long2ObjectOpenHashMap;
import java.util.ArrayList;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class BarTypeFactory {
    public static final Logger Log = LoggerFactory.getLogger((String)"BarTypeFactory");
    private static final String PREFIX_SEPARATOR = ":";
    private static BarTypeFactory instance = null;
    private ArrayList<BarType> registeredBarTypes = new ArrayList();
    private Long2ObjectOpenHashMap<BarType> createdBarTypes = new Long2ObjectOpenHashMap();

    private BarTypeFactory() {
        try {
            this.addBarType(new FxTimeBar("M1"));
            this.addBarType(new FuturesTimeBar("M1"));
            this.addBarType(new FxIntradayBar());
            this.addBarType(new FuturesIntradayBar());
        }
        catch (TimeframeNotSupportedException timeframeNotSupportedException) {
            Log.error("Error initializing BarTypes", (Throwable)timeframeNotSupportedException);
        }
    }

    private void addBarType(BarType barType) {
        this.registeredBarTypes.add(barType);
    }

    private static BarTypeFactory get() {
        if (instance == null) {
            instance = new BarTypeFactory();
        }
        return instance;
    }

    public static BarType getBarType(String string, int n) throws DataException {
        return BarTypeFactory.get()._getBarType(string, n);
    }

    private BarType _getBarType(String string, int n) throws DataException {
        long l = this.getUniqueHash(string, n);
        if (!this.createdBarTypes.containsKey(l)) {
            BarType barType = null;
            for (BarType barType2 : this.registeredBarTypes) {
                if (barType2.getBarTimeType() != n || !barType2.checkTimeframeIsSupported(string)) continue;
                barType = barType2;
                break;
            }
            if (barType == null) {
                throw new DataException(4, "No BarType was found for timeframe '" + string + "' and barTimeType '" + n + "' !");
            }
            BarType barType3 = barType.clone(string);
            this.createdBarTypes.put(l, (Object)barType3);
        }
        return (BarType)this.createdBarTypes.get(l);
    }

    private long getUniqueHash(String string, int n) throws DataException {
        try {
            return TimeframeManager.getTFHash(string) + (long)n;
        }
        catch (Exception exception) {
            throw new DataException(6, exception.getMessage());
        }
    }

    private static boolean isTimePeriod(String string) {
        return true;
    }

    public static void checkTimeframeIsValid(String string) throws DataException {
        if (string == null || string.isEmpty()) {
            throw new DataException(6, "Timeframe wasn't recognized.");
        }
        if ((string = string.toUpperCase()).equalsIgnoreCase("TICK")) {
            return;
        }
        if (string.equalsIgnoreCase("Intraday")) {
            return;
        }
        if (string.equalsIgnoreCase("Weekly")) {
            return;
        }
        if (string.equalsIgnoreCase("Monthly")) {
            return;
        }
        String string2 = string.substring(0, 1);
        if (!(string2.equals("S") || string2.equals("M") || string2.equals("H") || string2.equals("D"))) {
            throw new DataException(6, "Timeframe '" + string + "' is not supported!");
        }
        try {
            String string3 = string.substring(1, string.length());
            int n = Integer.parseInt(string3);
        }
        catch (NumberFormatException numberFormatException) {
            throw new DataException(6, "Timeframe '" + string + "' is not supported!");
        }
    }
}

