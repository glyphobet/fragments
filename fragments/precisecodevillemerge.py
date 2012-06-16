# This code is based on code from
#   http://revctrl.org/PreciseCodevilleMerge?action=AttachFile
# That code was in turn based on BSD-licensed code from the Codeville distributed version control system
# -*- coding: utf-8
from __future__ import unicode_literals
try:
    xrange
except NameError: # Python3 compatibility
    xrange = range

from bisect import bisect

def unique_lcs(a, b):
    # set index[line in a] = position of line in a unless
    # unless a is a duplicate, in which case it's set to None
    index = {}
    for i in xrange(len(a)):
        line = a[i]
        if line in index:
            index[line] = None
        else:
            index[line]= i
    # make btoa[i] = position of line i in a, unless
    # that line doesn't occur exactly once in both,
    # in which case it's set to None
    btoa = [None] * len(b)
    index2 = {}
    for pos, line in enumerate(b):
        next = index.get(line)
        if next is not None:
            if line in index2:
                # unset the previous mapping, which we now know to
                # be invalid because the line isn't unique
                btoa[index2[line]] = None
                del index[line]
            else:
                index2[line] = pos
                btoa[pos] = next
    # this is the Patience sorting algorithm
    # see http://en.wikipedia.org/wiki/Patience_sorting
    backpointers = [None] * len(b)
    stacks = []
    lasts = []
    k = 0
    for bpos, apos in enumerate(btoa):
        if apos is None:
            continue
        # as an optimization, check if the next line comes at the end,
        # because it usually does
        if stacks and stacks[-1] < apos:
            k = len(stacks)
        # as an optimization, check if the next line comes right after
        # the previous line, because usually it does
        elif stacks and stacks[k] < apos and (k == len(stacks) - 1 or stacks[k+1] > apos):
            k += 1
        else:
            k = bisect(stacks, apos)
        if k > 0:
            backpointers[bpos] = lasts[k-1]
        if k < len(stacks):
            stacks[k] = apos
            lasts[k] = bpos
        else:
            stacks.append(apos)
            lasts.append(bpos)
    if len(lasts) == 0:
        return []
    result = []
    k = lasts[-1]
    while k is not None:
        result.append((btoa[k], k))
        k = backpointers[k]
    result.reverse()
    return result

def recurse_matches(a, b, ahi, bhi, answer, maxrecursion):
    oldlen = len(answer)
    if maxrecursion < 0:  # pragma: no cover
        # this will never happen normally, this check is to prevent DOS attacks
        return
    oldlength = len(answer)
    if len(answer) == 0:
        alo, blo = 0, 0
    else:
        alo, blo = answer[-1]
        alo += 1
        blo += 1
    if alo == ahi or blo == bhi:
        return
    for apos, bpos in unique_lcs(a[alo:ahi], b[blo:bhi]):
        # recurse between lines which are unique in each file and match
        apos += alo
        bpos += blo
        recurse_matches(a, b, apos, bpos, answer, maxrecursion - 1)
        answer.append((apos, bpos))
    if len(answer) > oldlength:
        # find matches between the last match and the end
        recurse_matches(a, b, ahi, bhi, answer, maxrecursion - 1)
    elif a[alo] == b[blo]:
        # find matching lines at the very beginning
        while alo < ahi and blo < bhi and a[alo] == b[blo]:
            answer.append((alo, blo))
            alo += 1
            blo += 1
        recurse_matches(a, b, ahi, bhi, answer, maxrecursion - 1)
    elif a[ahi - 1] == b[bhi - 1]:
        # find matching lines at the very end
        nahi = ahi - 1
        nbhi = bhi - 1
        while nahi > alo and nbhi > blo and a[nahi - 1] == b[nbhi - 1]:
            nahi -= 1
            nbhi -= 1
        recurse_matches(a, b, nahi, nbhi, answer, maxrecursion - 1)
        for i in xrange(ahi - nahi):
            answer.append((nahi + i, nbhi + i))

class Weave(object):
    def __init__(self):
        # [(lineid, line)]
        self.weave = []
        # {revid: [parent]}
        self.parents = {}
        # {revid: [((lineid1, lineid2), state)]}
        # states are integers
        # each edge's state starts at 0, then goes to 1, 2, etc.
        # odd states are when both lines are present and no lines are
        # between them, even otherwise
        # edges at the beginning and end are denoted by (None, lineid) and
        # (lineid, None) respectively. If the file is empty then (None, None)
        # is used.
        # the merge between two states is the greater of the two values
        self.newedgestates = {}

    def add_revision(self, revid, lines, parents):
        assert revid not in self.parents
        for p in parents:
            assert p in self.parents
        self.parents[revid] = [i for i in parents]

        # match against living lines
        # require that a line be part of living edges on either
        # side to be part of a living line,
        # to avoid including something in 'living lines' just
        # because a deletion happened next to it
        alivepre = set()
        alivepost = set()
        for ((ida, idb), state) in self._make_vals(revid).items():
            if state & 1 == 1:
                if ida is not None:
                    alivepre.add(ida)
                if idb is not None:
                    alivepost.add(idb)
        living = alivepre.intersection(alivepost)
        mapping = []
        livinglines = []
        for (pos, (lineid, line)) in enumerate(self.weave):
            if lineid in living:
                mapping.append(pos)
                livinglines.append(line)
        matches2 = []
        recurse_matches(lines, livinglines, len(lines), len(livinglines), matches2, 10)

        # match against the whole weave
        matches = []
        lines2 = [line for (lineid, line) in self.weave]
        for p, q in matches2:
            recurse_matches(lines, lines2, p, mapping[q], matches, 10)
            matches.append((p, mapping[q]))
        recurse_matches(lines, lines2, len(lines), len(lines2), matches, 10)

        # build a new weave
        alledges = set()
        for i in self.newedgestates.values():
            for (edge, state) in i:
                alledges.add(edge)
        newweave = []
        revpos = -1
        weavepos = -1
        matches.append((len(lines), len(lines2)))
        currentlines = []
        for a, b in matches:
            # take a guess as to whether it's better to put
            # extant lines before or after new lines
            hit = True
            if weavepos != -1 and weavepos + 1 != len(self.weave):
                hit = (self.weave[weavepos][0],
                    self.weave[weavepos + 1][0]) in alledges
            if hit:
                # add current weave lines to the new weave
                newweave.extend(self.weave[weavepos + 1:b])
            # add lines which have never appeared before to the weave
            for i in xrange(revpos + 1, a):
                lineid = (revid, i)
                currentlines.append(lineid)
                newweave.append((lineid, lines[i]))
            if not hit:
                # add current weave lines to the new weave
                newweave.extend(self.weave[weavepos + 1:b])
            if b != len(lines2):
                newweave.append(self.weave[b])
                currentlines.append(self.weave[b][0])
            revpos = a
            weavepos = b
        self.weave = newweave
        # calculate which lines had their states changed in this revision
        currentedges = set()
        if len(currentlines) > 0:
            for i in xrange(len(currentlines) - 1):
                currentedges.add((currentlines[i], currentlines[i+1]))
            currentedges.add((None, currentlines[0]))
            currentedges.add((currentlines[-1], None))
        else:
            currentedges.add((None, None))
        newedgevals = []
        vals = self._make_vals(revid)
        for edge in currentedges:
            if edge not in vals:
                newedgevals.append((edge, 1))
        for edge, state in vals.items():
            if (state & 1 == 1) != (edge in currentedges):
                newedgevals.append((edge, state + 1))
        if len(newedgevals) > 0:
            self.newedgestates[revid] = newedgevals

    def _make_vals(self, revid):
        # return {lineid: state} for the given revision
        unused = [revid]
        s = set()
        while unused:
            nextrev = unused.pop()
            if nextrev not in s:
                unused.extend(self.parents[nextrev])
                s.add(nextrev)
        v = {}
        for n in s:
            for p, q in self.newedgestates.get(n, []):
                v[p] = max(v.get(p, 0), q)
        return v

    def _lineids(self, vals):
        # return set of lineids of lines alive in output of _make_vals
        lineids = set()
        for (ida, idb), state in vals.items():
            if state & 1 == 1:
                if ida is not None:
                    lineids.add(ida)
                if idb is not None:
                    lineids.add(idb)
        return lineids

    def retrieve_revision(self, revid):
        # returns a list of strings
        ids = self._lineids(self._make_vals(revid))
        return [line for (lineid, line) in self.weave if lineid in ids]

    def cherry_pick(self, reva, revb):
        # pulls just the change in reva (without history) into revb
        v = {}
        for p, q in self.newedgestates.get(reva, []):
            v[p] = max(v.get(p, 0), q)

        alines = self._lineids(self._make_vals(reva))
        return self.merge(reva, revb, edgesa=v, alines=alines)

    def merge(self, reva, revb, edgesa=None, alines=None, edgesb=None, blines=None):
        # returns [line]
        # non-conflict lines are strings, conflict sections are
        # ([linesa], [linesb])
        if edgesa is None:
            edgesa = self._make_vals(reva)
        if alines is None:
            alines = self._lineids(edgesa)
        if edgesb is None:
            edgesb = self._make_vals(revb)
        if blines is None:
            blines = self._lineids(edgesb)
        lastalineid = None
        lastblineid = None
        awins = False
        bwins = False
        apartial = []
        bpartial = []
        result = []
        for (lineid, line) in (self.weave + [(None, None)]):
            if lineid is None or lineid in alines:
                edge = (lastalineid, lineid)
                aval = edgesa.get(edge, 0)
                bval = edgesb.get(edge, 0)
                if aval > bval:
                    awins = True
                if bval > aval:
                    bwins = True
                lastalineid = lineid
            if lineid is None or lineid in blines:
                edge = (lastblineid, lineid)
                aval = edgesa.get(edge, 0)
                bval = edgesb.get(edge, 0)
                if aval > bval:
                    awins = True
                if bval > aval:
                    bwins = True
                lastblineid = lineid
            if lineid is None or (lineid in alines and lineid in blines):
                #if not (awins ^ bwins):
                if awins and bwins:
                    result.append((apartial, bpartial))
                elif awins:
                    result.extend(apartial)
                elif bwins:
                    result.extend(bpartial)
                awins = False
                bwins = False
                apartial = []
                bpartial = []
                if line is not None:
                    result.append(line)
            else:
                if lineid in alines:
                    apartial.append(line)
                if lineid in blines:
                    bpartial.append(line)
        return result
