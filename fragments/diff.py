# -*- coding: utf-8
from __future__ import unicode_literals

from . import color

def _visible_in_diff(merge_result, context_lines=3):
    """Collects the set of lines that should be visible in a diff with a certain number of context lines"""
    i = old_line = new_line = 0
    while i < len(merge_result):
        line_or_conflict = merge_result[i]
        if isinstance(line_or_conflict, tuple):
            yield old_line, new_line, line_or_conflict
            old_line += len(line_or_conflict[0])
            new_line += len(line_or_conflict[1])
        else:
            for j in (list(range(max(0, i-context_lines), i                                        )) +  # look behind for nearby conflicts
                      list(range(i+1                    , min(len(merge_result), i+1+context_lines)))):  # look ahead for nearby conflicts
                if isinstance(merge_result[j], tuple):
                    yield old_line, new_line, line_or_conflict
                    break
            else:
                yield None # sentinel to mark boundaries between diff section groups
            old_line += 1
            new_line += 1
        i += 1
    yield None


def _split_diff(merge_result, context_lines=3):
    """Split diffs and context lines into groups based on None sentinel"""
    collect = []
    for item in _visible_in_diff(merge_result, context_lines=context_lines):
        if item is None:
            if collect:
                yield collect
            collect = []
        else:
            collect.append(item)


def _diff_group_position(group):
    """Generate a unified diff position line for a diff group"""
    old_start = group[0][0]
    new_start = group[0][1]
    old_length = new_length = 0
    for old_line, new_line, line_or_conflict in group:
        if isinstance(line_or_conflict, tuple):
            old, new = line_or_conflict
            old_length += len(old)
            new_length += len(new)
        else:
            old_length += 1
            new_length += 1
    if old_length:
        old_start += 1
    if new_length:
        new_start += 1

    return color.LineNumber('@@ -%s,%s +%s,%s @@' % (old_start, old_length, new_start, new_length))


def _diff_group(group):
    """Generate a diff section for diff group"""
    yield _diff_group_position(group)

    for old_line, new_line, line_or_conflict in group:
        if isinstance(line_or_conflict, tuple):
            old, new = line_or_conflict
            for o in old:
                yield color.Deleted('-' + o.strip('\n'))

            if new and old and new[-1].endswith('\n') and not old[-1].endswith('\n'): # new last line has a newline but old last line doesn't
                yield "\ No newline at end of file"

            for n in new:
                yield color.Added('+' + n.strip('\n'))

            if old and new and old[-1].endswith('\n') and not new[-1].endswith('\n'): # old last line has a newline but new last line doesn't
                yield "\ No newline at end of file"

        else:
            yield ' ' + line_or_conflict.strip('\n')


def _full_diff(merge_result, key, context_lines=3):
    """Generate a full diff based on a Weave merge result"""
    header_printed = False
    for group in _split_diff(merge_result, context_lines=context_lines):
        if not header_printed:
            header_printed = True
            yield color.Header('diff a/%s b/%s' % (key, key))
            yield color.DeletedHeader('--- %s' % key)
            yield color.AddedHeader('+++ %s' % key)

        for l in _diff_group(group):
            yield l
