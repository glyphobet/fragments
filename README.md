Fragments
=========

Fragments is neither a templating language, nor a version control system, but it combines aspects of both. It enables a programmer to violate the [DRY (Don't Repeat Yourself)](http://en.wikipedia.org/wiki/Don't_repeat_yourself) principle; it is a [Multiple Source of Truth](http://en.wikipedia.org/wiki/Single_Source_of_Truth) engine. You could think of it as "fragmentation control".

What is Fragmentation Control?
---------------------------------------------

Generating HTML with templating languages is difficult because HTML templates often have two semi-incompatible purposes. The first purpose is sometimes called page "inheritance": managing common HTML elements & structure: headers, sidebars, and footers; across multiple templates. The second purpose is to perform idiosyncratic display logic on variable data coming from some sort of backend. Separate these two tasks and your templates become much simpler. Fragments takes care of common HTML elements and structure, leaving the actual display logic to your templating language or application.

The machinery to manage common code fragments across multiple files already exists in modern version control systems. Instead of a "diachronic" system, which manages many changes to a single file over time, Fragments is a "synchronic" system, which can apply a single change to many files synchronously. Each HTML file (or any other type of file, really) is in effect its own "branch", and whenever you modify a file ("branch") you can apply ("merge") that change into whichever other files ("branches") you choose. In this sense Fragments is a different kind of "source control"--rather than controlling versions/revisions, it controls fragments. Hence the term "fragmentation control".

How does it work?
-----------------

The merge algorithm is a version of [Precise Codeville Merge](http://revctrl.org/PreciseCodevilleMerge) modified to support cherry-picking. Precise Codeville Merge was chosen because it supports [convergence](http://revctrl.org/Convergence). That is, if two files are independently modified in the same way, they merge together cleanly. This makes adding new files easy; just copy an existing file, change it as desired, and commit it. Subsequent changes to any un-modified, common sections, in that file or in its siblings, will be applicable across the rest of the repository.

Fragments is also not HTML specific. XML, CSS, JSON, YAML, source code from your favorite obscure programming language; if it's got newlines, Fragments can manage it. Fragments is even smart enough to know not to merge totally different files together. It could even conceivably replace some CMS-managed websites with pure static HTML.

Integration with Version Control
--------------------------------

Fragments has no "history"; It only stores the previous committed state of a file. Storing history is up to your ("diachronic") version control system. Fragments stores its repository configuration in such a way to allow your version control system to manage it painlessly and obviously. Configuration is stored in a `_fragments` directory. This directory name is not preceded by a `.`, and all the files in it are stored as plain text. The configuration resides one directory above your actual content, so as to not interfere with template loading code, and so it is not accidentally deployed to production along with your actual content.

Invisibility
------------

Fragments is invisible to people who don't know it's being used. If you (or someone else) makes more than one change to a file, Fragments allows you to perform chunk-based interactive application of changes, similar to `git commit --patch` or `hg record`. In other words, you can give a single HTML file to your web designer, let him or her modify it as desired, and then have a programmer selectively apply some of those changes across all other HTML files, while leaving other changes only in the modified file.

Future Improvements
-------------------

### Preprocessors

Since Fragments is diff-based, it will not do well with minified or otherwise compressed content. Do not expect it to handle changes to your 1,000 character, single line, über-compressed CSS file. The more newlines in your files, the more robust Fragments' merging will be.

Adding preprocessors for different file formats would potentially make Fragments' merging even more robust. Running a preprocessor before `commit` and `apply` would make the merging more robust by ensuring that XML tags, (some) HTML tags, and CSS declarations get their own lines, and by placing a canonical number of newlines around CSS rules, functions and any other structures in the document.

Commands
--------

* `help [COMMAND]`

    Display global help, or help for _COMMAND_ if specified.

* `init`

    Initialize a new fragments repository, in `\_fragments`.

* `stat [FILENAME [FILENAME ...]]`

    Get the current status of the fragments repository.

* `follow FILENAME [FILENAME ...]`

    Start following changes to one or more files.

* `forget FILENAME [FILENAME ...]`

    Stop following changes to one or more files.

* `rename OLD_FILENAME NEW_FILENAME`

    Rename _OLD\_FILENAME_ to _NEW\_FILENAME_, moving the actual file on disk if it has not already been moved.

* `fork SOURCE\_FILENAME [SOURCE\_FILENAME ...] DESTINATION\_FILENAME`

    Create a new file in _DESTINATION\_FILENAME_ based on one or more _SOURCE\_FILENAME_s. Common sections are preserved; differing sections are replaced with a single newline.

* `diff [[-U | --unified] NUM] [FILENAME [FILENAME ...]]`

    Show differences between committed and uncommitted versions.

    `-U NUM`, `--unified NUM` number of lines of context to show

* `commit [FILENAME [FILENAME ...]]`

    Commit changes to one or more files.

* `revert [FILENAME [FILENAME ...]]`

    Revert changes to one or more files.

* `apply [-i | -a] [[-U | --unified] NUM] FILENAME`

    Apply changes in _FILENAME_ that were made since last commit to as many other followed files as possible.

    `-i, --interactive` interactively select changes to apply

    `-a, --automatic` automatically apply all changes

    `-U NUM`, `--unified NUM` number of lines of context to show

