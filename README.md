What exacly this plugin should do?

Adds the following commands to menu:

    JavaC: Compile Current File
    JavaC: Compile & Run Current File

    JavaC: Compile Current Project
    JavaC: Compile & Run Current Project

    JavaC: Clear Project


First two just compile current file and make output in this same directory (and run if needed).
Second one working only with prepared project. It should looking for 'settings.sublime-javac' file,
load configuration from it and compile full project (and run if needed).

Settings format (js):

{
    "project_name"      : "HelloWorld",
    "output_dir"        : "output",
    "sources_dir"       : "src",
    "resources"         : [],
    "libs"              : [],
    "entry_file"        : "Test/HelloWorld.java",
    "entry_point"       : "Test.HelloWorld"
}