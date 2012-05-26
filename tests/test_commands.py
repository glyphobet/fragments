import unittest
import os, shutil, tempfile, types, time
import pdb

from fragments import commands, __version__
from fragments.commands import ExecutionError
from fragments.config import configuration_file_name, configuration_directory_name, ConfigurationDirectoryNotFound, FragmentsConfig

def help  (*a): return list(commands.help  (*a))
def init  (*a): return list(commands.init  (*a))
def stat  (*a): return list(commands.stat  (*a))
def follow(*a): return list(commands.follow(*a))
def forget(*a): return list(commands.forget(*a))
def rename(*a): return list(commands.rename(*a))
def commit(*a): return list(commands.commit(*a))
def revert(*a): return list(commands.revert(*a))
def diff  (*a): return list(commands.diff  (*a))
def apply (*a, **kw): return list(commands.apply (*a, **kw))



class CommandBase(unittest.TestCase):

    test_content_directory = 'test_content'

    def setUp(self):
        super(CommandBase, self).setUp()
        self.file_counter = 1
        self.path = os.path.realpath(tempfile.mkdtemp())
        self.content_path = os.path.join(self.path, self.test_content_directory)
        os.mkdir(self.content_path)
        self.assertTrue(os.path.exists(os.path.join(self.path, self.test_content_directory)))
        os.chdir(self.content_path)

    def tearDown(self):
        shutil.rmtree(self.path)
        super(CommandBase, self).tearDown()

    def _create_file(self, file_name=None, contents='CONTENTS\nCONTENTS\n'):
        if file_name is None:
            file_name = 'file%d.ext' % self.file_counter
            self.file_counter += 1
        file_path = os.path.join(self.content_path, file_name)
        new_file = file(file_path, 'w')
        new_file.write(contents)
        return file_name, file_path


class TestHelpCommand(CommandBase):

    def test_help(self):
        help()


class TestInitCommand(CommandBase):

    def test_init_creates_fragments_directory_and_config_json(self):
        init()
        self.assertTrue(os.path.exists(os.path.join(self.path, configuration_directory_name)))
        self.assertTrue(os.path.exists(os.path.join(self.path, configuration_directory_name, configuration_file_name)))

    def test_init_raises_error_on_unwritable_parent(self):
        os.chmod(self.path, 0500)
        self.assertRaises(ExecutionError, init)
        os.chmod(self.path, 0700)

    def test_init_json(self):
        init()
        config = FragmentsConfig()
        self.assertIn('files', config)
        self.assertIn('version', config)
        self.assertIsInstance(config['files'], dict)
        self.assertIsInstance(config['version'], tuple)

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

    def test_stat(self):
        init()
        config = FragmentsConfig()
        self.assertEquals(stat(), [
            'fragments configuration version %s.%s.%s' % __version__,
            'stored in %s' % config.directory,
        ])

    def test_unknown_file_stat(self):
        init()
        file_name, file_path = self._create_file()
        config = FragmentsConfig()
        self.assertEquals(stat(file_name), [
            'fragments configuration version %s.%s.%s' % __version__,
            'stored in %s' % config.directory,
            '?\t%s' % file_path[len(config.root)+1:]
        ])

    def test_new_file_stat(self):
        init()
        file_name, file_path = self._create_file()
        follow(file_name)
        config = FragmentsConfig()
        self.assertEquals(stat(file_name), [
            'fragments configuration version %s.%s.%s' % __version__,
            'stored in %s' % config.directory,
            'A\t%s' % file_path[len(config.root)+1:]
        ])

    def test_unmodified_file_stat(self):
        init()
        file_name, file_path = self._create_file()
        follow(file_name)
        commit(file_name)
        config = FragmentsConfig()
        self.assertEquals(stat(file_name), [
            'fragments configuration version %s.%s.%s' % __version__,
            'stored in %s' % config.directory,
            ' \t%s' % file_path[len(config.root)+1:]
        ])

    def test_modified_file_stat(self):
        init()
        file_name, file_path = self._create_file()
        yestersecond = time.time() - 2
        os.utime(file_path, (yestersecond, yestersecond))
        follow(file_name)
        commit(file_name)
        config = FragmentsConfig()
        f = open(file_path, 'a')
        f.write("CHICKENS\n")
        f.close()
        self.assertEquals(stat(file_name), [
            'fragments configuration version %s.%s.%s' % __version__,
            'stored in %s' % config.directory,
            'M\t%s' % file_path[len(config.root)+1:]
        ])

    def test_removed_file_stat(self):
        init()
        file_name, file_path = self._create_file()
        follow(file_name)
        commit(file_name)

        config = FragmentsConfig()
        os.unlink(file_path)
        self.assertEquals(stat(file_name), [
            'fragments configuration version %s.%s.%s' % __version__,
            'stored in %s' % config.directory,
            'D\t%s' % file_path[len(config.root)+1:]
        ])

    def test_error_file_stat(self):
        init()
        file_name, file_path = self._create_file()
        follow(file_name)
        commit(file_name)
        config = FragmentsConfig()
        key = file_path[len(config.root)+1:]
        os.unlink(file_path)
        os.unlink(os.path.join(config.directory, config['files'][key]))
        self.assertEquals(stat(file_name), [
            'fragments configuration version %s.%s.%s' % __version__,
            'stored in %s' % config.directory,
            'E\t%s' % key
        ])


class TestFollowCommand(CommandBase, PostInitCommandMixIn):

    command = staticmethod(follow)

    def test_follow_file(self):
        init()
        file_name, file_path = self._create_file()
        follow_output = follow(file_name)
        config = FragmentsConfig()
        key = file_path[len(os.path.split(config.directory)[0])+1:]
        self.assertIn(key, config['files'])
        self.assertEquals(follow_output, ["'%s' is now being followed, UUID %s" % (file_name,config['files'][key])])

    def test_file_twice_on_the_command_line(self):
        init()
        file_name, file_path = self._create_file()
        follow(file_name, file_name)
        config = FragmentsConfig()
        key = file_path[len(os.path.split(config.directory)[0])+1:]
        self.assertIn(key, config['files'])

    def test_follow_file_two_times(self):
        init()
        file_name, file_path = self._create_file()
        follow(file_name)
        config = FragmentsConfig()
        key = file_path[len(os.path.split(config.directory)[0])+1:]
        uuid = config['files'][key]
        follow(file_name)
        config = FragmentsConfig()
        self.assertIn(key, config['files'])
        self.assertEquals(config['files'][key], uuid)

    def test_follow_two_files(self):
        init()
        file1_name, file1_path = self._create_file()
        file2_name, file2_path = self._create_file()
        follow(file1_name, file2_name)
        config = FragmentsConfig()
        key1 = file1_path[len(os.path.split(config.directory)[0])+1:]
        key2 = file2_path[len(os.path.split(config.directory)[0])+1:]
        self.assertIn(key1, config['files'])
        self.assertIn(key2, config['files'])

    def test_follow_nonexistent_file(self):
        init()
        nonexistent_path = os.path.join(os.getcwd(), 'nonexistent.file')
        self.assertEquals(follow(nonexistent_path), ["Could not access %r to follow it" % nonexistent_path])

    def test_follow_file_outside_repository(self):
        init()
        outside_path = os.path.realpath(tempfile.mkdtemp())
        outside_file = os.path.join(outside_path, 'outside.repository')
        self.assertEquals(follow(outside_path), ["Could not follow %r; it is outside the repository" % outside_path])


class TestForgetCommand(CommandBase, PostInitCommandMixIn):

    command = staticmethod(forget)

    def test_forget_unfollowed_file(self):
        init()
        file_name, file_path = self._create_file()
        self.assertEquals(forget(file_name), ["Could not forget %r, it was not being followed" % file_name])

    def test_follow_forget_file(self):
        init()
        file_name, file_path = self._create_file()
        follow(file_name)
        config = FragmentsConfig()
        key = file_path[len(os.path.split(config.directory)[0])+1:]
        uuid = config['files'][key]
        forget(file_name)
        config = FragmentsConfig()
        key = file_path[len(os.path.split(config.directory)[0])+1:]
        self.assertNotIn(key, config['files'])
        self.assertFalse(os.path.exists(os.path.join(config.directory, uuid)))

    def test_follow_commit_forget_file(self):
        init()
        file_name, file_path = self._create_file()
        follow(file_name)
        config = FragmentsConfig()
        key = file_path[len(os.path.split(config.directory)[0])+1:]
        uuid = config['files'][key]
        commit(file_name)
        forget(file_name)
        config = FragmentsConfig()
        key = file_path[len(os.path.split(config.directory)[0])+1:]
        self.assertNotIn(key, config['files'])
        self.assertFalse(os.path.exists(os.path.join(config.directory, uuid)))

    def test_forget_file_outside_repository(self):
        init()
        outside_path = os.path.realpath(tempfile.mkdtemp())
        outside_file = os.path.join(outside_path, 'outside.repository')
        self.assertEquals(forget(outside_file), ["Could not forget %r; it is outside the repository" % outside_file])


class TestRenameCommand(CommandBase, PostInitCommandMixIn):

    command = staticmethod(lambda : rename('foo', 'bar'))

    def test_cant_rename_followed_file(self):
        init()
        file_name, file_path = self._create_file()
        self.assertEquals(rename(file_name, 'new_file'), ["Could not rename %r, it is not being tracked" % file_name])

    def test_cant_rename_onto_other_followed_file(self):
        init()
        file1_name, file1_path = self._create_file()
        file2_name, file2_path = self._create_file()
        follow(file1_name, file2_name)
        commit(file1_name, file2_name)
        self.assertEquals(rename(file1_name, file2_name), ["Could not rename %r to %r, %r is already being tracked" % (file1_name, file2_name, file2_name)])

    def test_cant_rename_onto_existing_file(self):
        init()
        file1_name, file1_path = self._create_file()
        file2_name, file2_path = self._create_file()
        follow(file1_name)
        commit(file1_name)
        self.assertEquals(rename(file1_name, file2_name), ["Could not rename %r to %r, both files already exist" % (file1_name, file2_name)])

    def test_cant_rename_if_neither_file_exists(self):
        init()
        file1_name, file1_path = self._create_file()
        file2_name, file2_path = self._create_file()
        follow(file1_name)
        commit(file1_name)
        os.unlink(file1_path)
        os.unlink(file2_path)
        self.assertEquals(rename(file1_name, file2_name), ["Could not rename %r to %r, neither file exists" % (file1_name, file2_name)])

    def test_rename_moves_file_if_not_already_moved(self):
        init()
        file1_name, file1_path = self._create_file()
        follow(file1_name)
        commit(file1_name)
        self.assertEquals(rename(file1_name, 'other.ext'), [])
        self.assertFalse(os.access(file1_path, os.R_OK|os.W_OK))
        self.assertTrue(os.access('other.ext', os.R_OK|os.W_OK))
        config = FragmentsConfig()
        old_key = file1_path[len(config.root)+1:]
        new_key = os.path.realpath('other.ext')[len(config.root)+1:]
        self.assertNotIn(old_key, config['files'])
        self.assertIn(new_key, config['files'])

    def test_rename_succeeds_if_file_already_moved(self):
        init()
        file1_name, file1_path = self._create_file()
        follow(file1_name)
        commit(file1_name)
        os.rename(file1_name, 'other.ext')
        self.assertEquals(rename(file1_name, 'other.ext'), [])
        self.assertFalse(os.access(file1_path, os.R_OK|os.W_OK))
        self.assertTrue(os.access('other.ext', os.R_OK|os.W_OK))
        config = FragmentsConfig()
        old_key = file1_path[len(config.root)+1:]
        new_key = os.path.realpath('other.ext')[len(config.root)+1:]
        self.assertNotIn(old_key, config['files'])
        self.assertIn(new_key, config['files'])


class TestCommitCommand(CommandBase, PostInitCommandMixIn):

    command = staticmethod(commit)

    def test_commit_file(self):
        init()
        file_name, file_path = self._create_file()
        follow(file_name)
        commit(file_name)
        config = FragmentsConfig()
        prefix = os.path.split(config.directory)[0]
        key = file_path[len(prefix)+1:]
        self.assertIn(key, config['files'])
        self.assertTrue(os.access(os.path.join(config.directory, config['files'][key]), os.R_OK|os.W_OK))
        self.assertEquals(
            file(os.path.join(config.directory, config['files'][key]), 'r').read(),
            file(file_path, 'r').read(),
        )

    def test_commit_modify_commit_file(self):
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

        config = FragmentsConfig()
        key = file_path[len(config.root)+1:]

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

    def test_commit_unfollowed_file(self):
        init()
        file_name, file_path = self._create_file()
        config = FragmentsConfig()
        key = file_path[len(config.root)+1:]
        self.assertEquals(commit(file_path), ["Could not commit %r because it is not being followed" % key])

    def test_commit_removed_file(self):
        init()
        file_name, file_path = self._create_file()
        follow(file_name)
        commit(file_path)
        os.unlink(file_path)
        config = FragmentsConfig()
        key = file_path[len(config.root)+1:]
        self.assertEquals(commit(file_path), ["Could not commit %r because it has been removed, instead revert or remove it" % key])

    def test_commit_unchanged_file(self):
        init()
        file_name, file_path = self._create_file()
        yestersecond = time.time() - 2
        os.utime(file_path, (yestersecond, yestersecond))
        original_content = file(file_path, 'r').read()

        follow(file_name)
        commit(file_name)
        self.assertEquals(commit(file_name), [])


class TestRevertCommand(CommandBase, PostInitCommandMixIn):

    command = staticmethod(revert)

    def test_commit_modify_revert_file(self):
        init()
        file_name, file_path = self._create_file()
        original_content = file(file_path, 'r').read()

        # pretend file was actually created two seconds ago
        # so that commit will detect changes
        yestersecond = time.time() - 2
        os.utime(file_path, (yestersecond, yestersecond))

        follow(file_name)
        commit(file_name)

        f = file(file_path, 'a')
        f.write("GIBBERISH!\n")
        f.close()

        config = FragmentsConfig()
        prefix = os.path.split(config.directory)[0]
        key = file_path[len(prefix)+1:]

        self.assertIn(key, config['files'])
        self.assertTrue(os.access(os.path.join(config.directory, config['files'][key]), os.R_OK|os.W_OK))
        self.assertNotEquals(
            file(os.path.join(config.directory, config['files'][key]), 'r').read(),
            file(file_path, 'r').read(),
        )

        revert(file_name)
        self.assertEquals(
            file(os.path.join(config.directory, config['files'][key]), 'r').read(),
            file(file_path, 'r').read(),
        )

        self.assertEquals(
            original_content,
            file(file_path, 'r').read(),
        )

    def test_follow_modify_revert_file(self):
        init()
        file_name, file_path = self._create_file()
        original_content = file(file_path, 'r').read()

        # pretend file was actually created two seconds ago
        # so that commit will detect changes
        yestersecond = time.time() - 2
        os.utime(file_path, (yestersecond, yestersecond))

        follow(file_name)
        config = FragmentsConfig()
        key = file_path[len(config.root)+1:]
        self.assertEquals(revert(file_name), ["Could not revert %r because it has never been committed" % key])

    def test_revert_unfollowed_file(self):
        init()
        file_name, file_path = self._create_file()
        config = FragmentsConfig()
        key = file_path[len(config.root)+1:]
        self.assertEquals(revert(file_name), ["Could not revert %r because it is not being followed" % key])

    def test_revert_removed_file(self):
        init()
        file_name, file_path = self._create_file()
        original_content = file(file_path, 'r').read()

        follow(file_name)
        commit(file_name)
        os.unlink(file_path)
        revert(file_name)

        self.assertEquals(
            original_content,
            file(file_path, 'r').read(),
        )

    def test_revert_unchanged_file(self):
        init()
        file_name, file_path = self._create_file()
        original_content = file(file_path, 'r').read()

        follow(file_name)
        commit(file_name)
        self.assertEquals(revert(file_name), [])


class TestDiffCommand(CommandBase, PostInitCommandMixIn):

    maxDiff = None
    command = staticmethod(diff)
    original_file = "Line One\nLine Two\nLine Three\nLine Four\nLine Five\n"

    def test_diff(self):
        init()
        file1_name, file1_path = self._create_file(contents=self.original_file)
        yestersecond = time.time() - 2
        os.utime(file1_path, (yestersecond, yestersecond))

        follow(file1_name)
        commit(file1_name)
        file(file1_name, 'w').write(self.original_file.replace('Line Three', 'Line 2.6666\nLine Three and One Third'))
        self.assertEquals(list(diff(file1_name)), [
            '--- test_content/file1.ext',
            '+++ test_content/file1.ext',
            '@@ -1,5 +1,6 @@',
            ' Line One',
            ' Line Two',
            '-Line Three',
            '+Line 2.6666',
            '+Line Three and One Third',
            ' Line Four',
            ' Line Five'])

    def test_two_nearby_section_diff(self):
        init()
        file1_name, file1_path = self._create_file(contents=self.original_file)
        yestersecond = time.time() - 2
        os.utime(file1_path, (yestersecond, yestersecond))

        follow(file1_name)
        commit(file1_name)
        file(file1_name, 'w').write(self.original_file.replace('Line One', 'Line 0.999999').replace('Line Five', 'Line 4.999999'))
        self.assertEquals(list(diff(file1_name)), [
            '--- test_content/file1.ext',
            '+++ test_content/file1.ext',
            '@@ -1,5 +1,5 @@',
            '-Line One',
            '+Line 0.999999',
            ' Line Two',
            ' Line Three',
            ' Line Four',
            '-Line Five',
            '+Line 4.999999'])


    def test_two_distant_section_diff(self):
        original_file = "Line One\nLine Two\nLine Three\nLine Four\nLine Five\nLine Six\nLine Seven\nLine Eight\nLine Nine\n"
        init()
        file1_name, file1_path = self._create_file(contents=original_file)
        yestersecond = time.time() - 2
        os.utime(file1_path, (yestersecond, yestersecond))

        follow(file1_name)
        commit(file1_name)
        file(file1_name, 'w').write(original_file.replace('Line One', 'Line 0.999999').replace('Line Nine', 'Line 8.999999'))
        self.assertEquals(list(diff(file1_name)), [
            '--- test_content/file1.ext',
            '+++ test_content/file1.ext',
            '@@ -1,4 +1,4 @@',
            '-Line One',
            '+Line 0.999999',
            ' Line Two',
            ' Line Three',
            ' Line Four',
            '@@ -6,4 +6,4 @@',
            ' Line Six',
            ' Line Seven',
            ' Line Eight',
            '-Line Nine',
            '+Line 8.999999'])


    def test_unmodified_file_diff(self):
        init()
        file1_name, file1_path = self._create_file(contents=self.original_file)
        yestersecond = time.time() - 2
        os.utime(file1_path, (yestersecond, yestersecond))

        follow(file1_name)
        commit(file1_name)
        self.assertEquals(list(diff(file1_name)), [])

    def test_mtime_different_but_not_contents_diff(self):
        init()
        file1_name, file1_path = self._create_file(contents=self.original_file)
        now = time.time()
        yestersecond = now - 2
        os.utime(file1_path, (yestersecond, yestersecond))

        follow(file1_name)
        commit(file1_name)
        os.utime(file1_path, (now, now))
        self.assertEquals(list(diff(file1_name)), [])

    def test_diff_unfollowed_file(self):
        init()
        file1_name, file1_path = self._create_file(contents=self.original_file)
        yestersecond = time.time() - 2
        os.utime(file1_path, (yestersecond, yestersecond))
        self.assertEquals(list(diff(file1_name)), ["Could not diff 'test_content/file1.ext', it is not being followed"])

    def test_diff_uncommitted_file(self):
        init()
        file1_name, file1_path = self._create_file(contents=self.original_file)
        yestersecond = time.time() - 2
        os.utime(file1_path, (yestersecond, yestersecond))

        follow(file1_path)
        self.assertEquals(list(diff(file1_name)), [
            '--- test_content/file1.ext',
            '+++ test_content/file1.ext',
            '@@ -0,0 +1,5 @@',
            '+Line One',
            '+Line Two',
            '+Line Three',
            '+Line Four',
            '+Line Five'])

    def test_diff_removed_file(self):
        init()
        file1_name, file1_path = self._create_file(contents=self.original_file)
        yestersecond = time.time() - 2
        os.utime(file1_path, (yestersecond, yestersecond))

        follow(file1_path)
        commit(file1_path)
        
        os.unlink(file1_path)
        self.assertEquals(list(diff(file1_name)), [
            '--- test_content/file1.ext',
            '+++ test_content/file1.ext',
            '@@ -1,5 +0,0 @@',
            '-Line One',
            '-Line Two',
            '-Line Three',
            '-Line Four',
            '-Line Five'])

    def test_diff_uncommitted_removed_file(self):
        init()
        file1_name, file1_path = self._create_file(contents=self.original_file)
        yestersecond = time.time() - 2
        os.utime(file1_path, (yestersecond, yestersecond))

        follow(file1_path)
        os.unlink(file1_path)
        self.assertEquals(list(diff(file1_name)), [])


class TestApplyCommand(CommandBase, PostInitCommandMixIn):
    maxDiff = None
    command = staticmethod(lambda : apply('file.ext'))

    html_file1_contents = """<!DOCTYPE html>
<html>
    <head>
        <title>
            Page One
        </title>
        <link href="default.css" />
        <link href="site.css" />
        <script href="script.js" />
        <script href="other.js" />
        <script type="text/javascript">
            var whole = function (buncha) {
                $tuff;
            };
        </script>
    </head>
    <body>
        <h1>One</h1>
    </body>
</html>"""

    html_file2_contents = """<!DOCTYPE html>
<html>
    <head>
        <title>
            Page Two
        </title>
        <link href="default.css" />
        <link href="site.css" />
        <link href="custom.css" />
        <script href="script.js" />
        <script href="other.js" />
    </head>
    <body>
        <h1>Two</h1>
    </body>
</html>"""

    css_file1_contents = """
body {
    margin-left: 0em;
    background-attachment: fixed;
}
table {
    content: "this is totally random";
}
"""

    def test_apply(self):
        init()
        file1_name, file1_path = self._create_file(contents=self.html_file1_contents)
        follow(file1_name)
        commit(file1_name)

        file2_name, file2_path = self._create_file(contents=self.html_file2_contents)
        follow(file2_name)
        commit(file2_name)

        new_file1_contents = self.html_file1_contents.replace('<link href="default.css" />', '<link href="layout.css" />\n        <link href="colors.css" />')
        open(file1_name, 'w').write(new_file1_contents)
        self.assertEqual(apply(file1_name, interactive=False), [
            '@@ -4,7 +4,8 @@',
            '         <title>',
            '             Page One',
            '         </title>',
            '-        <link href="default.css" />',
            '+        <link href="layout.css" />',
            '+        <link href="colors.css" />',
            '         <link href="site.css" />',
            '         <script href="script.js" />',
            '         <script href="other.js" />',
            "Changes in 'test_content/file1.ext' applied cleanly to u'test_content/file2.ext'"
        ])

        target_file2_contents = self.html_file2_contents.replace('<link href="default.css" />', '<link href="layout.css" />\n        <link href="colors.css" />')
        self.assertEqual(open(file2_name, 'r').read(), target_file2_contents)

    def test_apply_interactive_yes(self):
        init()
        file1_name, file1_path = self._create_file(contents=self.html_file1_contents)
        follow(file1_name)
        commit(file1_name)

        file2_name, file2_path = self._create_file(contents=self.html_file2_contents)
        follow(file2_name)
        commit(file2_name)

        new_file1_contents = self.html_file1_contents.replace('<link href="default.css" />', '<link href="layout.css" />\n        <link href="colors.css" />')
        open(file1_name, 'w').write(new_file1_contents)

        apply_generator = commands.apply(file1_name)

        self.assertEqual(next(apply_generator), '@@ -4,7 +4,8 @@'                     )
        self.assertEqual(next(apply_generator), '         <title>'                    )
        self.assertEqual(next(apply_generator), '             Page One'               )
        self.assertEqual(next(apply_generator), '         </title>'                   )
        self.assertEqual(next(apply_generator), '-        <link href="default.css" />')
        self.assertEqual(next(apply_generator), '+        <link href="layout.css" />' )
        self.assertEqual(next(apply_generator), '+        <link href="colors.css" />' )
        self.assertEqual(next(apply_generator), '         <link href="site.css" />'   )
        self.assertEqual(next(apply_generator), '         <script href="script.js" />')
        self.assertEqual(next(apply_generator), '         <script href="other.js" />' )
        self.assertEqual(next(apply_generator), 'Apply this change? y/n')
        self.assertEqual(apply_generator.send('y'), "Changes in 'test_content/file1.ext' applied cleanly to u'test_content/file2.ext'")

        target_file2_contents = self.html_file2_contents.replace('<link href="default.css" />', '<link href="layout.css" />\n        <link href="colors.css" />')
        self.assertEqual(open(file2_name, 'r').read(), target_file2_contents)

    def test_apply_interactive_no(self):
        init()
        file1_name, file1_path = self._create_file(contents=self.html_file1_contents)
        follow(file1_name)
        commit(file1_name)

        file2_name, file2_path = self._create_file(contents=self.html_file2_contents)
        follow(file2_name)
        commit(file2_name)

        new_file1_contents = self.html_file1_contents.replace('<link href="default.css" />', '<link href="layout.css" />\n        <link href="colors.css" />')
        open(file1_name, 'w').write(new_file1_contents)

        apply_generator = commands.apply(file1_name)

        self.assertEqual(next(apply_generator), '@@ -4,7 +4,8 @@'                     )
        self.assertEqual(next(apply_generator), '         <title>'                    )
        self.assertEqual(next(apply_generator), '             Page One'               )
        self.assertEqual(next(apply_generator), '         </title>'                   )
        self.assertEqual(next(apply_generator), '-        <link href="default.css" />')
        self.assertEqual(next(apply_generator), '+        <link href="layout.css" />' )
        self.assertEqual(next(apply_generator), '+        <link href="colors.css" />' )
        self.assertEqual(next(apply_generator), '         <link href="site.css" />'   )
        self.assertEqual(next(apply_generator), '         <script href="script.js" />')
        self.assertEqual(next(apply_generator), '         <script href="other.js" />' )
        self.assertEqual(next(apply_generator), 'Apply this change? y/n')
        self.assertEqual(apply_generator.send('n'), "Changes in 'test_content/file1.ext' applied cleanly to u'test_content/file2.ext'")

        self.assertEqual(open(file2_name, 'r').read(), self.html_file2_contents)

    def test_cant_apply_nonexistent_file(self):
        init()
        self.assertEqual(apply("nonexistent.file"), ["Could not apply changes in 'test_content/nonexistent.file', it is not being followed"])

    def test_cant_apply_unfollowed_file(self):
        init()
        file1_name, file1_path = self._create_file(contents=self.html_file1_contents)
        os.unlink(file1_path)
        self.assertEqual(apply(file1_name), ["Could not apply changes in 'test_content/file1.ext', it is not being followed"])

    def test_cant_apply_removed_file(self):
        init()
        file1_name, file1_path = self._create_file(contents=self.html_file1_contents)
        follow(file1_name)
        commit(file1_name)
        os.unlink(file1_path)
        self.assertEqual(apply(file1_name), ["Could not apply changes in 'test_content/file1.ext', it no longer exists on disk"])

    def test_cant_apply_uncommitted_file(self):
        init()
        file1_name, file1_path = self._create_file(contents=self.html_file1_contents)
        follow(file1_name)
        self.assertEqual(apply(file1_name), ["Could not apply changes in 'test_content/file1.ext', it has never been committed"])

    def test_cant_apply_missing_history_file(self):
        init()
        file1_name, file1_path = self._create_file(contents=self.html_file1_contents)
        follow(file1_name)
        commit(file1_name)
        config = FragmentsConfig()
        key = file1_path[len(config.root)+1:]
        uuid_path = os.path.join(config.directory, config['files'][key])
        os.unlink(uuid_path)
        self.assertEqual(apply(file1_name), ["Could not apply changes in 'test_content/file1.ext', it has never been committed"])

    def test_apply_detects_convergent_changes(self):
        init()
        file1_name, file1_path = self._create_file(contents=self.html_file1_contents)
        follow(file1_name)
        commit(file1_name)

        file2_name, file2_path = self._create_file(contents=self.html_file2_contents)
        follow(file2_name)
        commit(file2_name)

        new_file1_contents = self.html_file1_contents.replace('<link href="default.css" />', '<link href="layout.css" />\n        <link href="colors.css" />')
        open(file1_name, 'w').write(new_file1_contents)

        new_file2_contents = self.html_file2_contents.replace('<link href="default.css" />', '<link href="layout.css" />\n        <link href="colors.css" />')
        open(file2_name, 'w').write(new_file2_contents)

        self.assertEqual(apply(file1_name, interactive=False), [
            '@@ -4,7 +4,8 @@',
            '         <title>',
            '             Page One',
            '         </title>',
            '-        <link href="default.css" />',
            '+        <link href="layout.css" />',
            '+        <link href="colors.css" />',
            '         <link href="site.css" />',
            '         <script href="script.js" />',
            '         <script href="other.js" />',
            "Changes in 'test_content/file1.ext' applied cleanly to u'test_content/file2.ext'"
        ])

        self.assertEqual(open(file2_name, 'r').read(), new_file2_contents)

    def test_apply_skips_unrelated_files(self):
        init()
        file1_name, file1_path = self._create_file(contents=self.html_file1_contents)
        follow(file1_name)
        commit(file1_name)

        file2_name, file2_path = self._create_file(contents=self.html_file2_contents)
        follow(file2_name)
        commit(file2_name)

        css_name, css_path = self._create_file(contents=self.css_file1_contents)
        follow(css_name)
        commit(css_name)

        new_file1_contents = self.html_file1_contents.replace('<link href="default.css" />', '<link href="layout.css" />\n        <link href="colors.css" />')
        open(file1_name, 'w').write(new_file1_contents)

        self.assertEqual(apply(file1_name, interactive=False), [
            '@@ -4,7 +4,8 @@',
            '         <title>',
            '             Page One',
            '         </title>',
            '-        <link href="default.css" />',
            '+        <link href="layout.css" />',
            '+        <link href="colors.css" />',
            '         <link href="site.css" />',
            '         <script href="script.js" />',
            '         <script href="other.js" />',
            "Changes in 'test_content/file1.ext' cannot apply to u'test_content/file3.ext', skipping",
            "Changes in 'test_content/file1.ext' applied cleanly to u'test_content/file2.ext'"
        ])
        self.assertEqual(open(css_name, 'r').read(), self.css_file1_contents)

    def test_apply_generates_conflict(self):
        init()
        file1_name, file1_path = self._create_file(contents=self.html_file1_contents)
        follow(file1_name)
        commit(file1_name)

        file2_name, file2_path = self._create_file(contents=self.html_file2_contents)
        follow(file2_name)
        commit(file2_name)

        new_file1_contents = self.html_file1_contents.replace('<link href="default.css" />', '<link href="layout.css" />')
        open(file1_name, 'w').write(new_file1_contents)
        new_file2_contents = self.html_file2_contents.replace('<link href="default.css" />', '<link href="colors.css" />')
        open(file2_name, 'w').write(new_file2_contents)

        self.assertEqual(apply(file1_name, interactive=False), [
            '@@ -4,7 +4,7 @@',
            '         <title>',
            '             Page One',
            '         </title>',
            '-        <link href="default.css" />',
            '+        <link href="layout.css" />',
            '         <link href="site.css" />',
            '         <script href="script.js" />',
            '         <script href="other.js" />',
            "Conflict merging 'test_content/file1.ext' => u'test_content/file2.ext'"
        ])
        self.assertEqual(open(file2_name, 'r').read(), new_file2_contents.replace('        <link href="colors.css" />', '''>>>>>>>
        <link href="layout.css" />
=======
        <link href="colors.css" />
>>>>>>>'''))
