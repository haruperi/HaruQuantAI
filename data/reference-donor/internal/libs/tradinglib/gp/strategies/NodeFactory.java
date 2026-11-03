/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.IRandomGenerator
 *  org.jdom2.Element
 *  org.jdom2.JDOMException
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.gp.strategies;

import com.strategyquant.lib.IRandomGenerator;
import com.strategyquant.tradinglib.TradingOption;
import com.strategyquant.tradinglib.generator.StrategyGenerator;
import com.strategyquant.tradinglib.generator.StrategyGeneratorCache;
import com.strategyquant.tradinglib.gp.AbstractFactory;
import com.strategyquant.tradinglib.gp.strategies.BuildSettings;
import com.strategyquant.tradinglib.gp.strategies.Node;
import com.strategyquant.tradinglib.options.parameters.StockpickerOptions;
import com.strategyquant.tradinglib.util.StockpickerGenFixer;
import java.io.IOException;
import org.jdom2.Element;
import org.jdom2.JDOMException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class NodeFactory
extends AbstractFactory<Node> {
    private static final Logger Log = LoggerFactory.getLogger((String)"NodeFactory");
    private BuildSettings buildSettings;
    private StrategyGenerator strategyGenerator;

    public NodeFactory(BuildSettings buildSettings) {
        this.buildSettings = buildSettings;
    }

    @Override
    public Node generateRandomCandidate(IRandomGenerator iRandomGenerator) throws Exception {
        Element element = this.generateStrategy(iRandomGenerator);
        Node node = new Node(element);
        return node;
    }

    private Element generateStrategy(IRandomGenerator iRandomGenerator) throws JDOMException, IOException, Exception {
        Element element;
        int n;
        if (this.strategyGenerator == null) {
            this.strategyGenerator = StrategyGeneratorCache.getGenerator(this.buildSettings.getGeneratorHash(), iRandomGenerator, this.buildSettings.getStrategyTemplate(), this.buildSettings.getReplacements(), this.buildSettings.getBuildSettingsMap(), this.buildSettings.getATMGenerateConfig());
        }
        if ((n = StockpickerGenFixer.recognizeEngine(element = this.strategyGenerator.generate("Strategy"))) == 1316847364 || n == -1816889229) {
            this.addStockpickerFixes(element, iRandomGenerator);
        }
        return element;
    }

    private void addStockpickerFixes(Element element, IRandomGenerator iRandomGenerator) throws Exception {
        if (this.buildSettings.tradingOptions != null) {
            boolean bl = false;
            int n = 0;
            int n2 = 0;
            int n3 = 0;
            int n4 = 0;
            int n5 = 0;
            int n6 = 0;
            for (TradingOption tradingOption : this.buildSettings.tradingOptions) {
                if (!(tradingOption instanceof StockpickerOptions)) continue;
                StockpickerOptions stockpickerOptions = (StockpickerOptions)tradingOption;
                bl = true;
                n = stockpickerOptions.PickerEntryType;
                n2 = stockpickerOptions.PickerExitType;
                n3 = stockpickerOptions.PickerEndOfDayLong;
                n4 = stockpickerOptions.PickerEndOfDayShort;
                n5 = stockpickerOptions.PickerMaxOpenPositionsLong;
                n6 = stockpickerOptions.PickerMaxOpenPositionsShort;
                break;
            }
            if (!bl) {
                return;
            }
            Element element2 = element.getChild("Strategy");
            StockpickerGenFixer.fixEntryExitTriggers(iRandomGenerator, element2, n, n2);
            StockpickerGenFixer.fixExits(iRandomGenerator, element2, n3, n4);
            StockpickerGenFixer.fixMaxOpenPositions(element2, n5, n6);
        }
    }

    @Override
    public AbstractFactory<Node> clone() {
        return new NodeFactory(this.buildSettings.clone());
    }

    public Element generateRandomBlock(String string, Element element, int n, int n2) throws Exception {
        if (this.strategyGenerator == null) {
            throw new Exception("StrategyGenerator should be initialized at this point!");
        }
        return this.strategyGenerator.generateMutatedRandomBlock(string, element, n, n2);
    }

    @Override
    public void destroy() {
        if (this.strategyGenerator != null) {
            this.strategyGenerator.freeGenerator();
        }
    }

    @Override
    public Element mutateATM(Element element, IRandomGenerator iRandomGenerator) throws Exception {
        if (this.strategyGenerator == null) {
            throw new Exception("StrategyGenerator should be initialized at this point!");
        }
        return this.strategyGenerator.mutateATM(element, iRandomGenerator);
    }

    public Element verifyParameters(String string, Element element, Element element2) throws Exception {
        if (this.strategyGenerator == null) {
            throw new Exception("StrategyGenerator should be initialized at this point!");
        }
        return this.strategyGenerator.verifyParameters(string, element, element2);
    }
}

