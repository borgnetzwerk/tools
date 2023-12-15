- [Issues:](#issues)
- [Tasks:](#tasks)
- [Development](#development)
  - [Command pile and workflows](#command-pile-and-workflows)
    - [Get started](#get-started)
      - [Setup "Virtual environment" (venv)](#setup-virtual-environment-venv)
      - [Activate venv](#activate-venv)
    - [Everyday development](#everyday-development)
      - [Github: commit and push](#github-commit-and-push)
      - [Editable installation](#editable-installation)
    - [Packaging](#packaging)
      - [Package debugging](#package-debugging)
      - [Package publishing](#package-publishing)


# Issues:
1. Old files are terribly maintained
2. Support and testing, especially for other systems is not implemented yet
3. No documentation
4. No usable scripts
5. No effort put into customizing the various __init__.py

# Tasks:
1. Old files are terribly maintained
   1. Highlight which file is used in which workflow
   2. Update all used files
   3. Some subtasks:
      1. Convert "path/to/file" to "os.path.join(path, to, file)"
         1. Use Regex: ["'].*/
         2. Change path + "to/" + file as well, where some filenames and paths already have the "/" in it.
2. Support and testing, especially for other systems is not implemented yet
   1. Testing
      1. Implement Github Actions
      2. Investigate 
         1. ```from unittest import TestCase```
         2. tox.ini
         3. pytest
         4. How Hatch (Dependency Management System) plays into all of this
            1. What it can do automatically
   2. Systems
      1. Define tests for other systems, like linux, mac, ubuntu, windows
      2. Automatically create an (unused) requirements.txt for backwards compatibility
   3. Python versions
      1. Take care with highly specific Whisper / pytorch installation
3. No Documentation
   1. Investigate how to automatically generate "ReadTheDocs" documentation
4. No usable scripts
   1. Investigate how to best present pre-defined usable scripts.
5. No effort put into customizing the various __init__.py
    1. modify init to better guide the user
       1. Allow them to only import specific modules that are intended for external use
       2. Leave the rest to be called by these external interfaces only

# Development

## Command pile and workflows

### Get started
#### Setup "Virtual environment" (venv)
```
python -m venv .venv
```
This makes sure you have all packages in one place, without affecting your overall system. Also makes it easier to reset things if you ever need to put yourself into the position of "what would the user feel like to get it running from 0 again?"

#### Activate venv
```
.venv/Scripts/activate
```
*Hint*: Potentially, you need wrap it in an Set-ExecutionPolicy block, if you do not have the rights to execute scripts:
```
Set-ExecutionPolicy RemoteSigned
.venv/Scripts/activate
Set-ExecutionPolicy Restricted
```
*Hint*: this action is undone by typing ```deactivate```

### Everyday development
#### Github: commit and push
If you want, just use the Github Desktop version or the Visual Studio Code Github interface. Pressing buttons is simpler and often less dangerous.

#### Editable installation
```
pip install --editable .
```

This allows you to use ```import bnw_tools``` inside your venv, just like you would have installed it via pip. Any changes you make to the source code are instantly available, no need to re-install, package or anything.

See https://stackoverflow.com/questions/68033795/avoiding-sys-path-append-for-imports

### Packaging
Make sure you have installed PyPA's build in your venv:
```
py -m pip install --upgrade build
```
#### Package debugging
```
pip uninstall -y bnw_tools
py -m build
pip install dist\bnw_tools-0.0.1.2.tar.gz
```

*Note*: Change the version number

#### Package publishing 
```
twine upload dist/*
```
username: ```__token__```
password: *a valid PiPy token*