# Sublime Text 2 Plugin: Javac

## Basic

This plugin adds the following commands to sublime Command Palette:

    JavaC: Compile Current File
    JavaC: Compile & Run Current File
    JavaC: Compile Current Project
    JavaC: Compile & Run Current Project
    JavaC: Clear Project

## Installation

Move to you "Sublime 2 Text" packages folder and clone this repository to it:

    git clone git@github.com:psychowico/SublimeJavaCompiler.git

## Configuration

When you trying compile simple java file, you should just use *"JavaC: Compile Current File"* or *"JavaC: Compile & Run Current File"* options. When you want compile full project, more complex, with namespaces, libraries etc. you need add to project configuration file. When you run *"JavaC: Compile Current Project"* command JavaC offer you to generate project configuration file. It will be *settings.sublime-javac*.

    {
        "project_name"      : "HelloWorld",
        "output_dir"        : "output",
        "sources_dir"       : "src",
        "resources"         : [],
        "libs"              : [],
        "entry_file"        : "Test/HelloWorld.java",
        "entry_point"       : "Test.HelloWorld"
    }