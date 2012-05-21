import os
import pdb
from .precisecodevillemerge import Weave

def apply_changes(changed_path, config):
    weave = Weave()
    changed_key = changed_path[len(config.root)+1:]
    if changed_key not in config['files']:
        yield "Could not apply changes in %r, it is not being followed" % changed_key
        return
    elif not os.access(changed_path, os.R_OK|os.W_OK):
        yield "Could not apply changes in %r, it no longer exists on disk" % changed_key
        return

    changed_uuid = config['files'][changed_key]
    old_path = os.path.join(config.directory, changed_uuid)

    if not os.access(old_path, os.R_OK|os.W_OK):
        yield "Could not apply changes in %r, it has never been committed" % changed_key
        return

    weave.add_revision(1, file(old_path, 'r').readlines(), [])
    weave.add_revision(2, file(changed_path, 'r').readlines(), [1])

    for i, other_key in enumerate(config['files']):
        other_path = os.path.join(config.root, other_key)
        if other_path == changed_path:
            continue # don't try to apply changes to ourself
        revision = i + 3
        weave.add_revision(revision, file(other_path, 'r').readlines(), [])
        merge_result = weave.cherry_pick(2, revision) # Can I apply changes in revision 2 onto this other file?
        if tuple in (type(mr) for mr in merge_result):
            if len(merge_result) == 1:
                # total conflict, skip
                yield "Changes in %r cannot apply to %r, skipping" % (changed_key, other_key)
                continue
            other_file = file(other_path, 'w')
            for line_or_conflict in merge_result:
                if isinstance(line_or_conflict, basestring):
                    other_file.write(line_or_conflict)
                else:
                    other_file.write('>'*7 + '\n')
                    for line in line_or_conflict[0]:
                        other_file.write(line)
                    other_file.write('='*7 + '\n')
                    for line in line_or_conflict[1]:
                        other_file.write(line)
                    other_file.write('>'*7 + '\n')
            other_file.close()
            yield "Conflict merging %r => %r" % (changed_key, other_key)
        else:
            # Merge is clean:
            other_file = file(other_path, 'w')
            other_file.writelines(merge_result)
            other_file.close()
            yield "Changes in %r applied cleanly to %r" % (changed_key, other_key)
