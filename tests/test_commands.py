import unittest
import os, shutil, tempfile, types, time
import pdb

from fragments import commands
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
def apply (*a): return list(commands.apply (*a))



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
        self.assertIsInstance(config['version'], list)

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


class TestFollowCommand(CommandBase, PostInitCommandMixIn):

    command = staticmethod(follow)

    def test_follow_file(self):
        init()
        file_name, file_path = self._create_file()
        follow(file_name)
        config = FragmentsConfig()
        key = file_path[len(os.path.split(config.directory)[0])+1:]
        self.assertIn(key, config['files'])

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
        follow(nonexistent_path)

    def test_follow_file_outside_repository(self):
        init()
        outside_path = os.path.realpath(tempfile.mkdtemp())
        outside_file = os.path.join(outside_path, 'outside.repository')
        follow(outside_path)


class TestForgetCommand(CommandBase, PostInitCommandMixIn):

    command = staticmethod(forget)

    def test_forget_unfollowed_file(self):
        init()
        file_name, file_path = self._create_file()
        forget(file_name)

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
        forget(outside_path)


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

    def test_commit_unfollowed_file(self):
        init()
        file_name, file_path = self._create_file()
        commit(file_path)

    def test_commit_removed_file(self):
        init()
        file_name, file_path = self._create_file()
        follow(file_name)
        os.unlink(file_path)
        commit(file_name)


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
        revert(file_name)

    def test_revert_unfollowed_file(self):
        init()
        file_name, file_path = self._create_file()
        revert(file_name)

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


class TestDiffCommand(CommandBase, PostInitCommandMixIn):

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
            '--- test_content/file1.ext\n',
            '+++ test_content/file1.ext\n',
            '@@ -1,5 +1,6 @@\n',
            ' Line One\n',
            ' Line Two\n',
            '-Line Three\n',
            '+Line 2.6666\n',
            '+Line Three and One Third\n',
            ' Line Four\n',
            ' Line Five\n'])

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
            '--- test_content/file1.ext\n',
            '+++ test_content/file1.ext\n',
            '@@ -0,0 +1,5 @@\n',
            '+Line One\n',
            '+Line Two\n',
            '+Line Three\n',
            '+Line Four\n',
            '+Line Five\n'])

    def test_diff_removed_file(self):
        init()
        file1_name, file1_path = self._create_file(contents=self.original_file)
        yestersecond = time.time() - 2
        os.utime(file1_path, (yestersecond, yestersecond))

        follow(file1_path)
        commit(file1_path)
        
        os.unlink(file1_path)
        self.assertEquals(list(diff(file1_name)), [
            '--- test_content/file1.ext\n',
            '+++ test_content/file1.ext\n',
            '@@ -1,5 +0,0 @@\n',
            '-Line One\n',
            '-Line Two\n',
            '-Line Three\n',
            '-Line Four\n',
            '-Line Five\n'])

    def test_diff_uncommitted_removed_file(self):
        init()
        file1_name, file1_path = self._create_file(contents=self.original_file)
        yestersecond = time.time() - 2
        os.utime(file1_path, (yestersecond, yestersecond))

        follow(file1_path)
        os.unlink(file1_path)
        self.assertEquals(list(diff(file1_name)), [])


class TestApplyCommand(CommandBase, PostInitCommandMixIn):

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

    command = staticmethod(lambda : apply('file.ext'))

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
        apply(file1_name)

        target_file2_contents = self.html_file2_contents.replace('<link href="default.css" />', '<link href="layout.css" />\n        <link href="colors.css" />')
        self.assertEqual(open(file2_name, 'r').read(), target_file2_contents)

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

        apply(file1_name)

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

        apply(file1_name)
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

        self.assertEqual(apply(file1_name), ["Conflict merging 'test_content/file1.ext' => u'test_content/file2.ext'"])
        self.assertEqual(apply(file2_name), ["Conflict merging 'test_content/file2.ext' => u'test_content/file1.ext'"])
