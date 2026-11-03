/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.app.MainApp
 *  org.json.JSONArray
 *  org.json.JSONObject
 */
package com.strategyquant.datalib.metatrader4;

import com.strategyquant.datalib.metatrader4.Mt4SymbolProperties;
import com.strategyquant.lib.app.MainApp;
import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.UncheckedIOException;
import java.nio.charset.Charset;
import java.nio.charset.CharsetDecoder;
import java.nio.charset.CodingErrorAction;
import java.nio.file.Files;
import java.nio.file.OpenOption;
import java.nio.file.Paths;
import java.util.Collections;
import java.util.HashMap;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;
import java.util.stream.Stream;
import org.json.JSONArray;
import org.json.JSONObject;

public class Mt4Properties {
    private Map<String, Mt4SymbolProperties> values = new HashMap<String, Mt4SymbolProperties>();
    private static final String PropertiesPath = MainApp.getDataPath() + "//user//settings//DataConfig//mt4.properties";

    public Mt4Properties() throws IOException {
        this(PropertiesPath);
    }

    public Mt4Properties(String string) throws IOException {
        try {
            this.readPropetiesFileCommon(string);
        }
        catch (IOException | UncheckedIOException exception) {
            this.readPropertiesFileIgnoreInvalidCharacters(string);
        }
    }

    private void readPropetiesFileCommon(String string2) throws IOException {
        try (Stream<String> stream = Files.lines(Paths.get(string2, new String[0]));){
            stream.forEach(string -> this.storeLine((String)string));
        }
    }

    private void readPropertiesFileIgnoreInvalidCharacters(String string) throws IOException {
        Charset charset = Charset.forName("UTF-8");
        CharsetDecoder charsetDecoder = charset.newDecoder();
        charsetDecoder.onMalformedInput(CodingErrorAction.IGNORE);
        charsetDecoder.onUnmappableCharacter(CodingErrorAction.IGNORE);
        try (BufferedReader bufferedReader = new BufferedReader(new InputStreamReader(Files.newInputStream(Paths.get(string, new String[0]), new OpenOption[0]), charsetDecoder));){
            List list = bufferedReader.lines().collect(Collectors.toList());
            for (String string2 : list) {
                this.storeLine(string2);
            }
        }
    }

    private void storeLine(String string) {
        int n = string.indexOf("_");
        if (n == -1) {
            return;
        }
        String string2 = string.substring(0, n);
        String string3 = string.substring(string2.length() + 1);
        String[] stringArray = string3.split("=");
        if (stringArray.length == 2) {
            Mt4SymbolProperties mt4SymbolProperties = this.values.get(string2);
            if (mt4SymbolProperties == null) {
                mt4SymbolProperties = new Mt4SymbolProperties();
                this.values.put(string2, mt4SymbolProperties);
            }
            mt4SymbolProperties.put(stringArray[0].toLowerCase(), stringArray[1]);
        }
    }

    public JSONArray toJSON() {
        JSONArray jSONArray = new JSONArray();
        LinkedList<String> linkedList = new LinkedList<String>(this.values.keySet());
        Collections.sort(linkedList);
        for (String string : linkedList) {
            Mt4SymbolProperties mt4SymbolProperties = this.values.get(string);
            JSONObject jSONObject = new JSONObject();
            jSONObject.put("symbol", (Object)string);
            jSONObject.put("properties", (Object)mt4SymbolProperties.toJSON());
            jSONArray.put((Object)jSONObject);
        }
        return jSONArray;
    }

    public String findBySymbol(String string) throws Exception {
        if (!this.values.containsKey(string)) {
            throw new Exception(String.format("Symbol '%s' properties not found in '%s'", string, PropertiesPath));
        }
        return this.values.get(string).toString();
    }
}

