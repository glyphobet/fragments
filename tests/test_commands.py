import unittest
import os, shutil, tempfile
import pdb

from fragman.__main__ import ExecutionError, init, stat, add
from fragman.config import configuration_file_name, configuration_directory_name, ConfigurationDirectoryNotFound


class CommandBase(unittest.TestCase):

    test_content_directory = 'test_content'

    def setUp(self):
        self.path = tempfile.mkdtemp()
        self.content_path = os.path.join(self.path, self.test_content_directory) 
        os.mkdir(self.content_path)
        self.assertTrue(os.path.exists(os.path.join(self.path, self.test_content_directory)))
        os.chdir(self.content_path)

    def tearDown(self):
        shutil.rmtree(self.path)


class TestInitCommand(CommandBase):

    def test_init_creates_fragments_directory_and_config_json(self):
        init()
        self.assertTrue(os.path.exists(os.path.join(self.path, configuration_directory_name)))
        self.assertTrue(os.path.exists(os.path.join(self.path, configuration_directory_name, configuration_file_name)))

    def test_init_raises_error_on_second_run(self):
        init()
        self.assertRaises(ExecutionError, init)

    def test_fragments_directory_inside_content_directory(self):
        init()
        shutil.move(os.path.join(self.path, configuration_directory_name), self.content_path)
        stat()

    def test_find_fragments_directory_one_level_up(self):
        init()
        inner_directory = os.path.join(self.content_path, 'inner')
        os.mkdir(inner_directory)
        os.chdir(inner_directory)
        self.assertRaises(ExecutionError, init)
        self.assertFalse(os.path.exists(os.path.join(self.content_path, configuration_directory_name)))

    def test_recovery_from_missing_fragments_config_json(self):
        init()
        os.unlink(os.path.join(os.path.join(self.path, configuration_directory_name, configuration_file_name)))
        init()
        self.assertTrue(os.path.exists(os.path.join(self.path, configuration_directory_name, configuration_file_name)))
    
    def test_recovery_from_corrupt_fragments_config_json(self):
        init()
        corrupted_config = file(os.path.join(os.path.join(self.path, configuration_directory_name, configuration_file_name)), 'a')
        corrupted_config.write("GIBBERISH#$$$;,){no}this=>is NOT.json")
        corrupted_config.close()
        init()
        self.assertTrue(os.path.exists(os.path.join(self.path, configuration_directory_name, configuration_file_name)))
        self.assertTrue(os.path.exists(os.path.join(self.path, configuration_directory_name, configuration_file_name + '.corrupt')))


class PostInitCommandMixIn(object):

    def get_command(self):
        return globals()[self.command] # a little hacky

    def test_command_raises_error_before_init(self):
        self.assertRaises(ConfigurationDirectoryNotFound, self.get_command())

    def test_command_runs_after_init(self):
        init()
        self.get_command()()


class TestStatCommand(CommandBase, PostInitCommandMixIn):

    command = 'stat'


class TestAddCommand(CommandBase, PostInitCommandMixIn):

    command = 'add'

    def test_add_a_file(self):
        init()
        file_name = 'file.ext'
        new_file = file(os.path.join(self.content_path, file_name), 'w')
        new_file.write("CONTENTS\nCONTENTS\n")
        add(file_name)
