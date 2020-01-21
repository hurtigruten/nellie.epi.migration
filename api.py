from flask import Flask
from flask_executor import Executor
from helpers import IntListConverter
import excursions
import logging

logging.basicConfig(
    format = '%(asctime)s %(levelname)-8s %(message)s',
    level = logging.INFO,
    datefmt = '%Y-%m-%d %H:%M:%S')

app = Flask(__name__)
app.url_map.converters['int_list'] = IntListConverter
app.config['EXECUTOR_TYPE'] = 'thread'
app.config['EXECUTOR_MAX_WORKERS'] = 1


@app.route('/sync/excursions/')
@app.route('/sync/excursions')
def sync_excursions():
    return start_task_executor_if_available([excursions.run_sync])


@app.route('/sync/excursions/<int_list:excursion_ids>')
@app.route('/sync/excursions/<int_list:excursion_ids>/')
def sync_excursion_list(excursion_ids):
    return start_task_executor_if_available([excursions.run_sync, excursion_ids])


def start_task_executor_if_available(*task_and_parameters):
    global running_tasks
    for task_and_parameter in task_and_parameters:
        if running_tasks == 0:
            running_tasks += 1
            logging.info('Running tasks: %s' % running_tasks)
            try:
                task, parameters = task_and_parameter
                logging.info(task_and_parameter)
                logging.info(task)
                executor.submit(task, parameters)
                return 'Sync started for %s' % parameters
            except:
                task = task_and_parameter[0]
                logging.info(task)
                executor.submit(task)
                return 'Sync started for all content ids.'
        else:
            return 'There\'s a running process, please wait until finished...'


def executor_callback(future):
    global running_tasks
    running_tasks -= 1
    logging.info('Task finished with results: %s' % future.result())
    logging.info('Running tasks: %s' % running_tasks)
    logging.info('')
    logging.info('---------------------------------------------------------------')
    logging.info('')


executor = Executor()
executor.init_app(app)
executor.add_default_done_callback(executor_callback)

running_tasks = 0

if __name__ == '__main__':
    app.run(debug = True)
