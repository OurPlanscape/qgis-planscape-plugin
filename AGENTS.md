# information

- API schema: https://dev.planscape.org/planscape-backend/v2/schema/swagger
- package manager: uv

# Rules

- ALL api requests should be authenticated (with the exception of login)
- Authentication is done with a JWT Token, with the following headers: Authorization: Bearer <token>
- ALWAYS check the shape of input and output payloads against the API schema, when constructing API calls
- ALWAYS use uv to manage packages
- ALWAYS use a two-layer approach for domain and API objects. API and domain models should be implemented with dataclasses
- Do NOT conflate domain and API objects/models. Keep them separate
- For dock tree changes, declare node kinds and behavior in `planscape/gui/dock_nodes.py`; keep `PlanscapeDockWidget` focused on Qt wiring.
- Lazy dock nodes must use one `load_children` path for first expansion and refresh; do not duplicate API loading logic.
- ALWAYS use qgis_plugin_tools/tools/network to make api calls
- ALWAYS use qgis_plugin_tools/tools/resources to process resourceS
