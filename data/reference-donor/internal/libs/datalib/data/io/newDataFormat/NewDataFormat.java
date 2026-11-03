/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib.data.io.newDataFormat;

import com.strategyquant.datalib.data.io.newDataFormat.IRandomAccessReader;
import java.io.DataOutputStream;

public class NewDataFormat {
    public static final double OLD_VOLUME_CONSTANT = 100.0;
    public static final double VOLUME_CONSTANT = 100000.0;
    public static final int BLOCK_LENGTH = 1000;
    protected static final int MAGIC_SIZE = 15;
    public static final int BYTE = 0;
    public static final int SHORT = 1;
    public static final int INT = 2;
    public static final int LONG = 3;
    public static final int MINUS = 0;
    public static final int PLUS = 1;
    public static final int ASIS = 2;
    protected boolean start = true;
    protected double decimalsConstant;
    protected double volumeConstant;
    private int decimals;
    private boolean forceOldFormat;

    public NewDataFormat(boolean bl) {
        this.overrideDecimals(6);
        this.volumeConstant = 100000.0;
        this.start = true;
        this.forceOldFormat = bl;
    }

    public void overrideDecimals(int n) {
        this.decimals = n;
        this.decimalsConstant = Math.pow(10.0, n);
    }

    public void setVolumeConstant(double d) {
        this.volumeConstant = d;
    }

    protected boolean isForceOldFormat() {
        return this.forceOldFormat;
    }

    public void reset() {
        this.start = true;
    }

    public static int getDataType(long l) {
        long l2 = l = l >= 0L ? l : -l;
        if (l < 256L) {
            return 0;
        }
        if (l < 65536L) {
            return 1;
        }
        if (l < 0x100000000L) {
            return 2;
        }
        return 3;
    }

    public static int getLogicType(long l) {
        if (l < 0L) {
            return 0;
        }
        return 1;
    }

    public static void printBits(byte by) {
        String string = String.format("%8s", Integer.toBinaryString(by & 0xFF)).replace(' ', '0');
        System.out.println(string);
    }

    protected byte[] getConfigBytes(int[] nArray, int[] nArray2) throws Exception {
        byte[] byArray = new byte[nArray.length / 2];
        for (int i = nArray.length - 1; i >= 0; --i) {
            int n = i / 2;
            boolean bl = i % 2 == 0;
            int n2 = bl ? i + 1 : i - 1;
            int n3 = n;
            byArray[n3] = (byte)(byArray[n3] | nArray[n2]);
            int n4 = n;
            byArray[n4] = (byte)(byArray[n4] << 2);
            int n5 = n;
            byArray[n5] = (byte)(byArray[n5] | nArray2[n2]);
            if (bl) continue;
            int n6 = n;
            byArray[n6] = (byte)(byArray[n6] << 2);
        }
        return byArray;
    }

    protected void writeValue(DataOutputStream dataOutputStream, long l, int n) throws Exception {
        if (l < 0L) {
            l = -l;
        }
        switch (n) {
            case 0: {
                dataOutputStream.write((byte)l);
                break;
            }
            case 1: {
                dataOutputStream.writeShort((int)l);
                break;
            }
            case 2: {
                dataOutputStream.writeInt((int)l);
                break;
            }
            case 3: {
                dataOutputStream.writeLong(l);
                break;
            }
            default: {
                throw new Exception("Invalid data type of value " + n);
            }
        }
    }

    protected final long getValue(IRandomAccessReader iRandomAccessReader, int n) throws Exception {
        switch (n) {
            case 0: {
                return iRandomAccessReader.readByte() & 0xFF;
            }
            case 1: {
                return iRandomAccessReader.readShort() & 0xFFFF;
            }
            case 2: {
                return (long)iRandomAccessReader.readInt() & 0xFFFFFFFFL;
            }
            case 3: {
                return iRandomAccessReader.readLong();
            }
        }
        throw new Exception("Unknown data type of value " + n);
    }

    protected int getBitValue(byte[] byArray, int n) {
        if (this.start) {
            this.start = false;
        } else {
            int n2 = n;
            byArray[n2] = (byte)(byArray[n2] >> 2);
        }
        return byArray[n] & 3;
    }

    public int getDecimals() {
        return this.decimals;
    }
}

