/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SettingsMap
 *  org.jdom2.Element
 */
package com.strategyquant.tradinglib.gp.strategies;

import com.strategyquant.lib.SettingsMap;
import com.strategyquant.tradinglib.atm.ATMGenerateConfig;
import com.strategyquant.tradinglib.generator.StrategyGeneratorCache;
import com.strategyquant.tradinglib.options.TradingOptions;
import org.jdom2.Element;

public class BuildSettings {
    private Element elReplacements;
    private Element elStrategyTemplate;
    private SettingsMap buildSettings;
    private int generatorHash;
    private ATMGenerateConfig atmGenerateConfig;
    public TradingOptions tradingOptions = null;

    public BuildSettings(Element element, Element element2, SettingsMap settingsMap, ATMGenerateConfig aTMGenerateConfig) {
        this.elStrategyTemplate = element;
        this.elReplacements = element2;
        this.buildSettings = settingsMap;
        this.atmGenerateConfig = aTMGenerateConfig;
        this.generatorHash = StrategyGeneratorCache.getHash(element, element2, settingsMap, aTMGenerateConfig);
    }

    private BuildSettings() {
    }

    public BuildSettings clone() {
        BuildSettings buildSettings = new BuildSettings();
        buildSettings.elReplacements = this.elReplacements;
        buildSettings.elStrategyTemplate = this.elStrategyTemplate;
        buildSettings.buildSettings = this.buildSettings.clone();
        buildSettings.atmGenerateConfig = this.atmGenerateConfig;
        buildSettings.generatorHash = this.generatorHash;
        buildSettings.tradingOptions = this.tradingOptions;
        return buildSettings;
    }

    public int getGeneratorHash() {
        return this.generatorHash;
    }

    public Element getStrategyTemplate() {
        return this.elStrategyTemplate;
    }

    public Element getReplacements() {
        return this.elReplacements;
    }

    public SettingsMap getBuildSettingsMap() {
        return this.buildSettings;
    }

    public ATMGenerateConfig getATMGenerateConfig() {
        return this.atmGenerateConfig;
    }
}

