/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.utils.SQFileChooserFactory
 */
package com.strategyquant.wizard.desktop.loader;

import com.strategyquant.lib.utils.SQFileChooserFactory;
import com.strategyquant.wizard.desktop.indicators.CustomIndicatorFileImporter;
import com.strategyquant.wizard.desktop.settings.Settings;
import com.strategyquant.wizard.desktop.utils.FileUtils;
import java.awt.Component;
import java.io.File;
import javax.swing.JFileChooser;
import javax.swing.filechooser.FileNameExtensionFilter;

public class CustomIndicatorLoader {
    private Component parent;

    public CustomIndicatorLoader(Component component) {
        this.parent = component;
    }

    public String loadFile(String string) {
        File file = new File(FileUtils.getAppFolder() + "/" + "config" + "/" + string);
        if (!file.exists()) {
            return null;
        }
        CustomIndicatorFileImporter customIndicatorFileImporter = new CustomIndicatorFileImporter(this.parent);
        String string2 = customIndicatorFileImporter.load(file);
        return string2;
    }

    public String loadFile() {
        String string = Settings.get().get("indicatorFolder");
        JFileChooser jFileChooser = SQFileChooserFactory.createPersistingJFileChooser((String)(string.isEmpty() ? null : string)).getJFileChooser();
        FileNameExtensionFilter fileNameExtensionFilter = new FileNameExtensionFilter("MQ4", "*.mq4");
        jFileChooser.setFileFilter(fileNameExtensionFilter);
        int n = jFileChooser.showOpenDialog(this.parent);
        if (n == 0) {
            File file = jFileChooser.getSelectedFile();
            Settings.get().set("indicatorFolder", file.getParent());
            CustomIndicatorFileImporter customIndicatorFileImporter = new CustomIndicatorFileImporter(this.parent);
            String string2 = customIndicatorFileImporter.load(file);
            return string2;
        }
        return null;
    }

    public void dispose() {
        this.parent = null;
    }
}

