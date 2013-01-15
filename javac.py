import sublime, sublime_plugin
import thread, subprocess, os
import functools


class CompileCurrentFileCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        self.view.insert(edit, 0, "Hello,321 World!")

        #self.process = subprocess.Popen( ('javac'), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)