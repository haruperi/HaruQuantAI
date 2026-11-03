/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.propertygrid;

public class ParameterDoesntExistException
extends Exception {
    public ParameterDoesntExistException(String string) {
        super("Parameter '" + string + "' doesn't exist");
    }
}

