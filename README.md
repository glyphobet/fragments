Fragments
=========

Fragments is neither a templating language, nor a version control system, but it combines aspects of both. It enables a programmer to violate the [DRY (Don't Repeat Yourself)](http://en.wikipedia.org/wiki/Don't_repeat_yourself) principle; it is a [Multiple Source of Truth](http://en.wikipedia.org/wiki/Single_Source_of_Truth) engine. I prefer to think of it as a Differencing Fragmentation Manager.

What is a Differencing Fragmentation Manager?
---------------------------------------------

Generating HTML with templating languages is difficult because the templates have two semi-incompatible purposes. The first purpose is sometimes called page "inheritance": managing common HTML elements like headers, sidebars, and footers, across multiple templates. The second purpose is to perform display logic operating on data from a backend. Separate these two tasks and your templates become much simpler. Fragments takes care of common HTML elements, leaving the actual display logic to your templating language.

The machinery to manage common file fragments across multiple files already exists in modern version control systems. Instead of a "diachronic" system, which manages many changes to a single file over time, Fragments is a "synchronic" system, which can apply a single change to many files synchronously. Each HTML file (or any other type of file, really) is in effect its own "branch", and whenever you modify a file ("branch") you can merge that change into whichever other files ("branches") you wish. In this sense Fragments is really just version control turned on its side.

How does it work?
-----------------

The merge algorithm is a version of [Precise Codeville Merge](http://revctrl.org/PreciseCodevilleMerge) modified to support cherry-picking. Precise Codeville Merge was chosen because it supports [convergence](http://revctrl.org/Convergence). That is, if two files are independently modified in the same way, they merge together cleanly. This makes adding new files easy; just copy an existing file, change it as desired, and commit it. Subsequent changes to any un-modified, common sections, in that file or in its siblings, will be applicable across the rest of the repository.

Fragments is also not HTML specific. XML, CSS, JSON, YAML, source code from your favorite obscure programming language; if it's got newlines, Fragments can manage it. Fragments is even smart enough to know not to merge totally different files together. It could even conceivably replace some CMS-managed websites with pure static HTML.

Integration with Version Control
--------------------------------

Fragments has no "history" - it only stores the previous committed state of a file. Storing history is up to your ("diachronic") version control system. Fragments stores its repository configuration in such a way to allow your version control system to manage it painlessly and obviously. Configuration is stored in a `fragments` directory. This directory name is not preceded by a `.`, and all the files in it are stored as plain text. The configuration resides one directory above your actual content, so as to not interfere with template loading code, and so it is not accidentally deployed to production along with your actual content.

Future Improvements
-------------------

### Invisibility

Fragments is not yet ready to be invisible to people who don't know it's being used. Currently, all changes to a file are applied to other files as a single change. That means if you make *two* changes to a file, one of which should be merged across all other files, and another change which should *not* be merged, Fragments will only allow you to apply those changes or commit the file without applying them.

The next release of Fragments will add chunk-based application of changes, similar to `git commit --patch` or `hg record`. Once this is done, it will be possible to use Fragments even when some contributors don't even know it's being used. In other words, you can give a single HTML file to your web designer, let him or her modify it as desired, and then have a programmer selectively apply some of those changes across all other HTML files, while leaving other changes only in the modified file.

### Preprocessors

Since Fragments is diff-based, it will not do well with minified or otherwise compressed content. Do not expect it to handle changes to your 1,000 character, single line, über-compressed CSS file. The more newlines in your files, the more robust Fragments' merging will be.

Adding preprocessors for different file formats would potentially make Fragments' merging even more robust. Running a preprocessor before `commit` and `apply` would make the merging more robust by ensuring that XML tags, (some) HTML tags, and CSS declarations get their own lines, placing a canonical amount of whitespace between functions and CSS rules, and enforcing the project's coding standards.

Commands
--------

* `help`

    display help

* `init`

    initialize a new fragmentation manager repository

* `stat`

    get the current status of the repository

* `follow FILENAME [FILENAME ...]`

    start following changes to one or more files

* `forget FILENAME [FILENAME ...]`

    stop following changes to one or more files

* `rename OLD_FILENAME NEW_FILENAME`

    rename OLD\_FILENAME to NEW\_FILENAME, moving the actual file on disk if has not already been moved

* `diff [FILENAME [FILENAME ...]]`

    show differences between committed and uncommitted versions

* `commit [FILENAME [FILENAME ...]]`

    commit changes to one or more files

* `revert [FILENAME [FILENAME ...]]`

    revert changes to one or more files

* `apply FILENAME`

    apply changes in FILENAME that were made since last commit to as many other followed files as possible

