/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib;

import com.strategyquant.tradinglib.BlockDefinitionException;

public class Editors {
    public static final int RecognizeByType = 0;
    public static final int Spinner = 10;
    public static final int SpinnerWithVariables = 20;
    public static final int Editbox = 30;
    public static final int Selection = 40;
    public static final int SelectionWithVariables = 50;
    public static final int SelectionSymbols = 60;
    public static final int SelectionSymbolsWithAny = 70;
    public static final int SelectionVariables = 80;
    public static final int SelectionVariablesWithAny = 90;
    public static final int BooleanVariables = 100;
    public static final int Time = 110;
    public static final String WizardSpinner = "jspinner";
    public static final String WizardSpinnerVar = "jspinnerVar";
    public static final String WizardEditbox = "editbox";
    public static final String WizardCombo = "combo";
    public static final String WizardSymbolVar = "symbolVar";
    public static final String WizardSymbolVarWithAny = "symbolVarWithAny";
    public static final String WizardComboVar = "comboVar";
    public static final String WizardComboVarWithAny = "comboVarWithAny";
    public static final String WizardBooleanVar = "booleanVar";
    public static final int Formula = 200;

    public static String convertToWizardConstant(int n) throws BlockDefinitionException {
        switch (n) {
            case 10: {
                return WizardSpinner;
            }
            case 20: {
                return WizardSpinnerVar;
            }
            case 30: {
                return WizardEditbox;
            }
            case 40: {
                return WizardCombo;
            }
            case 50: {
                return WizardComboVar;
            }
            case 60: {
                return WizardSymbolVar;
            }
            case 70: {
                return WizardSymbolVarWithAny;
            }
            case 80: {
                return WizardComboVar;
            }
            case 90: {
                return WizardComboVarWithAny;
            }
            case 100: {
                return WizardBooleanVar;
            }
            case 110: {
                return "Time";
            }
            case 200: {
                return "Formula";
            }
        }
        throw new BlockDefinitionException("Unknowd parameter editor type: " + n);
    }

    public static String convertTimeToHHMM(String string) {
        if (string.equals("NaN")) {
            return "0000";
        }
        int n = Integer.parseInt(string);
        int n2 = n / 3600;
        int n3 = (n - n2 * 3600) / 60;
        return String.format("%02d%02d", n2, n3);
    }
}

