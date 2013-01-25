import sublime, sublime_plugin
import threading, subprocess, functools
import os

def invoke(callback, *args, **kwargs):
    # sublime.set_timeout gets used to send things onto the main thread
    # most sublime.[something] calls need to be on the main thread
    sublime.set_timeout(functools.partial(callback, *args, **kwargs), 0)

class OutputWindow(object):
    """ Thread-safe output window
    """
    def __init__(self, window, name='composer'):
        self.window = window
        self.name = name
        self.outputWindow = None

    def _getOutputWindow(self):
        if (None is self.outputWindow):
            self.outputWindow = self.window.get_output_panel(self.name)
            self.clear()

        return self.outputWindow

    def show(self):
        def _show(self):
            self._getOutputWindow()
            self.window.run_command("show_panel", {"panel": "output." + self.name})
        invoke(_show, self)

    def close(self):
        def _close(self):
            outputWindow = self._getOutputWindow()
            self.window.run_command("hide_panel", {"panel": "output." + self.name, "cancel": True})
        invoke(_close, self)

    def clear(self):
        def _clear(self):
            outputWindow = self._getOutputWindow()
            outputWindow.set_read_only(False)
            edit = outputWindow.begin_edit()
            outputWindow.erase(edit, sublime.Region(0, outputWindow.size()))
            outputWindow.end_edit(edit)
            outputWindow.set_read_only(True)
        invoke(_clear, self)

    def write(self, data, new_line=True):
        """ Thread-safe writing text to console and adding new line.
        """
        def _plain_write(outputWindow, data, new_line=True):

            str = data.decode("utf-8")
            str = str.replace('\r\n', '\n').replace('\r', '\n')
            if new_line: str += '\n'

            # selection_was_at_end = (len(self.output_view.sel()) == 1
            #  and self.output_view.sel()[0]
            #    == sublime.Region(self.output_view.size()))
            outputWindow.set_read_only(False)
            edit = outputWindow.begin_edit()
            a = outputWindow.insert(edit, outputWindow.size(), str)
            #if selection_was_at_end:
            outputWindow.show(outputWindow.size())
            outputWindow.end_edit(edit)
            outputWindow.set_read_only(True)

        text = str(data)
        outputWindow = self._getOutputWindow()
        invoke(self.show)
        invoke(_plain_write, outputWindow, text, new_line)

class CommandBase(sublime_plugin.TextCommand):

    def write(self, text):
        self.output().write(text)

    def output(self):
        if not hasattr(self, '_output'):
            self._output = OutputWindow(self.view.window())
            self._output.show()
        return self._output

    def call_new_thread(self, cmd, on_done=None, *args, **kwargs):
        def _done(self, has_errors):
            if not has_errors:
                self.output().close()
            on_done(has_errors)
        thread = JavaCThread('java', _done, self.write, args, kwargs)
        thread.start()


    def run(self, edit):
        self.view.run_command('save')

class JavaCThread(threading.Thread):
    """ Wrapper for calling externall application in thread for this plugin.
    first argument is application path, second (on_done) - callback, with one argument (has_errors).
    """
    def __init__(self, cmd, on_done = None, out_method = None, working_dir = ".", **kwargs):
        threading.Thread.__init__(self)
        if working_dir is None or working_dir == '':
            working_dir = '.'
        self.cmd = cmd
        self.on_done = on_done
        self.working_dir = working_dir
        self.kwargs = kwargs
        self.out_method = out_method

    def log(self, text):
        if self.out_method is None: return
        self.out_method(text)

    def run(self):
        try:
            log = self.log
            # Ignore directories that no longer exist
            if os.path.isdir(self.working_dir):

                # Per http://bugs.python.org/issue8557 shell=True is required to
                # get $PATH on Windows. Yay portable code.
                shell = os.name == 'nt'
                if self.working_dir != '':
                    os.chdir(self.working_dir)

                proc = subprocess.Popen(self.cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    shell=shell,
                    universal_newlines=True
                )

                for line in iter(proc.stdout.readline, ''):
                    log(line)

                proc.stdout.close()

                has_errors = False
                for line in iter(proc.stderr.readline, ''):
                    has_errors = True
                    log(line)

                proc.stderr.close()

                if self.on_done is not None:
                    invoke(self.on_done, has_errors)

        except subprocess.CalledProcessError, e:
            if self.on_done is not None:
                invoke(self.on_done, e.returncode)

    def readStdOut(self, proc):
        while True:
            data = os.read(proc.stdout.fileno(), 2 ** 15)
            if "" == data:
                proc.stdout.close()
                break
            else:
                self.write(data)
    def readStdErr(self, proc):
        has_errors = False
        while True:
            data = os.read(proc.stderr.fileno(), 2 ** 15)
            if "" == data:
                proc.stderr.close()
                # self.appendData("\n--- Execution Finished ---")
                #
                return has_errors
            else:
                self.write(data)
                has_errors = True