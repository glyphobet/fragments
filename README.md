Differencing Fragmentation Manager
==================================

Fragments is neither a templating language, nor a version control system, but it combines aspects of both. It enables a programmer to violate the [DRY (Don't Repeat Yourself)](http://en.wikipedia.org/wiki/Don't_repeat_yourself) principle; it is a [Multiple Source of Truth](http://en.wikipedia.org/wiki/Single_Source_of_Truth) engine.

Generating HTML with templating languages is generally a hassle because an application's templates have two tasks: the first is sometimes called page "inheritance": managing common HTML fragments like headers, sidebars, and footers, across multiple templates; and the second, which is display logic operating on data from a backend. Separate these two tasks and your templates become much simpler. Fragments takes care of common HTML fragments, leaving the actual display logic to you.

The machinery to manage common fragments across multiple files already exists in modern version control systems. Instead of a "diachronic" system, which manages many changes to a single file over time, Fragments is a "synchronic" system, which can apply a single change to many files synchronously. Each HTML file (or any other type of file, really) is in effect its own "branch", and whenever you modify a file ("branch") you can merge that change into whichever other files ("branches") you wish. In this sense Fragments is really just version control turned on its side.

Fragments has no "history" - it only stores the previous committed state of a file. Storing history is up to your version control system. Fragments stores its repository configuration in a `fragments` directory. This directory name is not preceded by a `.`, and all the files in it are stored as plain text, to allow your version control system to manage it painlessly and obviously. The configuration resides one directory above your content, so as to not interfere with template-identification code and to not accidentally be deployed along with production HTML.

The merge algorithm is a version of [Precise Codeville Merge](http://revctrl.org/PreciseCodevilleMerge) modified to support cherry-picking. Precise Codeville Merge was chosen because it supports [convergence](http://revctrl.org/Convergence). That is, if two files are independently modified in the same way, they merge together cleanly. This makes adding new files easy; just copy an existing file, change it as desired, and commit it. Subsequent changes to any un-modified, common sections of that file will automatically apply.

Fragments is designed to be invisible to people who don't know it's being used. You can give a single HTML file to your web designer, let him or her modify it as desired, and then have a programmer apply those changes across all other HTML files.

Fragments is also not HTML specific. XML, CSS, JSON, YAML, source code from your favorite obscure programming language; if it's got newlines, Fragments can manage it. Fragments is even smart enough to know not to merge totally different files together. It could even conceivably replace some CMS-managed websites with static HTML.

Since Fragments is diff-based, it will not do well with minified or otherwise compressed content. Do not expect it to handle changes to your 1,000 character, single line, über-compressed CSS file.

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

* `diff [FILENAME [FILENAME ...]]`

    show differences between committed and uncommitted versions

* `commit [FILENAME [FILENAME ...]]`

    commit changes to one or more files

* `revert [FILENAME [FILENAME ...]]`

    revert changes to one or more files

* `apply FILENAME [FILENAME ...]`

    apply changes in one or more files that were made since last commit to as many other followed files as possible

