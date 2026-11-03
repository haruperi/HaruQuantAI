/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.tradinglib.ResultsGroup
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Task.impl.AutomaticPortfolioBuilder.bruteForce;

import com.strategyquant.plugin.Task.impl.AutomaticPortfolioBuilder.bruteForce.PortfolioMasterComputer;
import com.strategyquant.tradinglib.ResultsGroup;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class PortfolioCombinator {
    public static final Logger Log = LoggerFactory.getLogger((String)"PortfolioCombinator");
    PortfolioMasterComputer computer;
    List<ResultsGroup> results;

    public PortfolioCombinator(PortfolioMasterComputer computer, List<ResultsGroup> results) {
        this.computer = computer;
        this.results = results;
    }

    public void combination(int K) throws Exception {
        int N = this.results.size();
        if (K > N) {
            throw new Exception("Invalid input, K > N");
        }
        int[] combination = new int[K];
        int r = 0;
        int index = 0;
        while (r >= 0) {
            if (index <= N + (r - K)) {
                combination[r] = index++;
                if (r == K - 1) {
                    if (this.computer.isStopped()) {
                        return;
                    }
                    this.computer.computePortfolio(this.cloneCombination(combination));
                    continue;
                }
                index = combination[r] + 1;
                ++r;
                continue;
            }
            if (--r > 0) {
                index = combination[r] + 1;
                continue;
            }
            index = combination[0] + 1;
        }
    }

    private int[] cloneCombination(int[] combination) {
        int[] combinationClone = new int[combination.length];
        for (int c = 0; c < combination.length; ++c) {
            combinationClone[c] = combination[c];
        }
        return combinationClone;
    }
}

