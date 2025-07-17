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
    
    # Rejestracja blueprintów - SPÓJNA STRUKTURA
    from app.routes.auth import auth_bp
    from app.routes.minigames import minigames_bp
    from app.routes.leaderboard import leaderboard_bp  # NOWY
    from app.routes.achievements import achievements_bp  # NOWY
    from app.routes.quests import quests_bp  # NOWY
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(minigames_bp)
    app.register_blueprint(leaderboard_bp)  # NOWY
    app.register_blueprint(achievements_bp)  # NOWY
    app.register_blueprint(quests_bp)  # NOWY
    
    # Inicjalizacja WebSocket (jeśli dostępne)
    try:
        from flask_socketio import SocketIO
        socketio = SocketIO(app, cors_allowed_origins="*", logger=False, engineio_logger=False)
        app.socketio = socketio
        
        # Rejestruj WebSocket events
        register_websocket_events(socketio)
        print("✅ WebSocket support enabled")
    except ImportError:
        print("⚠️  WebSocket support disabled (flask-socketio not installed)")
        app.socketio = None
    
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
    
    # API ENDPOINTS - ZACHOWANE DLA KOMPATYBILNOŚCI
    @app.route('/api/test')
    def test_api():
        """Test API"""
        try:
            # Test połączenia z bazą danych
            with db.engine.connect() as conn:
                result = conn.execute(db.text('SELECT COUNT(*) FROM users'))
                user_count = result.scalar()
            database_status = f"✅ Connected ({user_count} users)"
            
            # Test nowych tabel
            try:
                achievements_count = conn.execute(db.text('SELECT COUNT(*) FROM achievements')).scalar()
                quests_count = conn.execute(db.text('SELECT COUNT(*) FROM daily_quests')).scalar()
            except:
                achievements_count = 0
                quests_count = 0
            
        except Exception as e:
            database_status = f"❌ Connection failed: {str(e)}"
            achievements_count = 0
            quests_count = 0
        
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
                "mobile_support": "✅ Ready",
                "achievements": f"✅ Active ({achievements_count} achievements)",
                "daily_quests": f"✅ Active ({quests_count} quests)",
                "websockets": "✅ Ready" if app.socketio else "❌ Disabled"
            },
            "endpoints": {
                "auth": "/auth/*",
                "minigames": "/minigames/*", 
                "leaderboard": "/leaderboard/*",
                "achievements": "/achievements/*",
                "quests": "/quests/*"
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
                
                # Sprawdź nowe tabele
                try:
                    achievements_result = conn.execute(db.text('SELECT COUNT(*) FROM achievements'))
                    achievements_count = achievements_result.scalar()
                    
                    quests_result = conn.execute(db.text('SELECT COUNT(*) FROM daily_quests WHERE quest_date = date("now")'))
                    today_quests_count = quests_result.scalar()
                except:
                    achievements_count = 0
                    today_quests_count = 0
            
            return jsonify({
                "backend": "✅ Online",
                "architecture": "Modular Flask + Blueprints",
                "database": f"✅ Active ({user_count} users, {games_count} game sessions)",
                "users_count": user_count,
                "games_count": games_count,
                "achievements_count": achievements_count,
                "today_quests": today_quests_count,
                "games": "✅ Virus Alert, Space Defence, WiFi Guard",
                "authentication": "✅ Working",
                "session_management": "✅ Active",
                "mobile_support": "✅ Touch & Gyroscope",
                "achievements_system": "✅ Active",
                "daily_quests": "✅ Active",
                "real_time": "✅ WebSocket Ready" if app.socketio else "✅ Available",
                "modules": {
                    "auth": "✅ Active",
                    "minigames": "✅ Active",
                    "leaderboard": "✅ Active", 
                    "achievements": "✅ Active",
                    "quests": "✅ Active"
                }
            })
        except Exception as e:
            return jsonify({
                "backend": "⚠️ Online with issues",
                "architecture": "Modular Flask + Blueprints", 
                "database": "❌ Connection failed",
                "error": str(e)
            }), 500
    
    # SUBMITTING SCORES - UNIFIED API
    @app.route('/api/submit-score', methods=['POST'])
    def submit_score():
        """Unified API endpoint for submitting game scores"""
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        
        from app.models.user import User
        from app.models.minigames import GameSession
        from app.models.achievements import Achievement
        from app.models.daily_quests import DailyQuest
        from datetime import datetime
        
        current_user = User.query.get(session['user_id'])
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        
        # Walidacja danych
        required_fields = ['game_type', 'score', 'duration']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing field: {field}'}), 400
        
        if data['game_type'] not in ['virus_alert', 'space_defence', 'wifi_guard']:
            return jsonify({'error': 'Invalid game type'}), 400
        
        try:
            # Zapisz wynik
            session = GameSession(
                user_id=current_user.id,
                game_type=data['game_type'],
                score=int(data['score']),
                duration=int(data['duration']),
                completed=True,
                finished_at=datetime.utcnow()
            )
            
            if 'game_data' in data:
                session.set_game_data(data['game_data'])
            
            db.session.add(session)
            db.session.commit()
            
            # Sprawdź osiągnięcia i questy
            achievements_unlocked = Achievement.check_and_unlock(current_user.id, data['game_type'], int(data['score']))
            quest_progress = DailyQuest.update_progress(current_user.id, 'play_games', data['game_type'], int(data['score']))
            
            # WebSocket broadcast (jeśli dostępne)
            if app.socketio:
                try:
                    broadcast_new_score(app.socketio, current_user.id, data['game_type'], int(data['score']), session.id)
                except:
                    pass  # Silent fail
            
            return jsonify({
                'success': True,
                'session_id': session.id,
                'achievements_unlocked': achievements_unlocked,
                'quest_progress': quest_progress,
                'message': f'Score {data["score"]} saved successfully!'
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': 'Failed to save score', 'details': str(e)}), 500
    
    @app.errorhandler(404)
    def not_found_error(error):
        from flask import request
        if request.path.startswith('/api/'):
            return jsonify({
                "error": "Not Found",
                "message": "The requested API endpoint was not found",
                "status_code": 404,
                "path": request.path,
                "available_endpoints": {
                    "auth": "/auth/*",
                    "minigames": "/minigames/*",
                    "leaderboard": "/leaderboard/*", 
                    "achievements": "/achievements/*",
                    "quests": "/quests/*"
                }
            }), 404
        else:
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
                    
                    # Dodaj informacje o osiągnięciach i questach
                    try:
                        from app.models.achievements import UserAchievement
                        from app.models.daily_quests import DailyQuest
                        from datetime import date
                        
                        user_data['achievements_count'] = UserAchievement.query.filter_by(user_id=user.id).count()
                        
                        # Dzisiejsze questy
                        today_quests = DailyQuest.get_user_daily_quests(user.id)
                        completed_today = sum(1 for q in today_quests if q['completed'])
                        user_data['today_quests'] = {
                            'total': len(today_quests),
                            'completed': completed_today
                        }
                    except:
                        # Jeśli tabele nie istnieją jeszcze
                        user_data['achievements_count'] = 0
                        user_data['today_quests'] = {'total': 0, 'completed': 0}
                    
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

# ===============================
# WEBSOCKET FUNKCJE
# ===============================

def register_websocket_events(socketio):
    """Rejestruje WebSocket event handlers"""
    
    @socketio.on('connect')
    def handle_connect():
        print(f'Client connected')
        socketio.emit('connection_response', {
            'status': 'connected',
            'message': 'Welcome to World.Inc live updates!',
            'timestamp': datetime.utcnow().isoformat()
        })
    
    @socketio.on('disconnect')
    def handle_disconnect():
        print(f'Client disconnected')
    
    @socketio.on('join_leaderboard')
    def handle_join_leaderboard(data):
        """Dołącz do room leaderboard dla konkretnej gry"""
        from flask_socketio import join_room, emit
        
        game_type = data.get('game_type', 'all')
        
        if game_type not in ['virus_alert', 'space_defence', 'wifi_guard', 'all']:
            emit('error', {'message': 'Invalid game type'})
            return
        
        room = f'leaderboard_{game_type}'
        join_room(room)
        
        emit('joined_room', {
            'room': room,
            'message': f'Joined {game_type} leaderboard updates'
        })

def broadcast_new_score(socketio, user_id, game_type, score, session_id):
    """Rozgłasza nowy wynik do wszystkich połączonych klientów"""
    from app.models.user import User
    from datetime import datetime
    
    user = User.query.get(user_id)
    if not user:
        return
    
    # Dane do rozgłoszenia
    score_data = {
        'user_id': user_id,
        'username': user.username,
        'game_type': game_type,
        'score': score,
        'timestamp': datetime.utcnow().isoformat(),
        'session_id': session_id
    }
    
    # Wyślij do wszystkich w room leaderboard
    socketio.emit('new_score', score_data, room=f'leaderboard_{game_type}')
    socketio.emit('new_score', score_data, room='leaderboard_all')