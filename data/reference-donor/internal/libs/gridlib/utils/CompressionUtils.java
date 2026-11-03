/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.gridlib.utils;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.util.zip.DataFormatException;
import java.util.zip.Deflater;
import java.util.zip.Inflater;

public class CompressionUtils {
    public static byte[] compress(byte[] byArray) throws IOException {
        Deflater deflater = new Deflater();
        deflater.setLevel(9);
        deflater.setInput(byArray);
        try (ByteArrayOutputStream byteArrayOutputStream = new ByteArrayOutputStream(byArray.length);){
            byte[] byArray2;
            deflater.finish();
            byte[] byArray3 = new byte[1024];
            while (!deflater.finished()) {
                int n = deflater.deflate(byArray3);
                byteArrayOutputStream.write(byArray3, 0, n);
            }
            byteArrayOutputStream.close();
            byte[] byArray4 = byArray2 = byteArrayOutputStream.toByteArray();
            return byArray4;
        }
    }

    public static byte[] decompress(byte[] byArray) throws IOException, DataFormatException {
        Inflater inflater = new Inflater();
        inflater.setInput(byArray);
        try (ByteArrayOutputStream byteArrayOutputStream = new ByteArrayOutputStream(byArray.length);){
            byte[] byArray2;
            byte[] byArray3 = new byte[10240];
            while (!inflater.finished()) {
                int n = inflater.inflate(byArray3);
                byteArrayOutputStream.write(byArray3, 0, n);
            }
            byteArrayOutputStream.close();
            byte[] byArray4 = byArray2 = byteArrayOutputStream.toByteArray();
            return byArray4;
        }
    }
}

