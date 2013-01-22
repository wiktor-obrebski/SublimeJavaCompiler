import sublime, sublime_plugin
import thread, subprocess, os
import functools
import sublime

settings = sublime.load_settings("Preferences.sublime-settings")
sget     = settings.get

class CompileCurrentFileCommand(sublime_plugin.TextCommand):
    def init(self):
        self.view.run_command('save')

        self.output = output = OutputWindow( self.view.window() )

        output.writeLine("------------Compiling------------")
        output.writeLine('')

        self.file_name = self.view.file_name()
        self.file_dir = os.path.dirname(self.file_name)

        output.show()

    def compile(self):
        try:
            self.proc = subprocess.Popen(
                 [ sget('javac_path', 'javac'), self.file_name],
                 cwd = self.file_dir,
                 stdout = subprocess.PIPE,
                 stderr = subprocess.PIPE
            )

            self.has_errors = False

            if self.proc.stdout:
                self.readStdOut()
            if self.proc.stderr:
                self.readStdErr()

            self.proc.wait()

            self.output.writeLine("------------Compilation end------------")

            if not self.has_errors:
                self.output.close()

        except Exception, e:
            self.has_errors = True
            msg = "Error: %s" % e
            self.output.write(msg)


    def run(self, edit):
        self.init()
        thread.start_new_thread( self.compile, () )


    def readStdOut(self):
        while True:
            data = os.read(self.proc.stdout.fileno(), 2 ** 15)
            if "" == data :
                self.proc.stdout.close()
                break
            else:
                sublime.set_timeout(functools.partial(self.output.write, data), 0)

    def readStdErr(self):
        while True:
            data = os.read(self.proc.stderr.fileno(), 2 ** 15)
            if "" == data :
                self.proc.stderr.close()
                # self.appendData("\n--- Execution Finished ---")
                #
                break
            else:
                self.has_errors = True
                sublime.set_timeout(functools.partial(self.output.write, data), 0)
        pass

class CompileAndRunCurrentFileCommand(CompileCurrentFileCommand):

    def java_run(self):
        if self.has_errors: return
        try:

            self.base_name = os.path.splitext( os.path.basename(self.file_name) )[0]

            self.proc = subprocess.Popen(
                [ sget('java_path', 'java'), self.base_name],
                cwd = self.file_dir,
                stdout = subprocess.PIPE,
                stderr = subprocess.PIPE
            )


            if self.proc.stdout:
                self.readStdOut()
            if self.proc.stderr:
                self.readStdErr()

        except Exception, e:
            msg = "Error: %s" % e
            self.output.write(msg)

    def compile_and_run(self):
        self.compile()
        self.java_run()

    def run(self, edit):
        self.init()
        thread.start_new_thread(self.compile_and_run, ())




class OutputWindow(object):
    def __init__(self, window, name = 'composer'):
        self.window       = window
        self.name         = name
        self.outputWindow = None
        self.enabled      = 1

    def setEnabled(self, bool):
        self.enabled = bool

    def close(self):
        outputWindow = self.getOutputWindow()
        self.window.run_command("hide_panel", {"panel": "output." + self.name, "cancel": True})

    def getOutputWindow(self):
        if (None is self.outputWindow):
            self.outputWindow = self.window.get_output_panel(self.name)
            self.clear()

        return self.outputWindow

    def show(self):
        if self.enabled is False:
            return

        self.getOutputWindow()
        self.window.run_command("show_panel", {"panel": "output." + self.name})

    def clear(self):
        outputWindow = self.getOutputWindow()
        outputWindow.set_read_only(False)
        edit = outputWindow.begin_edit()
        outputWindow.erase(edit, sublime.Region(0, outputWindow.size()))
        outputWindow.end_edit(edit)
        outputWindow.set_read_only(True)

    def writeLine(self, data):
        self.write(data + '\n')

    def write(self, data):
        if self.enabled is False :
            return

        str = data.decode("utf-8")
        str = str.replace('\r\n', '\n').replace('\r', '\n')
        outputWindow = self.getOutputWindow()
        self.show()

        # selection_was_at_end = (len(self.output_view.sel()) == 1
        #  and self.output_view.sel()[0]
        #    == sublime.Region(self.output_view.size()))
        self.outputWindow.set_read_only(False)
        edit = outputWindow.begin_edit()
        outputWindow.insert(edit, outputWindow.size(), str)
        #if selection_was_at_end:
        outputWindow.show(outputWindow.size())
        outputWindow.end_edit(edit)
        outputWindow.set_read_only(True)
