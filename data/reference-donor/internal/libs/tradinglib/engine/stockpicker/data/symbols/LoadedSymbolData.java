/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.TradingException
 */
package com.strategyquant.tradinglib.engine.stockpicker.data.symbols;

import com.strategyquant.datalib.TradingException;

public class LoadedSymbolData {
    public float[] OpenD;
    public float[] HighD;
    public float[] LowD;
    public float[] CloseD;
    public float[] VolumeD;
    public float[] ValueD;
    public float[] OpenW;
    public float[] HighW;
    public float[] LowW;
    public float[] CloseW;
    public float[] VolumeW;
    public float[] OpenM;
    public float[] HighM;
    public float[] LowM;
    public float[] CloseM;
    public float[] VolumeM;
    private int realDataIndexStartD = -1;
    private int realDataIndexEndD = -1;
    private int realDataIndexStartW = -1;
    private int realDataIndexEndW = -1;
    private int realDataIndexStartM = -1;
    private int realDataIndexEndM = -1;
    private Exception loadException = null;

    public LoadedSymbolData() {
    }

    public LoadedSymbolData(int n, int n2, int n3) {
        this.OpenD = new float[n];
        this.HighD = new float[n];
        this.LowD = new float[n];
        this.CloseD = new float[n];
        this.VolumeD = new float[n];
        this.ValueD = new float[n];
        this.OpenW = new float[n2];
        this.HighW = new float[n2];
        this.LowW = new float[n2];
        this.CloseW = new float[n2];
        this.VolumeW = new float[n2];
        this.OpenM = new float[n3];
        this.HighM = new float[n3];
        this.LowM = new float[n3];
        this.CloseM = new float[n3];
        this.VolumeM = new float[n3];
    }

    public float OpenD(int n) {
        if (this.OpenD == null || n < this.realDataIndexStartD || n > this.realDataIndexEndD) {
            return 0.0f;
        }
        return this.OpenD[n];
    }

    public float OpenW(int n) {
        if (this.OpenW == null || n < this.realDataIndexStartW || n > this.realDataIndexEndW) {
            return 0.0f;
        }
        return this.OpenW[n];
    }

    public float OpenM(int n) {
        if (this.OpenM == null || n < this.realDataIndexStartM || n > this.realDataIndexEndM) {
            return 0.0f;
        }
        return this.OpenM[n];
    }

    public float CloseD(int n) {
        if (this.CloseD == null || n < this.realDataIndexStartD || n > this.realDataIndexEndD) {
            return 0.0f;
        }
        return this.CloseD[n];
    }

    public float CloseW(int n) {
        if (this.CloseW == null || n < this.realDataIndexStartW || n > this.realDataIndexEndW) {
            return 0.0f;
        }
        return this.CloseW[n];
    }

    public float CloseM(int n) {
        if (this.CloseM == null || n < this.realDataIndexStartM || n > this.realDataIndexEndM) {
            return 0.0f;
        }
        return this.CloseM[n];
    }

    public float HighD(int n) {
        if (this.HighD == null || n < this.realDataIndexStartD || n > this.realDataIndexEndD) {
            return 0.0f;
        }
        return this.HighD[n];
    }

    public float HighW(int n) {
        if (this.HighW == null || n < this.realDataIndexStartW || n > this.realDataIndexEndW) {
            return 0.0f;
        }
        return this.HighW[n];
    }

    public float HighM(int n) {
        if (this.HighM == null || n < this.realDataIndexStartM || n > this.realDataIndexEndM) {
            return 0.0f;
        }
        return this.HighM[n];
    }

    public float LowD(int n) {
        if (this.LowD == null || n < this.realDataIndexStartD || n > this.realDataIndexEndD) {
            return 0.0f;
        }
        return this.LowD[n];
    }

    public float LowW(int n) {
        if (this.LowW == null || n < this.realDataIndexStartW || n > this.realDataIndexEndW) {
            return 0.0f;
        }
        return this.LowW[n];
    }

    public float LowM(int n) {
        if (this.LowM == null || n < this.realDataIndexStartM || n > this.realDataIndexEndM) {
            return 0.0f;
        }
        return this.LowM[n];
    }

    public float VolumeD(int n) {
        if (this.VolumeD == null || n < this.realDataIndexStartD || n > this.realDataIndexEndD) {
            return 0.0f;
        }
        return this.VolumeD[n];
    }

    public float VolumeW(int n) {
        if (this.VolumeW == null || n < this.realDataIndexStartW || n > this.realDataIndexEndW) {
            return 0.0f;
        }
        return this.VolumeW[n];
    }

    public float VolumeM(int n) {
        if (this.VolumeM == null || n < this.realDataIndexStartM || n > this.realDataIndexEndM) {
            return 0.0f;
        }
        return this.VolumeM[n];
    }

    public void setRealDataIndexStartD(int n) throws TradingException {
        if (n < 0) {
            throw new TradingException(String.format("Cannot set START index of real data  - Index out of range %d, starts from 0.", n, 0));
        }
        this.realDataIndexStartD = n;
    }

    public void setRealDataIndexEndD(int n) throws TradingException {
        if (n >= this.OpenD.length) {
            throw new TradingException(String.format("Cannot set END index of real data  - Index out of range %d, size %d.", n, this.OpenD.length));
        }
        this.realDataIndexEndD = n;
    }

    public void setRealDataIndexStartW(int n) {
        this.realDataIndexStartW = n;
    }

    public void setRealDataIndexEndW(int n) {
        this.realDataIndexEndW = n;
    }

    public void setRealDataIndexStartM(int n) {
        this.realDataIndexStartM = n;
    }

    public void setRealDataIndexEndM(int n) {
        this.realDataIndexEndM = n;
    }

    public int getRealDataIndexStartD() {
        return this.realDataIndexStartD;
    }

    public int getRealDataIndexEndD() {
        return this.realDataIndexEndD;
    }

    public int getRealDataIndexStartW() {
        return this.realDataIndexStartW;
    }

    public int getRealDataIndexEndW() {
        return this.realDataIndexEndW;
    }

    public int getRealDataIndexStartM() {
        return this.realDataIndexStartM;
    }

    public int getRealDataIndexEndM() {
        return this.realDataIndexEndM;
    }

    public boolean dataExistsD(int n) {
        if (this.OpenD == null || n < this.realDataIndexStartD || n > this.realDataIndexEndD) {
            return false;
        }
        return this.OpenD[n] > 0.0f;
    }

    public Exception getException() {
        return this.loadException;
    }

    public void setException(Exception exception) {
        this.loadException = exception;
    }

    public int getRealDataIndexStart(String string) throws TradingException {
        switch (string) {
            case "D1": {
                return this.getRealDataIndexStartD();
            }
            case "Weekly": {
                return this.getRealDataIndexStartW();
            }
            case "Monthly": {
                return this.getRealDataIndexStartM();
            }
        }
        throw new TradingException(String.format("Cannot get data START index - unexpected timeframe %s.", string));
    }

    public int getRealDataIndexEnd(String string) throws TradingException {
        switch (string) {
            case "D1": {
                return this.getRealDataIndexEndD();
            }
            case "Weekly": {
                return this.getRealDataIndexEndW();
            }
            case "Monthly": {
                return this.getRealDataIndexEndM();
            }
        }
        throw new TradingException(String.format("Cannot get data END index - unexpected timeframe %s.", string));
    }

    public LoadedSymbolData clone() {
        LoadedSymbolData loadedSymbolData = new LoadedSymbolData();
        loadedSymbolData.OpenD = this.OpenD != null ? (float[])this.OpenD.clone() : null;
        loadedSymbolData.HighD = this.HighD != null ? (float[])this.HighD.clone() : null;
        loadedSymbolData.LowD = this.LowD != null ? (float[])this.LowD.clone() : null;
        loadedSymbolData.CloseD = this.CloseD != null ? (float[])this.CloseD.clone() : null;
        loadedSymbolData.VolumeD = this.VolumeD != null ? (float[])this.VolumeD.clone() : null;
        loadedSymbolData.ValueD = this.ValueD != null ? (float[])this.ValueD.clone() : null;
        loadedSymbolData.OpenW = this.OpenW != null ? (float[])this.OpenW.clone() : null;
        loadedSymbolData.HighW = this.HighW != null ? (float[])this.HighW.clone() : null;
        loadedSymbolData.LowW = this.LowW != null ? (float[])this.LowW.clone() : null;
        loadedSymbolData.CloseW = this.CloseW != null ? (float[])this.CloseW.clone() : null;
        loadedSymbolData.VolumeW = this.VolumeW != null ? (float[])this.VolumeW.clone() : null;
        loadedSymbolData.OpenM = this.OpenM != null ? (float[])this.OpenM.clone() : null;
        loadedSymbolData.HighM = this.HighM != null ? (float[])this.HighM.clone() : null;
        loadedSymbolData.LowM = this.LowM != null ? (float[])this.LowM.clone() : null;
        loadedSymbolData.CloseM = this.CloseM != null ? (float[])this.CloseM.clone() : null;
        loadedSymbolData.VolumeM = this.VolumeM != null ? (float[])this.VolumeM.clone() : null;
        loadedSymbolData.realDataIndexStartD = this.realDataIndexStartD;
        loadedSymbolData.realDataIndexEndD = this.realDataIndexEndD;
        loadedSymbolData.realDataIndexStartW = this.realDataIndexStartW;
        loadedSymbolData.realDataIndexEndW = this.realDataIndexEndW;
        loadedSymbolData.realDataIndexStartM = this.realDataIndexStartM;
        loadedSymbolData.realDataIndexEndM = this.realDataIndexEndM;
        loadedSymbolData.loadException = this.loadException;
        return loadedSymbolData;
    }
}

