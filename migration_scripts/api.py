from flask import Flask, request
from flask_executor import Executor
from helpers import IntListConverter, create_lookup_dictionary
from helpers import ListConverter
from flask_basicauth import BasicAuth
from dotenv import load_dotenv
import os
import logging
import excursions
import programs_nellie
import voyages
import ships
import publish_imported_assets

load_dotenv()

logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)

app = Flask(__name__)
app.debug = True
app.config["BASIC_AUTH_USERNAME"] = os.environ["SYNC_BASIC_AUTH_USER"]
app.config["BASIC_AUTH_PASSWORD"] = os.environ["SYNC_BASIC_AUTH_PASSWORD"]
app.config["EXECUTOR_TYPE"] = "thread"
app.config["EXECUTOR_MAX_WORKERS"] = 1
app.config["BASIC_AUTH_FORCE"] = True

app.url_map.converters["int_list"] = IntListConverter
app.url_map.converters["list"] = ListConverter


basic_auth = BasicAuth(app)

@app.route("/sync/programs/")
@app.route("/sync/programs")
def sync_programs():
    return start_task_executor_if_available(programs_nellie.run_sync)

@app.route("/sync/programs/<int_list:program_ids>/")
@app.route("/sync/programs/<int_list:program_ids>")
def sync_program_with_program_ids(program_ids):
    return start_task_executor_if_available(
        programs_nellie.run_sync, {"content_ids": program_ids, "include": True}
    )


@app.route("/sync/excursions/")
@app.route("/sync/excursions")
def sync_excursions():
    return start_task_executor_if_available(excursions.run_sync)


@app.route("/sync/excursions/<int_list:excursion_ids>/")
@app.route("/sync/excursions/<int_list:excursion_ids>")
def sync_excursion_with_excursion_ids(excursion_ids):
    return start_task_executor_if_available(
        excursions.run_sync, {"content_ids": excursion_ids, "include": True}
    )


@app.route("/sync/excursions/skip/<int_list:excursion_ids>/")
@app.route("/sync/excursions/skip/<int_list:excursion_ids>")
def sync_excursion_skip_excursion_ids(excursion_ids):
    return start_task_executor_if_available(
        excursions.run_sync, {"content_ids": excursion_ids, "include": False}
    )


@app.route("/sync/voyages/")
@app.route("/sync/voyages")
def sync_voyages():
    market = request.args.get("market")
    return start_task_executor_if_available(voyages.run_sync, {"market": market})


@app.route("/sync/voyages/<int_list:voyage_ids>/")
@app.route("/sync/voyages/<int_list:voyage_ids>")
def sync_voyages_with_voyage_ids(voyage_ids):
    market = request.args.get("market")
    return start_task_executor_if_available(
        voyages.run_sync, {"content_ids": voyage_ids, "include": True, "market": market}
    )


@app.route("/sync/voyages/skip/<int_list:voyage_ids>/")
@app.route("/sync/voyages/skip/<int_list:voyage_ids>")
def sync_voyages_skip_voyage_ids(voyage_ids):
    return start_task_executor_if_available(
        voyages.run_sync, {"content_ids": voyage_ids, "include": False}
    )


@app.route("/sync/ships/")
@app.route("/sync/ships")
def sync_ships():
    return start_task_executor_if_available(ships.run_sync)


@app.route("/sync/ships/<list:ship_ids>/")
@app.route("/sync/ships/<list:ship_ids>")
def sync_ships_with_ship_ids(ship_ids):
    return start_task_executor_if_available(
        ships.run_sync, {"content_ids": ship_ids, "include": True}
    )


@app.route("/sync/ships/skip/<list:ship_ids>/")
@app.route("/sync/ships/skip/<list:ship_ids>")
def sync_ships_skip_ship_ids(ship_ids):
    return start_task_executor_if_available(
        ships.run_sync, {"content_ids": ship_ids, "include": False}
    )


@app.route("/sync/all/")
@app.route("/sync/all")
def sync_all():
    global running_tasks
    if running_tasks == 0:
        running_tasks += 3
        logging.info("Running tasks: %s" % running_tasks)
        executor.submit(excursions.run_sync)
        executor.submit(voyages.run_sync)
        executor.submit(ships.run_sync)
        return "Sync started for all excursions, voyages and ships."
    else:
        return "There's a running process, please wait until finished..."


@app.route("/publish/<list:asset_type>/")
@app.route("/publish/<list:asset_type>")
def publish_asset_type(asset_type):
    return start_task_executor_if_available(
        publish_imported_assets.run_publish,
        {"content_ids": asset_type, "include": True},
    )


@app.route("/publish/all/")
@app.route("/publish/all")
def publish_all():
    return start_task_executor_if_available(publish_imported_assets.run_publish)


@app.route("/sync-and-publish/all/")
@app.route("/sync-and-publish/all")
def sync_and_publish_all():
    global running_tasks
    if running_tasks == 0:
        running_tasks += 4
        logging.info("Running tasks: %s" % running_tasks)
        executor.submit(excursions.run_sync)
        executor.submit(voyages.run_sync)
        executor.submit(ships.run_sync)
        executor.submit(publish_imported_assets.run_publish)
        return "Sync and asset publish started for all excursions, voyages and ships."
    else:
        return "There's a running process, please wait until finished..."


def start_task_executor_if_available(*task_and_parameters):
    global running_tasks
    create_lookup_dictionary()
    if running_tasks == 0:
        running_tasks += 1
        logging.info("Running tasks: %s" % running_tasks)
        try:
            task, parameters = task_and_parameters
            executor.submit(task, **parameters)
            if parameters.get("include"):
                return "Sync or publish started for %s" % parameters["content_ids"]
            else:
                return (
                    "Sync or publish started, skipping %s" % parameters["content_ids"]
                )
        except:
            task = task_and_parameters[0]
            executor.submit(task)
            return "Sync or publish started for all content ids."
    else:
        return "There's a running process, please wait until finished..."


def executor_callback(future):
    global running_tasks
    running_tasks -= 1
    logging.info("Task finished with results: %s" % future.result())
    logging.info("Running tasks: %s" % running_tasks)
    logging.info("")
    logging.info("---------------------------------------------------------------")
    logging.info("")


executor = Executor()
executor.init_app(app)
executor.add_default_done_callback(executor_callback)

running_tasks = 0

if __name__ == "__main__":
    app.run(host=os.environ["SYNC_HOST"])
    app.run(debug=os.environ["SYNC_DEBUG"])
