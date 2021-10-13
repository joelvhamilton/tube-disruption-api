import datetime
import sqlite3
import urllib

import flask
from flask import request
from controller import controller, task

app = flask.Flask(__name__)
app.config["DEBUG"] = True

# initialising controller instance for the app
app_controller = controller()

# scheduling all tasks that were in DB already when server started
test_db = sqlite3.connect('test.db')        
cursor = test_db.cursor()
cursor.execute('SELECT * FROM tasks;')
stored_tasks = cursor.fetchall()
for stored_task in stored_tasks:
    cursor2 = test_db.cursor()
    cursor2.execute('SELECT line_id FROM task_lines WHERE task_lines.task_id=\''+stored_task[1]+'\';')
    lines = cursor2.fetchall()
    task_being_scheduled = task(datetime.datetime.strptime(stored_task[0], '%Y-%m-%d %H:%M:%S'), lines[0]) # only the first item in lines[], as the query returns them all in a tuple in array[0]
    task_being_scheduled.id = stored_task[1]
    app_controller.schedule_task(task_being_scheduled)

# Home Route, not used.
@app.route('/v1', methods=['GET'])
def home():
    return {"message": "Wovenlight TFL App"}

# Endpoint to add a new task
@app.route('/v1/tasks', methods=['POST'])
def add_task():
    json_request_data = urllib.parse.parse_qs(request.get_data(parse_form_data=False, as_text=True))
    if (json_request_data.get('schedule_time') and json_request_data.get('lines')):
        # check that line id is valid!
        schedule_time = json_request_data.get('schedule_time')[0]
        lines = json_request_data.get('lines')[0].split(',')
        schedule_time = datetime.datetime.strptime(schedule_time, '%Y-%m-%dT%H:%M:%S')
        return app_controller.add_task(schedule_time, lines)
    elif (json_request_data.get('lines')):
            # perform task right now
            lines = json_request_data.get('lines')[0].split(',')
            return app_controller.add_task("now", lines)
    return {"message": "Unable to create task. Line_ids must be comma-separated."}

# Endpoint to get all tasks
@app.route('/v1/tasks', methods=['GET'])
def get_all_tasks():
    all_tasks = app_controller.get_all_tasks()
    return {'tasks': all_tasks}

# Endpoint to get a particular task with a given id
@app.route('/v1/tasks/<task_id>', methods=['GET'])
def get_task(task_id):
    task_to_return = app_controller.get_task(task_id)
    return task_to_return

# Endpoint to delete a particular task with a given id
@app.route('/v1/tasks/<task_id>', methods=['DELETE'])
def delete_task(task_id):
    return app_controller.delete_task(task_id)

# Endpoint to edit a particular task with a given id which has not yet run
@app.route('/v1/tasks/<task_id>', methods=['PATCH'])
def edit_task(task_id):
    json_request_data = urllib.parse.parse_qs(request.get_data(parse_form_data=False, as_text=True))
    task_to_edit = app_controller.get_task(task_id)
    if (json_request_data.get('lines')):
        lines = json_request_data.get('lines')[0].split(',')
    else:
        lines = task_to_edit.lines
    if (json_request_data.get('schedule_time')):
        schedule_time = json_request_data.get('schedule_time')[0]
        schedule_time = datetime.datetime.strptime(schedule_time, '%Y-%m-%dT%H:%M:%S')
    else:
        schedule_time = task_to_edit.schedule_time
    return app_controller.edit_task(task_id, schedule_time, lines)
    

app.run(host="localhost", port=5555)