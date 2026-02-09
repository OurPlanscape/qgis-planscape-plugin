# Planscape
![tests](https://github.com/OurPlanscape/qgis-planscape-plugin/workflows/Tests/badge.svg)
[![codecov.io](https://codecov.io/github/OurPlanscape/qgis-planscape-plugin/coverage.svg?branch=main)](https://codecov.io/github/OurPlanscape/qgis-planscape-plugin?branch=main)
![release](https://github.com/OurPlanscape/qgis-planscape-plugin/workflows/Release/badge.svg)

[![GPLv2 license](https://img.shields.io/badge/License-GPLv2-blue.svg)](https://www.gnu.org/licenses/old-licenses/gpl-2.0.en.html)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)

## Development

Install your virtualenv with:

* `uv venv .venv --python /usr/bin/python3 --system-site-packages`

This will create a virtualenv, inside your project folder, with your QGIS Python interpreter
and using system-site-packages. You might need to replace `/usr/bin/python3` with your current QGIS
Python interpreter.

### Figuring out your Python3 interpreter

1. open qgis
2. Hit `Ctrl+Alt+P`
3. This will open up the python console inside QGIS
4. Type in:

```
import sys
print(sys.executable)
```

This should return you the current interpreter.

### Testing the plugin on QGIS

A symbolic link / directory junction should be made to the directory containing the installed plugins pointing to the dev plugin package.

#### On Windows Command promt

:warning: STILL NOT CONFIGURED

```console
mklink /J %AppData%\QGIS\QGIS3\profiles\default\python\plugins\planscape .\planscape
```

#### On Windows PowerShell

:warning: STILL NOT CONFIGURED

```console
New-Item -ItemType SymbolicLink -Path ${env:APPDATA}\QGIS\QGIS3\profiles\default\python\plugins\planscape -Value ${pwd}\planscape
```

#### On Linux

do:

1. `make install-plugin`
2. Open up QGIS
3. Go to Plugins > Manage and Install Plugins
4. Go to Settings
5. Mark "Show also Experimental Plugins"
6. Go to Installed tab
7. Search for `Planscape`
8. Activate the plugin
9. The `Planscape` plugin should be available under the Plugins menu.

#### Useful stuff

1. Install a plugin called `Plugin Reloader`
2. Enable it

This plugin will enable you to configure a plugin for reloading. This is very
useful during testing, where you will often have to reload the the plugin for checking
if your changes are ok.

Just reload the plugin without the need to close/open QGIS.