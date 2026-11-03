/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.gridlib.utils;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.io.Serializable;

public class BeanUtils {
    public static byte[] serialize(Object object) throws IOException {
        try (ByteArrayOutputStream byteArrayOutputStream = new ByteArrayOutputStream();){
            ObjectOutputStream objectOutputStream = null;
            objectOutputStream = new ObjectOutputStream(byteArrayOutputStream);
            objectOutputStream.writeObject(object);
            objectOutputStream.flush();
            byte[] byArray = byteArrayOutputStream.toByteArray();
            return byArray;
        }
    }

    /*
     * Enabled aggressive exception aggregation
     */
    public static Serializable deserializeObject(byte[] byArray) throws IOException, ClassNotFoundException {
        try (ByteArrayInputStream byteArrayInputStream = new ByteArrayInputStream(byArray);){
            Serializable serializable;
            try (ObjectInputStream objectInputStream = new ObjectInputStream(byteArrayInputStream);){
                Object object = objectInputStream.readObject();
                serializable = (Serializable)object;
            }
            return serializable;
        }
        catch (Exception exception) {
            exception.printStackTrace();
            throw exception;
        }
    }
}

