#!/bin/bash
python2.7 setup.py bdist_egg register upload
python2.7 setup.py sdist     register upload

markdown_py README.md > index.html
rm pypi-docs.zip
zip pypi-docs.zip index.html
rm index.html
echo "Now upload pypi-docs.zip to PyPi here: http://pypi.python.org/pypi?%3Aaction=pkg_edit&name=fragments"
echo "Remember to remove pypi-docs.zip when you're done."
