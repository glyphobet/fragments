Fragments
=========

Fragments uses concepts from version control to replace many uses of templating languages. It provides diff-based templating, instead of a templating language; It is "fragmentation control" instead of revision control.

Fragments enables a programmer to violate the [DRY (Don't Repeat Yourself)](http://en.wikipedia.org/wiki/Don't_repeat_yourself) principle; it is a [Multiple Source of Truth](http://en.wikipedia.org/wiki/Single_Source_of_Truth) engine.

What is diff-based templating?
------------------------------

Generating HTML with templating languages is difficult because templating languages often have two semi-incompatible purposes. The first purpose is sometimes called page "inheritance": managing common HTML elements & structure: headers, sidebars, and footers; across multiple templates. The second purpose is to perform idiosyncratic display logic on data coming from another source. When these two purposes can be separated, templates can be much simpler.

Fragments manages this first purpose, common HTML elements and structure, with diff and merge algorithms. The actual display logic is left to your application, or to a templating language whose templates are themselves managed by Fragments.

What is fragmentation control?
------------------------------

The machinery to manage common and different code fragments across multiple versions of _a single file_ already exists in modern version control systems. Fragments adapts these tools to manage common and different versions of _several different files_.

Each file is in effect its own "branch", and whenever you modify a file ("branch") you can apply ("merge") that change into whichever other files ("branches") you choose. In this sense Fragments is a different kind of "source control"--rather than controlling versions/revisions over time, it controls fragments across many files that all exist simultaneously. Hence the term "fragmentation control".

As I am a linguist, I have to point out that the distinction between [Synchronic](http://en.wikipedia.org/wiki/Synchronic_analysis) and [Diachronic](http://en.wikipedia.org/wiki/Diachronics) Linguistics gave me this idea in the first place.

How does it work?
-----------------

The merge algorithm is a version of [Precise Codeville Merge](http://revctrl.org/PreciseCodevilleMerge) modified to support cherry-picking. Precise Codeville Merge was chosen because it supports [convergence](http://revctrl.org/Convergence). That is, if two files are independently modified in the same way, they merge together cleanly. This makes adding new files easy; just copy an existing file (or use Fragment's `fork` command), change it as desired, and commit it. Subsequent changes to any un-modified, common sections, in that file or in its siblings, will be applicable across the rest of the repository.

Fragments is also not HTML specific. If it's got newlines, Fragments can manage it. That means XML, CSS, JSON, YAML, or even source code from any programming language where newlines are common (sorry, Perl). Fragments is even smart enough to know not to merge totally different files together. It could even conceivably replace simpler CMS-managed websites with pure static HTML.

Integration with Version Control
--------------------------------

Fragments has no history; It only stores the previous committed state of a file. Storing history is up to your version control system. But Fragments stores its repository configuration in such a way to allow your version control system to manage it painlessly and obviously. Configuration is stored in a `_fragments` directory. This directory name is not preceded by a `.`, and all the files in it are stored as plain text. The configuration resides one directory above your actual content, so it does not interfere with template loading code, and so it is not accidentally deployed to production along with your actual content.

The `rename` and `forget` commands in Fragments are also written to not interfere with a version control's rename and remove commands, as these commands will sometimes need to be used in tandem.

Invisibility
------------

Fragments is invisible to people who don't know it's being used. If you (or someone else) makes more than one change to a file, Fragments allows you to perform chunk-based interactive application of changes, similar to `git commit --patch` or `hg record`. In other words, you can give a single HTML file to your web designer, let him or her modify it as desired, and then have a programmer selectively apply some of those changes across all other HTML files, while leaving other changes only in the modified file.

Future Improvements
-------------------

### Preprocessors

Since Fragments is diff-based, it will not do well with minified or otherwise compressed content. Do not expect it to handle changes to your 1,000 character, single line, über-compressed CSS file. The more newlines in your files, the more robust Fragments' merging will be.

Adding preprocessors for different file formats would potentially make Fragments' merging even more robust. Running a preprocessor before `commit` and `apply` would make the merging more robust by ensuring that XML tags, (some) HTML tags, and CSS declarations get their own lines, and by placing a canonical number of newlines around CSS rules, functions and any other structures in the document.

### Miscellaneous

* Colorized `diff` and `stat` output
* A better interactive mode including the ability to skip and return to hunks (like git does with `j/J/k/K`)
* Command-line completion modes for bash and/or zsh
* Short command resolution, so you can type `fragments st` for `fragments stat`, &c.
* Command aliasing and default configuration
* Pluggable merge algorithms, if they prove useful

Commands
--------

* `help [COMMAND]`

    Display global help, or help for _COMMAND_ if specified.

* `init`

    Initialize a new fragments repository, in a directory named `_fragments/`.

* `stat [FILENAME [FILENAME ...]]`

    Get the current status of the fragments repository, limited to _FILENAME_(s) if specified.

* `follow FILENAME [FILENAME ...]`

    Start following changes to one or more _FILENAME_(s).

* `forget FILENAME [FILENAME ...]`

    Stop following changes to one or more _FILENAME_(s).

* `rename OLD_FILENAME NEW_FILENAME`

    Rename _OLD\_FILENAME_ to _NEW\_FILENAME_, moving the actual file on disk if it has not already been moved.

* `diff [[-U | --unified] NUM] [FILENAME [FILENAME ...]]`

    Show differences between committed and uncommitted versions, limited to _FILENAME_(s) if specified.

    `-U NUM`, `--unified NUM` number of lines of context to show

* `commit [FILENAME [FILENAME ...]]`

    Commit changes to the fragments repository, limited to _FILENAME_(s) if specified.

* `revert [FILENAME [FILENAME ...]]`

    Revert changes to the fragments repository, limited to _FILENAME_(s) if specified.

* `fork SOURCE_FILENAME [SOURCE_FILENAME ...] TARGET_FILENAME`

    Create a new file in _TARGET\_FILENAME_ based on one or more _SOURCE\_FILENAME_(s).
    Common sections are preserved; differing sections are replaced with a single newline.

* `apply [-i | -a] [[-U | --unified] NUM] SOURCE_FILENAME [TARGET_FILENAME [TARGET_FILENAME ...]]`

    Apply changes in _SOURCE\_FILENAME_ that were made since last commit, where possible.
    Limit application to _TARGET\_FILENAME_(s) if specified.
    Files that conflict in their entirety will be skipped.
    Smaller conflicts will be written to the file as conflict sections.

    `-i, --interactive` interactively select changes to apply

    `-a, --automatic` automatically apply all changes

    `-U NUM`, `--unified NUM` number of lines of context to show

