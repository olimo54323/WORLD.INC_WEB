from app import create_app
from app.extensions import db

# Utwórz aplikację
app = create_app('development')

# Utwórz tabele
with app.app_context():
    db.create_all()
    print("✅ Database initialized!")

if __name__ == '__main__':
    print("🚀 World.Inc Modular Backend Starting...")
    print("🔗 http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)