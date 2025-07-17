# app/routes/quests.py - NOWY PLIK
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from app.extensions import db
from app.models.user import User
from app.models.daily_quests import DailyQuest, UserQuestProgress
from datetime import datetime, date, timedelta

quests_bp = Blueprint('quests', __name__, url_prefix='/quests')

def require_auth():
    """Sprawdza czy użytkownik jest zalogowany"""
    if 'user_id' not in session:
        return None
    return User.query.get(session['user_id'])

@quests_bp.route('/')
def index():
    """Główna strona questów"""
    current_user = require_auth()
    if not current_user:
        return redirect(url_for('auth.login'))
    
    # Pobierz dzisiejsze questy
    today_quests = DailyQuest.get_user_daily_quests(current_user.id)
    
    # Statystyki questów
    completed_today = sum(1 for q in today_quests if q['completed'])
    total_today = len(today_quests)
    
    # Punkty zdobyte dzisiaj z questów
    points_today = sum(q['reward_points'] for q in today_quests if q['completed'])
    
    # Historia questów (ostatnie 7 dni)
    week_ago = date.today() - timedelta(days=7)
    recent_quests = db.session.query(
        DailyQuest.quest_date,
        db.func.count(DailyQuest.id).label('total_quests'),
        db.func.count(UserQuestProgress.id).label('completed_quests'),
        db.func.sum(DailyQuest.reward_points).label('total_points')
    ).outerjoin(
        UserQuestProgress, 
        (DailyQuest.id == UserQuestProgress.quest_id) & 
        (UserQuestProgress.user_id == current_user.id) & 
        (UserQuestProgress.completed == True)
    ).filter(
        DailyQuest.quest_date >= week_ago,
        DailyQuest.is_active == True
    ).group_by(DailyQuest.quest_date).order_by(
        db.desc(DailyQuest.quest_date)
    ).all()
    
    history_data = []
    for quest_day in recent_quests:
        completion_rate = (quest_day.completed_quests / quest_day.total_quests * 100) if quest_day.total_quests > 0 else 0
        history_data.append({
            'date': quest_day.quest_date,
            'total_quests': quest_day.total_quests,
            'completed_quests': quest_day.completed_quests or 0,
            'completion_rate': round(completion_rate, 1),
            'points_earned': quest_day.total_points or 0
        })
    
    user_stats = {
        'completed_today': completed_today,
        'total_today': total_today,
        'points_today': points_today,
        'completion_rate_today': round((completed_today / total_today * 100), 1) if total_today > 0 else 0
    }
    
    return render_template('quests/index.html',
                         quests=today_quests,
                         user_stats=user_stats,
                         history=history_data,
                         user=current_user)

@quests_bp.route('/history')
def history():
    """Historia questów użytkownika"""
    current_user = require_auth()
    if not current_user:
        return redirect(url_for('auth.login'))
    
    # Parametry paginacji
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Pobierz historię questów
    quests_query = db.session.query(
        DailyQuest,
        UserQuestProgress
    ).outerjoin(
        UserQuestProgress,
        (DailyQuest.id == UserQuestProgress.quest_id) & 
        (UserQuestProgress.user_id == current_user.id)
    ).filter(
        DailyQuest.is_active == True
    ).order_by(db.desc(DailyQuest.quest_date))
    
    paginated_quests = quests_query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    history_data = []
    for quest, progress in paginated_quests.items:
        quest_data = quest.to_dict()
        quest_data['progress'] = progress.current_progress if progress else 0
        quest_data['completed'] = progress.completed if progress else False
        quest_data['completed_at'] = progress.completed_at.isoformat() if progress and progress.completed_at else None
        history_data.append(quest_data)
    
    return render_template('quests/history.html',
                         quests=history_data,
                         pagination=paginated_quests,
                         user=current_user)

@quests_bp.route('/leaderboard')
def leaderboard():
    """Ranking questów - kto ukończył najwięcej"""
    # Ranking użytkowników według ukończonych questów (ostatnie 30 dni)
    month_ago = date.today() - timedelta(days=30)
    
    top_questers = db.session.query(
        User.id,
        User.username,
        db.func.count(UserQuestProgress.id).label('completed_quests'),
        db.func.sum(DailyQuest.reward_points).label('total_points')
    ).join(
        UserQuestProgress, User.id == UserQuestProgress.user_id
    ).join(
        DailyQuest, UserQuestProgress.quest_id == DailyQuest.id
    ).filter(
        UserQuestProgress.completed == True,
        DailyQuest.quest_date >= month_ago
    ).group_by(User.id, User.username).order_by(
        db.desc('completed_quests'), db.desc('total_points')
    ).limit(20).all()
    
    leaderboard_data = []
    for i, user_data in enumerate(top_questers, 1):
        leaderboard_data.append({
            'rank': i,
            'user_id': user_data.id,
            'username': user_data.username,
            'completed_quests': user_data.completed_quests,
            'total_points': user_data.total_points or 0
        })
    
    # Pozycja aktualnego użytkownika
    current_user = require_auth()
    user_rank = None
    user_completed = 0
    user_points = 0
    
    if current_user:
        user_stats = db.session.query(
            db.func.count(UserQuestProgress.id).label('completed_quests'),
            db.func.sum(DailyQuest.reward_points).label('total_points')
        ).join(
            DailyQuest, UserQuestProgress.quest_id == DailyQuest.id
        ).filter(
            UserQuestProgress.user_id == current_user.id,
            UserQuestProgress.completed == True,
            DailyQuest.quest_date >= month_ago
        ).first()
        
        user_completed = user_stats.completed_quests or 0
        user_points = user_stats.total_points or 0
        
        # Znajdź pozycję użytkownika
        better_users = db.session.query(db.func.count(db.distinct(User.id))).join(
            UserQuestProgress, User.id == UserQuestProgress.user_id
        ).join(
            DailyQuest, UserQuestProgress.quest_id == DailyQuest.id
        ).filter(
            UserQuestProgress.completed == True,
            DailyQuest.quest_date >= month_ago
        ).group_by(User.id).having(
            db.func.count(UserQuestProgress.id) > user_completed
        ).count()
        
        user_rank = better_users + 1 if user_completed > 0 else None
    
    return render_template('quests/leaderboard.html',
                         leaderboard=leaderboard_data,
                         user_rank=user_rank,
                         user_completed=user_completed,
                         user_points=user_points,
                         period_days=30)

# ===============================
# API ENDPOINTS
# ===============================

@quests_bp.route('/api/daily')
def api_daily_quests():
    """API: Dzisiejsze questy użytkownika"""
    current_user = require_auth()
    if not current_user:
        return jsonify({'error': 'Authentication required'}), 401
    
    quest_date = request.args.get('date')
    if quest_date:
        try:
            quest_date = datetime.strptime(quest_date, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format'}), 400
    else:
        quest_date = date.today()
    
    quests = DailyQuest.get_user_daily_quests(current_user.id, quest_date)
    
    return jsonify({
        'quests': quests,
        'quest_date': quest_date.isoformat(),
        'total': len(quests),
        'completed': sum(1 for q in quests if q['completed'])
    })

@quests_bp.route('/api/progress', methods=['POST'])
def api_update_progress():
    """API: Aktualizuj postęp questów"""
    current_user = require_auth()
    if not current_user:
        return jsonify({'error': 'Authentication required'}), 401
    
    data = request.get_json()
    quest_type = data.get('quest_type')
    game_type = data.get('game_type')
    score = data.get('score')
    
    if not quest_type:
        return jsonify({'error': 'Missing quest_type'}), 400
    
    # Aktualizuj postęp questów
    updated_quests = DailyQuest.update_progress(current_user.id, quest_type, game_type, score)
    
    return jsonify({
        'updated_quests': updated_quests,
        'count': len(updated_quests)
    })

@quests_bp.route('/api/generate', methods=['POST'])
def api_generate_quests():
    """API: Wygeneruj nowe questy (admin only)"""
    current_user = require_auth()
    if not current_user or not hasattr(current_user, 'is_admin'):
        return jsonify({'error': 'Admin access required'}), 403
    
    data = request.get_json() or {}
    quest_date = data.get('date')
    
    if quest_date:
        try:
            quest_date = datetime.strptime(quest_date, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format'}), 400
    else:
        quest_date = date.today()
    
    # Wygeneruj questy
    created_quests = DailyQuest.generate_daily_quests(quest_date)
    
    if created_quests:
        return jsonify({
            'success': True,
            'created_quests': [q.to_dict() for q in created_quests],
            'count': len(created_quests),
            'quest_date': quest_date.isoformat()
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Quests already exist for this date or generation failed'
        }), 400

@quests_bp.route('/api/stats')
def api_quest_stats():
    """API: Globalne statystyki questów"""
    today = date.today()
    
    # Statystyki dzisiejsze
    today_quests = DailyQuest.query.filter_by(quest_date=today, is_active=True).count()
    today_completions = db.session.query(db.func.count(UserQuestProgress.id)).join(
        DailyQuest, UserQuestProgress.quest_id == DailyQuest.id
    ).filter(
        DailyQuest.quest_date == today,
        UserQuestProgress.completed == True
    ).scalar()
    
    # Statystyki użytkowników
    active_questers_today = db.session.query(
        db.func.count(db.distinct(UserQuestProgress.user_id))
    ).join(
        DailyQuest, UserQuestProgress.quest_id == DailyQuest.id
    ).filter(
        DailyQuest.quest_date == today
    ).scalar()
    
    # Najpopularniejszy typ questa
    popular_quest_type = db.session.query(
        DailyQuest.quest_type,
        db.func.count(UserQuestProgress.id).label('completion_count')
    ).join(UserQuestProgress).filter(
        UserQuestProgress.completed == True
    ).group_by(DailyQuest.quest_type).order_by(
        db.desc('completion_count')
    ).first()
    
    return jsonify({
        'today_quests': today_quests,
        'today_completions': today_completions or 0,
        'active_questers_today': active_questers_today or 0,
        'completion_rate_today': round((today_completions / (today_quests * active_questers_today) * 100), 1) if today_quests and active_questers_today else 0,
        'most_popular_quest_type': popular_quest_type.quest_type if popular_quest_type else None,
        'popular_quest_completions': popular_quest_type.completion_count if popular_quest_type else 0
    })

@quests_bp.route('/api/user/<int:user_id>/stats')
def api_user_quest_stats(user_id):
    """API: Statystyki questów konkretnego użytkownika"""
    current_user = require_auth()
    if not current_user or (current_user.id != user_id and not hasattr(current_user, 'is_admin')):
        return jsonify({'error': 'Unauthorized'}), 403
    
    user = User.query.get_or_404(user_id)
    
    # Statystyki ostatnich 30 dni
    month_ago = date.today() - timedelta(days=30)
    
    monthly_stats = db.session.query(
        db.func.count(UserQuestProgress.id).label('completed_quests'),
        db.func.sum(DailyQuest.reward_points).label('total_points')
    ).join(
        DailyQuest, UserQuestProgress.quest_id == DailyQuest.id
    ).filter(
        UserQuestProgress.user_id == user_id,
        UserQuestProgress.completed == True,
        DailyQuest.quest_date >= month_ago
    ).first()
    
    # Dzisiejsze questy
    today_quests = DailyQuest.get_user_daily_quests(user_id)
    today_completed = sum(1 for q in today_quests if q['completed'])
    
    # Streak (dni z rzędu z ukończonymi questami)
    streak = calculate_quest_streak(user_id)
    
    return jsonify({
        'user': user.to_dict(),
        'monthly_completed': monthly_stats.completed_quests or 0,
        'monthly_points': monthly_stats.total_points or 0,
        'today_total': len(today_quests),
        'today_completed': today_completed,
        'current_streak': streak
    })

def calculate_quest_streak(user_id):
    """Oblicza ile dni z rzędu użytkownik ukończył przynajmniej jeden quest"""
    streak = 0
    current_date = date.today()
    
    while True:
        # Sprawdź czy w danym dniu użytkownik ukończył jakiś quest
        completed_any = db.session.query(UserQuestProgress).join(
            DailyQuest, UserQuestProgress.quest_id == DailyQuest.id
        ).filter(
            UserQuestProgress.user_id == user_id,
            UserQuestProgress.completed == True,
            DailyQuest.quest_date == current_date
        ).first()
        
        if completed_any:
            streak += 1
            current_date -= timedelta(days=1)
        else:
            break
        
        # Zabezpieczenie przed nieskończoną pętlą
        if streak > 365:
            break
    
    return streak