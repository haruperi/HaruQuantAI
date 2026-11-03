/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.TradingException
 *  com.strategyquant.lib.SettingsMap
 *  com.strategyquant.lib.app.MainApp
 *  it.unimi.dsi.fastutil.objects.ObjectCollection
 *  org.jdom2.Attribute
 *  org.jdom2.JDOMException
 */
package com.strategyquant.tradinglib.stockchart;

import com.strategyquant.datalib.TradingException;
import com.strategyquant.lib.SettingsMap;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.tradinglib.Order;
import com.strategyquant.tradinglib.OrdersList;
import com.strategyquant.tradinglib.blocks.random.BlockDefinition;
import com.strategyquant.tradinglib.blocks.random.BlocksConfig;
import com.strategyquant.tradinglib.engine.stockpicker.Stockpicker;
import com.strategyquant.tradinglib.engine.stockpicker.data.LoadedPickerData;
import com.strategyquant.tradinglib.engine.stockpicker.data.stockGroups.LoadedStockGroupData;
import com.strategyquant.tradinglib.engine.stockpicker.data.timeline.PickerDataTimeline;
import com.strategyquant.tradinglib.talib.TALibIndicators;
import it.unimi.dsi.fastutil.objects.ObjectCollection;
import java.io.BufferedOutputStream;
import java.io.BufferedWriter;
import java.io.IOException;
import java.io.OutputStream;
import java.io.OutputStreamWriter;
import java.nio.ByteBuffer;
import java.util.Collections;
import java.util.HashMap;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.jar.JarEntry;
import java.util.jar.JarOutputStream;
import org.jdom2.Attribute;
import org.jdom2.JDOMException;

public class StockSaverForStockPicking {
    public static final int MAX_TRADES = 1000;
    private JarOutputStream jarOutStream;
    private OrdersList orders;
    private String path;
    private LoadedStockGroupData stockGroupData;
    private Map<String, Integer> orderCounts = new HashMap<String, Integer>();
    private Map<String, List<Object[]>> tmpMapPerSymbol;

    public void save(JarOutputStream jarOutputStream, LoadedPickerData loadedPickerData, Stockpicker stockpicker, OrdersList ordersList, String string) throws JDOMException, Exception {
        this.jarOutStream = jarOutputStream;
        this.stockGroupData = loadedPickerData.stockGroupData;
        this.orders = ordersList;
        this.path = "Results/" + this.correctResultKey(string);
        this.saveTimeLines(loadedPickerData);
        this.saveTrades();
        this.saveMetadata(stockpicker.TALibIndicators);
        this.saveIndicators(stockpicker.TALibIndicators);
    }

    private void saveTimeLines(LoadedPickerData loadedPickerData) throws IOException, TradingException {
        PickerDataTimeline pickerDataTimeline = loadedPickerData.timeline;
        ByteBuffer byteBuffer = ByteBuffer.allocate(pickerDataTimeline.SizeD() * 8);
        for (int i = 0; i < pickerDataTimeline.SizeD(); ++i) {
            long l = pickerDataTimeline.indexToTimeD(i);
            byteBuffer.putLong(l);
        }
        this.createEntry("timelines.dat");
        BufferedOutputStream bufferedOutputStream = new BufferedOutputStream(this.jarOutStream);
        bufferedOutputStream.write(byteBuffer.array());
        bufferedOutputStream.flush();
        this.jarOutStream.closeEntry();
    }

    private void saveIndicators(TALibIndicators tALibIndicators) throws IOException {
        for (String string : this.tmpMapPerSymbol.keySet()) {
            List<Object[]> list = this.tmpMapPerSymbol.get(string);
            for (Object[] objectArray : list) {
                long l = (Long)objectArray[5];
                float[][] fArray = tALibIndicators.getIndicatorValue(l);
                if (fArray == null) continue;
                String string2 = "indicator_" + l + ".dat";
                this.createEntry(string2);
                int n = (Integer)objectArray[3];
                float[] fArray2 = fArray[n];
                ByteBuffer byteBuffer = ByteBuffer.allocate(fArray2.length * 4);
                for (int i = 0; i < fArray2.length; ++i) {
                    byteBuffer.putFloat(fArray2[i]);
                }
                BufferedOutputStream bufferedOutputStream = new BufferedOutputStream(this.jarOutStream);
                bufferedOutputStream.write(byteBuffer.array());
                bufferedOutputStream.flush();
                this.jarOutStream.closeEntry();
            }
        }
    }

    private void createEntry(String string) throws IOException {
        JarEntry jarEntry = new JarEntry(this.path + "/" + string);
        this.jarOutStream.putNextEntry(jarEntry);
    }

    private void saveFromTo(ByteBuffer byteBuffer, long l, long l2) throws IOException {
        byteBuffer.putLong(l);
        byteBuffer.putLong(l2);
    }

    private float getFloat(double d) {
        return (float)((double)((float)d) * 10000.0 / 10000.0);
    }

    private void saveMetadata(TALibIndicators tALibIndicators) throws JDOMException, Exception {
        List<Object[]> list;
        Object object;
        this.createEntry("stock_desc.csv");
        BufferedWriter bufferedWriter = new BufferedWriter(new OutputStreamWriter((OutputStream)this.jarOutStream, "US-ASCII"));
        LinkedList<String> linkedList = new LinkedList<String>(this.stockGroupData.getSymbols());
        Collections.sort(linkedList);
        BlocksConfig blocksConfig = BlocksConfig.getConfig();
        ObjectCollection objectCollection = tALibIndicators.getIndicatorHashes().values();
        this.tmpMapPerSymbol = new HashMap<String, List<Object[]>>();
        for (Object[] object2 : objectCollection) {
            object = (String)object2[0];
            list = this.tmpMapPerSymbol.get(object);
            if (list == null) {
                list = new LinkedList<Object[]>();
                this.tmpMapPerSymbol.put((String)object, list);
            }
            list.add(object2);
        }
        for (String string : linkedList) {
            object = this.orderCounts.get(string);
            if (object == null) {
                object = 0;
            }
            bufferedWriter.write("S;" + string + ";" + object + System.getProperty("line.separator"));
            list = this.tmpMapPerSymbol.get(string);
            if (list == null) continue;
            for (Object[] objectArray : list) {
                String string2 = (String)objectArray[1];
                int n = (Integer)objectArray[2];
                String string3 = (String)objectArray[4];
                long l = (Long)objectArray[5];
                BlockDefinition blockDefinition = blocksConfig.getBlock("talib_" + string2);
                bufferedWriter.write("I;" + l + ";" + string2 + ";" + this.getIndicatorName(blockDefinition, n, (SettingsMap)objectArray[6]) + ";" + string3 + System.getProperty("line.separator"));
            }
        }
        bufferedWriter.flush();
        this.jarOutStream.closeEntry();
    }

    private String getIndicatorName(BlockDefinition blockDefinition, int n, SettingsMap settingsMap) {
        String[] stringArray;
        Attribute attribute = blockDefinition.getXml().getAttribute("display");
        if (attribute == null) {
            return blockDefinition.getName();
        }
        String string = attribute.getValue();
        for (String string2 : stringArray = settingsMap.getAllKeys()) {
            Object object = settingsMap.get(string2);
            if (object == null) {
                object = "";
            }
            String string3 = "#" + string2 + "#";
            string = string.replace(string3, object.toString());
        }
        string.replace("#Shift#", String.valueOf(n));
        return string.replace(".[]", "").replace("[]", "");
    }

    private void saveTrades() throws IOException {
        Set<String> set = this.stockGroupData.getSymbols();
        for (String string : set) {
            int n = this.saveTrades(string);
            this.orderCounts.put(string, n);
        }
    }

    private boolean shouldShowControlOrders() {
        boolean bl = false;
        try {
            bl = Boolean.parseBoolean(MainApp.settings().get("showControlOrders", "false"));
        }
        catch (Exception exception) {
            // empty catch block
        }
        return bl;
    }

    private int saveTrades(String string) throws IOException {
        if (this.orders == null || this.orders.size() == 0) {
            return 0;
        }
        int n = 0;
        boolean bl = this.shouldShowControlOrders();
        int n2 = 0;
        int n3 = 0;
        while (n3 < this.orders.size()) {
            Object object;
            int n4 = 41016;
            ByteBuffer byteBuffer = ByteBuffer.allocate(n4);
            byteBuffer.position(16);
            int n5 = 0;
            long l = -1L;
            long l2 = -1L;
            while (n5 < 1000 && n3 < this.orders.size()) {
                object = this.orders.get(n3);
                ++n3;
                if (((Order)object).Type != 1 && ((Order)object).Type != 2 || !string.equals(((Order)object).Symbol) || !bl && !((Order)object).isRealOrder()) continue;
                byte by = ((Order)object).Type;
                boolean bl2 = by != 1;
                byteBuffer.putLong(((Order)object).Ticket);
                byteBuffer.putLong(((Order)object).OpenTime);
                byteBuffer.putLong(((Order)object).CloseTime);
                byteBuffer.putFloat(this.getFloat(((Order)object).OpenPrice));
                byteBuffer.putFloat(this.getFloat(((Order)object).ClosePrice));
                byteBuffer.putFloat(this.getFloat(((Order)object).StopLoss));
                byteBuffer.putFloat(this.getFloat(((Order)object).TakeProfit));
                byteBuffer.put((byte)(bl2 ? 1 : 0));
                if (((Order)object).OpenTime < l || l == -1L) {
                    l = ((Order)object).OpenTime;
                }
                if (((Order)object).CloseTime > l2 || l2 == -1L) {
                    l2 = ((Order)object).CloseTime;
                }
                ++n5;
                ++n;
            }
            if (l2 != -1L && l != -1L) {
                byteBuffer.position(0);
                this.saveFromTo(byteBuffer, l, l2);
                object = string + "_" + n2;
                this.createEntry("trades_" + (String)object + ".dat");
                BufferedOutputStream bufferedOutputStream = new BufferedOutputStream(this.jarOutStream);
                bufferedOutputStream.write(byteBuffer.array());
                bufferedOutputStream.flush();
                this.jarOutStream.closeEntry();
            }
            ++n2;
        }
        return n;
    }

    private String correctResultKey(String string) {
        return string.replace("/", "_LOM_");
    }
}

