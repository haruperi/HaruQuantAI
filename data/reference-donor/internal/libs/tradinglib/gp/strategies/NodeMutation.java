/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.IRandomGenerator
 *  com.strategyquant.lib.SettingsMap
 *  it.unimi.dsi.fastutil.ints.IntArrayList
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.gp.strategies;

import com.strategyquant.lib.IRandomGenerator;
import com.strategyquant.lib.SettingsMap;
import com.strategyquant.tradinglib.atm.ATMGenerateConfig;
import com.strategyquant.tradinglib.generator.GenerateException;
import com.strategyquant.tradinglib.gp.AbstractFactory;
import com.strategyquant.tradinglib.gp.GPIDs;
import com.strategyquant.tradinglib.gp.IEvolutionaryOperator;
import com.strategyquant.tradinglib.gp.SelectedBlockGroups;
import com.strategyquant.tradinglib.gp.strategies.BuildSettings;
import com.strategyquant.tradinglib.gp.strategies.GenEvoChecker;
import com.strategyquant.tradinglib.gp.strategies.GeneratedObject;
import com.strategyquant.tradinglib.gp.strategies.GeneratedObjectsMap;
import com.strategyquant.tradinglib.gp.strategies.Node;
import it.unimi.dsi.fastutil.ints.IntArrayList;
import java.util.ArrayList;
import java.util.List;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class NodeMutation
implements IEvolutionaryOperator<Node> {
    public static final Logger Log = LoggerFactory.getLogger((String)"NodeMutation");
    private final double mutationProbability;
    private final double atmMutationProbability = 20.0;
    private boolean LimitSLPTRRR;
    private double LimitSLPTRRRFromCoef;
    private double LimitSLPTRRRToCoef;
    private SelectedBlockGroups selectedBlockGroups;
    private ATMGenerateConfig atmConfig;

    public NodeMutation(double d, BuildSettings buildSettings, SelectedBlockGroups selectedBlockGroups) {
        this.mutationProbability = d;
        this.selectedBlockGroups = selectedBlockGroups;
        SettingsMap settingsMap = buildSettings.getBuildSettingsMap();
        this.atmConfig = buildSettings.getATMGenerateConfig();
        this.LimitSLPTRRR = settingsMap.getBoolean("LimitSLPTRRR");
        if (this.LimitSLPTRRR) {
            double d2 = settingsMap.getInt("LimitSLPTRRRFrom");
            double d3 = settingsMap.getInt("LimitSLPTRRRTo");
            this.LimitSLPTRRRFromCoef = 1.0 / (d2 / 100.0);
            this.LimitSLPTRRRToCoef = 1.0 / (d3 / 100.0);
        }
    }

    @Override
    public List<Node> apply(List<Node> list, IRandomGenerator iRandomGenerator, AbstractFactory<Node> abstractFactory, int n, int n2) throws Exception {
        Node node;
        int n3;
        ArrayList<Node> arrayList = new ArrayList<Node>(list.size());
        for (n3 = 0; n3 < list.size(); ++n3) {
            node = list.get(n3);
            Node node2 = node.clone();
            Element element = this.mutate(node2, iRandomGenerator, abstractFactory);
            if (element != null && GenEvoChecker.passedRRRCheck(element, this.LimitSLPTRRR, this.LimitSLPTRRRToCoef, this.LimitSLPTRRRFromCoef)) {
                Node node3 = new Node(element);
                GPIDs gPIDs = node2.getGPIDs();
                GPIDs gPIDs2 = new GPIDs();
                gPIDs2.islandIndex = n;
                gPIDs2.generationIndex = n2;
                gPIDs2.generationType = "Mutation";
                gPIDs2.parent1 = gPIDs.toShortString();
                node3.setGPIDs(gPIDs2);
                node3.setModified();
                arrayList.add(node3);
                continue;
            }
            node2 = node.clone();
            arrayList.add(node2);
        }
        for (n3 = 0; n3 < list.size(); ++n3) {
            node = list.get(n3);
            node.clearGeneratedObjectsMap();
        }
        return arrayList;
    }

    private Element mutate(Node node, IRandomGenerator iRandomGenerator, AbstractFactory<Node> abstractFactory) throws Exception {
        Element element;
        GeneratedObject generatedObject;
        GeneratedObjectsMap generatedObjectsMap = node.getGeneratedObjectsMap();
        IntArrayList intArrayList = new IntArrayList();
        for (int i = 0; i < generatedObjectsMap.size(); ++i) {
            Element element2;
            block5: {
                if (!iRandomGenerator.probability(this.mutationProbability) || this.isObjectDependent(generatedObject = generatedObjectsMap.get(i), intArrayList)) continue;
                element2 = null;
                try {
                    element2 = generatedObject.mutate(iRandomGenerator, abstractFactory);
                }
                catch (GenerateException generateException) {
                    if (generateException.getMessage().contains("Cannot find block ")) break block5;
                    throw generateException;
                }
            }
            element2 = GenEvoChecker.fixZeroPeriodsAndExits(element2);
            if (element2 == null) continue;
            node.replaceObjectById(generatedObject.getGID(), element2);
            element2.setAttribute("genop", "mutated");
            intArrayList.add(generatedObject.getGID());
        }
        if (this.atmConfig != null && iRandomGenerator.probability(20.0) && (generatedObject = abstractFactory.mutateATM(element = node.getStrategy(), iRandomGenerator)) != null) {
            return generatedObject;
        }
        if (intArrayList.isEmpty()) {
            return null;
        }
        return node.getStrategy();
    }

    private boolean isObjectDependent(GeneratedObject generatedObject, IntArrayList intArrayList) {
        int n = generatedObject.getParentGID();
        if (n == 0) {
            return false;
        }
        for (int i = 0; i < intArrayList.size(); ++i) {
            if (n != intArrayList.getInt(i)) continue;
            return true;
        }
        return false;
    }
}

