from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from app.extensions import db
from app.models.user import User
from app.models.achievements import Achievement, UserAchievement
from app.models.minigames import GameSession
from datetime import datetime

achievements_bp = Blueprint('achievements', __name__, url_prefix='/achievements')

def require_auth():
    """Sprawdza czy użytkownik jest zalogowany"""
    if 'user_id' not in session:
        return None
    return User.query.get(session['user_id'])

# ===============================
# STRONY HTML
# ===============================

@achievements_bp.route('/')
def index():
    """Główna strona osiągnięć"""
    current_user = require_auth()
    if not current_user:
        return redirect(url_for('auth.login'))
    
    # Pobierz wszystkie osiągnięcia z statusem dla użytkownika
    achievements = Achievement.query.filter_by(is_active=True).order_by(Achievement.points.desc()).all()
    user_achievements = {ua.achievement_id: ua for ua in UserAchievement.query.filter_by(user_id=current_user.id).all()}
    
    achievements_data = []
    total_points = 0
    unlocked_count = 0
    
    for achievement in achievements:
        user_achievement = user_achievements.get(achievement.id)
        is_unlocked = user_achievement is not None
        
        if is_unlocked:
            total_points += achievement.points
            unlocked_count += 1
        
        # Nie pokazuj ukrytych osiągnięć jeśli nie są odblokowane
        if achievement.is_hidden and not is_unlocked:
            continue
            
        achievements_data.append({
            'achievement': achievement,
            'unlocked': is_unlocked,
            'unlocked_at': user_achievement.unlocked_at if user_achievement else None,
            'progress': get_achievement_progress(current_user.id, achievement) if not is_unlocked else 100
        })
    
    # Statystyki użytkownika
    user_stats = {
        'total_achievements': len(achievements),
        'unlocked_achievements': unlocked_count,
        'total_points': total_points,
        'completion_percentage': round((unlocked_count / len(achievements)) * 100, 1) if achievements else 0
    }
    
    return render_template('achievements/index.html', 
                         achievements=achievements_data,
                         user_stats=user_stats,
                         user=current_user)

@achievements_bp.route('/leaderboard')
def leaderboard():
    """Ranking osiągnięć - kto ma najwięcej punktów"""
    # Top 20 użytkowników z największą liczbą punktów z osiągnięć
    top_users = db.session.query(
        User.id,
        User.username,
        db.func.count(UserAchievement.id).label('achievements_count'),
        db.func.sum(Achievement.points).label('total_points')
    ).join(
        UserAchievement, User.id == UserAchievement.user_id
    ).join(
        Achievement, UserAchievement.achievement_id == Achievement.id
    ).group_by(User.id, User.username).order_by(
        db.desc('total_points'), db.desc('achievements_count')
    ).limit(20).all()
    
    leaderboard_data = []
    for i, user_data in enumerate(top_users, 1):
        leaderboard_data.append({
            'rank': i,
            'user_id': user_data.id,
            'username': user_data.username,
            'achievements_count': user_data.achievements_count,
            'total_points': user_data.total_points or 0
        })
    
    # Pozycja aktualnego użytkownika
    current_user = require_auth()
    user_rank = None
    user_points = 0
    
    if current_user:
        user_achievements = UserAchievement.query.filter_by(user_id=current_user.id).all()
        user_points = sum(ua.achievement.points for ua in user_achievements)
        
        # Znajdź pozycję użytkownika
        better_users = db.session.query(db.func.count(db.distinct(User.id))).join(
            UserAchievement, User.id == UserAchievement.user_id
        ).join(
            Achievement, UserAchievement.achievement_id == Achievement.id
        ).group_by(User.id).having(
            db.func.sum(Achievement.points) > user_points
        ).count()
        
        user_rank = better_users + 1 if user_points > 0 else None
    
    return render_template('achievements/leaderboard.html',
                         leaderboard=leaderboard_data,
                         user_rank=user_rank,
                         user_points=user_points)

@achievements_bp.route('/api/list')
def api_list_achievements():
    """API: Lista wszystkich osiągnięć"""
    current_user = require_auth()
    
    achievements = Achievement.query.filter_by(is_active=True).all()
    
    result = []
    for achievement in achievements:
        data = achievement.to_dict()
        
        # Dodaj informację czy użytkownik ma to osiągnięcie
        if current_user:
            user_achievement = UserAchievement.query.filter_by(
                user_id=current_user.id, 
                achievement_id=achievement.id
            ).first()
            data['unlocked'] = user_achievement is not None
            data['unlocked_at'] = user_achievement.unlocked_at.isoformat() if user_achievement else None
            data['progress'] = get_achievement_progress(current_user.id, achievement) if not user_achievement else 100
        else:
            data['unlocked'] = False
            data['unlocked_at'] = None
            data['progress'] = 0
        
        # Ukryj ukryte osiągnięcia jeśli nie są odblokowane
        if achievement.is_hidden and not data['unlocked']:
            data['name'] = '???'
            data['description'] = 'Hidden achievement'
            data['icon'] = 'question'
        
        result.append(data)
    
    return jsonify({'achievements': result})

@achievements_bp.route('/api/user/<int:user_id>')
def api_user_achievements(user_id):
    """API: Osiągnięcia konkretnego użytkownika"""
    current_user = require_auth()
    if not current_user or (current_user.id != user_id and not hasattr(current_user, 'is_admin')):
        return jsonify({'error': 'Unauthorized'}), 403
    
    user = User.query.get_or_404(user_id)
    user_achievements = UserAchievement.query.filter_by(user_id=user_id).all()
    
    achievements_data = []
    total_points = 0
    
    for ua in user_achievements:
        achievement_data = ua.achievement.to_dict()
        achievement_data['unlocked_at'] = ua.unlocked_at.isoformat()
        achievement_data['progress'] = ua.progress
        achievements_data.append(achievement_data)
        total_points += ua.achievement.points
    
    return jsonify({
        'user': user.to_dict(),
        'achievements': achievements_data,
        'total_points': total_points,
        'achievements_count': len(achievements_data)
    })

@achievements_bp.route('/api/check/<int:user_id>', methods=['POST'])
def api_check_achievements(user_id):
    """API: Sprawdź i odblokuj osiągnięcia dla użytkownika"""
    current_user = require_auth()
    if not current_user or current_user.id != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json() or {}
    game_type = data.get('game_type')
    score = data.get('score')
    
    # Sprawdź osiągnięcia
    unlocked_achievements = Achievement.check_and_unlock(user_id, game_type, score)
    
    return jsonify({
        'unlocked_achievements': unlocked_achievements,
        'count': len(unlocked_achievements)
    })

@achievements_bp.route('/api/stats')
def api_achievements_stats():
    """API: Globalne statystyki osiągnięć"""
    total_achievements = Achievement.query.filter_by(is_active=True).count()
    total_unlocks = UserAchievement.query.count()
    total_users_with_achievements = db.session.query(
        db.func.count(db.distinct(UserAchievement.user_id))
    ).scalar()
    
    # Najpopularniejsze osiągnięcie
    popular_achievement = db.session.query(
        Achievement.name,
        db.func.count(UserAchievement.id).label('unlock_count')
    ).join(UserAchievement).group_by(Achievement.id, Achievement.name).order_by(
        db.desc('unlock_count')
    ).first()
    
    # Najrzadsze osiągnięcie (nie ukryte)
    rare_achievement = db.session.query(
        Achievement.name,
        db.func.count(UserAchievement.id).label('unlock_count')
    ).outerjoin(UserAchievement).filter(
        Achievement.is_hidden == False,
        Achievement.is_active == True
    ).group_by(Achievement.id, Achievement.name).order_by(
        'unlock_count'
    ).first()
    
    return jsonify({
        'total_achievements': total_achievements,
        'total_unlocks': total_unlocks,
        'users_with_achievements': total_users_with_achievements,
        'most_popular': {
            'name': popular_achievement.name if popular_achievement else None,
            'unlock_count': popular_achievement.unlock_count if popular_achievement else 0
        },
        'rarest': {
            'name': rare_achievement.name if rare_achievement else None,
            'unlock_count': rare_achievement.unlock_count if rare_achievement else 0
        }
    })

@achievements_bp.route('/api/recent')
def api_recent_achievements():
    """API: Ostatnio odblokowane osiągnięcia"""
    recent_unlocks = db.session.query(
        UserAchievement.unlocked_at,
        User.username,
        Achievement.name,
        Achievement.icon,
        Achievement.points
    ).join(User).join(Achievement).order_by(
        db.desc(UserAchievement.unlocked_at)
    ).limit(10).all()
    
    recent_data = []
    for unlock in recent_unlocks:
        recent_data.append({
            'username': unlock.username,
            'achievement_name': unlock.name,
            'achievement_icon': unlock.icon,
            'points': unlock.points,
            'unlocked_at': unlock.unlocked_at.isoformat(),
            'time_ago': get_time_ago(unlock.unlocked_at)
        })
    
    return jsonify({'recent_achievements': recent_data})

# ===============================
# HELPER FUNCTIONS
# ===============================

def get_achievement_progress(user_id, achievement):
    """Oblicza postęp użytkownika dla danego osiągnięcia"""
    from app.models.minigames import GameSession
    
    try:
        if achievement.condition_type == 'score':
            # Najwyższy wynik w grze
            query = db.session.query(db.func.max(GameSession.score)).filter(
                GameSession.user_id == user_id,
                GameSession.completed == True
            )
            
            if achievement.condition_game:
                query = query.filter(GameSession.game_type == achievement.condition_game)
            
            current_value = query.scalar() or 0
            
        elif achievement.condition_type == 'games_played':
            # Liczba zagranych gier
            query = db.session.query(db.func.count(GameSession.id)).filter(
                GameSession.user_id == user_id,
                GameSession.completed == True
            )
            
            if achievement.condition_game:
                query = query.filter(GameSession.game_type == achievement.condition_game)
            
            current_value = query.scalar() or 0
            
        elif achievement.condition_type == 'time':
            # Całkowity czas gry
            query = db.session.query(db.func.sum(GameSession.duration)).filter(
                GameSession.user_id == user_id,
                GameSession.completed == True
            )
            
            if achievement.condition_game:
                query = query.filter(GameSession.game_type == achievement.condition_game)
            
            current_value = query.scalar() or 0
            
        else:
            current_value = 0
        
        # Oblicz procent postępu
        progress = min(100, (current_value / achievement.condition_value) * 100)
        return round(progress, 1)
        
    except Exception:
        return 0

def get_time_ago(timestamp):
    """Oblicza czas jaki minął od danej daty"""
    now = datetime.utcnow()
    diff = now - timestamp
    
    if diff.total_seconds() < 60:
        return "just now"
    elif diff.total_seconds() < 3600:
        minutes = int(diff.total_seconds() / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif diff.total_seconds() < 86400:
        hours = int(diff.total_seconds() / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    else:
        days = diff.days
        return f"{days} day{'s' if days != 1 else ''} ago"