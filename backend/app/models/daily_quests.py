# app/models/daily_quests.py - NOWY PLIK
from app.extensions import db
from datetime import datetime, date, timedelta
from sqlalchemy import func
import random

class DailyQuest(db.Model):
    """Model dziennych questów"""
    __tablename__ = 'daily_quests'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    quest_type = db.Column(db.String(50), nullable=False)  # play_games, score_points, play_specific_game
    target_value = db.Column(db.Integer, nullable=False)  # ile trzeba osiągnąć
    target_game = db.Column(db.String(50))  # dla questów specyficznych dla gry
    reward_points = db.Column(db.Integer, default=50)
    reward_type = db.Column(db.String(50), default='points')  # points, achievement, special
    quest_date = db.Column(db.Date, default=date.today)
    is_active = db.Column(db.Boolean, default=True)
    difficulty = db.Column(db.String(20), default='normal')  # easy, normal, hard
    icon = db.Column(db.String(50), default='tasks')  # FontAwesome icon
    
    # Relacja z progressem użytkowników
    user_progress = db.relationship('UserQuestProgress', backref='quest', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'quest_type': self.quest_type,
            'target_value': self.target_value,
            'target_game': self.target_game,
            'reward_points': self.reward_points,
            'reward_type': self.reward_type,
            'quest_date': self.quest_date.isoformat(),
            'difficulty': self.difficulty,
            'icon': self.icon
        }
    
    @staticmethod
    def generate_daily_quests(quest_date=None):
        """Generuje questy na dany dzień"""
        if quest_date is None:
            quest_date = date.today()
        
        # Sprawdź czy już są questy na ten dzień
        existing_quests = DailyQuest.query.filter_by(quest_date=quest_date, is_active=True).count()
        if existing_quests > 0:
            return False  # Już są questy na ten dzień
        
        # Szablony questów
        quest_templates = [
            # Questy na granie
            {
                'name': 'Daily Training',
                'description': 'Zagraj {target_value} gier, aby utrzymać swoje umiejętności',
                'quest_type': 'play_games',
                'target_value': 3,
                'reward_points': 50,
                'difficulty': 'easy',
                'icon': 'play'
            },
            {
                'name': 'Intensive Training',
                'description': 'Zagraj {target_value} gier i udowodnij swoją determinację',
                'quest_type': 'play_games',
                'target_value': 5,
                'reward_points': 75,
                'difficulty': 'normal',
                'icon': 'gamepad'
            },
            {
                'name': 'Marathon Agent',
                'description': 'Zagraj {target_value} gier w jednym dniu',
                'quest_type': 'play_games',
                'target_value': 10,
                'reward_points': 150,
                'difficulty': 'hard',
                'icon': 'trophy'
            },
            
            # Questy na punkty
            {
                'name': 'Point Collector',
                'description': 'Zdobądź łącznie {target_value} punktów',
                'quest_type': 'score_points',
                'target_value': 200,
                'reward_points': 60,
                'difficulty': 'normal',
                'icon': 'star'
            },
            {
                'name': 'High Scorer',
                'description': 'Zdobądź łącznie {target_value} punktów',
                'quest_type': 'score_points',
                'target_value': 500,
                'reward_points': 100,
                'difficulty': 'hard',
                'icon': 'medal'
            },
            
            # Questy specyficzne dla gier
            {
                'name': 'Virus Elimination',
                'description': 'Zagraj {target_value} razy w Virus Alert',
                'quest_type': 'play_specific_game',
                'target_value': 2,
                'target_game': 'virus_alert',
                'reward_points': 40,
                'difficulty': 'easy',
                'icon': 'bug'
            },
            {
                'name': 'Space Mission',
                'description': 'Zagraj {target_value} razy w Space Defence',
                'quest_type': 'play_specific_game',
                'target_value': 2,
                'target_game': 'space_defence',
                'reward_points': 40,
                'difficulty': 'easy',
                'icon': 'rocket'
            },
            {
                'name': 'Network Security',
                'description': 'Zagraj {target_value} razy w WiFi Guard',
                'quest_type': 'play_specific_game',
                'target_value': 2,
                'target_game': 'wifi_guard',
                'reward_points': 40,
                'difficulty': 'easy',
                'icon': 'wifi'
            },
            
            # Questy na perfekcję
            {
                'name': 'Perfect Score',
                'description': 'Zdobądź {target_value} punktów w jednej grze',
                'quest_type': 'single_game_score',
                'target_value': 300,
                'reward_points': 80,
                'difficulty': 'hard',
                'icon': 'crown'
            },
            {
                'name': 'Speed Runner',
                'description': 'Ukończ grę w mniej niż {target_value} sekund',
                'quest_type': 'time_limit',
                'target_value': 60,
                'reward_points': 70,
                'difficulty': 'normal',
                'icon': 'stopwatch'
            }
        ]
        
        # Wybierz 3-4 losowe questy na dzień
        num_quests = random.randint(3, 4)
        selected_templates = random.sample(quest_templates, num_quests)
        
        created_quests = []
        for template in selected_templates:
            # Dodaj losowość do wartości target
            if template['quest_type'] == 'play_games':
                if template['difficulty'] == 'easy':
                    template['target_value'] = random.randint(2, 3)
                elif template['difficulty'] == 'normal':
                    template['target_value'] = random.randint(4, 6)
                else:  # hard
                    template['target_value'] = random.randint(8, 12)
            
            elif template['quest_type'] == 'score_points':
                if template['difficulty'] == 'normal':
                    template['target_value'] = random.randint(150, 300)
                else:  # hard
                    template['target_value'] = random.randint(400, 600)
            
            # Stwórz quest
            quest = DailyQuest(
                name=template['name'],
                description=template['description'].format(target_value=template['target_value']),
                quest_type=template['quest_type'],
                target_value=template['target_value'],
                target_game=template.get('target_game'),
                reward_points=template['reward_points'],
                difficulty=template['difficulty'],
                icon=template['icon'],
                quest_date=quest_date
            )
            
            db.session.add(quest)
            created_quests.append(quest)
        
        db.session.commit()
        return created_quests
    
    @staticmethod
    def get_user_daily_quests(user_id, quest_date=None):
        """Pobiera dzienne questy dla użytkownika z progressem"""
        if quest_date is None:
            quest_date = date.today()
        
        # Pobierz wszystkie aktywne questy na dzień
        quests = DailyQuest.query.filter_by(quest_date=quest_date, is_active=True).all()
        
        result = []
        for quest in quests:
            # Pobierz progress użytkownika
            progress = UserQuestProgress.query.filter_by(
                user_id=user_id,
                quest_id=quest.id
            ).first()
            
            quest_data = quest.to_dict()
            quest_data['progress'] = progress.current_progress if progress else 0
            quest_data['completed'] = progress.completed if progress else False
            quest_data['completed_at'] = progress.completed_at.isoformat() if progress and progress.completed_at else None
            quest_data['progress_percentage'] = min(100, (quest_data['progress'] / quest.target_value) * 100)
            
            result.append(quest_data)
        
        return result
    
    @staticmethod
    def update_progress(user_id, quest_type, game_type=None, score=None):
        """Aktualizuje progress questów użytkownika"""
        today = date.today()
        updated_quests = []
        
        # Pobierz dzisiejsze questy
        quests = DailyQuest.query.filter_by(quest_date=today, is_active=True).all()
        
        for quest in quests:
            # Sprawdź czy quest pasuje do akcji
            should_update = False
            increment = 0
            
            if quest.quest_type == 'play_games':
                should_update = True
                increment = 1
            
            elif quest.quest_type == 'play_specific_game' and quest.target_game == game_type:
                should_update = True
                increment = 1
            
            elif quest.quest_type == 'score_points' and score:
                should_update = True
                increment = score
            
            elif quest.quest_type == 'single_game_score' and score:
                # Sprawdź czy to najlepszy wynik na dzisiaj
                existing_progress = UserQuestProgress.query.filter_by(
                    user_id=user_id,
                    quest_id=quest.id
                ).first()
                
                if not existing_progress or score > existing_progress.current_progress:
                    should_update = True
                    increment = score - (existing_progress.current_progress if existing_progress else 0)
            
            if should_update:
                # Pobierz lub stwórz progress
                progress = UserQuestProgress.query.filter_by(
                    user_id=user_id,
                    quest_id=quest.id
                ).first()
                
                if not progress:
                    progress = UserQuestProgress(
                        user_id=user_id,
                        quest_id=quest.id,
                        current_progress=0
                    )
                    db.session.add(progress)
                
                # Aktualizuj progress
                progress.current_progress += increment
                
                # Sprawdź czy quest został ukończony
                if not progress.completed and progress.current_progress >= quest.target_value:
                    progress.completed = True
                    progress.completed_at = datetime.utcnow()
                    
                    # Dodaj punkty użytkownikowi (jeśli masz system punktów)
                    # User.add_points(user_id, quest.reward_points)
                    
                    updated_quests.append({
                        'quest': quest.to_dict(),
                        'completed': True,
                        'reward_points': quest.reward_points
                    })
                else:
                    updated_quests.append({
                        'quest': quest.to_dict(),
                        'progress': progress.current_progress,
                        'completed': False
                    })
        
        db.session.commit()
        return updated_quests

class UserQuestProgress(db.Model):
    """Model postępu użytkownika w questach"""
    __tablename__ = 'user_quest_progress'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    quest_id = db.Column(db.Integer, db.ForeignKey('daily_quests.id'), nullable=False)
    current_progress = db.Column(db.Integer, default=0)
    completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Unikalna kombinacja user + quest
    __table_args__ = (db.UniqueConstraint('user_id', 'quest_id', name='unique_user_quest'),)
    
    # Relacje
    user = db.relationship('User', backref=db.backref('quest_progress', lazy=True))
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'quest_id': self.quest_id,
            'current_progress': self.current_progress,
            'completed': self.completed,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'started_at': self.started_at.isoformat(),
            'quest': self.quest.to_dict()
        }