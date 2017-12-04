# Welcome to rebase-helper

[![Code Health](https://landscape.io/github/phracek/rebase-helper/master/landscape.svg?style=flat)](https://landscape.io/github/phracek/rebase-helper/master) [![GitLab CI build status](https://gitlab.com/rebase-helper/rebase-helper/badges/master/build.svg)](https://gitlab.com/rebase-helper/rebase-helper/commits/master) [![Travis CI build status](https://travis-ci.org/rebase-helper/rebase-helper.svg?branch=master)](https://travis-ci.org/rebase-helper/rebase-helper) [![Documentation build status](https://readthedocs.org/projects/rebase-helper/badge/?version=latest)](https://readthedocs.org/projects/rebase-helper)

There are several steps that need to be done when rebasing a package. The goal of **rebase-helper** is to automate most of these steps.

## How to run rebase-helper

Execute **rebase-helper** from a directory containing SPEC file, sources and patches (usually cloned dist-git repository).

`rebase-helper 3.1.10`

Starting with **rebase-helper 0.10.0** you don't have to specify the new version at all, and **rebase-helper** will attempt to determine it automatically using one of available *versioneers*.

For complete CLI reference see [usage](https://rebase-helper.readthedocs.io/en/latest/user_guide/usage.html).

## General workflow
- *rebase-helper-workspace* and *rebase-helper-results* directories are created
- original SPEC file is copied to *rebase-helper-results/rebased-sources* directory and its Version tag is modified
- old and new source tarballs are downloaded and extracted to *rebase-helper-workspace* directory
  - new sources are extracted and added as a remote repository
- downstream patches are rebased on top of new sources using `git-rebase`
  - new git repository is initialized and the old sources are extracted and commited
  - each downstream patch is applied and changes introduced by it are commited
  - original patches are modified/deleted accordingly
  - resulting modified patches are saved to *rebase-helper-results/rebased-sources* directory

- old and new source RPMs are created and built with selected build tool
- resulting files are stored in *rebase-helper-results/rebased-sources*
- multiple checker tools are run against both sets of packages and their output is stored in *rebase-helper-results/checkers* directory
- diff against original files is saved to *rebase-helper-results/changes.patch*
- *rebase-helper-workspace* directory is removed
