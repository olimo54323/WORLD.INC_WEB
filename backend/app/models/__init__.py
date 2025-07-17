from .user import User
from .minigames import GameSession, VirusAlert, SpaceDefence, WifiGuard, Leaderboard
from .achievements import Achievement, UserAchievement
from .daily_quests import DailyQuest, UserQuestProgress

# Eksportuj wszystkie modele dla łatwego importu
__all__ = [
    'User',
    'GameSession', 
    'VirusAlert', 
    'SpaceDefence', 
    'WifiGuard', 
    'Leaderboard',
    'Achievement',
    'UserAchievement', 
    'DailyQuest',
    'UserQuestProgress'
]