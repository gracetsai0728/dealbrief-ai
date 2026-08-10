from pathlib import Path

from flask import Flask, abort, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import safe_join

from .config import Config
from .errors import ApiError
from .extensions import db
from .routes import api
from .swagger import swagger


FRONTEND_DIST = Path(__file__).resolve().parent / "frontend_dist"


def create_app(config_object=Config):
    app = Flask(__name__, static_folder=None)
    app.config.from_object(config_object)

    db.init_app(app)
    CORS(
        app,
        resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}},
        supports_credentials=True,
    )
    app.register_blueprint(api, url_prefix="/api")
    app.register_blueprint(swagger, url_prefix="/api")

    @app.get("/")
    def frontend_index():
        return send_from_directory(FRONTEND_DIST, "index.html")

    @app.get("/<path:path>")
    def frontend_files(path):
        # Unknown API URLs should keep returning the API's JSON 404 response
        # instead of falling back to the React application.
        if path == "api" or path.startswith("api/"):
            abort(404)

        requested_file = safe_join(str(FRONTEND_DIST), path)
        if requested_file and Path(requested_file).is_file():
            return send_from_directory(FRONTEND_DIST, path)

        # Support client-side routing by returning the React entry point for
        # any non-API path that is not a built asset.
        return send_from_directory(FRONTEND_DIST, "index.html")

    @app.errorhandler(ApiError)
    def handle_api_error(error):
        db.session.rollback()
        return jsonify({"error": error.to_dict()}), error.status_code

    @app.errorhandler(404)
    def handle_not_found(_error):
        return jsonify(
            {
                "error": {
                    "code": "NOT_FOUND",
                    "message": "The requested resource was not found.",
                    "details": None,
                }
            }
        ), 404

    @app.errorhandler(500)
    def handle_internal_error(error):
        db.session.rollback()
        app.logger.exception("Unhandled API error", exc_info=error)
        return jsonify(
            {
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected server error occurred.",
                    "details": None,
                }
            }
        ), 500

    return app
