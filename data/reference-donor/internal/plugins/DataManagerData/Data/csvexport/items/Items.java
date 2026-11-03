/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.json.JSONArray
 */
package com.strategyquant.plugin.DataManager.impl.Data.csvexport.items;

import com.strategyquant.plugin.DataManager.impl.Data.csvexport.items.AbstractItem;
import com.strategyquant.plugin.DataManager.impl.Data.csvexport.items.AskPrice;
import com.strategyquant.plugin.DataManager.impl.Data.csvexport.items.BidPrice;
import com.strategyquant.plugin.DataManager.impl.Data.csvexport.items.ClosePrice;
import com.strategyquant.plugin.DataManager.impl.Data.csvexport.items.Comma;
import com.strategyquant.plugin.DataManager.impl.Data.csvexport.items.Date;
import com.strategyquant.plugin.DataManager.impl.Data.csvexport.items.DateTime;
import com.strategyquant.plugin.DataManager.impl.Data.csvexport.items.HighPrice;
import com.strategyquant.plugin.DataManager.impl.Data.csvexport.items.LowPrice;
import com.strategyquant.plugin.DataManager.impl.Data.csvexport.items.OpenPrice;
import com.strategyquant.plugin.DataManager.impl.Data.csvexport.items.Semicolon;
import com.strategyquant.plugin.DataManager.impl.Data.csvexport.items.Spread;
import com.strategyquant.plugin.DataManager.impl.Data.csvexport.items.Symbol;
import com.strategyquant.plugin.DataManager.impl.Data.csvexport.items.Tab;
import com.strategyquant.plugin.DataManager.impl.Data.csvexport.items.Time;
import com.strategyquant.plugin.DataManager.impl.Data.csvexport.items.Volume;
import java.util.ArrayList;
import java.util.List;
import org.json.JSONArray;

public class Items {
    private static Items instance;
    public List<AbstractItem> available = new ArrayList<AbstractItem>();

    public static Items get() {
        if (instance == null) {
            instance = new Items();
        }
        return instance;
    }

    private Items() {
        this.available.add(new Date());
        this.available.add(new Time());
        this.available.add(new DateTime());
        this.available.add(new OpenPrice());
        this.available.add(new HighPrice());
        this.available.add(new LowPrice());
        this.available.add(new ClosePrice());
        this.available.add(new AskPrice());
        this.available.add(new BidPrice());
        this.available.add(new Volume());
        this.available.add(new Spread());
        this.available.add(new Symbol());
        this.available.add(new Comma());
        this.available.add(new Semicolon());
        this.available.add(new Tab());
    }

    public AbstractItem findByKey(String key) {
        for (int i = 0; i < this.available.size(); ++i) {
            if (!key.equals(this.available.get((int)i).key)) continue;
            return this.available.get(i);
        }
        return null;
    }

    public JSONArray toJson() {
        JSONArray items = new JSONArray();
        for (AbstractItem item : this.available) {
            items.put((Object)item.toJson());
        }
        return items;
    }
}

