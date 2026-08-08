from pathlib import Path

from flask import Blueprint, Response, send_file, url_for


swagger = Blueprint("swagger", __name__)

OPENAPI_SPEC_PATH = Path(__file__).with_name("openapi.yaml")


@swagger.get("/openapi.yaml")
def openapi_spec():
    return send_file(
        OPENAPI_SPEC_PATH,
        mimetype="application/yaml",
        max_age=0,
    )


@swagger.get("/docs")
def swagger_ui():
    specification_url = url_for("swagger.openapi_spec")
    html = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>DealBrief AI API Docs</title>
    <link
      rel="stylesheet"
      href="https://unpkg.com/swagger-ui-dist@5.32.6/swagger-ui.css"
    >
    <style>
      body {{
        margin: 0;
        background: #f8fafc;
      }}
      .swagger-ui .topbar {{
        display: none;
      }}
    </style>
  </head>
  <body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5.32.6/swagger-ui-bundle.js"></script>
    <script src="https://unpkg.com/swagger-ui-dist@5.32.6/swagger-ui-standalone-preset.js"></script>
    <script>
      window.onload = () => {{
        window.ui = SwaggerUIBundle({{
          url: {specification_url!r},
          dom_id: "#swagger-ui",
          deepLinking: true,
          displayRequestDuration: true,
          filter: true,
          presets: [
            SwaggerUIBundle.presets.apis,
            SwaggerUIStandalonePreset
          ],
          layout: "StandaloneLayout",
          validatorUrl: null
        }});
      }};
    </script>
  </body>
</html>
"""
    return Response(html, mimetype="text/html")
