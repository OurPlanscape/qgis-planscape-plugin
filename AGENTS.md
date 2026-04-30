# AGENTS.md

## Overview

This project is QGIS plugin that talks to planscape and allows users to manipulate existing resources
in Planscape API

## Restrictions

- DO NOT MAKE CHANGES TO `planscape/qgis_plugin_tools`

## Logging

- All loggers under our control MUST be named `logger`

## Repository Commands

- Install: `uv sync`
- Test: `uv run pytest .`
- Lint: `uv run ruff check .`
- Format: `uv run ruff format .`
- Install plugin: `make install-plugin`

## Architecture

- package manager: uv
- Keep API models (request/responses) and domain models separate
- ALWAYS use qgis_plugin_tools/tools/network to make api calls
- ALWAYS use qgis_plugin_tools/tools/resources to process resources
- Emit warnings when trying to install packages that depend on the runtime, such as pydantic
- naming pattern for actions: list, create, update, delete, retrieve
- DO NOT use EDIT instead of update.

## API

- Authorization header: `Authorization: Bearer <token>`
- Swagger/API schemas in https://dev.planscape.org/planscape-backend/v2/schema/swagger
- API logic should be located in `planscape/api`
- API call functions should use a `_request` suffix, e.g. `list_workspaces_request`
- ALL API calls must be logged with `logger.info('[API] <method>:<url>')

## Commands

- located in `planscape/gui/commands`
- contains code relative to api calls and changes to the UI.

## Git

- DO NOT COMMIT automatically
- DO NOT REVERT automatically

## UI

- UI node behaviors are located in planscape/gui/behaviors
- `PlanscapeDockWidget` needs to be focused on Qt wiring, no API logic
