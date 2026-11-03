/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.portfolioMaster;

import java.math.BigInteger;

public class PortfolioMasterUtils {
    public static BigInteger calculateMaxNumberOfPortfolios(int n, int n2, int n3) {
        BigInteger bigInteger = BigInteger.valueOf(0L);
        for (int i = n2; i <= n3; ++i) {
            bigInteger = bigInteger.add(PortfolioMasterUtils.fact(n).divide(PortfolioMasterUtils.fact(n - i).multiply(PortfolioMasterUtils.fact(i))));
        }
        return bigInteger;
    }

    private static BigInteger fact(int n) {
        return PortfolioMasterUtils.factorialBig(n);
    }

    private static BigInteger factorialBig(int n) {
        BigInteger bigInteger = BigInteger.ONE;
        for (int i = 1; i <= n; ++i) {
            bigInteger = bigInteger.multiply(BigInteger.valueOf(i));
        }
        return bigInteger;
    }
}

