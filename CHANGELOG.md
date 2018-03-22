# Change Log

## [Unreleased]
### Added
- Added `licensecheck` dependency for license checking.
- Added warning messages to inform about ABI and License changes.

## [0.12.0] - 2017-12-19
### Added
- Added **npmjs** and **cpan** versioneers
- Added possibility to specify custom py.test arguments
- Added possibility to customize changelog entry
- Added version check to abort rebase if requested version is not newer than current
- Added separate tox tasks for linting
- Implemented **rpmbuild** and **mock** SRPM build tools
- Added possibility to configure rebase-helper with configuration file
- Added possibility to blacklist certain SPEC hooks or versioneers
- Created `rebasehelper/rebase-helper` Docker Hub repository

### Changed
- Made several speed optimizations in the test suite
- Tests requiring superuser privileges are now automatically skipped if necessary
- Simplified build analysis and made related log messages more useful

### Fixed
- Fixed documentation builds on readthedocs.org broken by *rpm distribution* requirement
- Fixed reading username and e-mail from git configuration
- Added missing dependencies to Dockerfile
- Fixed processing of custom builder options
- Added workarounds for RPM bugs related to `%sources` and `%patches`
- Fixed several unhandled exceptions
- Fixed parsing tarball filename containing certain characters

## [0.11.0] - 2017-10-04
### Added
- Added `rpm-py-installer` to install `rpm-python` from pip
- Implemented detection of package category (*python*, *perl*, *ruby*, *nodejs*, *php*)
- Added **RubyGems** versioneer
- Added **RubyHelper** SPEC hook for getting additional sources based on instructions in SPEC file comments

### Changed
- Value of *Version* and *Release* tags is now preserved if there are any macros that can be modified instead
- Versioneers and SPEC hooks are now run only for matching package categories
- Bash completion is now generated from source code, so it is always up-to-date

### Fixed
- Prevented unwanted modifications of *%prep* section
- Fixed unexpected removal of rpms and build logs after last build retry
- Added files are no longer listed as removed in **rpmdiff** report

## [0.10.1] - 2017-08-30
### Added
- Added `--version` argument

### Changed
- **Anitya** versioneer now primarily searches for projects using Fedora mapping
- Python dependencies moved from `requirements.txt` to `setup.py`

### Fixed
- Made `CustomManPagesBuilder` work with Sphinx >= 1.6
- *%prep* section parser is now able to handle backslash-split lines

## [0.10.0] - 2017-08-25
### Added
- Implemented extensible SPEC hooks and versioneers
- Added **PyPI** SPEC hook for automatic fixing of Source URL of Python packages
- Added **Anitya** and **PyPI** versioneers for determining latest upstream version of a package
- Added possibility to download old version build of a package from Koji
- Added support for test suite to be run in Docker containers
- Implemented functional tests for automatic testing of whole rebase process
- Diff against original source files is now generated as *changes.patch*

### Changed
- Introduced plugin system for extending build tools, checkers and output tools
- Updated for **Koji 1.13** which finally brings Python 3 support
- Improved output information and reports
- Added colorized output
- Improved project documentation

### Fixed
- Pre-configured git username and e-mail address is now used if available
- Fixed several issues in **rpmdiff** and especially **abipkgdiff** checkers
- Fixed several test suite related issues


## [0.9.0] - 2017-01-05
### Added
- Old sources are now downloaded from Fedora lookaside cache
- Auto-generated and improved CLI documentation and man page
- Added support for downloading files of unknown size

### Changed
- `SpecFile` class preparation for pre-download hooks
- Code cleanup and refactorization

### Fixed
- Fixed regexp for getting release number from SPEC
- Fixed functionality of `--results-dir` option
- Several upstream monitoring fixes
- Fixed issues caused by Fedora Flag Day


## [0.8.0] - 2016-07-31
### Added
- Added support for JSON output format
- Added support for **copr** build tool
- Added support for passing arbitrary extra arguments to local builders (**mock**, **rpmbuild**) with `--builder-options`.
- Added new option `--build-retries` allows the user to specify number of build retries (by default *2*)
- Added support for **csmock** check tool

### Changed
- Renamed **fedpkg** build tool to **koji** to make it more clear
- Downloading of files is now done only using standard Python library and not using PyCURL

### Fixed
- Many bug fixes and code clean up


## [0.7.3] - 2016-04-08
### Added
- Added `rpm.addMacro`

### Fixed
- Handled exceptions raised during parsing of SPEC files
- Fixed unapplied patches mixing with deleted ones


## [0.7.2] - 2016-03-15
### Added
- Added information about scratch builds

### Fixed
- Added check if file exists and is empty for **the-new-hotness**
- Patches are applied in case `--builds-nowait` option is used


## [0.7.1] - 2016-02-22
### Added
- Two new command line options used by upstream monitoring

### Fixed
- **fedpkg** reimplementation


## [0.7.0] - 2016-01-13
### Changed
- Several improvements

### Fixed
- **pkgdiff** is now smarter
- Included `tar.bz2` into list of supported formats
- Added support for noarch package in case of **fedpkg** build
- Checker should return `None` if there is no debug package

### Removed
- Removed a bunch of debug stuff


## [0.6.2] - 2015-11-09
### Fixed
- Logs are being saved to their own directory
- Prep script is moved into workspace directory
- No more traceback in case `koji` module is not present
- Each checker creates its own log file
- **rebase-helper** informs if it failed or not
- Report on script is smarter


## [0.6.1] - 2015-10-30
### Added
- `upstream-monitoring.py` - used by upstream monitoring service
- `rebase-helper-fedmsg.py` - testing Python script


## [0.6.0] - 2015-07-31
### Added
- Parts of `%prep` section related to patching are executed
- Support for **abipkgdiff**

### Fixed
- Several fixes
- Replaced `yum` with `dnf`


## [0.5.0] - 2015-05-22
### Added
- Added support for building packages via **fedpkg** (or **koji**)
- Added summary report for better overview
- `continue` option implemented for `git rebase`
- Added several tests
- Added class for operating with Git repositories

### Changed
- `git rebase` is used instead of `patch` command

### Fixed
- Fixed several decoding issues
- Several **PEP8** and **W1202** fixes

### Removed
- `DiffHelper` class is not needed


## [0.4.0] - 2014-12-05
### Added
- Handling of extra versions like `b1`, `rc1`, etc.
- Added build log analyzer to detect unpackaged files or other issues
- Added Bash completion

### Changed
- Improved version extraction from archive name
- **rebase-helper** output is looged to `rebase-helper-results` directory
- `SpecFile` class rewritten


## [0.3.1] - 2014-07-25
### Added
- New build class
- `--build-only` option
- Installation of build dependencies in case of **rpmbuild** tool
- More tests
- `RebaseHelperError` class for catching exceptions

### Fixed
- Several fixes


## [0.3.0]
### Added
- **pkgdiff** tool for comparing RPM packages
- Tests for `Archive` class and SPEC file


## [0.2.0]
### Added
- `diff_helper` for comparing two tarballs
- Applying patches to tarballs
- `patch_helper`


## [0.1.0]
### Added
- Initial classes
- CLI interface
