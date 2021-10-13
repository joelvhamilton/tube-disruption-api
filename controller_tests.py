from controller import controller, task
import datetime

# this file contains unit tests for the controller functions

id = ""

def test_add_task():
    now = datetime.datetime.now()
    add_task_response = test_controller.add_task(now, ['central'])
    assert add_task_response['schedule_time'] == now.strftime('%Y-%m-%d %H:%M:%S')
    assert add_task_response['lines'] == ['central']

def test_delete_task():
    now = datetime.datetime.now()
    add_task_response = test_controller.add_task(now, ['central'])
    id = add_task_response['task_id']
    test_controller.delete_task(id)
    assert test_controller.get_task(id) == {'Message': 'No task with id '+id}

def test_get_task():
    now = datetime.datetime.now()
    add_task_response = test_controller.add_task(now, ['central'])
    id = add_task_response['task_id']
    assert test_controller.get_task(id)['task_details']['lines'][0][0] == 'central'

def test_edit_task():
    now = datetime.datetime.now()
    add_task_response = test_controller.add_task(now, ['central'])
    id = add_task_response['task_id']
    assert test_controller.edit_task(id, now, ['piccadilly'])['lines'][0][0] == 'piccadilly'

if __name__ == '__main__':
    test_controller = controller()
    test_add_task()
    test_delete_task()
    test_get_task()
