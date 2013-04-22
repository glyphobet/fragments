#!/bin/bash
rm -f .coverage
nosetests --with-coverage --cover-package=fragments
