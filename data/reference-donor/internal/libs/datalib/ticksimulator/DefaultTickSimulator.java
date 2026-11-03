/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQUtils
 */
package com.strategyquant.datalib.ticksimulator;

import com.strategyquant.datalib.TickEvent;
import com.strategyquant.datalib.data.io.VersatileData;
import com.strategyquant.datalib.ticksimulator.ITickSimulator;
import com.strategyquant.datalib.ticksimulator.SpreadsMap;
import com.strategyquant.lib.SQUtils;
import java.security.InvalidParameterException;

public class DefaultTickSimulator
implements ITickSimulator {
    private VersatileData data = new VersatileData();
    private int step = -1;
    private SpreadsMap spreadsMap;
    private int lastSpreadHash = -1;
    private double lastSpread;
    private double avgTickVolume;
    private double volume;
    private boolean growingCandle;
    private double spread;

    @Override
    public void init(VersatileData versatileData) {
        this.data.copyFrom(versatileData);
        this.data.sessionStartTime = this.data.time;
        this.step = 0;
        this.growingCandle = this.data.close > this.data.open;
        this.volume = this.avgTickVolume = this.data.volume / 4.0;
        if (versatileData.spread == -1.0) {
            this.spread = -1.0;
        } else {
            this.spread = this.getSpread(this.data.connectionHash, this.data.symbolHash);
            this.spread = this.spread >= 0.0 ? this.spread : 0.0;
        }
    }

    @Override
    public boolean getNextTick(TickEvent tickEvent) {
        if (this.step < 0) {
            return false;
        }
        if (this.data.type == 1 && this.step > 0) {
            return false;
        }
        if (this.data.type == 2 && this.step > 3) {
            return false;
        }
        if (this.data.type == 1) {
            double d = SQUtils.round7((double)(this.spread == -1.0 ? this.data.ask : this.data.bid + this.spread));
            tickEvent.set(this.data.time, this.data.connectionHash, this.data.symbolHash, this.data.bid, d, this.data.volume, this.data.sessionStartTime, false, false);
            ++this.step;
            return true;
        }
        if (this.data.type == 2) {
            if (this.step == 3) {
                this.volume = this.data.volume - 3.0 * this.avgTickVolume;
            }
            switch (this.step) {
                case 0: {
                    tickEvent.set(this.data.time, this.data.connectionHash, this.data.symbolHash, this.data.open, SQUtils.round7((double)(this.data.open + this.spread)), this.volume, this.data.sessionStartTime, true, false);
                    ++this.step;
                    return true;
                }
                case 1: {
                    if (this.growingCandle) {
                        tickEvent.set(this.data.time, this.data.connectionHash, this.data.symbolHash, this.data.low, SQUtils.round7((double)(this.data.low + this.spread)), this.volume, this.data.sessionStartTime, false, false);
                    } else {
                        tickEvent.set(this.data.time, this.data.connectionHash, this.data.symbolHash, this.data.high, SQUtils.round7((double)(this.data.high + this.spread)), this.volume, this.data.sessionStartTime, false, false);
                    }
                    ++this.step;
                    return true;
                }
                case 2: {
                    if (this.growingCandle) {
                        tickEvent.set(this.data.time, this.data.connectionHash, this.data.symbolHash, this.data.high, SQUtils.round7((double)(this.data.high + this.spread)), this.volume, this.data.sessionStartTime, false, false);
                    } else {
                        tickEvent.set(this.data.time, this.data.connectionHash, this.data.symbolHash, this.data.low, SQUtils.round7((double)(this.data.low + this.spread)), this.volume, this.data.sessionStartTime, false, false);
                    }
                    ++this.step;
                    return true;
                }
                case 3: {
                    tickEvent.set(this.data.time, this.data.connectionHash, this.data.symbolHash, this.data.close, SQUtils.round7((double)(this.data.close + this.spread)), this.volume, this.data.sessionStartTime, false, true);
                    ++this.step;
                    return true;
                }
            }
        }
        throw new InvalidParameterException("Shouldnt get here");
    }

    private double getSpread(int n, int n2) {
        int n3 = n + n2;
        if (n3 == this.lastSpreadHash) {
            return this.lastSpread;
        }
        if (this.spreadsMap != null && this.spreadsMap.containsKey(n3)) {
            double d = this.spreadsMap.getSpread(n3);
            this.lastSpreadHash = n3;
            this.lastSpread = d;
            return d;
        }
        return 0.0;
    }

    @Override
    public void setSymbolsSpread(SpreadsMap spreadsMap) {
        this.spreadsMap = spreadsMap;
    }

    private boolean isLastTick() {
        if (this.data.type == 1 && this.step + 1 > 0) {
            return true;
        }
        return this.data.type == 2 && this.step + 1 > 3;
    }
}

