import unittest
import os, shutil, tempfile, types, time
import pdb

from fragman.__main__ import ExecutionError, init, stat, follow, forget, commit
from fragman.config import configuration_file_name, configuration_directory_name, ConfigurationDirectoryNotFound, FragmanConfig


class CommandBase(unittest.TestCase):

    test_content_directory = 'test_content'

    def setUp(self):
        super(CommandBase, self).setUp()
        self.path = os.path.realpath(tempfile.mkdtemp())
        self.content_path = os.path.join(self.path, self.test_content_directory) 
        os.mkdir(self.content_path)
        self.assertTrue(os.path.exists(os.path.join(self.path, self.test_content_directory)))
        os.chdir(self.content_path)

    def tearDown(self):
        shutil.rmtree(self.path)
        super(CommandBase, self).tearDown()

    def _create_file(self, file_name='file.ext', contents='CONTENTS\nCONTENTS\n'):
        file_path = os.path.join(self.content_path, file_name)
        new_file = file(file_path, 'w')
        new_file.write(contents)
        return file_name, file_path


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

    def setUp(self):
        super(CommandBase, self).setUp()

    def test_command_attribute_set_properly(self):
        self.assertTrue(isinstance(self.command, types.FunctionType), 
            "%s.command attribute must be a staticmethod." % type(self).__name__)

    def test_command_raises_error_before_init(self):
        self.assertRaises(ConfigurationDirectoryNotFound, self.command)

    def test_command_runs_after_init(self):
        init()
        self.command()


class TestStatCommand(CommandBase, PostInitCommandMixIn):

    command = staticmethod(stat)


class TestfollowCommand(CommandBase, PostInitCommandMixIn):

    command = staticmethod(follow)

    def test_follow_a_file(self):
        init()
        file_name, file_path = self._create_file()
        follow(file_name)
        config = FragmanConfig()
        key = file_path[len(os.path.split(config.directory)[0])+1:]
        self.assertIn(key, config['files'])

    def test_file_twice_on_the_command_line(self):
        init()
        file_name, file_path = self._create_file()
        follow(file_name, file_name)
        config = FragmanConfig()
        key = file_path[len(os.path.split(config.directory)[0])+1:]
        self.assertIn(key, config['files'])

    def test_follow_file_two_times(self):
        init()
        file_name, file_path = self._create_file()
        follow(file_name)
        config = FragmanConfig()
        key = file_path[len(os.path.split(config.directory)[0])+1:]
        uuid = config['files'][key]
        follow(file_name)
        config = FragmanConfig()
        self.assertIn(key, config['files'])
        self.assertEquals(config['files'][key], uuid)

    def test_follow_two_files(self):
        init()
        file1_name, file1_path = self._create_file(file_name='file1.ext')
        file2_name, file2_path = self._create_file(file_name='file2.ext')
        follow(file1_name, file2_name)
        config = FragmanConfig()
        key1 = file1_path[len(os.path.split(config.directory)[0])+1:]
        key2 = file2_path[len(os.path.split(config.directory)[0])+1:]
        self.assertIn(key1, config['files'])
        self.assertIn(key2, config['files'])


class TestForgetCommand(CommandBase, PostInitCommandMixIn):

    command = staticmethod(forget)


class TestCommitCommand(CommandBase, PostInitCommandMixIn):

    command = staticmethod(commit)

    def test_commit_a_file(self):
        init()
        file_name, file_path = self._create_file()
        follow(file_name)
        commit(file_name)
        config = FragmanConfig()
        prefix = os.path.split(config.directory)[0]
        key = file_path[len(prefix)+1:]
        self.assertIn(key, config['files'])
        self.assertTrue(os.access(os.path.join(config.directory, config['files'][key]), os.R_OK|os.W_OK))
        self.assertEquals(
            file(os.path.join(config.directory, config['files'][key]), 'r').read(),
            file(file_path, 'r').read(),
        )

    def test_commit_and_modify_a_file(self):
        init()
        file_name, file_path = self._create_file()

        # pretend file was actually created two seconds ago
        # so that commit will detect changes
        yestersecond = time.time() - 2
        os.utime(file_path, (yestersecond, yestersecond))

        follow(file_name)
        commit(file_name)

        f = file(file_path, 'a')
        f.write("GIBBERISH!\n")
        f.close()

        config = FragmanConfig()
        prefix = os.path.split(config.directory)[0]
        key = file_path[len(prefix)+1:]

        self.assertIn(key, config['files'])
        self.assertTrue(os.access(os.path.join(config.directory, config['files'][key]), os.R_OK|os.W_OK))
        self.assertNotEquals(
            file(os.path.join(config.directory, config['files'][key]), 'r').read(),
            file(file_path, 'r').read(),
        )

        commit(file_name)
        self.assertEquals(
            file(os.path.join(config.directory, config['files'][key]), 'r').read(),
            file(file_path, 'r').read(),
        )
