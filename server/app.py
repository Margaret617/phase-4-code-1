from flask import Flask, request, make_response, jsonify
from flask_migrate import Migrate
from models import db, Hero, Power, HeroPower
import os
from sqlalchemy.orm import joinedload

# Set up the database
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get(
    "DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.json.compact = False

migrate = Migrate(app, db)
db.init_app(app)


@app.route('/')
def index():
    return '<h1>Code challenge</h1>'


@app.route('/heroes/<int:id>', methods=['GET'])
def get_hero(id):
    hero = Hero.query.options(joinedload(Hero.hero_powers)).get(id)  # Load hero_powers relationship
    if not hero:
        return jsonify({'error': 'Hero not found'}), 404
    return jsonify({
        'id': hero.id,
        'name': hero.name,
        'super_name': hero.super_name,
        'hero_powers': [{'strength': hp.strength, 'power_id': hp.power_id} for hp in hero.hero_powers]
    })
    

@app.route('/heroes', methods=['GET'])
def get_heroes():
    heroes = Hero.query.all()
    return make_response(jsonify([hero.to_dict() for hero in heroes]), 200)


@app.route('/powers', methods=['GET'])
def get_powers():
    powers = Power.query.all()
    return make_response(jsonify([power.to_dict() for power in powers]), 200)


@app.route('/powers/<int:id>', methods=['GET'])
def get_power_by_id(id):
    power = Power.query.get(id)
    if power is None:
        return make_response(jsonify({'error': 'Power not found'}), 404)
    return make_response(jsonify(power.to_dict()), 200)


@app.route('/powers/<int:id>', methods=['PATCH'])
def update_power(id):
    power = Power.query.get_or_404(id)
    
    data = request.get_json()
    if 'description' in data:
        description = data['description']
        if not isinstance(description, str) or len(description) < 20:
            return jsonify({'errors': ["Description must be present and at least 20 characters long."]}), 400  # Return as a list
        
        power.description = description
        db.session.commit()
    
    return jsonify({
        'id': power.id,
        'name': power.name,
        'description': power.description
    }), 200


@app.route('/hero_powers', methods=['POST'])
def create_hero_power():
    data = request.get_json()
    strength = data.get('strength')
    hero_id = data.get('hero_id')
    power_id = data.get('power_id')

    # Validate strength
    if strength not in ['Strong', 'Weak', 'Average']:
        return jsonify({'errors': ["validation errors"]}), 400
    
    # Create HeroPower
    hero_power = HeroPower(hero_id=hero_id, power_id=power_id, strength=strength)
    db.session.add(hero_power)
    db.session.commit()

    # Fetch hero and power for response
    hero = Hero.query.get_or_404(hero_id)
    power = Power.query.get_or_404(power_id)

    return jsonify({
        'id': hero_power.id,
        'hero_id': hero_power.hero_id,
        'power_id': hero_power.power_id,
        'strength': hero_power.strength,
        'hero': {
            'name': hero.name,
            'super_name': hero.super_name
        },
        'power': {
            'name': power.name,
            'description': power.description
        }
    }), 201


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


@app.errorhandler(400)
def bad_request(error):
    return make_response(jsonify({'error': 'Bad request'}), 400)


with app.app_context():
    db.create_all() 

if __name__ == '__main__':
    app.run(port=5555, debug=True)
