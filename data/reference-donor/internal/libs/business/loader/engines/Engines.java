/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.wizard.desktop.loader.engines;

import com.strategyquant.wizard.desktop.loader.engines.Engine;
import java.util.LinkedList;
import java.util.List;

public class Engines {
    private List<Engine> engines = new LinkedList<Engine>();

    public void addEngine(Engine engine) {
        this.engines.add(engine);
    }

    public String toJson() {
        StringBuilder stringBuilder = new StringBuilder();
        stringBuilder.append("{\"engines\":[");
        boolean bl = true;
        for (Engine engine : this.engines) {
            if (!bl) {
                stringBuilder.append(",");
            }
            stringBuilder.append(engine.toJson());
            bl = false;
        }
        stringBuilder.append("]}");
        return stringBuilder.toString();
    }
}

