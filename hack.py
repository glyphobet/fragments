#!/usr/bin/env python

file_a = """<html>
    <head>
        <title>Page One</title>
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
</html>""".split('\n')

file_b = """<html>
    <head>
        <title>Page Two</title>
        <link href="default.css" />
        <link href="site.css" />
        <link href="custom.css" />
        <script href="script.js" />
        <script href="other.js" />
    </head>
    <body>
        <h1>Two</h1>
    </body>
</html>""".split('\n')

new_file_b = """<html>
    <head>
        <title>Page Two</title>
        <link href="default.css" />
        <link href="site.css" />
        <link href="custom.css" />
        <script href="script.js" />
        <script href="other.js" />
    </head>
    <body class="FINGER">
        <h1>Two</h1>
    </body>
</html>
""".split('\n')

import pdb
import fragman.precisecodevillemerge as pcvm
weave = pcvm.Weave()
weave.add_revision(1, file_a, [])
weave.add_revision(2, file_b, [])

weave.add_revision(3, new_file_b, [2]) # changed class on <body> tag
print weave.cherry_pick(3, 1) # can I apply new class on <body> tag to document 1 ?
pdb.set_trace()