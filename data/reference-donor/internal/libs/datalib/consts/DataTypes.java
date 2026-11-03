/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib.consts;

public class DataTypes {
    public static final byte Stock = 1;
    public static final byte Futures = 2;
    public static final byte Forex = 3;
    public static final byte CFDs = 4;
    public static final byte ETF = 5;
    public static final byte Index = 6;
    public static final byte Crypto = 7;
    public static final byte Bond = 8;
    public static final String DATATYPE_STOCK = "Stock";
    public static final String DATATYPE_FUTURES = "Futures";
    public static final String DATATYPE_FOREX = "Forex";
    public static final String DATATYPE_CFDS = "CFDs";
    public static final String DATATYPE_ETF = "ETF";
    public static final String DATATYPE_INDEX = "Index";
    public static final String DATATYPE_CRYPTO = "Crypto";
    public static final String DATATYPE_BOND = "Bond";

    public static String toString(int n) {
        switch (n) {
            case 1: {
                return DATATYPE_STOCK;
            }
            case 2: {
                return DATATYPE_FUTURES;
            }
            case 3: {
                return DATATYPE_FOREX;
            }
            case 4: {
                return DATATYPE_CFDS;
            }
            case 5: {
                return DATATYPE_ETF;
            }
            case 6: {
                return DATATYPE_INDEX;
            }
            case 7: {
                return DATATYPE_CRYPTO;
            }
            case 8: {
                return DATATYPE_BOND;
            }
        }
        return n + "";
    }

    public static byte getDataType(String string) throws Exception {
        switch (string) {
            case "Stock": {
                return 1;
            }
            case "Futures": {
                return 2;
            }
            case "Forex": {
                return 3;
            }
            case "CFDs": {
                return 4;
            }
            case "ETF": {
                return 5;
            }
            case "Index": {
                return 6;
            }
            case "Crypto": {
                return 7;
            }
            case "Bond": {
                return 8;
            }
        }
        throw new Exception("Unknown data type: '" + string + "'");
    }
}

