import sublime
import javacbase
import os, json
from javacbase import sget

project_config_filename = "settings.sublime-javac"

class CompileCurrentProjectCommand(javacbase.CommandBase):
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

        self.build_dist_folder    = os.path.join(build_path,'dist')
        self.output_jar_file = '.'.join([self.project_name, 'jar'])

        self.entry_point = settings.get('entry_point', 'Namespace.EntryPointClass')
        self.entry_file  = settings.get('entry_file', 'Namespace/EntryPointClass.java')


    def init(self):
        """ Looking for 'project_config_filename' file in project folders, and load
        config from it. If it non exists, it will display menu where you can choose
        where it should be generated.
        """
        self.view.run_command('save')

        dirs   = self.view.window().folders()
        files = [os.path.join(_dir, project_config_filename) for _dir in dirs ]
        files = [_file for _file in files if os.path.exists(_file)]
        if len(files) > 1:
            self.write("Found more than one '%s' file. Can not continue." % project_config_filename)
            return False
        if len(files) == 0:
            self.write("Can not found anyone '%s' file. Can not continue." % project_config_filename)
            return False

        self.load_config(files[0])

        return True

    def pack_jar_order(self):
        self.write("\n------------Packing jar------------")
        self.write("")

        output_path = os.path.join(self.build_dist_folder, self.output_jar_file)
        jar = [
           sget('jar_path', 'jar'),
           'cfev',
           output_path,
           self.entry_point,
           '.'
        ]
        cwd = self.build_classes_path
        return (jar, cwd)

    def compile_project_order(self):

        self.write("\n------------Compiling project------------")
        self.write("")

        javac = [
            sget('javac_path', 'javac'),
            '-verbose',
            '-d', self.build_classes_path,
            self.entry_file
        ]
        return (javac, self.src)

    def run(self, edit):
        javacbase.CommandBase.run(self, edit)
        if self.init():
            orders = (self.compile_project_order, self.pack_jar_order)
            self.call_new_thread_chain(orders)


class CompileAndRunCurrentProjectCommand(CompileCurrentProjectCommand):
    def run(self, edit):
        javacbase.CommandBase.run(self, edit)
        if self.init():
            orders = (
                self.compile_project_order,
                self.pack_jar_order,
                self.run_jar_order
            )
            self.call_new_thread_chain(orders)

    def run_jar_order(self):
        java = [
            sget('java_path', 'java'),
            '-jar',
            self.output_jar_file
        ]
        cwd = self.build_dist_folder

        return (java, cwd)


class CompileCurrentFileCommand(javacbase.CommandBase):
    def init(self):
        self.file_name = self.view.file_name()
        self.file_dir = os.path.dirname(self.file_name)

    def compile(self):
        javac = [sget('javac_path', 'javac'), self.file_name]
        cwd = self.file_dir

        return javac, cwd

    def run(self, edit):
        javacbase.CommandBase.run(self, edit)
        self.init()
        self.call_new_thread_chain((self.compile,))


class CompileAndRunCurrentFileCommand(CompileCurrentFileCommand):

    def java_run(self):
        base_name = os.path.splitext(os.path.basename(self.file_name))[0]
        java = [
            sget('java_path', 'java'),
            base_name
        ]
        cwd = self.file_dir
        return java, cwd

    def run(self, edit):
        self.write(self)
        javacbase.CommandBase.run(self, edit)
        self.init()
        orders = (self.compile, self.java_run)
        self.call_new_thread_chain(orders)