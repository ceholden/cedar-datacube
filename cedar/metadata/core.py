
import datetime as dt
import time

import pprint

# Input: JSON file


###############################################################
# Dummy functions which does not work right now
def get_tracking_file(tracking_id):
    # #TODO: make this function return a dictionary representing the tracking file
    return {}


# cedar status list
def list_submissions(data):
    # #TODO: how to get all the submissions?
    submissions = []
    submission_names = []
    for submission in submissions:
        submission_names.append(get_tracking_file(submission)['tracking']['name'])
    return submission_names


# cedar status update <tracking_id>
def update_order(data, tracking_id):
    # # TODO: update the status of a submission with given tracking_id
    update_notice = f'Updated status of submission: {tracking_id}'
    return [update_notice]

###############################################################


# Getter functions getting information from a dictionary.
def get_status_program_info(data):
    return data['program']


def get_status_submission_info(data):
    # Obtain Submission Information from a tracking_data
    return data['submission']


def get_status_orders_info(data):
    # Obtain a list of orders made in the submission
    return data['orders']


# Helper functions

def get_order_statistics(orders_info):
    orders_stats = dict()

    orders_stats['order_amount'] = len(orders_info)
    completed = 0
    unsubmitted = 0
    runtime_list = []
    active = 0
    for order in orders_info:
        print(order)
        if order['status']['state'] == 'COMPLETED':
            completed += 1
        elif order['status']['state'] == 'UNSUBMITTED':
            runtime = check_runtime(order)
            if runtime != -1:
                runtime_list.append(runtime)
            unsubmitted += 1
        else:
            runtime = check_runtime(order)
            if runtime != -1:
                runtime_list.append(runtime)
            active += 1
    orders_stats['completed_amount'] = completed
    orders_stats['unsubmitted_amount'] = unsubmitted
    orders_stats['active_amount'] = active
    if len(runtime_list) != 0:
        orders_stats['avg_runtime'] = sum(runtime_list) / len(runtime_list)
    orders_stats['avg_runtime'] = -1
    return orders_stats


def check_runtime(order):
    start_time = order['status']['start_timestamp_ms']
    update_time = order['status']['update_timestamp_ms']
    now_timestamp = int(round(time.time()))
    if start_time != '' and update_time != '':
        runtime = (update_time - start_time)
    elif start_time != '' and update_time == '':
        runtime = (now_timestamp - start_time)
    else:
        runtime = -1
    return runtime


def convert_datetime_to_print(datetime_string):
    timestamp = 'NaN'
    if not (datetime_string == 0 or datetime_string is ''):
        timestamp = dt.datetime.fromisoformat(datetime_string).strftime('%Y-%m-%d %H:%M:%S')
    return timestamp


def print_selected_tiles(submission_info):
    selected_tiles = submission_info['tile_indices']
    output_str = ''
    for i in range(len(selected_tiles)):
        if i != len(selected_tiles) - 1:
            output_str += f'    * {i + 1}: {selected_tiles[i][0]}, {selected_tiles[i][1]}\n'
        else:
            output_str += f'    * {i + 1}: {selected_tiles[i][0]}, {selected_tiles[i][1]}'
    return output_str


def output_url_set(orders_info):
    output_url = set()
    for order in orders_info:
        output_url.update(order['status']['output_url'])
    return list(output_url)
##


# cli printing implementations

# cedar status info --program
def info_program(program_info):
    info = f'Ordered with {program_info["name"]} = {program_info["version"]} and Earth Engine = {program_info["ee"]}'
    output = [info]
    return output


# cedar status info --submission
def info_submission(submission_info):
    submission_date = f'Submitted on {convert_datetime_to_print(submission_info["submitted"])}'
    name = f'Tile Name: {submission_info["tile_grid"]["name"]}'
    tile_range = f'Tile Indices:\n{print_selected_tiles(submission_info)}'
    start = f'Start Period: {submission_info["period_start"]}'
    end = f'End Period: {submission_info["period_end"]}'
    freq = f'Period Frequency: {submission_info["period_freq"]}'
    output = [submission_date, name, tile_range, start, end, freq]
    return output


# cedar status info --orders
def info_orders(orders_info):
    orders_stats = get_order_statistics(orders_info)
    total = f'Total Orders: {orders_stats["order_amount"]}'
    process = f'    Active: {orders_stats["active_amount"]}'
    process += f'\n    Unsubmitted: {orders_stats["unsubmitted_amount"]}'
    process += f'\n    Complete: {orders_stats["completed_amount"]}'
    output = [total, process]
    return output


def info_orders_specific(orders_info):
    orders_stats = get_order_statistics(orders_info)
    order_output = []
    avg_runtime = orders_stats['avg_runtime']
    if avg_runtime != -1:
        avg_runtime_out = f'Average Runtime: {avg_runtime} ms'
    else:
        avg_runtime_out = f'Average Runtime: NaN'
    output_urls = f'Output URLs: {output_url_set(orders_info)}'
    for count in range(1, orders_stats['order_amount']+1):
        order_output += info_order(orders_info, count)
    return [avg_runtime_out, output_urls] + order_output


def info_order(orders_info, order_indice):
    orders_stats = get_order_statistics(orders_info)
    if orders_stats['order_amount'] < order_indice or 0 >= order_indice:
        error_msg = 'Index out of range: Please enter a valid indice'
        return [error_msg]
    order = orders_info[order_indice-1]
    order_name = f'Order Name: {order["name"]}'
    order_id = f'    * ID: {order["status"]["id"]}'
    order_state = f'    * State: {order["status"]["state"]}'

    creation_time = order["status"]["creation_timestamp_ms"]
    start_time = order["status"]["start_timestamp_ms"]
    last_update_time = order["status"]["update_timestamp_ms"]

    creation_timestamp = convert_datetime_to_print(creation_time)
    start_timestamp = convert_datetime_to_print(start_time)
    last_update_timestamp = convert_datetime_to_print(last_update_time)

    order_created = f'    * Created: {creation_timestamp}'
    order_start = f'    * Started: {start_timestamp}'
    order_last_update = f'    * Last Updated: {last_update_timestamp}'
    output = [order_name, order_id, order_state, order_created, order_start, order_last_update]
    return output


# # cedar status info <tracking_id> --program --submission --orders --order <order_indices>
def info_status(tracking_data, show_program_info=True, show_submission_info=True, show_orders_info=True,
                show_order_specific=True, show_order=True, order_indice=3):
    """
    A function for cli command, 'cedar status info ...'

    Parameters
    ----------
    tracking_data : dict
        Required argument which specifies which tracking file information to be displayed
    show_program_info : bool, optional
        Optional argument with default value of True. Specified by the '--program' flag in CLI.
        Displays program information.
    show_submission_info : bool, optional
        Optional argument with default value of True. Specified by the '--submission' flag in CLI.
        Displays submission information.
    show_orders_info : bool, optional
        Optional argument with default value of True. Specified by the '--program' flag in CLI.
        Displays status of orders in a submission
    show_order_specific : bool, optional
        Optional argument with default value of False. Specified by the '--program' flag in CLI.
        Displays specific information about individual orders in a submission.
    show_order : bool, optional
        Optional argument with default value of False. Specified by the '--order <order_indice>' flag in CLI.
        order_indice must be specified when this flag is raised.
        Shows specific information on a single order specified
    order_indice : int, optional
        Optional argument with default value of -1. Specified by the '--program' flag in CLI.
        Used as an argument for show_order flag to specify which order to be displayed

    Returns
    -------
    output : list
        Outputs a list of strings. Each element in the list represents a line in CLI.
    """
    output = []
    if show_program_info:
        program_info = get_status_program_info(tracking_data)
        output += info_program(program_info)
    if show_submission_info:
        submission_info = get_status_submission_info(tracking_data)
        output += info_submission(submission_info)
    orders_info = get_status_orders_info(tracking_data)
    if show_orders_info or show_order_specific:
        output += info_orders(orders_info)
        if show_order_specific:
            output += info_orders_specific(orders_info)
    if show_order and order_indice != -1:
        output += info_order(orders_info, order_indice)
    return output


# Output: List of strings that should be outputted


if __name__ == '__main__':
    pass
