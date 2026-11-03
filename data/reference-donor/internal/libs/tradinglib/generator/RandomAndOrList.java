/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.IRandomGenerator
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.generator;

import com.strategyquant.lib.IRandomGenerator;
import com.strategyquant.tradinglib.generator.GenerateException;
import com.strategyquant.tradinglib.generator.RandomAndOr;
import java.util.ArrayList;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

class RandomAndOrList
extends ArrayList<RandomAndOr> {
    public static final Logger Log = LoggerFactory.getLogger((String)"RandomAndOrList");

    RandomAndOrList() {
    }

    void setRAO(int n, String string) {
        int n2 = string.hashCode();
        for (RandomAndOr randomAndOr : this) {
            if (randomAndOr.id != 0 && randomAndOr.id != n2 || randomAndOr.type != -1) continue;
            randomAndOr.type = n;
        }
    }

    String getGeneratedKey(int n) {
        for (RandomAndOr randomAndOr : this) {
            if (randomAndOr.type != 1 || randomAndOr.id != n) continue;
            return randomAndOr.key;
        }
        return null;
    }

    void fixValues() {
        for (RandomAndOr randomAndOr : this) {
            if (randomAndOr.type == -1) {
                randomAndOr.type = 1;
                continue;
            }
            if (randomAndOr.type != 2 || this.checkRandomIdExistsInList(randomAndOr.id)) continue;
            randomAndOr.type = 1;
        }
    }

    private boolean checkRandomIdExistsInList(int n) {
        for (RandomAndOr randomAndOr : this) {
            if (randomAndOr.id != n || randomAndOr.type != 1) continue;
            return true;
        }
        return false;
    }

    void replaceValues(int n, IRandomGenerator iRandomGenerator, String string) throws GenerateException {
        for (RandomAndOr randomAndOr : this) {
            if (n == 1) {
                if (randomAndOr.type != 1) continue;
                randomAndOr.key = iRandomGenerator.nextInt(2) == 0 ? "AND" : "OR";
                randomAndOr.elRnd.setAttribute("key", randomAndOr.key);
            } else {
                if (randomAndOr.type != 2) continue;
                String string2 = this.getGeneratedKey(randomAndOr.id);
                if (string2 == null) {
                    throw new GenerateException("This shouldn't happen!");
                }
                randomAndOr.elRnd.setAttribute("key", string2);
            }
            randomAndOr.elRnd.setAttribute("generated", string);
        }
    }
}

