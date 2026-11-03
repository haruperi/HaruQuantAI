/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.gp;

import com.strategyquant.tradinglib.databank.TopStrategiesData;
import com.strategyquant.tradinglib.gp.FitnessCollectionData;
import com.strategyquant.tradinglib.gp.GPFitnessComparator;
import com.strategyquant.tradinglib.gp.GPFitnessEvolutionData;
import com.strategyquant.tradinglib.gp.GPSettings;
import com.strategyquant.tradinglib.gp.IGPNode;
import java.util.ArrayList;
import java.util.Collections;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class GPFitnessEvolution<T extends IGPNode> {
    private static final Logger Log = LoggerFactory.getLogger((String)"GPFitnessEvolution");
    private GPFitnessEvolutionData data;
    private GPSettings<T> gpSettings;
    GPFitnessComparator<T> gpComparatorIS;
    GPFitnessComparator<T> gpComparatorIST;
    GPFitnessComparator<T> gpComparatorISV;
    GPFitnessComparator<T> gpComparatorOOS;

    public GPFitnessEvolution(int n, GPSettings<T> gPSettings) {
        this.gpSettings = gPSettings;
        this.data = new GPFitnessEvolutionData(n, gPSettings.maxGenerations);
        this.gpComparatorIS = new GPFitnessComparator(gPSettings.naturalFitness, 10);
        this.gpComparatorIST = new GPFitnessComparator(gPSettings.naturalFitness, 11);
        this.gpComparatorISV = new GPFitnessComparator(gPSettings.naturalFitness, 40);
        this.gpComparatorOOS = new GPFitnessComparator(gPSettings.naturalFitness, 20);
    }

    public void reset() {
        this.data.reset();
    }

    public void computeFitnessData(ArrayList<T> arrayList, int n) {
        this.data.generation = n;
        if (this.data.generationData[n] == null) {
            this.data.generationData[n] = new FitnessCollectionData(n + 1);
        }
        this.comuteFitnessDataFor((byte)10, arrayList, n);
        this.comuteFitnessDataFor((byte)11, arrayList, n);
        this.comuteFitnessDataFor((byte)40, arrayList, n);
        this.comuteFitnessDataFor((byte)20, arrayList, n);
    }

    private void comuteFitnessDataFor(byte by, ArrayList<T> arrayList, int n) {
        double d = 0.0;
        double d2 = 0.0;
        double d3 = 0.0;
        switch (by) {
            case 10: {
                Collections.sort(arrayList, this.gpComparatorIS);
                break;
            }
            case 11: {
                Collections.sort(arrayList, this.gpComparatorIST);
                break;
            }
            case 40: {
                Collections.sort(arrayList, this.gpComparatorISV);
                break;
            }
            case 20: {
                Collections.sort(arrayList, this.gpComparatorOOS);
            }
        }
        for (int i = 0; i < arrayList.size(); ++i) {
            IGPNode iGPNode = (IGPNode)arrayList.get(i);
            d = iGPNode.getFitness(by);
            d2 += d;
            if (i >= TopStrategiesData.TOP_AVG_COUNT) continue;
            d3 += d;
        }
        IGPNode iGPNode = (IGPNode)arrayList.get(0);
        int n2 = Math.min(TopStrategiesData.TOP_AVG_COUNT, arrayList.size());
        this.data.populationSize = arrayList.size();
        switch (by) {
            case 10: {
                this.data.generationData[n].bestFitnessIS = iGPNode.getFitness((byte)10);
                if (n2 > 0) {
                    this.data.generationData[n].topAvgFitnessIS = d3 / (double)n2;
                }
                if (this.data.populationSize <= 0) break;
                this.data.generationData[n].avgFitnessIS = d2 / (double)this.data.populationSize;
                break;
            }
            case 11: {
                this.data.generationData[n].bestFitnessIST = iGPNode.getFitness((byte)11);
                if (n2 > 0) {
                    this.data.generationData[n].topAvgFitnessIST = d3 / (double)n2;
                }
                if (this.data.populationSize <= 0) break;
                this.data.generationData[n].avgFitnessIST = d2 / (double)this.data.populationSize;
                break;
            }
            case 40: {
                this.data.generationData[n].bestFitnessISV = iGPNode.getFitness((byte)40);
                if (n2 > 0) {
                    this.data.generationData[n].topAvgFitnessISV = d3 / (double)n2;
                }
                if (this.data.populationSize <= 0) break;
                this.data.generationData[n].avgFitnessISV = d2 / (double)this.data.populationSize;
                break;
            }
            case 20: {
                this.data.generationData[n].bestFitnessOOS = iGPNode.getFitness((byte)20);
                if (n2 > 0) {
                    this.data.generationData[n].topAvgFitnessOOS = d3 / (double)n2;
                }
                if (this.data.populationSize <= 0) break;
                this.data.generationData[n].avgFitnessOOS = d2 / (double)this.data.populationSize;
            }
        }
    }

    public boolean isStagnating() {
        if (!this.gpSettings.restartOnStagnation) {
            return false;
        }
        if (this.gpSettings.stagnationGenerationsToRestart > 0) {
            double d = 0.0;
            double d2 = 0.0;
            int n = 0;
            int n2 = this.data.generation - this.gpSettings.stagnationGenerationsToRestart;
            if (n2 < 0) {
                n2 = 0;
            }
            for (int i = 0; i <= this.data.generation; ++i) {
                FitnessCollectionData fitnessCollectionData = this.data.generationData[i];
                if (fitnessCollectionData == null) continue;
                d = this.getFitnessBySampleType(fitnessCollectionData, (byte)this.gpSettings.stagnationFitnessRestartType);
                if (d == 0.0) {
                    return false;
                }
                if (i == 0) {
                    d2 = d;
                    continue;
                }
                if (d <= d2) {
                    ++n;
                    continue;
                }
                d2 = d;
                n = 0;
            }
            if (n >= this.gpSettings.stagnationGenerationsToRestart) {
                return true;
            }
        }
        return false;
    }

    private double getFitnessBySampleType(FitnessCollectionData fitnessCollectionData, byte by) {
        switch (by) {
            case 10: {
                return fitnessCollectionData.topAvgFitnessIS;
            }
            case 11: {
                return fitnessCollectionData.topAvgFitnessIST;
            }
            case 40: {
                return fitnessCollectionData.topAvgFitnessISV;
            }
        }
        return fitnessCollectionData.topAvgFitnessIS;
    }

    public GPFitnessEvolutionData getData() {
        return this.data;
    }
}

