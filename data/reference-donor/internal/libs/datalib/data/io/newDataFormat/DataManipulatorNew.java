/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.lib.crypting.AESCrypterDecrypter
 *  com.strategyquant.lib.historyData.ICryptable
 */
package com.strategyquant.datalib.data.io.newDataFormat;

import com.strategyquant.datalib.InstrumentInfo;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.lib.crypting.AESCrypterDecrypter;
import com.strategyquant.lib.historyData.ICryptable;
import java.io.UnsupportedEncodingException;
import java.security.InvalidAlgorithmParameterException;
import java.security.InvalidKeyException;
import java.security.NoSuchAlgorithmException;
import java.security.spec.InvalidKeySpecException;
import java.security.spec.InvalidParameterSpecException;
import javax.crypto.NoSuchPaddingException;

public abstract class DataManipulatorNew
implements ICryptable {
    public static final String HEADER_PREFIX = "ABCDEFGH";
    public static final String HEADER_SUFFIX = "SnRbTs";
    public static final String CRYPTED_DATA_TYPE = "C";
    public static final String DATA_TYPE = "D";
    public static final String SUPPORTED_OLD_VERSION = "4.1";
    public static final String VERSION = "4.2";
    private AESCrypterDecrypter crypterDecrypter;
    private boolean crypted;
    private String password;

    protected byte[] encryptModificators(byte[] byArray) throws Exception {
        this.ensureCrypterDecrypter();
        byte[] byArray2 = this.crypterDecrypter.encrypt(byArray);
        return byArray2;
    }

    protected byte[] decryptModificators(byte[] byArray) throws Exception {
        this.ensureCrypterDecrypter();
        byte[] byArray2 = this.crypterDecrypter.decrypt(byArray);
        return byArray2;
    }

    public boolean isCrypted() {
        return this.crypted;
    }

    protected void setCrypted(boolean bl) {
        this.crypted = bl;
    }

    public static void setDecimals(InstrumentInfo instrumentInfo, DataManipulatorNew dataManipulatorNew) {
        if (instrumentInfo != null && (instrumentInfo.instrument.equals("ZF") || instrumentInfo.instrument.equals("ZF - CBOT")) && instrumentInfo.dataType == 2) {
            dataManipulatorNew.overrideDecimals(7);
        } else if (instrumentInfo != null && instrumentInfo.dataType == 7) {
            dataManipulatorNew.overrideDecimals(8);
        }
    }

    private void ensureCrypterDecrypter() throws InvalidKeyException, NoSuchAlgorithmException, UnsupportedEncodingException, InvalidKeySpecException, NoSuchPaddingException, InvalidParameterSpecException, InvalidAlgorithmParameterException {
        if (this.crypterDecrypter == null) {
            this.crypterDecrypter = new AESCrypterDecrypter(this.getPassword());
        }
    }

    private String getPassword() {
        if (this.password != null) {
            return this.password;
        }
        return MainApp.v571hfnsHw().eHvc2JguAd();
    }

    public void setPassword(String string) {
        this.password = string;
    }

    public abstract void overrideDecimals(int var1);
}

