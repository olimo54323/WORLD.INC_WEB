from flask import Flask, jsonify
from app.extensions import db, cors
from app.config import config

def create_app(config_name='development'):
    app = Flask(__name__)
    
    # Konfiguracja
    app.config.from_object(config[config_name])
    
    # Extensions (tylko db i cors na razie)
    db.init_app(app)
    cors.init_app(app)
    
    @app.route('/')
    def home():
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>🌍 World.Inc</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body class="bg-dark text-white">
            <div class="container mt-5 text-center">
                <h1>🌍 WORLD.INC</h1>
                <p class="lead">Modular Backend Working!</p>
                
                <div class="card bg-secondary mt-4">
                    <div class="card-body">
                        <h5>🔧 System Test</h5>
                        <button class="btn btn-success" onclick="testAPI()">Test API</button>
                        <div id="result" class="mt-3"></div>
                    </div>
                </div>
                
                <div class="mt-4">
                    <a href="/api/test" class="btn btn-info me-2">📋 API Test</a>
                    <a href="/api/status" class="btn btn-warning">📊 Status</a>
                </div>
            </div>
            
            <script>
                async function testAPI() {
                    try {
                        const response = await fetch('/api/test');
                        const data = await response.json();
                        document.getElementById('result').innerHTML = 
                            '<div class="alert alert-success">✅ ' + data.message + '</div>';
                    } catch (error) {
                        document.getElementById('result').innerHTML = 
                            '<div class="alert alert-danger">❌ ' + error.message + '</div>';
                    }
                }
            </script>
        </body>
        </html>
        """
    
    @app.route('/api/test')
    def test_api():
        return jsonify({
            "message": "🌍 Modular World.Inc API working!",
            "status": "Ready to save the world!",
            "version": "1.0"
        })
    
    @app.route('/api/status')
    def status():
        return jsonify({
            "backend": "✅ Online",
            "architecture": "Modular Flask"
        })
    
    return app