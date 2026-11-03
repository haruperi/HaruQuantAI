/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.app.MainApp
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Servlet.impl.CodeEditor.templates;

import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.plugin.Servlet.impl.CodeEditor.CodeEditorServletException;
import com.strategyquant.plugin.Servlet.impl.CodeEditor.templates.Template;
import java.io.File;
import java.util.ArrayList;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class Templates {
    public static final Logger Log = LoggerFactory.getLogger(Templates.class);
    private final ArrayList<Template> availableTemplates = new ArrayList();
    public static final String TEMPLATES_PATH = MainApp.getDataPath() + "internal/web/" + "SQEDITOR" + "/templates/";
    public static final String CODE_BLOCKS_TPL_PATH = TEMPLATES_PATH + "/CodeBlocks.tpl";
    public static final String PSEUDO_CODE_BLOCKS_TPL_PATH = TEMPLATES_PATH + "/PseudoCodeBlocks.tpl";
    public static final String EMPTY_FILE_PATH = TEMPLATES_PATH + "/EmptyFile.tpl";

    public Templates() {
        this.loadAvailableTemplates();
    }

    public List<Template> getAvailableTemplates() {
        return this.availableTemplates;
    }

    public void loadAvailableTemplates() {
        try {
            this.availableTemplates.clear();
            this.loadTemplates(new File(TEMPLATES_PATH + "SQ"));
        }
        catch (Exception e) {
            Log.error("Exc. ", (Throwable)e);
        }
    }

    private void loadTemplates(File fDir) {
        if (!fDir.isDirectory()) {
            return;
        }
        File[] children = fDir.listFiles();
        if (children == null) {
            return;
        }
        for (File f : children) {
            if (f.isDirectory()) {
                this.loadTemplates(f);
                continue;
            }
            String ext = SQUtils.getExtension((String)f.getName());
            if (!ext.equalsIgnoreCase("tpl")) continue;
            try {
                this.availableTemplates.add(new Template(f));
            }
            catch (Exception e) {
                Log.error(String.format("Template '%s' could not be loaded. Reason: %s", f.getAbsolutePath(), e.getMessage()), (Throwable)e);
            }
        }
    }

    public Template findTemplateByPath(String path) throws CodeEditorServletException {
        for (Template template : this.availableTemplates) {
            if (!template.getTemplateFileAbsolutePath().equals(path)) continue;
            return template;
        }
        throw new CodeEditorServletException(String.format("Template '%s' doesn't exist.", path));
    }

    public Template findTemplateByFileName(String name) throws CodeEditorServletException {
        for (Template template : this.availableTemplates) {
            String fileName = SQUtils.stripExtension((String)template.getTemplateFileName());
            if (!fileName.equals(name)) continue;
            return template;
        }
        throw new CodeEditorServletException("Template doesn't exist.");
    }
}

