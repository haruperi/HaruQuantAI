/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.lib.SQUtils
 *  it.unimi.dsi.fastutil.bytes.Byte2ObjectOpenHashMap
 *  it.unimi.dsi.fastutil.ints.Int2ByteOpenHashMap
 *  it.unimi.dsi.fastutil.ints.Int2ObjectMap$Entry
 *  it.unimi.dsi.fastutil.ints.Int2ObjectMap$FastEntrySet
 *  it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap
 *  it.unimi.dsi.fastutil.objects.ObjectArrayList
 *  it.unimi.dsi.fastutil.objects.ObjectListIterator
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib;

import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.tradinglib.Order;
import com.strategyquant.tradinglib.strategy.LiveOrderObj;
import it.unimi.dsi.fastutil.bytes.Byte2ObjectOpenHashMap;
import it.unimi.dsi.fastutil.ints.Int2ByteOpenHashMap;
import it.unimi.dsi.fastutil.ints.Int2ObjectMap;
import it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap;
import it.unimi.dsi.fastutil.objects.ObjectArrayList;
import it.unimi.dsi.fastutil.objects.ObjectListIterator;
import java.io.Externalizable;
import java.io.IOException;
import java.io.ObjectInput;
import java.io.ObjectOutput;
import java.util.Collections;
import java.util.Comparator;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class OrdersList
implements Externalizable {
    public static final Logger Log = LoggerFactory.getLogger((String)"OrdersList");
    private static final String ORDER_FILE_FORMAT = "SQOrderFileFormat:";
    private static final String ConstantAll = "*";
    private ObjectArrayList<Order> list;
    private String identifier;

    public OrdersList(String string) {
        this.identifier = string;
        this.list = new ObjectArrayList();
    }

    public OrdersList(String string, int n) {
        this.identifier = string;
        this.list = new ObjectArrayList(n);
    }

    public void add(Order order) {
        this.list.add((Object)order);
    }

    public ObjectListIterator<Order> listIterator() {
        return this.list.listIterator();
    }

    public ObjectListIterator<Order> listIterator(int n) {
        return this.list.listIterator(n);
    }

    public void add(LiveOrderObj liveOrderObj) {
        Order order = new Order(liveOrderObj);
        this.add(order);
    }

    public Order get(int n) {
        return (Order)this.list.get(n);
    }

    public void shuffle() {
        Collections.shuffle(this.list);
    }

    public void clear() {
        this.list.clear();
        this.list.trim();
    }

    public int size() {
        return this.list.size();
    }

    public void addAll(OrdersList ordersList) {
        this.list.addAll(ordersList.list);
    }

    public void replaceWithList(OrdersList ordersList) {
        this.list.clear();
        this.list = ordersList.list;
    }

    public OrdersList filter(String string, byte by, byte by2) {
        return this.filter(string, by, by2, false, false, false);
    }

    public OrdersList filter(String string, byte by, byte by2, boolean bl) {
        return this.filter(string, by, by2, bl, false, false);
    }

    public OrdersList filterWithClone(String string, byte by, byte by2) {
        return this.filter(string, by, by2, false, true, false);
    }

    public OrdersList filterExcludingControlOrders(String string, byte by, byte by2, boolean bl) {
        return this.filter(string, by, by2, bl, true, true);
    }

    private OrdersList filter(String string, byte by, byte by2, boolean bl, boolean bl2, boolean bl3) {
        OrdersList ordersList = new OrdersList("FilteredOL");
        String string2 = ConstantAll;
        if (!string.equals("Portfolio") && !DataManager.isGroupAlias((String)string)) {
            string2 = string;
        }
        boolean bl4 = !string2.equals(ConstantAll);
        int n = string2.hashCode();
        boolean bl5 = by != 0;
        boolean bl6 = by2 != 127;
        for (int i = 0; i < this.size(); ++i) {
            Order order = (Order)this.list.get(i);
            if (!bl4 ? order.IsInPortfolio == 0 : order == null || order.SetupName == null || order.SetupName.hashCode() != n) continue;
            if (bl5 && order.isLong() && by == -1 || order.isShort() && by == 1) continue;
            if (bl6) {
                if (by2 == 10) {
                    if (order.SampleType != 10 && order.SampleType != 11 && (order.SampleType < 40 || order.SampleType > 50)) {
                        continue;
                    }
                } else if (by2 == 40) {
                    if (order.SampleType < 40 || order.SampleType > 50) {
                        continue;
                    }
                } else if (by2 != 20 ? by2 != order.SampleType : order.SampleType < 20 || order.SampleType > 30) continue;
            }
            if (bl && !order.isFilledOrder() || bl3 && !order.isRealOrder()) continue;
            if (bl2) {
                ordersList.add(new Order(order));
                continue;
            }
            ordersList.add(order);
        }
        return ordersList;
    }

    public boolean isEmpty() {
        return this.list.isEmpty();
    }

    public OrdersList clone() {
        OrdersList ordersList = new OrdersList(String.format("%s.cloned", this.identifier));
        ordersList.addAll(this);
        return ordersList;
    }

    public OrdersList cloneDeep() {
        OrdersList ordersList = new OrdersList(String.format("%s.cloned", this.identifier));
        for (int i = 0; i < this.size(); ++i) {
            Order order = this.get(i);
            ordersList.add(new Order(order));
        }
        return ordersList;
    }

    public void remove(int n) {
        this.list.remove(n);
    }

    @Override
    public void writeExternal(ObjectOutput objectOutput) throws IOException {
        this.serialize(objectOutput);
    }

    @Override
    public void readExternal(ObjectInput objectInput) throws IOException, ClassNotFoundException {
        this.deserialize(objectInput);
    }

    public void serialize(ObjectOutput objectOutput) throws IOException {
        Order order;
        objectOutput.writeUTF(String.format("%s%d", ORDER_FILE_FORMAT, 11));
        objectOutput.writeInt(0);
        objectOutput.writeInt(0);
        objectOutput.writeInt(0);
        objectOutput.writeInt(0);
        objectOutput.writeInt(0);
        objectOutput.writeInt(0);
        objectOutput.writeInt(1);
        Int2ObjectOpenHashMap int2ObjectOpenHashMap = new Int2ObjectOpenHashMap();
        for (int i = 0; i < this.size(); ++i) {
            order = this.get(i);
            this.prepareStringsCache(order, (Int2ObjectOpenHashMap<String>)int2ObjectOpenHashMap);
        }
        Int2ByteOpenHashMap int2ByteOpenHashMap = this.writeStringCache(objectOutput, (Int2ObjectOpenHashMap<String>)int2ObjectOpenHashMap);
        for (int i = 0; i < this.size(); ++i) {
            order = this.get(i);
            this.writeOrderFormat8(objectOutput, order, (Int2ObjectOpenHashMap<String>)int2ObjectOpenHashMap, int2ByteOpenHashMap);
        }
        objectOutput.flush();
    }

    private Int2ByteOpenHashMap writeStringCache(ObjectOutput objectOutput, Int2ObjectOpenHashMap<String> int2ObjectOpenHashMap) throws IOException {
        objectOutput.writeInt(int2ObjectOpenHashMap.size());
        Int2ByteOpenHashMap int2ByteOpenHashMap = null;
        if (int2ObjectOpenHashMap.size() < 120) {
            int2ByteOpenHashMap = new Int2ByteOpenHashMap();
            Int2ObjectMap.FastEntrySet fastEntrySet = int2ObjectOpenHashMap.int2ObjectEntrySet();
            byte by = 1;
            for (Int2ObjectMap.Entry entry : fastEntrySet) {
                int2ByteOpenHashMap.put(entry.getIntKey(), by);
                by = (byte)(by + 1);
                objectOutput.writeUTF((String)entry.getValue());
            }
        } else {
            Int2ObjectMap.FastEntrySet fastEntrySet = int2ObjectOpenHashMap.int2ObjectEntrySet();
            for (Int2ObjectMap.Entry entry : fastEntrySet) {
                objectOutput.writeInt(entry.getIntKey());
                objectOutput.writeUTF((String)entry.getValue());
            }
        }
        return int2ByteOpenHashMap;
    }

    private void prepareStringsCache(Order order, Int2ObjectOpenHashMap<String> int2ObjectOpenHashMap) {
        int n;
        if (order.Symbol != null && !int2ObjectOpenHashMap.containsKey(n = SQUtils.betterHashCode((String)order.Symbol))) {
            int2ObjectOpenHashMap.put(n, (Object)order.Symbol);
        }
        if (order.SetupName != null && !int2ObjectOpenHashMap.containsKey(n = SQUtils.betterHashCode((String)order.SetupName))) {
            int2ObjectOpenHashMap.put(n, (Object)order.SetupName);
        }
        if (order.StrategyName != null && !int2ObjectOpenHashMap.containsKey(n = SQUtils.betterHashCode((String)order.StrategyName))) {
            int2ObjectOpenHashMap.put(n, (Object)order.StrategyName);
        }
        if (order.Comment != null && !int2ObjectOpenHashMap.containsKey(n = SQUtils.betterHashCode((String)order.Comment))) {
            int2ObjectOpenHashMap.put(n, (Object)order.Comment);
        }
    }

    private void writeOrderFormat8(ObjectOutput objectOutput, Order order, Int2ObjectOpenHashMap<String> int2ObjectOpenHashMap, Int2ByteOpenHashMap int2ByteOpenHashMap) throws IOException {
        this.writeUTFUsingMap(objectOutput, order.Symbol, int2ObjectOpenHashMap, int2ByteOpenHashMap);
        this.writeUTFUsingMap(objectOutput, order.SetupName, int2ObjectOpenHashMap, int2ByteOpenHashMap);
        this.writeUTFUsingMap(objectOutput, order.StrategyName, int2ObjectOpenHashMap, int2ByteOpenHashMap);
        this.writeUTFUsingMap(objectOutput, order.Comment, int2ObjectOpenHashMap, int2ByteOpenHashMap);
        objectOutput.writeInt(order.Ticket);
        objectOutput.writeInt(order.Order);
        objectOutput.writeByte(order.Type);
        objectOutput.writeByte(order.CloseType);
        objectOutput.writeByte(order.SampleType);
        objectOutput.writeLong(order.OriginalOpenTime);
        objectOutput.writeByte(order.OriginalType);
        objectOutput.writeFloat(order.Size);
        objectOutput.writeFloat(order.OriginalPrice);
        objectOutput.writeLong(order.OpenTime);
        objectOutput.writeFloat(order.OpenPrice);
        objectOutput.writeLong(order.CloseTime);
        objectOutput.writeFloat(order.ClosePrice);
        objectOutput.writeFloat(order.StopLoss);
        objectOutput.writeFloat(order.TakeProfit);
        objectOutput.writeShort(order.BarsInTrade);
        objectOutput.writeFloat(order.PL);
        objectOutput.writeFloat(order.PctPL);
        objectOutput.writeFloat(order.PctPL_TWR);
        objectOutput.writeFloat(order.PipsPL);
        objectOutput.writeFloat(order.DD);
        objectOutput.writeFloat(order.PctDD);
        objectOutput.writeFloat(order.PipsDD);
        objectOutput.writeFloat(order.CommSwap);
        objectOutput.writeBoolean(order.CommSwapApplied);
        objectOutput.writeFloat(order.MAE);
        objectOutput.writeFloat(order.PipsMAE);
        objectOutput.writeFloat(order.MFE);
        objectOutput.writeFloat(order.PipsMFE);
        objectOutput.writeInt(order.Duration);
        objectOutput.writeFloat(order.AccountBalance);
        objectOutput.writeFloat(order.PctAccountBalance);
        objectOutput.writeFloat(order.PipsAccountBalance);
        objectOutput.writeInt(order.MagicNumber);
        objectOutput.writeByte(order.IsInPortfolio);
        objectOutput.writeFloat(order.Extra1);
        objectOutput.writeFloat(order.SlippageInMoney);
        objectOutput.writeByte(order.ExitIndex);
        objectOutput.writeFloat(order.ATROnOpen);
    }

    private void writeUTFUsingMap(ObjectOutput objectOutput, String string, Int2ObjectOpenHashMap<String> int2ObjectOpenHashMap, Int2ByteOpenHashMap int2ByteOpenHashMap) throws IOException {
        if (int2ByteOpenHashMap == null) {
            if (string == null) {
                objectOutput.writeInt(0);
            } else {
                objectOutput.writeInt(SQUtils.betterHashCode((String)string));
            }
        } else if (string == null) {
            objectOutput.writeByte(0);
        } else {
            objectOutput.writeByte(int2ByteOpenHashMap.get(SQUtils.betterHashCode((String)string)));
        }
    }

    public void deserialize(ObjectInput objectInput) throws IOException {
        if (objectInput.available() > 0) {
            String string = objectInput.readUTF();
            int n = string.startsWith(ORDER_FILE_FORMAT) ? Integer.parseInt(string.replace(ORDER_FILE_FORMAT, "")) : 0;
            int[] nArray = new int[7];
            if (n >= 10) {
                for (int i = 0; i < 7; ++i) {
                    nArray[i] = objectInput.readInt();
                }
            }
            if (n >= 5) {
                this.loadOrdersUsingFormat10(objectInput, string, n, nArray);
            } else {
                this.loadOrdersUsingPreviousFormats(objectInput, string, n);
            }
        }
    }

    private void loadOrdersUsingFormat10(ObjectInput objectInput, String string, int n, int[] nArray) throws IOException {
        int n2 = objectInput.readInt();
        Int2ObjectOpenHashMap int2ObjectOpenHashMap = null;
        Byte2ObjectOpenHashMap byte2ObjectOpenHashMap = null;
        if (n2 < 120) {
            byte2ObjectOpenHashMap = new Byte2ObjectOpenHashMap();
            for (int i = 0; i < n2; ++i) {
                String string2 = this.intern(objectInput.readUTF());
                byte2ObjectOpenHashMap.put((byte)(i + 1), (Object)string2);
            }
        } else {
            int2ObjectOpenHashMap = new Int2ObjectOpenHashMap();
            for (int i = 0; i < n2; ++i) {
                int n3 = objectInput.readInt();
                String string3 = this.intern(objectInput.readUTF());
                int2ObjectOpenHashMap.put(n3, (Object)string3);
            }
        }
        while (objectInput.available() > 0) {
            Order order = n >= 7 ? this.loadOrderFormat10(objectInput, (Int2ObjectOpenHashMap<String>)int2ObjectOpenHashMap, (Byte2ObjectOpenHashMap<String>)byte2ObjectOpenHashMap, n, nArray) : this.loadOrderFormat5(objectInput, (Int2ObjectOpenHashMap<String>)int2ObjectOpenHashMap, (Byte2ObjectOpenHashMap<String>)byte2ObjectOpenHashMap, n);
            if (n < 9) {
                order.CommSwap = -order.CommSwap;
            }
            if (order.SampleType == 20) {
                order.SampleType = (byte)21;
            }
            this.add(order);
            string = null;
        }
    }

    private Order loadOrderFormat10(ObjectInput objectInput, Int2ObjectOpenHashMap<String> int2ObjectOpenHashMap, Byte2ObjectOpenHashMap<String> byte2ObjectOpenHashMap, int n, int[] nArray) throws IOException {
        Order order = new Order();
        order.Symbol = this.readUTFUsingMap(objectInput, int2ObjectOpenHashMap, byte2ObjectOpenHashMap);
        order.SetupName = this.readUTFUsingMap(objectInput, int2ObjectOpenHashMap, byte2ObjectOpenHashMap);
        order.StrategyName = this.readUTFUsingMap(objectInput, int2ObjectOpenHashMap, byte2ObjectOpenHashMap);
        order.Comment = this.readUTFUsingMap(objectInput, int2ObjectOpenHashMap, byte2ObjectOpenHashMap);
        order.Ticket = objectInput.readInt();
        order.Order = objectInput.readInt();
        order.Type = objectInput.readByte();
        order.CloseType = objectInput.readByte();
        order.SampleType = objectInput.readByte();
        order.OriginalOpenTime = objectInput.readLong();
        order.OriginalType = objectInput.readByte();
        order.Size = objectInput.readFloat();
        order.OriginalPrice = objectInput.readFloat();
        order.OpenTime = objectInput.readLong();
        order.OpenPrice = objectInput.readFloat();
        order.CloseTime = objectInput.readLong();
        order.ClosePrice = objectInput.readFloat();
        order.StopLoss = objectInput.readFloat();
        order.TakeProfit = objectInput.readFloat();
        order.BarsInTrade = objectInput.readShort();
        order.PL = objectInput.readFloat();
        order.PctPL = objectInput.readFloat();
        order.PctPL_TWR = objectInput.readFloat();
        order.PipsPL = objectInput.readFloat();
        order.DD = objectInput.readFloat();
        order.PctDD = objectInput.readFloat();
        order.PipsDD = objectInput.readFloat();
        order.CommSwap = objectInput.readFloat();
        order.CommSwapApplied = objectInput.readBoolean();
        order.MAE = objectInput.readFloat();
        order.PipsMAE = objectInput.readFloat();
        order.MFE = objectInput.readFloat();
        order.PipsMFE = objectInput.readFloat();
        objectInput.readInt();
        order.Duration = this.getDuration(order);
        order.AccountBalance = objectInput.readFloat();
        order.PctAccountBalance = objectInput.readFloat();
        order.PipsAccountBalance = objectInput.readFloat();
        order.MagicNumber = objectInput.readInt();
        order.IsInPortfolio = objectInput.readByte();
        order.Extra1 = objectInput.readFloat();
        order.SlippageInMoney = objectInput.readFloat();
        if (n >= 8) {
            order.ExitIndex = objectInput.readByte();
        }
        if (n >= 10 && n >= 10) {
            this.readAdditionalData(n, 0, nArray, objectInput, order, int2ObjectOpenHashMap, byte2ObjectOpenHashMap);
            this.readAdditionalData(n, 1, nArray, objectInput, order, int2ObjectOpenHashMap, byte2ObjectOpenHashMap);
            this.readAdditionalData(n, 2, nArray, objectInput, order, int2ObjectOpenHashMap, byte2ObjectOpenHashMap);
            this.readAdditionalData(n, 3, nArray, objectInput, order, int2ObjectOpenHashMap, byte2ObjectOpenHashMap);
            this.readAdditionalData(n, 4, nArray, objectInput, order, int2ObjectOpenHashMap, byte2ObjectOpenHashMap);
            this.readAdditionalData(n, 5, nArray, objectInput, order, int2ObjectOpenHashMap, byte2ObjectOpenHashMap);
            this.readAdditionalData(n, 6, nArray, objectInput, order, int2ObjectOpenHashMap, byte2ObjectOpenHashMap);
        }
        return order;
    }

    private void readAdditionalData(int n, int n2, int[] nArray, ObjectInput objectInput, Order order, Int2ObjectOpenHashMap<String> int2ObjectOpenHashMap, Byte2ObjectOpenHashMap<String> byte2ObjectOpenHashMap) throws IOException {
        for (int i = 0; i < nArray[n2]; ++i) {
            if (n2 == 0) {
                this.readUTFUsingMap(objectInput, int2ObjectOpenHashMap, byte2ObjectOpenHashMap);
                continue;
            }
            if (n2 == 1) {
                objectInput.readByte();
                continue;
            }
            if (n2 == 2) {
                objectInput.readInt();
                continue;
            }
            if (n2 == 3) {
                objectInput.readLong();
                continue;
            }
            if (n2 == 4) {
                objectInput.readBoolean();
                continue;
            }
            if (n2 == 5) {
                objectInput.readDouble();
                continue;
            }
            if (n2 == 6) {
                if (i == 0) {
                    order.ATROnOpen = objectInput.readFloat();
                    continue;
                }
                objectInput.readFloat();
                continue;
            }
            throw new IOException("Unrecognized index: " + n2);
        }
    }

    private Order loadOrderFormat5(ObjectInput objectInput, Int2ObjectOpenHashMap<String> int2ObjectOpenHashMap, Byte2ObjectOpenHashMap<String> byte2ObjectOpenHashMap, int n) throws IOException {
        Order order = new Order();
        order.Symbol = this.readUTFUsingMap(objectInput, int2ObjectOpenHashMap, byte2ObjectOpenHashMap);
        order.SetupName = this.readUTFUsingMap(objectInput, int2ObjectOpenHashMap, byte2ObjectOpenHashMap);
        order.StrategyName = this.readUTFUsingMap(objectInput, int2ObjectOpenHashMap, byte2ObjectOpenHashMap);
        order.Comment = this.readUTFUsingMap(objectInput, int2ObjectOpenHashMap, byte2ObjectOpenHashMap);
        order.Ticket = objectInput.readInt();
        order.Order = objectInput.readInt();
        order.Type = objectInput.readByte();
        order.CloseType = objectInput.readByte();
        order.SampleType = objectInput.readByte();
        order.OriginalOpenTime = objectInput.readLong();
        order.OriginalType = objectInput.readByte();
        order.Size = (float)objectInput.readDouble();
        order.OriginalPrice = (float)objectInput.readDouble();
        order.OpenTime = objectInput.readLong();
        order.OpenPrice = (float)objectInput.readDouble();
        order.CloseTime = objectInput.readLong();
        order.ClosePrice = (float)objectInput.readDouble();
        order.StopLoss = (float)objectInput.readDouble();
        order.TakeProfit = (float)objectInput.readDouble();
        order.BarsInTrade = objectInput.readShort();
        order.PL = objectInput.readFloat();
        order.PctPL = objectInput.readFloat();
        order.PctPL_TWR = objectInput.readFloat();
        order.PipsPL = objectInput.readFloat();
        order.DD = objectInput.readFloat();
        order.PctDD = objectInput.readFloat();
        order.PipsDD = objectInput.readFloat();
        order.CommSwap = objectInput.readFloat();
        order.CommSwapApplied = objectInput.readBoolean();
        order.MAE = objectInput.readFloat();
        objectInput.readFloat();
        order.PipsMAE = objectInput.readFloat();
        order.MFE = objectInput.readFloat();
        objectInput.readFloat();
        order.PipsMFE = objectInput.readFloat();
        objectInput.readInt();
        order.Duration = this.getDuration(order);
        order.AccountBalance = objectInput.readFloat();
        order.PctAccountBalance = objectInput.readFloat();
        order.PipsAccountBalance = objectInput.readFloat();
        objectInput.readFloat();
        order.MagicNumber = objectInput.readInt();
        order.IsInPortfolio = objectInput.readByte();
        order.Extra1 = objectInput.readFloat();
        if (n == 6) {
            order.SlippageInMoney = objectInput.readFloat();
        }
        return order;
    }

    private String readUTFUsingMap(ObjectInput objectInput, Int2ObjectOpenHashMap<String> int2ObjectOpenHashMap, Byte2ObjectOpenHashMap<String> byte2ObjectOpenHashMap) throws IOException {
        if (byte2ObjectOpenHashMap == null) {
            int n = objectInput.readInt();
            if (n == 0) {
                return null;
            }
            return (String)int2ObjectOpenHashMap.get(n);
        }
        byte by = objectInput.readByte();
        if (by == 0) {
            return null;
        }
        return (String)byte2ObjectOpenHashMap.get(by);
    }

    private void loadOrdersUsingPreviousFormats(ObjectInput objectInput, String string, int n) throws IOException {
        while (objectInput.available() > 0) {
            Order order = this.loadOrder(objectInput, string, n);
            this.add(order);
            string = null;
        }
    }

    private Order loadOrder(ObjectInput objectInput, String string, int n) throws IOException {
        if (n == 4) {
            return this.loadOrderFormat4(objectInput);
        }
        if (n == 3) {
            return this.loadOrderFormat3(objectInput);
        }
        if (n == 2) {
            return this.loadOrderFormat2(objectInput);
        }
        return this.loadOrderFormat01(objectInput, string, n);
    }

    private Order loadOrderFormat4(ObjectInput objectInput) throws IOException {
        Order order = new Order();
        order.Symbol = this.readUTF(objectInput);
        order.SetupName = this.readUTF(objectInput);
        order.StrategyName = this.readUTF(objectInput);
        order.Comment = this.readUTF(objectInput);
        order.Ticket = objectInput.readInt();
        order.Order = objectInput.readInt();
        order.Type = objectInput.readByte();
        order.CloseType = objectInput.readByte();
        order.SampleType = objectInput.readByte();
        order.OriginalOpenTime = objectInput.readLong();
        order.OriginalType = objectInput.readByte();
        order.Size = (float)objectInput.readDouble();
        order.OriginalPrice = (float)objectInput.readDouble();
        order.OpenTime = objectInput.readLong();
        order.OpenPrice = (float)objectInput.readDouble();
        order.CloseTime = objectInput.readLong();
        order.ClosePrice = (float)objectInput.readDouble();
        order.StopLoss = (float)objectInput.readDouble();
        order.TakeProfit = (float)objectInput.readDouble();
        order.BarsInTrade = objectInput.readShort();
        order.PL = objectInput.readFloat();
        order.PctPL = objectInput.readFloat();
        order.PctPL_TWR = objectInput.readFloat();
        order.PipsPL = objectInput.readFloat();
        order.DD = objectInput.readFloat();
        order.PctDD = objectInput.readFloat();
        order.PipsDD = objectInput.readFloat();
        order.CommSwap = objectInput.readFloat();
        order.CommSwapApplied = objectInput.readBoolean();
        order.MAE = objectInput.readFloat();
        objectInput.readFloat();
        order.PipsMAE = objectInput.readFloat();
        order.MFE = objectInput.readFloat();
        objectInput.readFloat();
        order.PipsMFE = objectInput.readFloat();
        objectInput.readInt();
        order.Duration = this.getDuration(order);
        order.AccountBalance = objectInput.readFloat();
        order.PctAccountBalance = objectInput.readFloat();
        order.PipsAccountBalance = objectInput.readFloat();
        objectInput.readFloat();
        order.MagicNumber = objectInput.readInt();
        order.IsInPortfolio = objectInput.readByte();
        order.Extra1 = objectInput.readFloat();
        return order;
    }

    private String readUTF(ObjectInput objectInput) throws IOException {
        byte by = objectInput.readByte();
        if (by == 0) {
            return null;
        }
        String string = this.intern(objectInput.readUTF());
        return string;
    }

    private Order loadOrderFormat3(ObjectInput objectInput) throws IOException {
        Order order = new Order();
        order.Symbol = this.intern(objectInput.readUTF());
        order.SetupName = this.intern(objectInput.readUTF());
        order.StrategyName = this.intern(objectInput.readUTF());
        order.Comment = this.intern(objectInput.readUTF());
        order.Ticket = objectInput.readInt();
        order.Order = objectInput.readInt();
        order.Type = objectInput.readByte();
        order.CloseType = objectInput.readByte();
        order.SampleType = objectInput.readByte();
        order.OriginalOpenTime = objectInput.readLong();
        order.OriginalType = objectInput.readByte();
        order.Size = (float)objectInput.readDouble();
        order.OriginalPrice = (float)objectInput.readDouble();
        order.OpenTime = objectInput.readLong();
        order.OpenPrice = (float)objectInput.readDouble();
        order.CloseTime = objectInput.readLong();
        order.ClosePrice = (float)objectInput.readDouble();
        order.StopLoss = (float)objectInput.readDouble();
        order.TakeProfit = (float)objectInput.readDouble();
        order.BarsInTrade = objectInput.readShort();
        order.PL = objectInput.readFloat();
        order.PctPL = objectInput.readFloat();
        order.PctPL_TWR = objectInput.readFloat();
        order.PipsPL = objectInput.readFloat();
        order.DD = objectInput.readFloat();
        order.PctDD = objectInput.readFloat();
        order.PipsDD = objectInput.readFloat();
        order.CommSwap = objectInput.readFloat();
        order.CommSwapApplied = objectInput.readBoolean();
        order.MAE = objectInput.readFloat();
        objectInput.readFloat();
        order.PipsMAE = objectInput.readFloat();
        order.MFE = objectInput.readFloat();
        objectInput.readFloat();
        order.PipsMFE = objectInput.readFloat();
        objectInput.readInt();
        order.Duration = this.getDuration(order);
        order.AccountBalance = objectInput.readFloat();
        order.PctAccountBalance = objectInput.readFloat();
        order.PipsAccountBalance = objectInput.readFloat();
        objectInput.readFloat();
        order.MagicNumber = objectInput.readInt();
        order.IsInPortfolio = objectInput.readByte();
        order.Extra1 = objectInput.readFloat();
        objectInput.readFloat();
        objectInput.readFloat();
        objectInput.readUTF();
        return order;
    }

    private Order loadOrderFormat2(ObjectInput objectInput) throws IOException {
        Order order = new Order();
        order.Symbol = this.intern(objectInput.readUTF());
        order.SetupName = this.intern(objectInput.readUTF());
        order.StrategyName = this.intern(objectInput.readUTF());
        order.Comment = this.intern(objectInput.readUTF());
        order.Ticket = objectInput.readInt();
        order.Order = objectInput.readInt();
        order.Type = objectInput.readByte();
        order.CloseType = objectInput.readByte();
        order.SampleType = objectInput.readByte();
        order.OriginalOpenTime = objectInput.readLong();
        order.OriginalType = objectInput.readByte();
        order.Size = (float)objectInput.readDouble();
        order.OriginalPrice = (float)objectInput.readDouble();
        order.OpenTime = objectInput.readLong();
        order.OpenPrice = (float)objectInput.readDouble();
        order.CloseTime = objectInput.readLong();
        order.ClosePrice = (float)objectInput.readDouble();
        order.StopLoss = (float)objectInput.readDouble();
        order.TakeProfit = (float)objectInput.readDouble();
        order.BarsInTrade = objectInput.readShort();
        order.PL = objectInput.readFloat();
        order.PctPL = objectInput.readFloat();
        order.PctPL_TWR = objectInput.readFloat();
        order.PipsPL = objectInput.readFloat();
        order.DD = objectInput.readFloat();
        order.PctDD = objectInput.readFloat();
        order.PipsDD = objectInput.readFloat();
        order.CommSwap = objectInput.readFloat();
        order.CommSwapApplied = objectInput.readBoolean();
        order.MAE = objectInput.readFloat();
        objectInput.readFloat();
        order.PipsMAE = objectInput.readFloat();
        order.MFE = objectInput.readFloat();
        objectInput.readFloat();
        order.PipsMFE = objectInput.readFloat();
        objectInput.readInt();
        order.Duration = this.getDuration(order);
        order.AccountBalance = objectInput.readFloat();
        order.PctAccountBalance = objectInput.readFloat();
        order.PipsAccountBalance = objectInput.readFloat();
        objectInput.readFloat();
        order.MagicNumber = objectInput.readInt();
        order.IsInPortfolio = objectInput.readByte();
        return order;
    }

    private Order loadOrderFormat01(ObjectInput objectInput, String string, int n) throws IOException {
        Order order = new Order();
        order.Symbol = n == 0 && string != null ? string : this.intern(objectInput.readUTF());
        order.SetupName = this.intern(objectInput.readUTF());
        order.StrategyName = this.intern(objectInput.readUTF());
        order.Comment = this.intern(objectInput.readUTF());
        order.Ticket = objectInput.readInt();
        order.Order = objectInput.readInt();
        order.Type = objectInput.readByte();
        order.CloseType = objectInput.readByte();
        order.SampleType = objectInput.readByte();
        order.OriginalOpenTime = objectInput.readLong();
        order.OriginalType = objectInput.readByte();
        order.Size = (float)objectInput.readDouble();
        order.OriginalPrice = (float)objectInput.readDouble();
        order.OpenTime = objectInput.readLong();
        order.OpenPrice = (float)objectInput.readDouble();
        order.CloseTime = objectInput.readLong();
        order.ClosePrice = (float)objectInput.readDouble();
        order.StopLoss = (float)objectInput.readDouble();
        order.TakeProfit = (float)objectInput.readDouble();
        order.BarsInTrade = objectInput.readShort();
        order.PL = (float)objectInput.readDouble();
        order.PctPL = (float)objectInput.readDouble();
        order.PctPL_TWR = (float)objectInput.readDouble();
        order.PipsPL = (float)objectInput.readDouble();
        order.DD = (float)objectInput.readDouble();
        order.PctDD = (float)objectInput.readDouble();
        order.PipsDD = (float)objectInput.readDouble();
        order.CommSwap = (float)objectInput.readDouble();
        order.CommSwapApplied = objectInput.readBoolean();
        order.MAE = (float)objectInput.readDouble();
        objectInput.readDouble();
        order.PipsMAE = (float)objectInput.readDouble();
        order.MFE = (float)objectInput.readDouble();
        objectInput.readDouble();
        order.PipsMFE = (float)objectInput.readDouble();
        objectInput.readLong();
        order.Duration = this.getDuration(order);
        order.AccountBalance = (float)objectInput.readDouble();
        order.PctAccountBalance = (float)objectInput.readDouble();
        order.PipsAccountBalance = (float)objectInput.readDouble();
        objectInput.readDouble();
        order.Extra1 = (float)objectInput.readDouble();
        objectInput.readDouble();
        objectInput.readDouble();
        objectInput.readDouble();
        objectInput.readDouble();
        objectInput.readUTF();
        objectInput.readUTF();
        objectInput.readUTF();
        if (n > 0) {
            order.MagicNumber = objectInput.readInt();
        }
        return order;
    }

    private String intern(String string) {
        return string != null ? string.intern() : null;
    }

    private int getDuration(Order order) {
        long l = (order.CloseTime - order.OpenTime) / 1000L;
        return (int)(l < Integer.MAX_VALUE ? l : Integer.MAX_VALUE);
    }

    public boolean contains(Order order) {
        return this.list.contains((Object)order);
    }

    public void sort(Comparator<Order> comparator) {
        this.list.sort(comparator);
    }

    public void removeEndOfTest() {
        ObjectListIterator objectListIterator = this.list.iterator();
        while (objectListIterator.hasNext()) {
            Order order = (Order)objectListIterator.next();
            if (order.CloseType != 4) continue;
            objectListIterator.remove();
        }
    }

    public void removeById(long l) {
        ObjectListIterator objectListIterator = this.list.iterator();
        while (objectListIterator.hasNext()) {
            Order order = (Order)objectListIterator.next();
            if (order.OrderId != l) continue;
            objectListIterator.remove();
        }
    }
}

