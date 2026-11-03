/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.snippets.CustomClassesLoader
 *  com.strategyquant.lib.snippets.compile.SQStructure
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.task.settings.blocks;

import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.snippets.CustomClassesLoader;
import com.strategyquant.lib.snippets.compile.SQStructure;
import com.strategyquant.tradinglib.IBlock;
import java.util.ArrayList;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class BlocksList {
    private static final Logger Log = LoggerFactory.getLogger((String)"BlocksList");

    public static ArrayList<IBlock> getBlocks(String string) {
        String string2 = SQStructure.getCompiledCustomDirPath((String)string);
        ArrayList<IBlock> arrayList = new ArrayList<IBlock>();
        BlocksList.loadClasses(arrayList, string);
        for (String string3 : SQUtils.listSubdirectories((String)string2)) {
            BlocksList.loadClasses(arrayList, string + "/" + string3);
        }
        return arrayList;
    }

    private static void loadClasses(ArrayList<IBlock> arrayList, String string) {
        try {
            CustomClassesLoader customClassesLoader = new CustomClassesLoader(string);
            while (customClassesLoader.hasNext()) {
                String string2 = customClassesLoader.getNext();
                Object object = customClassesLoader.createInstance(string2);
                if (object instanceof IBlock) {
                    IBlock iBlock = (IBlock)object;
                    arrayList.add(iBlock);
                    continue;
                }
                if (!Log.isDebugEnabled()) continue;
                Log.debug("Class: " + string2 + " is not an instance of block");
            }
        }
        catch (Exception exception) {
            Log.error("An error occured while loading custom classes.", (Throwable)exception);
        }
    }
}

