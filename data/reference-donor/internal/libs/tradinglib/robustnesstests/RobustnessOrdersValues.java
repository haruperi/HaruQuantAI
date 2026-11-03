/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.robustnesstests;

import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.util.jar.JarOutputStream;

public class RobustnessOrdersValues {
    private int[] arr;
    private int size;

    public RobustnessOrdersValues(int n) {
        this.size = n;
        this.arr = new int[this.size];
    }

    public RobustnessOrdersValues(InputStream inputStream) throws IOException {
        DataInputStream dataInputStream = new DataInputStream(inputStream);
        this.size = dataInputStream.readInt();
        if (this.size > 0) {
            this.arr = new int[this.size];
            byte[] byArray = new byte[this.size * 4];
            byArray = dataInputStream.readAllBytes();
            for (int i = 0; i < this.size; ++i) {
                this.arr[i] = this.convertByteArrayToInt(new byte[]{byArray[i * 4], byArray[i * 4 + 1], byArray[i * 4 + 2], byArray[i * 4 + 3]});
            }
        }
        dataInputStream.close();
    }

    private int convertByteArrayToInt(byte[] byArray) {
        if (byArray == null || byArray.length != 4) {
            return 0;
        }
        return (0xFF & byArray[0]) << 24 | (0xFF & byArray[1]) << 16 | (0xFF & byArray[2]) << 8 | (0xFF & byArray[3]) << 0;
    }

    public int size() {
        return this.size;
    }

    public int[] arr() {
        return this.arr;
    }

    public void set(int n, double d) {
        if (n < 0) {
            throw new IllegalArgumentException("Index must be bigget than zero.");
        }
        if (n > this.arr.length - 1) {
            throw new IllegalArgumentException("Index is bigger than array size, have you initialized it properly?");
        }
        this.arr[n] = (int)(d * 100.0);
    }

    public void saveOrderValuesToFile(JarOutputStream jarOutputStream) throws IOException {
        DataOutputStream dataOutputStream = new DataOutputStream(jarOutputStream);
        dataOutputStream.writeInt(this.size);
        if (this.size > 0) {
            byte[] byArray = new byte[this.size * 4];
            for (int i = 0; i < this.size; ++i) {
                System.arraycopy(this.convertIntToByteArray(this.arr[i]), 0, byArray, i * 4, 4);
            }
            dataOutputStream.write(byArray);
        }
    }

    private byte[] convertIntToByteArray(int n) {
        return new byte[]{(byte)(n >> 24 & 0xFF), (byte)(n >> 16 & 0xFF), (byte)(n >> 8 & 0xFF), (byte)(n >> 0 & 0xFF)};
    }

    public RobustnessOrdersValues clone() {
        RobustnessOrdersValues robustnessOrdersValues = new RobustnessOrdersValues(this.size());
        for (int i = 0; i < this.arr.length; ++i) {
            robustnessOrdersValues.arr[i] = this.arr[i];
        }
        return robustnessOrdersValues;
    }
}

