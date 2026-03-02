import os
import logging
from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException
from src.infrastructure.config.extensions import db, migrate
from src.infrastructure.config.logging_setup import setup_logging
from dotenv import load_dotenv

def create_app(config_object=None):
    load_dotenv()
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting Application...")
    
    app = Flask(__name__)
    
    if config_object:
        app.config.from_object(config_object)
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
        if not app.config['SQLALCHEMY_DATABASE_URI']:
            raise RuntimeError("DATABASE_URL environment variable is not set")
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    migrate.init_app(app, db)

    with app.app_context():
        import src.infrastructure.adapters.output.persistence.models

    # Register Blueprints
    from src.infrastructure.adapters.input.api.v1.loans_routes import loans_bp
    app.register_blueprint(loans_bp)

    # Global Error Handlers
    @app.errorhandler(ValueError)
    def handle_value_error(e):
        logger = logging.getLogger(__name__)
        logger.warning(f"Error: {str(e)}", extra={"payload": request.get_json(silent=True)})
        return jsonify({
            "error": "Bad Request",
            "message": str(e)
        }), 400

    @app.errorhandler(TypeError)
    def handle_type_error(e):
        logger = logging.getLogger(__name__)
        logger.warning(f"Type Error: {str(e)}")
        return jsonify({
            "error": "Unprocessable Entity",
            "message": "Invalid data type provided in the request payload."
        }), 422

    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        logger = logging.getLogger(__name__)
        logger.warning(f"HTTP Exception: {e.name} - {e.description}")
        return jsonify({
            "error": e.name,
            "message": e.description
        }), e.code

    @app.errorhandler(Exception)
    def handle_generic_exception(e):
        logger = logging.getLogger(__name__)
        logger.error(f"Internal Server Error: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Internal Server Error",
            "message": "An unexpected error occurred."
        }), 500

    @app.route('/health')
    def health():
        return jsonify({
            "status": "success", 
            "message": "Financial Flask service is running correctly",
            "environment": os.getenv('FLASK_ENV', 'development')
        }), 200

    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.getenv('PORT', 5001))
    app.run(debug=True, host='0.0.0.0', port=port)