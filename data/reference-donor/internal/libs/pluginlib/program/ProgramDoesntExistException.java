/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.pluginlib.program;

public class ProgramDoesntExistException
extends Exception {
    public ProgramDoesntExistException(String string) {
        super("Program '" + string + "' doesn't exist");
    }
}

