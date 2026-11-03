/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.wizard.desktop.utils;

import java.io.BufferedReader;
import java.io.DataOutputStream;
import java.io.IOException;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;

public class JsonUtils {
    public static String getErrorResonse(String string) {
        return "\"result\":\"error\",\"errors\":{\"message\":" + string + "}";
    }

    public static String doPost(String string, String string2) throws IOException {
        String string3;
        URL uRL = new URL(string);
        HttpURLConnection httpURLConnection = (HttpURLConnection)uRL.openConnection();
        httpURLConnection.setRequestMethod("POST");
        httpURLConnection.setRequestProperty("Content-Type", "application/x-www-form-urlencoded");
        httpURLConnection.setRequestProperty("Content-Length", String.valueOf(string2.length()));
        httpURLConnection.setDoOutput(true);
        DataOutputStream dataOutputStream = new DataOutputStream(httpURLConnection.getOutputStream());
        dataOutputStream.writeBytes(string2);
        dataOutputStream.flush();
        dataOutputStream.close();
        BufferedReader bufferedReader = new BufferedReader(new InputStreamReader(httpURLConnection.getInputStream(), StandardCharsets.UTF_8));
        StringBuffer stringBuffer = new StringBuffer();
        while ((string3 = bufferedReader.readLine()) != null) {
            stringBuffer.append(string3);
        }
        bufferedReader.close();
        return stringBuffer.toString();
    }

    public static String doGet(String string) throws IOException {
        String string2;
        URL uRL = new URL(string);
        HttpURLConnection httpURLConnection = (HttpURLConnection)uRL.openConnection();
        httpURLConnection.setRequestMethod("GET");
        httpURLConnection.setRequestProperty("User-Agent", "");
        BufferedReader bufferedReader = new BufferedReader(new InputStreamReader(httpURLConnection.getInputStream()));
        StringBuffer stringBuffer = new StringBuffer();
        while ((string2 = bufferedReader.readLine()) != null) {
            stringBuffer.append(string2);
        }
        bufferedReader.close();
        return stringBuffer.toString();
    }
}

