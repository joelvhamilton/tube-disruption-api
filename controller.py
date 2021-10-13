import datetime
import json
import sqlite3
import time

import datetime
from flask import request
import sched
import threading
from tfl_service import tfl_service

# task class for ease of passing data around when scheduling/executing/creating tasks
class task():
    schedule_time = ""
    lines = ""
    result = ""
    id = ""

    def __init__(self, schedule_time, lines):
        self.schedule_time = schedule_time
        self.lines = lines
        test_db = sqlite3.connect('test.db')        
        cursor = test_db.cursor()
        cursor.execute('SELECT task_id FROM tasks;')
        res = cursor.fetchall()
        max_id = 0
        for id in res:
            if (eval(id[0])> max_id):
                max_id = eval(id[0])
        self.id = str(max_id+1)

    def to_string(self):
        return (str(self.schedule_time) + " " + str(self.lines) + " " + str(self.id))

# controller class for the app, deals with all logic (scheduling tasks, executing tasks, and all db manipulations)
class controller:

    # function which calls the service to fetch the disruption data
    def execute_task(self, task):
        test_db = sqlite3.connect('test.db')        
        cursor = test_db.cursor()
        result = tfl_service.get_disruptions(task.lines).content.decode()
        json_results = json.loads(result)
        for disruption in json_results:
            category = disruption.get('category')
            description = disruption.get('description')
            cursor.execute('INSERT INTO results VALUES (\''+task.id+'\', \''+category + '\', \''+description+'\')')
        test_db.commit()
    
    # function which schedules the task to run at the correct time
    def schedule_task(self, task):
        scheduler = sched.scheduler(time.time, time.sleep)
        task_event = scheduler.enter((task.schedule_time - datetime.datetime.now()).seconds, 1, self.execute_task, (task,)) # the first argument of this call is the delay between now and the schedule_time.
        t = threading.Thread(target = scheduler.run)
        t.start()

    # function which adds a task to the db, and creates the object to be passed into the schedule_task function
    def add_task(self, schedule_time, lines):
        t = task(schedule_time, lines)
        test_db = sqlite3.connect('test.db')        
        cursor = test_db.cursor()
        if schedule_time=="now":
            t = task(schedule_time, lines)
            schedule_time = datetime.datetime.now()
            self.execute_task(t)
            cursor.execute('INSERT INTO tasks VALUES (\''+str(schedule_time.strftime('%Y-%m-%d %H:%M:%S'))+'\', \''+t.id+'\');')
            for line in lines:
                cursor.execute('INSERT INTO task_lines VALUES (\''+line+'\', \''+t.id+'\');')
            test_db.commit()
            cursor.execute('SELECT category, description FROM results WHERE task_id =\''+t.id+'\';')
            results = cursor.fetchall()
            results_json = []
            for result in results:
                result_json = {'category': result[0], 'information': result[1]}
                results_json.append(result_json)
                return {'message': 'Successfully created task.', 'task_id': t.id, 'schedule_time': str(schedule_time.strftime('%Y-%m-%d %H:%M:%S')), 'lines': lines, 'results': results_json}
        else:
            t = task(schedule_time, lines)
            self.schedule_task(t)
            cursor.execute('INSERT INTO tasks VALUES (\''+str(schedule_time.strftime('%Y-%m-%d %H:%M:%S'))+'\', \''+t.id+'\');')
            for line in lines:
                cursor.execute('INSERT INTO task_lines VALUES(\''+line+'\', \''+t.id+'\')')       
            test_db.commit()
            return {'message': 'Successfully created task.', 'task_id': t.id, 'schedule_time': str(schedule_time.strftime('%Y-%m-%d %H:%M:%S')), 'lines': lines}   

    # function which returns all tasks from the db, and their results and lines values.
    def get_all_tasks(self):
        test_db = sqlite3.connect('test.db')
        cursor = test_db.cursor()
        cursor.execute('SELECT task_id, schedule_time FROM tasks;')
        all_tasks = cursor.fetchall()
        json_tasks = []
        for task in all_tasks:
            cursor.execute('SELECT line_id FROM task_lines WHERE task_id='+task[0])
            lines = cursor.fetchall()
            cursor.execute('SELECT category, description FROM results WHERE task_id=\''+task[0]+'\';')
            results = cursor.fetchall()
            task_json = {'id': task[0], 'schedule_time': task[1], 'lines': lines}
            if len(results)==0:
                json_tasks.append({'task_details': task_json, 'results':'Task has not run yet'})
            else:
                results_json = []
                for result in results:
                    result_json = {'category': result[0], 'information': result[1]}
                    results_json.append(result_json)
                json_tasks.append({'task_details': task_json, 'results': results_json})
        return json_tasks
    
    # function to retrieve a task with the given id from the db
    def get_task(self, id):
        # need to do error handling for no task with this id
        test_db = sqlite3.connect('test.db')
        cursor = test_db.cursor()
        cursor.execute('SELECT task_id, schedule_time FROM tasks WHERE task_id='+id+';')
        tasks = cursor.fetchall()
        if (len(tasks) == 0):
            return {'Message': 'No task with id '+id}
        task = tasks[0]
        cursor.execute('SELECT line_id FROM task_lines WHERE task_id='+task[0])
        lines = cursor.fetchall()
        cursor.execute('SELECT category, description FROM results WHERE task_id='+task[0]+';')            
        results = cursor.fetchall()
        task_json = {'id': task[0], 'schedule_time': task[1], 'lines': lines}
        if len(results)==0:
            return {'task_details': task_json, 'results':'Task has not run yet, or ran but yielded no results.'}
        else:
            results_json = []
            for result in results:
                result_json = {'category': result[0], 'information': result[1]}
                results_json.append(result_json)
            return {'task_details': task_json, 'results': results_json}
    
    # function to edit the task in the db with the given id 
    # (it updates task details, but deletes lines and adds them again because there can be multiple entries in the task_lines db for a given id)
    def edit_task(self, id, schedule_time, lines):
        # need to do error handling for no task with this id
        test_db = sqlite3.connect('test.db')        
        cursor = test_db.cursor()
        cursor.execute('SELECT * FROM tasks WHERE task_id = \''+id+'\';')
        task = cursor.fetchall()
        if (len(task) == 0):
            return {'Message': 'No task with id '+id}
        cursor.execute('SELECT * FROM results WHERE task_id='+id)
        results = cursor.fetchall()
        print(results)
        if (len(results) > 0):
            return {"message": "this task has already run, so it cannot be edited."}
        cursor.execute('UPDATE tasks SET schedule_time=\''+str(schedule_time.strftime('%Y-%m-%d %H:%M:%S'))+'\' WHERE task_id = \''+id+'\'')
        cursor.execute('DELETE FROM task_lines WHERE task_id=\''+id+'\'')
        for line in lines:
            cursor.execute('INSERT INTO task_lines VALUES (\''+line+'\', '+id+')')
        test_db.commit()
        return {'message': 'Successfully updated task.', 'task_id': id, 'schedule_time': str(schedule_time.strftime('%Y-%m-%d %H:%M:%S')), 'lines': lines}
    
    # function to delete the task in the tb with the given id
    def delete_task(self, id):
        test_db = sqlite3.connect('test.db')        
        cursor = test_db.cursor()
        cursor.execute('SELECT * FROM tasks WHERE task_id = \''+id+'\';')
        task = cursor.fetchall()
        if (len(task) == 0):
            return {'Message': 'No task with id '+id}
        cursor.execute('DELETE FROM task_lines WHERE task_id=\''+id+'\'')
        cursor.execute('DELETE FROM tasks WHERE task_id=\''+id+'\'')
        test_db.commit()
        return {'message':'Successfully deleted task', 'task_id': id}