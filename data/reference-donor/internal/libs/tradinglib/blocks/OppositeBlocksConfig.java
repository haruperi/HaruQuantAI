/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQUtils
 *  it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.blocks;

import com.strategyquant.lib.SQUtils;
import com.strategyquant.tradinglib.Blocks;
import com.strategyquant.tradinglib.IBlock;
import com.strategyquant.tradinglib.OppositeBlock;
import com.strategyquant.tradinglib.Output;
import com.strategyquant.tradinglib.Parameter;
import it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.OutputStream;
import java.io.OutputStreamWriter;
import java.lang.reflect.Field;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.TreeMap;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class OppositeBlocksConfig {
    public static final Logger Log = LoggerFactory.getLogger((String)"OppositeBlocksConfig");

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public void run(String string) throws Exception {
        TreeMap<String, String> treeMap = Blocks.generateOppositeBlocksMap();
        File file = new File(string);
        BufferedWriter bufferedWriter = null;
        try {
            if (!file.exists()) {
                file.getParentFile().mkdirs();
            }
            bufferedWriter = new BufferedWriter(new OutputStreamWriter((OutputStream)new FileOutputStream(file), StandardCharsets.UTF_8));
            bufferedWriter.append("Block;OppositeBlock\n");
            for (String string2 : treeMap.keySet()) {
                bufferedWriter.append(string2);
                bufferedWriter.append(";");
                bufferedWriter.append(treeMap.get(string2));
                bufferedWriter.append("\r\n");
            }
        }
        catch (Exception exception) {
        }
        finally {
            try {
                if (bufferedWriter != null) {
                    bufferedWriter.close();
                }
            }
            catch (IOException iOException) {}
        }
    }

    public HashMap<String, String> load(String string, Int2ObjectOpenHashMap<IBlock> int2ObjectOpenHashMap) {
        HashMap<String, String> hashMap = new HashMap<String, String>();
        File file = new File(string);
        if (!file.exists()) {
            Log.debug("File '" + string + "' doesn't exist!");
            return this.fillMissingBlocks(hashMap, int2ObjectOpenHashMap);
        }
        ArrayList arrayList = new ArrayList();
        try {
            SQUtils.fileToArrayList(arrayList, (String)string, (String)"\r\n");
        }
        catch (Exception exception) {
            Log.error("Cannot read OppositeBlocks.csv file: " + exception.getMessage(), (Throwable)exception);
        }
        for (int i = 0; i < arrayList.size(); ++i) {
            String string2 = (String)arrayList.get(i);
            if (string2.contains("OppositeBlock")) continue;
            string2 = string2.trim();
            String[] stringArray = (string2 = string2.replace("\"", "")).split(";");
            if (stringArray.length == 2) {
                if (this.checkBlocksExistAndHaveSameParameters(stringArray[0], stringArray[1], int2ObjectOpenHashMap)) {
                    hashMap.put(stringArray[0], stringArray[1]);
                    continue;
                }
                Log.error(String.format("Block '%s' or '%s' doesn't exist, or blocks don't have same parameters, using default opposite block!", stringArray[0], stringArray[1]));
                continue;
            }
            Log.error("Wrong opposite block format on line " + i + " : " + string2);
        }
        return this.fillMissingBlocks(hashMap, int2ObjectOpenHashMap);
    }

    private boolean checkBlocksExistAndHaveSameParameters(String string, String string2, Int2ObjectOpenHashMap<IBlock> int2ObjectOpenHashMap) {
        if (!int2ObjectOpenHashMap.containsKey(string.hashCode())) {
            return false;
        }
        if (!int2ObjectOpenHashMap.containsKey(string2.hashCode())) {
            return false;
        }
        IBlock iBlock = (IBlock)int2ObjectOpenHashMap.get(string.hashCode());
        IBlock iBlock2 = (IBlock)int2ObjectOpenHashMap.get(string2.hashCode());
        return this.blocksHaveSameParameters(iBlock, iBlock2);
    }

    private boolean blocksHaveSameParameters(IBlock iBlock, IBlock iBlock2) {
        Field[] fieldArray = iBlock.getClass().getFields();
        if (fieldArray == null) {
            return true;
        }
        for (int i = 0; i < fieldArray.length; ++i) {
            Field field = fieldArray[i];
            if (field.getAnnotation(Parameter.class) != null && !this.findFieldInBlock(field, iBlock2)) {
                return false;
            }
            if (field.getAnnotation(Output.class) == null || this.findFieldInBlock(field, iBlock2)) continue;
            return false;
        }
        return true;
    }

    private boolean findFieldInBlock(Field field, IBlock iBlock) {
        Field[] fieldArray = iBlock.getClass().getFields();
        if (fieldArray == null) {
            return true;
        }
        for (int i = 0; i < fieldArray.length; ++i) {
            Field field2 = fieldArray[i];
            if (!field.getName().equals(field2.getName())) continue;
            return field.getType().toString().equals(field2.getType().toString());
        }
        return false;
    }

    private HashMap<String, String> fillMissingBlocks(HashMap<String, String> hashMap, Int2ObjectOpenHashMap<IBlock> int2ObjectOpenHashMap) {
        for (IBlock iBlock : int2ObjectOpenHashMap.values()) {
            String string = iBlock.getClass().getSimpleName();
            String string2 = null;
            if (hashMap.containsKey(string)) continue;
            OppositeBlock oppositeBlock = iBlock.getClass().getAnnotation(OppositeBlock.class);
            if (oppositeBlock != null && int2ObjectOpenHashMap.containsKey((string2 = oppositeBlock.value()).hashCode())) {
                hashMap.put(string, string2);
                continue;
            }
            hashMap.put(string, string);
        }
        return hashMap;
    }
}

