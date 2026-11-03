/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.pluginlib.program;

import com.strategyquant.pluginlib.program.IProgram;
import com.strategyquant.pluginlib.program.ProgramDoesntExistException;
import java.util.HashMap;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class Program {
    public static final Logger Log = LoggerFactory.getLogger(Program.class);
    public static HashMap<String, IProgram> programsMap = new HashMap();

    public static IProgram get(String string) throws ProgramDoesntExistException {
        if (!programsMap.containsKey(string)) {
            throw new ProgramDoesntExistException(string);
        }
        return programsMap.get(string);
    }

    public static void register(String string, IProgram iProgram) {
        if (programsMap.containsKey(string)) {
            Log.error("Duplicate registered program with name '" + string + "', skipping second registration!");
        } else {
            programsMap.put(string, iProgram);
            Log.debug("Program '" + string + "' was registered.");
        }
    }

    public static boolean isRegistered(String string) {
        return programsMap.containsKey(string);
    }
}

