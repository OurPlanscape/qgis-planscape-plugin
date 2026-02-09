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

On Windows Command promt
```console
mklink /J %AppData%\QGIS\QGIS3\profiles\default\python\plugins\planscape .\planscape
```

On Windows PowerShell
```console
New-Item -ItemType SymbolicLink -Path ${env:APPDATA}\QGIS\QGIS3\profiles\default\python\plugins\planscape -Value ${pwd}\planscape
```

On Linux
```console
ln -s planscape/ ~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/planscape
```

After that you should be able to enable the plugin in the QGIS Plugin Manager.

### VsCode setup

On VS Code use the workspace [qgis-planscape-plugin.code-workspace](qgis-planscape-plugin.code-workspace).
The workspace contains all the settings and extensions needed for development.

Select the Python interpreter with Command Palette (Ctrl+Shift+P). Select `Python: Select Interpreter` and choose
the one with the path `.venv\Scripts\python.exe`.

## License
This plugin is distributed under the terms of the [GNU General Public License, version 2](https://www.gnu.org/licenses/old-licenses/gpl-2.0.en.html) license.

See [LICENSE](LICENSE) for more information.
