/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.pluginlib.annotations.Category
 *  com.strategyquant.pluginlib.annotations.License
 *  com.strategyquant.pluginlib.annotations.Name
 *  com.strategyquant.pluginlib.annotations.ShortDesc
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.results.file.ILoaderPlugin
 *  com.strategyquant.tradinglib.results.file.MissingInstrumentException
 *  net.xeoh.plugins.base.annotations.PluginImplementation
 *  net.xeoh.plugins.base.annotations.meta.Author
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Loader.impl.SQ3;

import com.strategyquant.lib.L;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.plugin.Loader.impl.SQ3.SQ3FileLoader;
import com.strategyquant.pluginlib.annotations.Category;
import com.strategyquant.pluginlib.annotations.License;
import com.strategyquant.pluginlib.annotations.Name;
import com.strategyquant.pluginlib.annotations.ShortDesc;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.results.file.ILoaderPlugin;
import com.strategyquant.tradinglib.results.file.MissingInstrumentException;
import net.xeoh.plugins.base.annotations.PluginImplementation;
import net.xeoh.plugins.base.annotations.meta.Author;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@Author(name="Mark Fric")
@Name(name="SQ3LoaderPlugin plugin")
@Category(name="File Loader")
@License(text="")
@ShortDesc(text="Short description")
@PluginImplementation
public class SQ3LoaderPlugin
implements ILoaderPlugin {
    public static final Logger Log = LoggerFactory.getLogger((String)"SQ3LoaderPlugin");
    public static final String[] extensions = new String[]{"str", "stp", "sqa"};

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

    public ResultsGroup load(String fileName, boolean exceptionOnMissingInstrument, String missingInstrumentReplacement, String userSecretCode) throws Exception {
        try {
            SQ3FileLoader loader = new SQ3FileLoader();
            ResultsGroup sr = loader.load(fileName, exceptionOnMissingInstrument, missingInstrumentReplacement);
            sr.computeAllStats();
            String fileExtension = SQUtils.getExtension((String)fileName).toLowerCase();
            if (fileExtension.equals("str")) {
                // empty if block
            }
            return sr;
        }
        catch (MissingInstrumentException e) {
            throw e;
        }
        catch (Exception ex) {
            Log.error("Failed to load SQStrategy report file: " + fileName + " Exc: ", (Throwable)ex);
            throw new Exception(L.t((String)"Failed to load SQStrategy report file: %s - %s", (Object[])new Object[]{fileName, ex.getMessage()}));
        }
    }

    public ResultsGroup finishLoad(ResultsGroup result) throws Exception {
        return result;
    }
}

