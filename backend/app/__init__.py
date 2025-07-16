from flask import Flask, jsonify, render_template, session, redirect, url_for, flash
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
    from app.routes.minigames import minigames_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(minigames_bp)
    
    @app.route('/')
    def home():
        """Strona główna"""
        return render_template('index.html')
    
    @app.route('/game')
    def game():
        """Strona gry (wymaga logowania)"""
        if 'user_id' not in session:
            flash('Musisz się zalogować aby rozpocząć grę', 'warning')
            return redirect(url_for('auth.login'))
        
        # Przekierowanie do minigier
        return redirect(url_for('minigames.index'))
    
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
            "version": "2.0.0",
            "database": database_status,
            "features": {
                "authentication": "✅ Active",
                "user_management": "✅ Active", 
                "minigames": "✅ Operational",
                "leaderboards": "✅ Active",
                "mobile_support": "✅ Ready"
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
                
                # Sprawdź liczbę sesji gier
                games_result = conn.execute(db.text('SELECT COUNT(*) FROM game_sessions'))
                games_count = games_result.scalar()
            
            return jsonify({
                "backend": "✅ Online",
                "architecture": "Modular Flask + Minigames",
                "database": f"✅ Active ({user_count} users, {games_count} game sessions)",
                "users_count": user_count,
                "games_count": games_count,
                "games": "✅ Virus Alert, Space Defence, WiFi Guard",
                "authentication": "✅ Working",
                "session_management": "✅ Active",
                "mobile_support": "✅ Touch & Gyroscope"
            })
        except Exception as e:
            return jsonify({
                "backend": "⚠️ Online with issues",
                "architecture": "Modular Flask + Minigames", 
                "database": "❌ Connection failed",
                "error": str(e)
            }), 500
    
    @app.errorhandler(404)
    def not_found_error(error):
        # Check if it's an API request
        from flask import request
        if request.path.startswith('/api/'):
            return jsonify({
                "error": "Not Found",
                "message": "The requested API endpoint was not found",
                "status_code": 404,
                "path": request.path
            }), 404
        else:
            # For non-API routes, show custom 404 page
            return render_template('404.html'), 404
    
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
    
    @app.context_processor
    def inject_globals():
        """Dodaje globalne funkcje i zmienne do templateów"""
        return dict(
            enumerate=enumerate,
            len=len,
            max=max,
            min=min,
            sum=sum,
            round=round,
            int=int
        )
    
    return app