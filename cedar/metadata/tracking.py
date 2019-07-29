""" Classes and other core tools for tracking & image metadata
"""
from collections import Mapping, defaultdict
import datetime as dt
import json
from pathlib import Path

import numpy as np

from .core import get_task_metadata
from .. import validation


_HERE = Path(__file__).resolve().parent
SCHEMA_TRACKING = _HERE.joinpath('schema_tracking.json')
SCHEMA_IMAGE = _HERE.joinpath('schema_image.json')


class TrackingMetadata(Mapping):
    """ CEDAR order tracking metadata

    Parameters
    ----------
    metadata : dict
        Tracking metadata information as a dict
    schema : dict, optional
        Validate metadata against a specific schema
    """
    def __init__(self, metadata, schema=None):
        self._metadata = metadata
        self.schema = schema or self._load_schema()
        self.validate()

    @classmethod
    def from_file(cls, filename, schema=None):
        """ Create from a tracking metadata file
        """
        with open(filename) as src:
            metadata = json.load(src)
        return cls(metadata, schema=schema)

    @classmethod
    def from_json(cls, json_str, schema=None):
        """ Load tracking metadata from a JSON string
        """
        metadata = json.loads(json_str)
        return cls(metadata, schema=schema)

    # Mapping object requirements
    def __getitem__(self, key):
        return self._metadata[key]

    def __len__(self):
        return len(self._metadata)

    def __iter__(self):
        return iter(self._metadata)

    # Main sections -- make them available as attributes
    @property
    def program(self):
        return self['program']

    @property
    def submission(self):
        return self['submission']

    @property
    def tracking(self):
        return self['tracking']

    @property
    def orders(self):
        return self['orders']

    @property
    def metadata(self):
        return self['metadata']

    @property
    def states(self):
        """ dict: Summary of EE task status for this order
        """
        return summarize_states(self.orders)

    @property
    def progress(self):
        """ float: Percent of EE tasks completed in this order
        """
        states = self.states
        n = sum(states.values())
        n_completed = states.get(_EE_COMPLETED, 0)
        return n_completed / n if n_completed else 0.

    @property
    def complete(self):
        """ bool: True if all orders have completed
        """
        return list(self.states) == [_EE_COMPLETED]

    @property
    def tasks(self):
        """ List[ee.batch.Task]: EarthEngine tasks associated with this order
        """
        from ..utils import get_ee_tasks, load_ee
        ee_api = load_ee(False)  # should initialize elsewhere
        tasks = get_ee_tasks()
        order_tasks = [tasks[order['status']['id']] for order in self.orders]
        return order_tasks

    def update(self):
        """ Update the tracking metadata by checking EE task status

        Returns
        -------
        self
            Returns a new instance of this TrackingMetadata with updated info
        """
        updated = []
        for task, order in zip(self.tasks, self.orders):
            order_ = order.copy()
            task_info = get_task_metadata(task)
            order.update(task_info)
            updated.append(order)

        data = dict(self)
        data['orders'] = updated

        return self.__class__(data)

    # schema
    def validate(self):
        validation.validate_with_defaults(self._metadata, self.schema,
                                          resolve=SCHEMA_TRACKING.parent)

    @staticmethod
    def _load_schema(filename=SCHEMA_TRACKING):
        with open(str(filename)) as src:
            return json.load(src)

    # repr, printing, etc info
    def __repr__(self):
        return repr_tracking(self)

    def _repr_html_(self):
        # TODO
        return "CEDAR Tracking Metadata"


# -----------------------------------------------------------------------------
# String repr
def repr_tracking(tracking_data,
                  show_program=True, show_submission=True, show_tracking=True,
                  show_states=True, show_runtimes=True,
                  show_orders=None):
    """ Return string formatted information about CEDAR tracking metadata
    """
    lines = []

    if show_program:
        lines.extend(repr_metadata_program(tracking_data['program']))
    if show_submission:
        lines.extend(repr_tracking_submission(tracking_data['submission']))
    if show_tracking:
        lines.extend(repr_tracking_tracking(tracking_data['tracking']))

    # Top level order information is always added
    lines.extend(repr_tracking_orders(tracking_data['orders'],
                                      show_states=show_states,
                                      show_runtimes=show_runtimes))

    if show_orders is not None:
        # Handle 'True', which is shortcut to showing all order details
        if show_orders is True:
            show_orders = range(len(tracking_data['orders']))

        # Otherwise expect sequence of order indexes (1st, 2nd, etc)
        for order_id in show_orders:
            order_md = tracking_data['orders'][order_id]
            order_repr = repr_metadata_order(order_md, f'Order #{order_id}')
            lines.extend(order_repr)

    return '\n'.join(lines)


def repr_metadata_program(info, header='Program Info:'):
    lines = _indent([
        f'* {info["name"]}={info["version"]}',
        f'* earthengine-api={info["ee"]}'
    ], n=1)
    return [header] + lines


def repr_tracking_submission(info, header='Submission Info:'):
    tile_indices = [f'({i[0]}, {i[1]})' for i in info['tile_indices']]

    # Format subsection first so it can be added as a string
    period_info_str = ['* Period:'] + _indent([
        f'* Start: {info["period_start"]}',
        f'* End:   {info["period_end"]}',
        f'* Freq:  {info["period_freq"]}'
    ], n=2)

    lines = _indent([
        f'* Submitted on {info["submitted"]}',
        f'* Tile Grid: "{info["tile_grid"]["name"]}"',
        f'* Tile Indices : {", ".join(tile_indices)}',
        '\n'.join(period_info_str)
    ])
    return [header] + lines


def repr_tracking_tracking(info, header='Tracking Info'):
    lines = _indent([
        f'* Name: {info["name"]}',
        f'* Prefix: {info["prefix"]}',
        f'* Collections: {", ".join(info["collections"])}',
        f'* Image template: {info["name_template"]}',
        f'* Image prefix: {info["prefix_template"]}'
    ], n=1)
    return [header] + lines


def repr_tracking_orders(info, show_states=True, show_runtimes=True,
                         header='Orders'):
    lines = [f'* Count: {len(info)}']
    if show_states:
        states = summarize_states(info)
        lines_ = [f'- {state}: {n}' for state, n in states.items()]
        lines.append('* States:')
        lines.extend(_indent(lines_, n=1))

    if show_runtimes:
        runtimes = summarize_runtimes(info)
        mean = _format_runtime(runtimes['mean'])
        std = _format_runtime(runtimes['std'])
        line = f'* Runtime: {mean} +/- {std} minutes'
        lines.append(line)

    return [header] + _indent(lines)


def repr_metadata_order(info, header='Order:'):
    summary = _summarize_order(info)
    s_runtime = _format_runtime(summary['runtime'])
    lines = _indent([
        f'- Name: {summary["name"]}',
        f'- Prefix: {summary["prefix"]}',
        f'- ID: {summary["id"]}',
        f'- Task state: {summary["state"]}',
        f'- Runtime: {s_runtime} minutes',
        f'- Image pieces: {summary["n_images"]}',
        f'- Output URL: {summary["output_url"]}',
    ], n=1)
    return [header] + lines


# -----------------------------------------------------------------------------
# Calculations
def calculate_order_runtime(start_time, update_time, nan=np.nan):
    if start_time and update_time:
        return update_time - start_time
    elif start_time:
        now = dt.datetime.now().timestamp()
        return now - start_time
    else:
        return nan


def summarize_states(orders):
    """ Returns tallies of order task status
    """
    order_states = defaultdict(lambda: 0)
    for order in orders:
        order_states[order['status']['state']] += 1
    return dict(order_states)


def summarize_runtimes(orders):
    """ Summarize runtimes of order tasks
    """
    runtimes = []
    for order in orders:
        runtime = calculate_order_runtime(
            order['status']['start_timestamp_ms'],
            order['status']['update_timestamp_ms'])
        runtimes.append(runtime)

    runtimes = np.asarray(runtimes)
    mask = np.isfinite(runtimes)
    any_ = mask.any()

    return {
        'runtimes': runtimes,
        'total': np.sum(runtimes[mask]) if any_ else np.nan,
        'n': runtimes.size,
        'mean': np.mean(runtimes[mask]) if any_ else np.nan,
        'std': np.std(runtimes[mask]) if any_ else np.nan
    }


def _summarize_order(order):
    summary = {k: order[k] for k in ('name', 'prefix', )}
    summary['id'] = order['status']['id']
    summary['state'] = order['status']['state']
    summary['runtime'] = calculate_order_runtime(
        order['status']['start_timestamp_ms'],
        order['status']['update_timestamp_ms'])
    summary['n_images'] = len(order['status']['output_url'])
    summary['output_url'] = list(set(order['status']['output_url']))

    return summary


# Helpers
def _indent(lines, n=1, length=4):
    return [' ' * n * length + line for line in lines]


def _format_runtime(time_ms):
    if time_ms:
        return '{0:02.2f}'.format(time_ms / 60. / 1000.)
    else:
        return 'nan'


_EE_UNSUBMITTED = 'UNSUBMITTED'
_EE_READY = 'READY'
_EE_RUNNING = 'RUNNING'
_EE_COMPLETED = 'COMPLETED'
_EE_FAILED = 'FAILED'
_EE_CANCEL_REQUESTED = 'CANCEL_REQUESTED'
_EE_CANCELLED = 'CANCELLED'
