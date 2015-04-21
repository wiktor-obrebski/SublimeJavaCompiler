###### I am not have a time to maintaining this project anymore. Feel free to fork and continue - or just create some pull-request, I am still here.

# Sublime Text Plugin: Javac

## Basic

This plugin adds the following commands to sublime Command Palette:

    JavaC: Compile Current File
    JavaC: Compile & Run Current File
    JavaC: Compile Current Project
    JavaC: Compile & Run Current Project
    JavaC: Generate Jar Package For Project
    JavaC: Generate & Run Jar Package For Project
    JavaC: Clear Project

## Installation

Move to you "Sublime Text" packages folder and clone this repository to it:

    git clone git@github.com:psychowico/SublimeJavaCompiler.git

## Configuration

When you trying compile simple java file, you should just use *"JavaC: Compile Current File"* or *"JavaC: Compile & Run Current File"* options. When you want compile full project, more complex, with namespaces, libraries etc. you need add to project configuration file. When you run *"JavaC: Compile Current Project"* command JavaC offer you to generate project configuration file. It will be *settings.sublime-javac*.

    {
        "project_name"      : "HelloWorld",
        "output_dir"        : "output",
        "sources_dir"       : "src",
        "encoding"          : "utf-8",
        "resources"         : [],
        "libs"              : [],
        "entry_file"        : "Test/HelloWorld.java",
        "entry_point"       : "Test.HelloWorld"
    }

Options meaning:

 * *project_name* - simply project name, use as output name for generating jar file
 * *output_dir*   - where jar and classes file should be generated
 * *sources_dir*  - where *.java sources of you file are stored
 * *encoding*     - compilation encoding, utf-8 default
 * *resources*    - list of resources files, they will be copied to you output classes directory and included in jar package (you can use asterix for file groups)
 * *libs*         - java jar external packages should be linked to you project
 * *entry_file*   - entry file where you have class with "Main" program function
 * *entry_point*  - class with "Main" program function

All pathes are relative to you project main directory (where *settings.sublime-javac* file is stored).

### Keyboard

You can add keyboard shortcuts by clicking in you "Preferences/Key Bindings - User" and add additional lines:

    { "keys": ["f5"], "command": "javac_compile_and_run_project" },
    { "keys": ["f6"], "command": "javac_compile_project" },
    { "keys": ["shift+f5"], "command": "javac_compile_and_run_file" },
    { "keys": ["shift+f6"], "command": "javac_compile_file" },
    { "keys": ["ctrl+shift+f7"], "command": "javac_clear_project" }

### Settings

You can change settings about Java path or hide output-window option.

 * Open your SublimeJavaCompiler User Settings Preferences file ```Preferences -> Package Settings -> Sublime Java Compiler -> Settings - User```
 * Add or update items.

These are the basic settings you can change:

    {
    	"java_path" : "java",
    	"javac_path": "javac",
    	"jar_path"  : "jar",
    	"javac_autohide": true,
    	"hide_output_after_compilation": true
    }
