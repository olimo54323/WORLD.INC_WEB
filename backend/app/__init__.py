from flask import Flask, jsonify, render_template, session
from app.extensions import db, cors
from app.config import config

def create_app(config_name='development'):
    app = Flask(__name__)
    
    # Konfiguracja
    app.config.from_object(config[config_name])
    
    # Extensions
    db.init_app(app)
    cors.init_app(app)
    
    # Rejestracja blueprintów
    from app.routes.auth import auth_bp
    app.register_blueprint(auth_bp)
    
    @app.route('/')
    def home():
        """Strona główna"""
        return render_template('index.html')
    
    @app.route('/game')
    def game():
        """Strona gry (wymaga logowania)"""
        if 'user_id' not in session:
            from flask import flash, redirect, url_for
            flash('Musisz się zalogować aby rozpocząć grę', 'warning')
            return redirect(url_for('auth.login'))
        
        # TODO: Tutaj będzie główna strona gry
        return render_template('index.html')  # Tymczasowo przekierowanie na index
    
    @app.route('/api/test')
    def test_api():
        """Test API"""
        try:
            # Test połączenia z bazą danych
            with db.engine.connect() as conn:
                result = conn.execute(db.text('SELECT COUNT(*) FROM users'))
                user_count = result.scalar()
            database_status = f"✅ Connected ({user_count} users)"
        except Exception:
            database_status = "❌ Connection failed"
        
        return jsonify({
            "message": "🌍 World.Inc API working perfectly!",
            "status": "Ready to save the world!",
            "version": "1.0.0",
            "database": database_status,
            "features": {
                "authentication": "✅ Active",
                "user_management": "✅ Active", 
                "game_sessions": "🔲 Coming Soon",
                "leaderboards": "🔲 Coming Soon"
            }
        })
    
    @app.route('/api/status')
    def status():
        """Status systemu"""
        try:
            # Sprawdź bazę danych
            with db.engine.connect() as conn:
                result = conn.execute(db.text('SELECT COUNT(*) FROM users'))
                user_count = result.scalar()
            
            return jsonify({
                "backend": "✅ Online",
                "architecture": "Modular Flask",
                "database": f"✅ Active ({user_count} users)",
                "users_count": user_count,
                "games": "🔲 In Development",
                "authentication": "✅ Working",
                "session_management": "✅ Active"
            })
        except Exception as e:
            return jsonify({
                "backend": "⚠️ Online with issues",
                "architecture": "Modular Flask", 
                "database": "❌ Connection failed",
                "error": str(e)
            }), 500
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return jsonify({
            "error": "Not Found",
            "message": "The requested resource was not found",
            "status_code": 404
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "status_code": 500
        }), 500
    
    # Funkcje pomocnicze dla templateów
    @app.context_processor
    def inject_user():
        """Dodaje informacje o użytkowniku do wszystkich templateów"""
        user_data = None
        if 'user_id' in session:
            try:
                from app.models.user import User
                user = User.query.get(session['user_id'])
                if user:
                    user_data = user.to_dict()
            except Exception:
                # Jeśli jest problem z bazą danych, wyczyść sesję
                session.clear()
        
        return dict(current_user=user_data)
    
    return app