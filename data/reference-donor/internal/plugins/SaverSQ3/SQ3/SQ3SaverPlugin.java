/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.pluginlib.annotations.Category
 *  com.strategyquant.pluginlib.annotations.License
 *  com.strategyquant.pluginlib.annotations.Name
 *  com.strategyquant.pluginlib.annotations.ShortDesc
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.results.file.ISaverPlugin
 *  net.xeoh.plugins.base.annotations.PluginImplementation
 *  net.xeoh.plugins.base.annotations.meta.Author
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Saver.impl.SQ3;

import com.strategyquant.plugin.Saver.impl.SQ3.SQ3FileSaver;
import com.strategyquant.pluginlib.annotations.Category;
import com.strategyquant.pluginlib.annotations.License;
import com.strategyquant.pluginlib.annotations.Name;
import com.strategyquant.pluginlib.annotations.ShortDesc;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.results.file.ISaverPlugin;
import java.util.Map;
import net.xeoh.plugins.base.annotations.PluginImplementation;
import net.xeoh.plugins.base.annotations.meta.Author;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@Author(name="Mark Fric")
@Name(name="SQ3SaverPlugin plugin")
@Category(name="File Saver")
@License(text="")
@ShortDesc(text="Short description")
@PluginImplementation
public class SQ3SaverPlugin
implements ISaverPlugin {
    public static final Logger Log = LoggerFactory.getLogger(SQ3SaverPlugin.class);
    public static final String[] extensions = new String[]{"str"};

    public String getProduct() {
        return "any";
    }

    public int getPreferredPosition() {
        return 0;
    }

    public void initPlugin() throws Exception {
    }

    public String[] getFileExtensions() {
        return extensions;
    }

    public void save(ResultsGroup rg, String fileName, Map<String, String[]> parameterMap) throws Exception {
        try {
            SQ3FileSaver saver = new SQ3FileSaver();
            saver.save(rg, fileName, parameterMap);
        }
        catch (Exception ex) {
            Log.error("Failed to save SQ3 file '" + fileName + "'. Exc: ", (Throwable)ex);
            throw new Exception("Failed to save SQ3 file '" + fileName + "' - " + ex.getMessage());
        }
    }

    public ISaverPlugin clone() {
        return new SQ3SaverPlugin();
    }
}

