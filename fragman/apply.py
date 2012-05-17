import os
import pdb
from .precisecodevillemerge import Weave

def apply_changes(changed_path, config):
    weave = Weave()
    changed_key = changed_path[len(config.root)+1:]
    changed_uuid = config['files'][changed_key]
    weave.add_revision(1, file(os.path.join(config.directory, changed_uuid), 'r').readlines(), [])
    weave.add_revision(2, file(changed_path, 'r').readlines(), [1])

    for i, other_key in enumerate(config['files']):
        revision = i + 3
        other_path = os.path.join(config.root, other_key)
        if other_path == changed_path:
            continue # don't try to apply changes to ourself
        weave.add_revision(revision, file(other_path, 'r').readlines(), [])
        merge_result = weave.cherry_pick(2, revision) # Can I apply changes in revision 2 onto this other file?
        if tuple in (type(mr) for mr in merge_result):
            if len(merge_result) == 1:
                # total conflict, skip
                yield "Changes in %r cannot apply to %r, skipping" % (changed_key, other_key)
            # recover!
            yield "NEED TO RECOVER %r => %r" % (changed_key, other_key)
        else:
            # Merge is clean:
            other_file = file(other_path, 'w')
            other_file.writelines(merge_result)
            other_file.close()
            yield "Changes in %r applied cleanly to %r" % (changed_key, other_key)
