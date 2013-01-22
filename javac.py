import sublime, sublime_plugin
import thread, subprocess, os
import functools
import sublime
import json

settings = sublime.load_settings("Preferences.sublime-settings")
sget     = settings.get
project_config_filename = "settings.sublime-javac"

class CompileCurrentProjectCommand(sublime_plugin.TextCommand):
    def load_config(self, project_config_path):

        def clear_path(path, ):
            if path[0] in ['.', '/']: return path
            return os.path.join(rel_dir, path)

        settings_obj = open(project_config_path)
        settings = json.load(settings_obj)
        settings_obj.close()

        rel_dir = os.path.dirname(project_config_path)

        self.src          = clear_path(settings.get('sources_directory', 'src'))
        self.project_name = settings.get('project_name', 'project')

        build_path  = clear_path(settings.get('output_directory', 'output'))
        self.build_classes_path = os.path.join(build_path,'build/classes')
        self.build_dist_path    = os.path.join(build_path,'dist')

        self.entry_point = settings.get('entry_point', 'Namespace.EntryPointClass')
        self.entry_file  = settings.get('entry_file', 'Namespace/EntryPointClass.java')


    def init(self):
        self.view.run_command('save')

        self.output = output = OutputWindow( self.view.window() )

        output.writeLine("------------Compiling project------------")
        output.writeLine("")

        output.show()

        window = self.view.window()
        dirs   = window.folders()
        files = [os.path.join(_dir, project_config_filename) for _dir in dirs ]
        files = [_file for _file in files if os.path.exists(_file)]
        if len(files) > 1:
            output.writeLine("Found more than one '%s' file. Can not continue." % project_config_filename)
            return False
        if len(files) == 0:
            output.writeLine("Can not found anyone '%s' file. Can not continue." % project_config_filename)
            return False

        self.load_config(files[0])

        return True

    def pack_jar(self):
        #jar cfe run.jar Test.HelloWorld Test
        try:
            output = self.output

            output_name = '.'.join([self.project_name, 'jar'])
            output_path = os.path.join(self.build_dist_path, output_name)

            proc = subprocess.Popen(
                 [ sget('jar_path', 'jar'),
                   'cfe',
                   output_path,
                   self.entry_point,
                   '.'
                 ],
                 cwd = self.build_classes_path,
                 stdout = subprocess.PIPE,
                 stderr = subprocess.PIPE
            )

            if proc.stdout:
                output.readStdOut(proc)
            if proc.stderr:
                output.readStdErr(proc)

            proc.wait()

            output.lazy_write_line("------------Packing jar end------------")

            # if sget('hide_output_after_compilation', True):
            #     output.close()

        except Exception, e:
            msg = "Error: %s" % e
            self.output.write(msg)

    def compile(self):
        try:
            output = self.output

            proc = subprocess.Popen(
                 [ sget('javac_path', 'javac'),
                   '-verbose',
                   '-d', self.build_classes_path,
                   self.entry_file ],
                 cwd = self.src,
                 stdout = subprocess.PIPE,
                 stderr = subprocess.PIPE
            )

            if proc.stdout:
                output.readStdOut(proc)
            if proc.stderr:
                output.readStdErr(proc)

            proc.wait()

            output.lazy_write_line("------------Compilation end------------")

            self.pack_jar()
            # if sget('hide_output_after_compilation', True):
            #     output.close()

        except Exception, e:
            msg = "Error: %s" % e
            self.output.write(msg)


    def run(self, edit):
        if self.init():
            thread.start_new_thread(self.compile, ())

        #self.output.close()

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

    def readStdOut(self, proc):
        while True:
            data = os.read(proc.stdout.fileno(), 2 ** 15)
            if "" == data :
                proc.stdout.close()
                break
            else:
                sublime.set_timeout(functools.partial(self.write, data), 0)

    def readStdErr(self, proc):
        has_errors = False
        while True:
            data = os.read(proc.stderr.fileno(), 2 ** 15)
            if "" == data :
                proc.stderr.close()
                # self.appendData("\n--- Execution Finished ---")
                #
                return has_errors
            else:
                sublime.set_timeout(functools.partial(self.write, data), 0)
                has_errors = True

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

    def lazy_write_line(self, text):
        sublime.set_timeout(functools.partial(self.writeLine, text), 0)

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
