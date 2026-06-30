import os
from flask import Flask, render_template

def create_app() -> Flask:
    # Use workspace folder for templates/static if needed
    app = Flask(__name__, 
                template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
                static_folder=os.path.join(os.path.dirname(__file__), 'static'))
    
    app.config['SECRET_KEY'] = 'eightfold-intern-assignment-key'
    
    # Register blueprints
    from api.routes import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    @app.route('/')
    def index():
        return render_template('index.html')
        
    return app
