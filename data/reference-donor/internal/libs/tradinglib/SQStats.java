/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.settings.IXMLAble
 *  com.strategyquant.lib.utils.ISQCloneable
 *  it.unimi.dsi.fastutil.ints.Int2FloatOpenHashMap
 *  it.unimi.dsi.fastutil.ints.Int2IntOpenHashMap
 *  it.unimi.dsi.fastutil.ints.Int2LongOpenHashMap
 *  it.unimi.dsi.fastutil.ints.Int2ObjectMap$Entry
 *  it.unimi.dsi.fastutil.ints.Int2ObjectMap$FastEntrySet
 *  it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap
 *  it.unimi.dsi.fastutil.ints.IntIterator
 *  it.unimi.dsi.fastutil.ints.IntSet
 *  org.apache.commons.codec.binary.Base64
 *  org.jdom2.Attribute
 *  org.jdom2.DataConversionException
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib;

import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.settings.IXMLAble;
import com.strategyquant.lib.utils.ISQCloneable;
import com.strategyquant.tradinglib.results.StatsKeyCache;
import it.unimi.dsi.fastutil.ints.Int2FloatOpenHashMap;
import it.unimi.dsi.fastutil.ints.Int2IntOpenHashMap;
import it.unimi.dsi.fastutil.ints.Int2LongOpenHashMap;
import it.unimi.dsi.fastutil.ints.Int2ObjectMap;
import it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap;
import it.unimi.dsi.fastutil.ints.IntIterator;
import it.unimi.dsi.fastutil.ints.IntSet;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.IOException;
import java.io.ObjectInput;
import java.io.ObjectOutput;
import java.util.List;
import java.util.Map;
import org.apache.commons.codec.binary.Base64;
import org.jdom2.Attribute;
import org.jdom2.DataConversionException;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class SQStats
implements IXMLAble,
ISQCloneable<SQStats> {
    public static final Logger Log = LoggerFactory.getLogger((String)"SQStats");
    private int[] intValues = new int[StatsKeyCache.getIntsCount()];
    private float[] doubleValues = new float[StatsKeyCache.getDoublesCount()];
    private long[] longValues = new long[StatsKeyCache.getLongsCount()];
    private Int2IntOpenHashMap unknownIntsMap = null;
    private Int2FloatOpenHashMap unknownDoublesMap = null;
    private Int2LongOpenHashMap unknownLongsMap = null;
    private Int2ObjectOpenHashMap<Object> objectMap = null;

    public void set(String string, int n) {
        StatsKeyCache.StatInfo statInfo = StatsKeyCache.getKey(string);
        if (statInfo != null) {
            switch (statInfo.type) {
                case 1: {
                    this.intValues[statInfo.index] = n;
                    return;
                }
                case 3: {
                    this.doubleValues[statInfo.index] = n;
                    return;
                }
                case 2: {
                    this.longValues[statInfo.index] = n;
                    return;
                }
            }
            throw new IllegalArgumentException("Shouldn't get here!");
        }
        int n2 = StatsKeyCache.registerKey(string, (byte)1);
        if (this.unknownIntsMap == null) {
            this.unknownIntsMap = new Int2IntOpenHashMap();
        }
        this.unknownIntsMap.put(n2, n);
    }

    public void set(String string, Object object) {
        int n = StatsKeyCache.registerKey(string, (byte)4);
        if (this.objectMap == null) {
            this.objectMap = new Int2ObjectOpenHashMap();
        }
        this.objectMap.put(n, object);
    }

    public void set(String string, long l) {
        StatsKeyCache.StatInfo statInfo = StatsKeyCache.getKey(string);
        if (statInfo != null) {
            switch (statInfo.type) {
                case 1: {
                    this.intValues[statInfo.index] = (int)l;
                    return;
                }
                case 3: {
                    this.doubleValues[statInfo.index] = l;
                    return;
                }
                case 2: {
                    this.longValues[statInfo.index] = l;
                    return;
                }
            }
            throw new IllegalArgumentException("Shouldn't get here!");
        }
        int n = StatsKeyCache.registerKey(string, (byte)2);
        if (this.unknownLongsMap == null) {
            this.unknownLongsMap = new Int2LongOpenHashMap();
        }
        this.unknownLongsMap.put(n, l);
    }

    public void set(String string, double d) {
        StatsKeyCache.StatInfo statInfo = StatsKeyCache.getKey(string);
        if (statInfo != null) {
            switch (statInfo.type) {
                case 1: {
                    this.intValues[statInfo.index] = (int)d;
                    return;
                }
                case 3: {
                    this.doubleValues[statInfo.index] = (float)d;
                    return;
                }
                case 2: {
                    this.longValues[statInfo.index] = (long)d;
                    return;
                }
            }
            throw new IllegalArgumentException("Shouldn't get here!");
        }
        int n = StatsKeyCache.registerKey(string, (byte)3);
        if (this.unknownDoublesMap == null) {
            this.unknownDoublesMap = new Int2FloatOpenHashMap();
        }
        this.unknownDoublesMap.put(n, (float)d);
    }

    public int getInt(String string) {
        return this.getInt(string, 0);
    }

    public int getInt(String string, int n) {
        StatsKeyCache.StatInfo statInfo = StatsKeyCache.getKey(string);
        if (statInfo != null) {
            switch (statInfo.type) {
                case 1: {
                    return this.intValues[statInfo.index];
                }
                case 3: {
                    return (int)this.doubleValues[statInfo.index];
                }
                case 2: {
                    return (int)this.longValues[statInfo.index];
                }
            }
            throw new IllegalArgumentException("Shouldn't get here!");
        }
        int n2 = string.hashCode();
        if (this.unknownIntsMap != null && this.unknownIntsMap.containsKey(n2)) {
            return this.unknownIntsMap.get(n2);
        }
        if (this.unknownDoublesMap != null && this.unknownDoublesMap.containsKey(n2)) {
            return (int)this.unknownDoublesMap.get(n2);
        }
        if (this.unknownLongsMap != null && this.unknownLongsMap.containsKey(n2)) {
            return (int)this.unknownLongsMap.get(n2);
        }
        return n;
    }

    public long getLong(String string) {
        return this.getLong(string, 0L);
    }

    public long getLong(String string, long l) {
        StatsKeyCache.StatInfo statInfo = StatsKeyCache.getKey(string);
        if (statInfo != null) {
            switch (statInfo.type) {
                case 1: {
                    return this.intValues[statInfo.index];
                }
                case 3: {
                    return (long)this.doubleValues[statInfo.index];
                }
                case 2: {
                    return this.longValues[statInfo.index];
                }
            }
            throw new IllegalArgumentException("Shouldn't get here!");
        }
        int n = string.hashCode();
        if (this.unknownLongsMap != null && this.unknownLongsMap.containsKey(n)) {
            return this.unknownLongsMap.get(n);
        }
        if (this.unknownDoublesMap != null && this.unknownDoublesMap.containsKey(n)) {
            return (long)this.unknownDoublesMap.get(n);
        }
        if (this.unknownIntsMap != null && this.unknownIntsMap.containsKey(n)) {
            return this.unknownIntsMap.get(n);
        }
        return l;
    }

    public double getDouble(String string) {
        return this.getDouble(string, 0.0);
    }

    public double getDouble(String string, double d) {
        StatsKeyCache.StatInfo statInfo = StatsKeyCache.getKey(string);
        if (statInfo != null) {
            switch (statInfo.type) {
                case 1: {
                    return this.intValues[statInfo.index];
                }
                case 3: {
                    return this.doubleValues[statInfo.index];
                }
                case 2: {
                    return this.longValues[statInfo.index];
                }
            }
            throw new IllegalArgumentException("Shouldn't get here!");
        }
        int n = string.hashCode();
        if (this.unknownDoublesMap != null && this.unknownDoublesMap.containsKey(n)) {
            return this.unknownDoublesMap.get(n);
        }
        if (this.unknownIntsMap != null && this.unknownIntsMap.containsKey(n)) {
            return this.unknownIntsMap.get(n);
        }
        if (this.unknownLongsMap != null && this.unknownLongsMap.containsKey(n)) {
            return this.unknownLongsMap.get(n);
        }
        return d;
    }

    public Element getXML() {
        try {
            return this.getXMLOptimizedFormat();
        }
        catch (IOException iOException) {
            Log.error("Error loading stats", (Throwable)iOException);
            return null;
        }
    }

    public void setFromXML(Element element) {
        if (element == null) {
            return;
        }
        this.clearData();
        String string = element.getAttributeValue("e");
        if (string == null) {
            this.loadUsingOldFormat(element);
        } else {
            try {
                this.loadUsingOptimizedFormat(element);
            }
            catch (IOException iOException) {
                Log.error("Error loading stats", (Throwable)iOException);
            }
        }
    }

    private void loadUsingOptimizedFormat(Element element) throws IOException {
        String string = element.getText();
        int n = 1;
        String string2 = element.getAttributeValue("version");
        if (string2 != null) {
            n = Integer.parseInt(string2);
        }
        DataInputStream dataInputStream = new DataInputStream(new ByteArrayInputStream(Base64.decodeBase64((String)string)));
        block8: while (dataInputStream.available() > 0) {
            byte by = dataInputStream.readByte();
            switch (by) {
                case 1: {
                    byte by2 = dataInputStream.readByte();
                    this.intValues[by2] = dataInputStream.readInt();
                    continue block8;
                }
                case 3: {
                    byte by2 = dataInputStream.readByte();
                    if (n > 1) {
                        this.doubleValues[by2] = dataInputStream.readFloat();
                        continue block8;
                    }
                    this.doubleValues[by2] = (float)dataInputStream.readDouble();
                    continue block8;
                }
                case 2: {
                    byte by2 = dataInputStream.readByte();
                    this.longValues[by2] = dataInputStream.readLong();
                    continue block8;
                }
                case 101: {
                    String string3 = dataInputStream.readUTF();
                    this.set(string3, dataInputStream.readInt());
                    continue block8;
                }
                case 103: {
                    String string3 = dataInputStream.readUTF();
                    if (n > 1) {
                        this.set(string3, dataInputStream.readFloat());
                        continue block8;
                    }
                    this.set(string3, dataInputStream.readDouble());
                    continue block8;
                }
                case 102: {
                    String string3 = dataInputStream.readUTF();
                    this.set(string3, dataInputStream.readLong());
                    continue block8;
                }
            }
            throw new IllegalArgumentException("Shouldn't get here!");
        }
    }

    private void loadUsingOldFormat(Element element) {
        Object object;
        List list = element.getAttributes();
        block15: for (int i = 0; i < list.size(); ++i) {
            Attribute attribute = (Attribute)list.get(i);
            String string = attribute.getName();
            object = StatsKeyCache.getShortKey(string.hashCode());
            if (object == null) continue;
            switch (((StatsKeyCache.StatInfo)object).type) {
                case 1: {
                    this.intValues[((StatsKeyCache.StatInfo)object).index] = (int)this.getAttrValue(attribute, 1);
                    continue block15;
                }
                case 3: {
                    this.doubleValues[((StatsKeyCache.StatInfo)object).index] = (float)this.getAttrValue(attribute, 3);
                    continue block15;
                }
                case 2: {
                    this.longValues[((StatsKeyCache.StatInfo)object).index] = (long)this.getAttrValue(attribute, 2);
                    continue block15;
                }
                default: {
                    throw new IllegalArgumentException("This shouldn't happen!");
                }
            }
        }
        block16: for (Attribute attribute : element.getChildren()) {
            String string = attribute.getName();
            if (attribute.getContentSize() <= 0) continue;
            object = attribute.getAttributeValue("type");
            if (object == null) {
                throw new IllegalArgumentException("Unknown type '" + (String)object + "'!");
            }
            switch (object) {
                case "Integer": {
                    this.set(string, Integer.parseInt(attribute.getValue()));
                    continue block16;
                }
                case "Long": {
                    this.set(string, Long.parseLong(attribute.getValue()));
                    continue block16;
                }
                case "Double": {
                    this.set(string, Double.parseDouble(attribute.getValue()));
                    continue block16;
                }
            }
            this.set(string, attribute.getValue());
        }
    }

    private double getAttrValue(Attribute attribute, int n) {
        try {
            switch (n) {
                case 1: {
                    return attribute.getIntValue();
                }
                case 3: {
                    return attribute.getDoubleValue();
                }
                case 2: {
                    return attribute.getLongValue();
                }
            }
            throw new IllegalArgumentException("Shouldn't get here!");
        }
        catch (DataConversionException dataConversionException) {
            try {
                return attribute.getDoubleValue();
            }
            catch (DataConversionException dataConversionException2) {
                return -1.23456789E8;
            }
        }
    }

    public void clearData() {
        int n3;
        for (n3 = 0; n3 < this.intValues.length; ++n3) {
            this.intValues[n3] = 0;
        }
        for (n3 = 0; n3 < this.doubleValues.length; ++n3) {
            this.doubleValues[n3] = 0.0f;
        }
        for (n3 = 0; n3 < this.longValues.length; ++n3) {
            this.longValues[n3] = 0L;
        }
        if (this.unknownIntsMap != null) {
            this.unknownIntsMap.replaceAll((n, n2) -> 0);
        }
        if (this.unknownDoublesMap != null) {
            this.unknownDoublesMap.replaceAll((n, f) -> Float.valueOf(0.0f));
        }
        if (this.unknownLongsMap != null) {
            this.unknownLongsMap.replaceAll((n, l) -> 0L);
        }
    }

    public void copyValuesFrom(SQStats sQStats) {
        int n;
        for (n = 0; n < this.intValues.length; ++n) {
            this.intValues[n] = sQStats.intValues[n];
        }
        for (n = 0; n < this.doubleValues.length; ++n) {
            this.doubleValues[n] = sQStats.doubleValues[n];
        }
        for (n = 0; n < this.longValues.length; ++n) {
            this.longValues[n] = sQStats.longValues[n];
        }
        if (sQStats.unknownIntsMap != null) {
            if (this.unknownIntsMap == null) {
                this.unknownIntsMap = new Int2IntOpenHashMap();
            }
            this.unknownIntsMap.putAll((Map)sQStats.unknownIntsMap);
        }
        if (sQStats.unknownIntsMap != null) {
            if (this.unknownIntsMap == null) {
                this.unknownIntsMap = new Int2IntOpenHashMap();
            }
            this.unknownIntsMap.putAll((Map)sQStats.unknownIntsMap);
        }
        if (sQStats.unknownDoublesMap != null) {
            if (this.unknownDoublesMap == null) {
                this.unknownDoublesMap = new Int2FloatOpenHashMap();
            }
            this.unknownDoublesMap.putAll((Map)sQStats.unknownDoublesMap);
        }
        if (sQStats.unknownLongsMap != null) {
            if (this.unknownLongsMap == null) {
                this.unknownLongsMap = new Int2LongOpenHashMap();
            }
            this.unknownLongsMap.putAll((Map)sQStats.unknownLongsMap);
        }
    }

    public void copyValueFrom(SQStats sQStats, String string) {
        StatsKeyCache.StatInfo statInfo = StatsKeyCache.getKey(string);
        if (statInfo != null) {
            switch (statInfo.type) {
                case 1: {
                    this.intValues[statInfo.index] = sQStats.intValues[statInfo.index];
                    return;
                }
                case 3: {
                    this.doubleValues[statInfo.index] = sQStats.doubleValues[statInfo.index];
                    return;
                }
                case 2: {
                    this.longValues[statInfo.index] = sQStats.longValues[statInfo.index];
                    return;
                }
            }
            throw new IllegalArgumentException("Shouldn't get here!");
        }
        int n = StatsKeyCache.registerKey(string, (byte)4);
        if (this.unknownDoublesMap != null && this.unknownDoublesMap.containsKey(n) || sQStats.unknownDoublesMap != null && sQStats.unknownDoublesMap.containsKey(n)) {
            if (this.unknownDoublesMap == null) {
                this.unknownDoublesMap = new Int2FloatOpenHashMap();
            }
            this.unknownDoublesMap.put(n, (float)sQStats.getDouble(string));
            return;
        }
        if (this.unknownIntsMap != null && this.unknownIntsMap.containsKey(n) || sQStats.unknownIntsMap != null && sQStats.unknownIntsMap.containsKey(n)) {
            if (this.unknownIntsMap == null) {
                this.unknownIntsMap = new Int2IntOpenHashMap();
            }
            this.unknownIntsMap.put(n, sQStats.getInt(string));
            return;
        }
        if (this.unknownLongsMap != null && this.unknownLongsMap.containsKey(n) || sQStats.unknownLongsMap != null && sQStats.unknownLongsMap.containsKey(n)) {
            if (this.unknownLongsMap == null) {
                this.unknownLongsMap = new Int2LongOpenHashMap();
            }
            this.unknownLongsMap.put(n, sQStats.getLong(string));
            return;
        }
        if (Log.isDebugEnabled()) {
            // empty if block
        }
    }

    public boolean containsKey(String string) {
        StatsKeyCache.StatInfo statInfo = StatsKeyCache.getKey(string);
        if (statInfo != null) {
            return true;
        }
        int n = string.hashCode();
        if (this.unknownDoublesMap != null && this.unknownDoublesMap.containsKey(n)) {
            return true;
        }
        if (this.unknownIntsMap != null && this.unknownIntsMap.containsKey(n)) {
            return true;
        }
        return this.unknownLongsMap != null && this.unknownLongsMap.containsKey(n);
    }

    public SQStats getClone() throws Exception {
        int n;
        SQStats sQStats = new SQStats();
        for (n = 0; n < this.intValues.length; ++n) {
            sQStats.intValues[n] = this.intValues[n];
        }
        for (n = 0; n < this.doubleValues.length; ++n) {
            sQStats.doubleValues[n] = this.doubleValues[n];
        }
        for (n = 0; n < this.longValues.length; ++n) {
            sQStats.longValues[n] = this.longValues[n];
        }
        if (this.unknownIntsMap != null) {
            if (sQStats.unknownIntsMap == null) {
                sQStats.unknownIntsMap = new Int2IntOpenHashMap();
            }
            sQStats.unknownIntsMap.putAll((Map)this.unknownIntsMap);
        }
        if (this.unknownDoublesMap != null) {
            if (sQStats.unknownDoublesMap == null) {
                sQStats.unknownDoublesMap = new Int2FloatOpenHashMap();
            }
            sQStats.unknownDoublesMap.putAll((Map)this.unknownDoublesMap);
        }
        if (this.unknownLongsMap != null) {
            if (sQStats.unknownLongsMap == null) {
                sQStats.unknownLongsMap = new Int2LongOpenHashMap();
            }
            sQStats.unknownLongsMap.putAll((Map)this.unknownLongsMap);
        }
        if (this.objectMap != null) {
            IntIterator intIterator = this.objectMap.keySet().iterator();
            while (intIterator.hasNext()) {
                Object object;
                int n2 = (Integer)intIterator.next();
                Object object2 = this.objectMap.get(n2);
                if (object2 == null || (object = SQUtils.cloneObject((Object)object2)) == null) continue;
                if (sQStats.objectMap == null) {
                    sQStats.objectMap = new Int2ObjectOpenHashMap();
                }
                sQStats.objectMap.put(n2, object);
            }
        }
        return sQStats;
    }

    public Element getXMLOptimizedFormat() throws IOException {
        String string;
        Element element = new Element("SQStats");
        element.setAttribute("version", "2");
        ByteArrayOutputStream byteArrayOutputStream = new ByteArrayOutputStream();
        DataOutputStream dataOutputStream = new DataOutputStream(byteArrayOutputStream);
        block5: for (Int2ObjectMap.Entry entry : StatsKeyCache.defaultKeysMap.int2ObjectEntrySet()) {
            StatsKeyCache.StatInfo statInfo = (StatsKeyCache.StatInfo)entry.getValue();
            switch (statInfo.type) {
                case 1: {
                    dataOutputStream.writeByte(1);
                    dataOutputStream.writeByte(statInfo.index);
                    dataOutputStream.writeInt(this.intValues[statInfo.index]);
                    continue block5;
                }
                case 3: {
                    dataOutputStream.writeByte(3);
                    dataOutputStream.writeByte(statInfo.index);
                    dataOutputStream.writeFloat(this.doubleValues[statInfo.index]);
                    continue block5;
                }
                case 2: {
                    dataOutputStream.writeByte(2);
                    dataOutputStream.writeByte(statInfo.index);
                    dataOutputStream.writeLong(this.longValues[statInfo.index]);
                    continue block5;
                }
            }
            throw new IllegalArgumentException("Shouldn't get here!");
        }
        if (this.unknownIntsMap != null) {
            for (Int2ObjectMap.Entry entry : this.unknownIntsMap.int2IntEntrySet()) {
                int n = entry.getIntKey();
                int n2 = entry.getIntValue();
                dataOutputStream.writeByte(101);
                string = StatsKeyCache.getUnknownKeyName(n);
                dataOutputStream.writeUTF(string);
                dataOutputStream.writeInt(n2);
            }
        }
        if (this.unknownDoublesMap != null) {
            for (Int2ObjectMap.Entry entry : this.unknownDoublesMap.int2FloatEntrySet()) {
                int n = entry.getIntKey();
                float f = entry.getFloatValue();
                dataOutputStream.writeByte(103);
                string = StatsKeyCache.getUnknownKeyName(n);
                dataOutputStream.writeUTF(string);
                dataOutputStream.writeFloat(f);
            }
        }
        if (this.unknownLongsMap != null) {
            for (Int2ObjectMap.Entry entry : this.unknownLongsMap.int2LongEntrySet()) {
                int n = entry.getIntKey();
                long l = entry.getLongValue();
                dataOutputStream.writeByte(102);
                String string2 = StatsKeyCache.getUnknownKeyName(n);
                dataOutputStream.writeUTF(string2);
                dataOutputStream.writeLong(l);
            }
        }
        dataOutputStream.flush();
        String string3 = Base64.encodeBase64String((byte[])byteArrayOutputStream.toByteArray());
        element.setAttribute("e", "b64");
        element.setText(string3);
        return element;
    }

    public void serialize(ObjectOutput objectOutput) throws IOException {
        String string;
        objectOutput.writeInt(2);
        Int2ObjectMap.FastEntrySet fastEntrySet = StatsKeyCache.defaultKeysMap.int2ObjectEntrySet();
        IntSet intSet = this.unknownIntsMap == null ? null : this.unknownIntsMap.keySet();
        IntSet intSet2 = this.unknownDoublesMap == null ? null : this.unknownDoublesMap.keySet();
        IntSet intSet3 = this.unknownLongsMap == null ? null : this.unknownLongsMap.keySet();
        int n = fastEntrySet.size() + (intSet == null ? 0 : intSet.size()) + (intSet2 == null ? 0 : intSet2.size()) + (intSet3 == null ? 0 : intSet3.size());
        objectOutput.writeInt(n);
        block5: for (Int2ObjectMap.Entry entry : fastEntrySet) {
            StatsKeyCache.StatInfo statInfo = (StatsKeyCache.StatInfo)entry.getValue();
            switch (statInfo.type) {
                case 1: {
                    objectOutput.writeByte(1);
                    objectOutput.writeByte(statInfo.index);
                    objectOutput.writeInt(this.intValues[statInfo.index]);
                    continue block5;
                }
                case 3: {
                    objectOutput.writeByte(3);
                    objectOutput.writeByte(statInfo.index);
                    objectOutput.writeFloat(this.doubleValues[statInfo.index]);
                    continue block5;
                }
                case 2: {
                    objectOutput.writeByte(2);
                    objectOutput.writeByte(statInfo.index);
                    objectOutput.writeLong(this.longValues[statInfo.index]);
                    continue block5;
                }
            }
            throw new IllegalArgumentException("Shouldn't get here!");
        }
        if (intSet != null) {
            for (Int2ObjectMap.Entry entry : this.unknownIntsMap.int2IntEntrySet()) {
                int n2 = entry.getIntKey();
                int n3 = entry.getIntValue();
                objectOutput.writeByte(101);
                string = StatsKeyCache.getUnknownKeyName(n2);
                SQUtils.writeUTF((ObjectOutput)objectOutput, (String)string);
                objectOutput.writeInt(n3);
            }
        }
        if (intSet2 != null) {
            for (Int2ObjectMap.Entry entry : this.unknownDoublesMap.int2FloatEntrySet()) {
                int n4 = entry.getIntKey();
                float f = entry.getFloatValue();
                objectOutput.writeByte(103);
                string = StatsKeyCache.getUnknownKeyName(n4);
                SQUtils.writeUTF((ObjectOutput)objectOutput, (String)string);
                objectOutput.writeFloat(f);
            }
        }
        if (intSet3 != null) {
            for (Int2ObjectMap.Entry entry : this.unknownLongsMap.int2LongEntrySet()) {
                int n5 = entry.getIntKey();
                long l = entry.getLongValue();
                objectOutput.writeByte(102);
                String string2 = StatsKeyCache.getUnknownKeyName(n5);
                SQUtils.writeUTF((ObjectOutput)objectOutput, (String)string2);
                objectOutput.writeLong(l);
            }
        }
    }

    public void deserialize(ObjectInput objectInput) throws IOException {
        int n = objectInput.readInt();
        if (n != 1 && n != 2) {
            throw new IllegalArgumentException("Incorrect format " + n);
        }
        int n2 = objectInput.readInt();
        block8: for (int i = 0; i < n2; ++i) {
            byte by = objectInput.readByte();
            switch (by) {
                case 1: {
                    byte by2 = objectInput.readByte();
                    this.intValues[by2] = objectInput.readInt();
                    continue block8;
                }
                case 3: {
                    byte by2 = objectInput.readByte();
                    if (n == 1) {
                        this.doubleValues[by2] = (float)objectInput.readDouble();
                        continue block8;
                    }
                    this.doubleValues[by2] = objectInput.readFloat();
                    continue block8;
                }
                case 2: {
                    byte by2 = objectInput.readByte();
                    this.longValues[by2] = objectInput.readLong();
                    continue block8;
                }
                case 101: {
                    String string = SQUtils.readUTFIntern((ObjectInput)objectInput);
                    this.set(string, objectInput.readInt());
                    continue block8;
                }
                case 103: {
                    String string = SQUtils.readUTFIntern((ObjectInput)objectInput);
                    if (n == 1) {
                        this.set(string, objectInput.readDouble());
                        continue block8;
                    }
                    this.set(string, objectInput.readFloat());
                    continue block8;
                }
                case 102: {
                    String string = SQUtils.readUTFIntern((ObjectInput)objectInput);
                    this.set(string, objectInput.readLong());
                    continue block8;
                }
                default: {
                    throw new IllegalArgumentException("Shouldn't get here!");
                }
            }
        }
    }
}

