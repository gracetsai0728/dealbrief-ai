from flask import Flask, jsonify
from flask_cors import CORS

from .config import Config
from .errors import ApiError
from .extensions import db
from .routes import api
from .swagger import swagger


def create_app(config_object=Config):
    app = Flask(__name__)
    app.config.from_object(config_object)

    db.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}})
    app.register_blueprint(api, url_prefix="/api")
    app.register_blueprint(swagger, url_prefix="/api")

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
