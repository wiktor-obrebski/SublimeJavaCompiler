import sublime
import javacbase
import os, json
import shutil
import glob
from javacbase import sget

project_config_filename = "settings.sublime-javac"

class JavacCompileProjectCommand(javacbase.CommandBase):
    def load_config(self, project_config_path):

        def clear_path(path, ):
            if path[0] in ['.', '/']: return path
            return os.path.join(rel_dir, path)

        settings_obj = open(project_config_path)
        settings = json.load(settings_obj)
        settings_obj.close()

        self.project_dir = rel_dir = os.path.dirname(project_config_path)

        self.base_libs = settings.get('libs', [])
        self.libs = [clear_path(path) for path in self.base_libs]
        self.libs.append('.')

        self.resources = [clear_path(path) for path in settings.get('resources', [])]

        self.src          = clear_path(settings.get('sources_dir', 'src'))
        if not os.path.isdir(self.src): os.makedirs(self.src)

        self.project_name = settings.get('project_name', 'project')

        self.output_dir = build_path  = clear_path(settings.get('output_dir', 'output'))

        self.build_classes_path = os.path.join(build_path,'classes')
        #delete old files
        filelist = glob.glob(os.path.join(self.build_classes_path, "*.class"))
        for f in filelist: os.remove(f)

        if not os.path.isdir(self.build_classes_path): os.makedirs(self.build_classes_path)

        self.build_dist_folder    = os.path.join(build_path,'dist')
        if not os.path.isdir(self.build_dist_folder): os.makedirs(self.build_dist_folder)
        #delete old files
        filelist = glob.glob(os.path.join(self.build_dist_folder, "*.jar"))
        for f in filelist: os.remove(f)

        self.output_jar_file = '.'.join([self.project_name, 'jar'])

        self.entry_point = settings.get('entry_point', 'Namespace.EntryPointClass')
        self.entry_file  = settings.get('entry_file', 'Namespace/EntryPointClass.java')

    def generate_base_config(self, target_dir):
        target_path = os.path.join(target_dir, project_config_filename)

        _file = open(target_path, 'w')
        _file.write("""{
    "project_name"      : "HelloWorld",
    "output_dir"  : "output",
    "sources_dir" : "src",
    "resources"   : [],
    "libs"        : [],

    "entry_file"        : "Test/HelloWorld.java",
    "entry_point"       : "Test.HelloWorld"
}"""    )
        _file.close()
        if hasattr(self, '_output'):
            self.output().close()
        self.view.window().open_file(target_path)

    def init(self):
        """ Looking for 'project_config_filename' file in project folders, and load
        config from it. If it non exists, it will display menu where you can choose
        where it should be generated.
        """
        self.view.run_command('save')

        window = self.view.window()
        dirs   = window.folders()
        files = [os.path.join(_dir, project_config_filename) for _dir in dirs ]
        files = [_file for _file in files if os.path.exists(_file)]
        if len(files) > 1:
            self.write("Found more than one '%s' file. Can not continue." % project_config_filename)
            return False
        if len(files) == 0:
            def show_folders(result):
                if result == 1 or result == -1: return
                if len(dirs) > 1:
                    def choose(result):
                        if result == -1: return
                        self.generate_base_config(dirs[result])
                    _list = [[os.path.basename(_dir), _dir] for _dir in dirs]
                    window.show_quick_panel(_list, choose)
                else:
                    self.generate_base_config(dirs[0])
            options = [
                ['Generate new configuration.', 'Generate new java project file configuration.'],
                ['Cancel', 'Abandon compilation.']
            ]
            window.show_quick_panel(options, show_folders)
            return False

        self.load_config(files[0])
        if hasattr(self, '_output'):
            self.output().clear()

        return True

    def compile_project_order(self):

        self.write("\n------------Compiling project------------")
        self.write("")

        javac = [
            sget('javac_path', 'javac'),
            '-d', self.build_classes_path,
			'-encoding', 'ISO-8859-1'
        ]
        libs = self.libs

        if len(self.libs) > 0:
            javac.extend(['-cp', '%s' % os.pathsep.join(libs)])
        javac.append( self.entry_file )

        return (javac, self.src)

    def copy_resources(self):
        files_to_copy = []
        for pathname in self.resources:
            files_to_copy.extend(glob.glob(pathname))

        op = os.path
        for path in files_to_copy:
            filename  = op.basename(path)
            targetdir = op.join(self.build_classes_path, op.relpath(op.dirname(path), self.src))
            targetpath = op.join(targetdir, filename)
            if not op.isfile(targetpath):
                if not op.isdir(targetdir): os.makedirs(targetdir)
                shutil.copy(path, targetpath)

    def _run(self, edit):
        self.view.run_command('save')
        if self.init():
            self.copy_resources()
            orders = (self.compile_project_order, )
            self.call_new_thread_chain(orders)


class JavacCompileAndRunProjectCommand(JavacCompileProjectCommand):

    def run_classes_order(self):
        java = [
            sget('java_path', 'java'),
        ]
        libs = self.libs

        if len(self.libs) > 0:
            java.extend(['-cp', '%s' % os.pathsep.join(libs)])

        java.append( self.entry_point )

        cwd = self.build_classes_path

        self.write("\n------------Running application------------")
        self.write("")

        return java, cwd

    def _run(self, edit):
        self.view.run_command('save')
        if self.init():
            self.copy_resources()
            self.output().clear()
            orders = (
                self.compile_project_order,
                self.run_classes_order
            )
            self.call_new_thread_chain(orders)


class JavacClearProjectCommand(JavacCompileProjectCommand):

    def _clearing(self, result):
        if result == 0 and self.init():
            self.view.run_command('save')

            self.write("\n------------Clearing project------------")
            self.write("")
            if os.path.isdir(self.output_dir):
                shutil.rmtree(self.output_dir)
            if sget('javac_autohide', True):
                self.output().close()

    def _run(self, edit):
        options = [
            ['Confirmation', 'All files in my "output" directory will be deleted.'],
            ['Cancel', 'Abandon project clearing.']
        ]
        self.view.window().show_quick_panel(options, self._clearing)


class JavacCompileFileCommand(javacbase.CommandBase):
    def init(self):
        self.file_name = self.view.file_name()
        self.file_dir = os.path.dirname(self.file_name)

    def compile(self):
        javac = [sget('javac_path', 'javac'), self.file_name]
        cwd = self.file_dir

        self.write("\n------------Compiling file------------")
        self.write("")

        return javac, cwd

    def _run(self, edit):
        self.view.run_command('save')
        self.init()
        self.output().clear()
        self.call_new_thread_chain((self.compile,))


class JavacCompileAndRunFileCommand(JavacCompileFileCommand):

    def java_run(self):
        base_name = os.path.splitext(os.path.basename(self.file_name))[0]
        java = [
            sget('java_path', 'java'),
            base_name
        ]
        cwd = self.file_dir
        return java, cwd

    def _run(self, edit):
        self.init()
        orders = (self.compile, self.java_run)
        self.call_new_thread_chain(orders)

class JavacGenerateJarCommand(JavacCompileProjectCommand):

    def pack_jar_order(self):
        self.write("\n------------Packing jar------------")
        self.write("")

        output_path = os.path.join(self.build_dist_folder, self.output_jar_file)
        jar = [
           sget('jar_path', 'jar'),
           'cmfev',
           'Manifest',
           output_path,
           self.entry_point,
           '.'
        ]
        cwd = self.build_classes_path
        return (jar, cwd)

    def prepare_manifest(self):
        libs = self.base_libs
        text = 'Class-Path: %s' % ' '.join(libs)
        path = os.path.join(self.build_classes_path, 'Manifest')

        _file = open(path, 'w')
        _file.write(text)
        _file.close()

    def copy_libs(self):
        op = os.path
        libs = self.libs[:]
        libs.remove('.')
        for path in libs:
            target_file = op.join(self.build_dist_folder, op.relpath(path, self.project_dir))
            target_dir  = op.dirname(target_file)
            if not op.isfile(target_file):
                if not op.isdir(target_dir): os.makedirs(target_dir)
                shutil.copy(path, target_file)

    def _run(self, edit):
        self.view.run_command('save')
        if self.init():
            self.output().clear()
            self.copy_resources()
            self.copy_libs()
            self.prepare_manifest()
            orders = (
                self.compile_project_order,
                self.pack_jar_order
            )
            self.call_new_thread_chain(orders)

class JavacGenerateAndRunJarCommand(JavacGenerateJarCommand):

    def run_jar_order(self):
        java = [
            sget('java_path', 'java'),
            '-jar',
            self.output_jar_file
        ]
        cwd = self.build_dist_folder

        self.write("\n------------Running application------------")
        self.write("")

        return java, cwd

    def _run(self, edit):
        self.view.run_command('save')
        if self.init():
            self.output().clear()
            self.copy_resources()
            self.copy_libs()
            orders = (
                self.compile_project_order,
                self.prepare_manifest,
                self.pack_jar_order,
                self.run_jar_order
            )
            self.call_new_thread_chain(orders)