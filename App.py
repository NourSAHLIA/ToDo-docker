from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import time,json
import redis


app = Flask(__name__)

time.sleep(5)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://admin:admin@db:5432/tasks'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Connect to Redis
# "redis" = the service name in docker-compose
cache = redis.Redis(host='redis', port=6379)

class Task(db.Model):
    __tablename__ = 'tasks'

    id          = db.Column(db.Integer, primary_key=True)   
    title       = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(500), default='')
    completed   = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            'id':          self.id,
            'title':       self.title,
            'description': self.description,
            'completed':   self.completed,
        }



with app.app_context():
    db.create_all()


@app.route('/')
def welcome():
    visits = cache.incr('visit_count')
    return f"Welcome to the TODO API with redis — visits: {visits}"


@app.route('/tasks', methods=['GET'])
def get_tasks():
    
    cached = cache.get('all_tasks')
    if cached:
        return jsonify(json.loads(cached)), 200

    
    tasks = Task.query.all()
    result = [t.to_dict() for t in tasks]

    
    cache.setex('all_tasks', 30, json.dumps(result))

    return jsonify(result), 200


@app.route('/tasks', methods=['POST'])
def create_task():
    req_data = request.get_json()

    if not req_data or not req_data.get('title'):
        return jsonify({'error': 'title is required'}), 400

    task = Task(
        title=req_data['title'].strip(),
        description=req_data.get('description', '')
    )
    db.session.add(task)
    db.session.commit()

    # clear the cache so next GET fetches fresh data
    cache.delete('all_tasks')

    return jsonify(task.to_dict()), 201


@app.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    task = Task.query.get(task_id)   
    if task is None:
        return jsonify({'error': f'Task {task_id} not found'}), 404

    db.session.delete(task)   
    db.session.commit()       
    
    cache.delete('all_tasks')
    
    return jsonify({'message': f'Task {task_id} deleted'}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)






"""
---------------------------------------------------------------------------------------------------------
tasks = []
next_id = 1


@app.route('/')
def welcom():
    return "welcome"


@app.route('/tasks/<string:title>', methods=['GET'])
def get_task(title):
    for task in tasks:
        if task['title'] == title:             
            return jsonify(task), 200           
    return jsonify({'message': 'task not found'}), 404


@app.route('/tasks', methods=['GET'])
def get_tasks():
   
    return jsonify(tasks), 200


@app.route('/tasks', methods=['POST'])
def create_task():
   
    global next_id
    req_data = request.get_json()

    if not req_data or not req_data.get('title'):   
        return jsonify({'error': 'title is required'}), 400

    new_task = {
        'id':          next_id,
        'title':       req_data['title'].strip(),       
        'description': req_data.get('description', ''),
        'completed':   False,
    }

    tasks.append(new_task)
    next_id += 1

    return jsonify(new_task), 201


@app.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    global tasks
    task = next((t for t in tasks if t['id'] == task_id), None)

    if task is None:
        return jsonify({'error': f'Task {task_id} not found'}), 404

    tasks = [t for t in tasks if t['id'] != task_id]
    return jsonify({'message': f'Task {task_id} deleted'}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)"""