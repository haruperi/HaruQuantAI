/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 */
package com.strategyquant.tradinglib;

import com.strategyquant.lib.L;
import com.strategyquant.tradinglib.Order;
import com.strategyquant.tradinglib.table.TableColumn;
import java.util.Locale;

public abstract class TradelistColumn
extends TableColumn {
    public TradelistColumn(String string) {
        super(string, "Decimal2");
    }

    public TradelistColumn(String string, String string2) {
        super(string, string2);
    }

    public TradelistColumn(String string, String string2, boolean bl) {
        super(string, string2, bl);
    }

    public boolean setValue(Order order, double d) throws Exception {
        if (!this.isEditable()) {
            throw new Exception(L.t((String)"Column '%s' is not editable, you cannot call setValue() !", (Object[])new Object[]{this.getClass().getSimpleName()}));
        }
        throw new Exception(L.t((String)"Column '%s' is editable, it has to implement setValue() method !", (Object[])new Object[]{this.getClass().getSimpleName()}));
    }

    public abstract Object getValue(Order var1) throws Exception;

    public String getFormattedValue(Object object) throws Exception {
        if (object == null) {
            return "";
        }
        double d = 0.0;
        if (object instanceof Float) {
            d = ((Float)object).floatValue();
        } else if (object instanceof Double) {
            d = (Double)object;
        } else if (object instanceof Integer) {
            d = ((Integer)object).intValue();
        } else if (object instanceof Short) {
            d = ((Short)object).shortValue();
        } else if (object instanceof String) {
            return (String)object;
        }
        switch (this.getType()) {
            case "Decimal2": 
            case "Decimal2PL": 
            case "Decimal2Pips": 
            case "Decimal2Pct": {
                return String.format(Locale.ROOT, "%.2f", d);
            }
            case "Decimal4": {
                return String.format(Locale.ROOT, "%.4f", d);
            }
            case "Decimal5": {
                return String.format(Locale.ROOT, "%.5f", d);
            }
            case "Integer": {
                if (object instanceof Short) {
                    return String.valueOf((short)d);
                }
                return String.valueOf((int)d);
            }
            case "Text": {
                return object.toString();
            }
        }
        return "N/A";
    }
}

