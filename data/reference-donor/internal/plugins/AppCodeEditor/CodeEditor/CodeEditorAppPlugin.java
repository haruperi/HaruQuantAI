/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.lib.hw.OperatingSystem
 *  com.strategyquant.pluginlib.annotations.Category
 *  com.strategyquant.pluginlib.annotations.License
 *  com.strategyquant.pluginlib.annotations.Name
 *  com.strategyquant.pluginlib.annotations.ShortDesc
 *  com.strategyquant.pluginlib.program.IProgram
 *  com.strategyquant.pluginlib.program.Program
 *  com.strategyquant.tradinglib.plugindef.app.IAppPlugin
 *  net.xeoh.plugins.base.annotations.PluginImplementation
 *  net.xeoh.plugins.base.annotations.meta.Author
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.App.impl.CodeEditor;

import com.strategyquant.lib.L;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.lib.hw.OperatingSystem;
import com.strategyquant.pluginlib.annotations.Category;
import com.strategyquant.pluginlib.annotations.License;
import com.strategyquant.pluginlib.annotations.Name;
import com.strategyquant.pluginlib.annotations.ShortDesc;
import com.strategyquant.pluginlib.program.IProgram;
import com.strategyquant.pluginlib.program.Program;
import com.strategyquant.tradinglib.plugindef.app.IAppPlugin;
import net.xeoh.plugins.base.annotations.PluginImplementation;
import net.xeoh.plugins.base.annotations.meta.Author;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@Author(name="Mark Fric")
@Name(name="Trader")
@Category(name="App")
@License(text="")
@ShortDesc(text="Short description")
@PluginImplementation
public class CodeEditorAppPlugin
implements IAppPlugin,
IProgram {
    public static final Logger Log = LoggerFactory.getLogger(CodeEditorAppPlugin.class);

    public String getName() {
        return "CodeEditor";
    }

    public String getProduct() {
        return "SQUANT";
    }

    public int getPreferredPosition() {
        return 2;
    }

    public void initPlugin() throws Exception {
        Program.register((String)"CodeEditor", (IProgram)this);
    }

    public String getContextPath() {
        return "/editor";
    }

    public String getAppCode() {
        return "SQEDITOR";
    }

    public String getTooltip() {
        return "CodeEditor";
    }

    public String getProject() {
        return null;
    }

    public String getDefaultTaskType() {
        return null;
    }

    public String getDefaultTaskName() {
        return null;
    }

    public Object call(String methodName, Object ... parameters) throws Exception {
        if (methodName.equals("open")) {
            new Thread(){

                @Override
                public void run() {
                    try {
                        String[] command = null;
                        OperatingSystem os = new OperatingSystem();
                        if (os.isWindows()) {
                            command = new String[]{"cmd", "/c", "start", "\"\"", MainApp.getDataPath() + "CodeEditor.exe"};
                        } else if (os.isMac()) {
                            command = new String[]{"./CodeEditor"};
                        } else if (os.isUnix()) {
                            command = new String[]{"./CodeEditor"};
                        } else {
                            throw new Exception(L.t((String)"Operating system not recognized", (Object[])new Object[0]));
                        }
                        Runtime.getRuntime().exec(command);
                    }
                    catch (Exception e) {
                        Log.error("Failed to open CodeEditor.", (Throwable)e);
                    }
                }
            }.start();
        }
        return null;
    }
}

