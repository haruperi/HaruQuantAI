/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.pluginlib.program;

public class ProgramMethodDoesntExistException
extends Exception {
    public ProgramMethodDoesntExistException(String string) {
        super("Program method '" + string + "' doesn't exist");
    }
}

