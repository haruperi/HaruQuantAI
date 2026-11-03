/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib;

public class CustomCellFormat {
    public static final String ValuePositive = "value-positive";
    public static final String ValueNegative = "value-negative";
    public static final String BackgroundOOS = "background-oos";
    public String textStyle;
    public String backgroundStyle;
    public String customStyle;

    public String getHtmlContent(Object object) {
        String string = object + "";
        if (this.customStyle != null && (this.textStyle != null || this.backgroundStyle != null)) {
            string = this.textStyle != null ? this.textStyle + "," : "";
            string = string + (this.backgroundStyle != null ? this.backgroundStyle + "," : "");
            string = "<div class='" + (string.isEmpty() ? string : string.substring(0, string.length() - 1)) + "' style='" + this.customStyle + "'>" + object + "</div>";
        } else if (this.customStyle != null) {
            string = "<div style='" + this.customStyle + "'>" + object + "</div>";
        } else if (this.textStyle != null || this.backgroundStyle != null) {
            string = this.textStyle != null ? this.textStyle + "," : "";
            string = string + (this.backgroundStyle != null ? this.backgroundStyle + "," : "");
            string = "<div class='" + (string.isEmpty() ? string : string.substring(0, string.length() - 1)) + "'>" + object + "</div>";
        }
        return string;
    }

    public void reset() {
        this.textStyle = null;
        this.backgroundStyle = null;
        this.customStyle = null;
    }
}

