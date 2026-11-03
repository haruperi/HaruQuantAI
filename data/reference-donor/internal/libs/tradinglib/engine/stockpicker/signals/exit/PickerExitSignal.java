/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.engine.stockpicker.signals.exit;

import com.strategyquant.tradinglib.Directions;
import com.strategyquant.tradinglib.OrderCloseTypes;

public class PickerExitSignal {
    public String symbol;
    public byte direction;
    public byte closeType;

    public PickerExitSignal(String string, byte by, byte by2) {
        this.symbol = string;
        this.direction = by;
        this.closeType = by2;
    }

    public String toString() {
        StringBuilder stringBuilder = new StringBuilder();
        this.toString(stringBuilder);
        return stringBuilder.toString();
    }

    public void toString(StringBuilder stringBuilder) {
        stringBuilder.append(this.symbol);
        stringBuilder.append(" [");
        stringBuilder.append(OrderCloseTypes.toString(this.closeType));
        stringBuilder.append(", ");
        stringBuilder.append(Directions.typeToString(this.direction));
        stringBuilder.append("]");
    }
}

