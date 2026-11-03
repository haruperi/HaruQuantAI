/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib.indicators;

import java.util.ArrayList;

public class SParametersParser {
    private String input = null;
    public String type = null;
    public ArrayList<InputParameter> list = new ArrayList();
    private static final int STATE_READ_NAME = 1;
    private static final int STATE_WAIT_READ_NEW_VALUE = 2;
    private static final int STATE_READ_VALUE = 3;
    private static final int STATE_READ_STRING_VALUE = 4;

    public SParametersParser(String string) {
        this.input = string;
    }

    public void parse() throws Exception {
        String[] stringArray = this.input.split("[\\s]+");
        if (stringArray.length < 3) {
            throw new Exception("Unknown input(param) definition!");
        }
        this.type = stringArray[1].trim();
        String string = this.input.substring(this.input.indexOf(stringArray[1]) + stringArray[1].length()).trim();
        if (this.type.equalsIgnoreCase("color")) {
            string = string.replaceAll("C'[^C']*'", "Yellow");
        }
        this.parseValues(string);
    }

    private void parseValues(String string) {
        int n = 95;
        int n2 = 1;
        String string2 = "";
        String string3 = null;
        block6: for (int i = 0; i < string.length(); ++i) {
            char c = string.charAt(i);
            switch (n2) {
                case 1: {
                    if (string2 == null && c == ',') continue block6;
                    if (c == '=') {
                        n2 = 2;
                        continue block6;
                    }
                    if (c == ',') {
                        this.list.add(new InputParameter(string2, null));
                        string2 = "";
                        continue block6;
                    }
                    if (string2 == null) {
                        string2 = "";
                    }
                    string2 = string2 + c;
                    continue block6;
                }
                case 2: {
                    if (Character.isWhitespace(c)) continue block6;
                    if (c == '\"') {
                        n2 = 4;
                        continue block6;
                    }
                    string3 = "" + c;
                    n2 = 3;
                    continue block6;
                }
                case 4: {
                    if (c == '\"' && n != 92) {
                        this.list.add(new InputParameter(string2, string3));
                        string2 = null;
                        string3 = null;
                        n2 = 1;
                    } else {
                        if (string3 == null) {
                            string3 = "";
                        }
                        string3 = string3 + c;
                    }
                    n = c;
                    continue block6;
                }
                case 3: {
                    if (c == ',') {
                        this.list.add(new InputParameter(string2, string3));
                        string2 = null;
                        string3 = null;
                        n2 = 1;
                        continue block6;
                    }
                    if (string3 == null) {
                        string3 = "";
                    }
                    string3 = string3 + c;
                }
            }
        }
        if (string2 != null) {
            this.list.add(new InputParameter(string2, string3));
        }
    }

    public class InputParameter {
        public String name = null;
        public String value = null;

        public InputParameter(String string, String string2) {
            this.name = string;
            this.value = string2;
        }
    }
}

