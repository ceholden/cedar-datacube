""" Classes and other core tools for tracking & image metadata
"""
from collections import Mapping, defaultdict
import datetime as dt
import json
from pathlib import Path

import numpy as np

from .. import validation


_HERE = Path(__file__).resolve().parent
SCHEMA_TRACKING = _HERE.joinpath('schema_tracking.json')
SCHEMA_IMAGE = _HERE.joinpath('schema_image.json')


class TrackingMetadata(Mapping):
    """ CEDAR order tracking metadata
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


def repr_tracking(tracking_data,
                  show_program=True, show_submission=True, show_tracking=True,
                  show_states=True, show_runtimes=True,
                  show_orders=None):
    """ Return string formatted information about CEDAR tracking metadata
    """
    lines = []

    if show_program:
        lines.append(repr_metadata_program(tracking_data['program']))
    if show_submission:
        lines.append(repr_tracking_submission(tracking_data['submission']))
    if show_tracking:
        lines.append(repr_tracking_tracking(tracking_data['tracking']))

    # Top level order information is always added
    lines.append(repr_tracking_orders(tracking_data['orders'],
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
            lines.append(order_repr)

    return '\n'.join(lines)


def repr_metadata_program(info):
    lines = [
        f'* {info["name"]}={info["version"]}',
        f'* earthengine-api={info["ee"]}'
    ]
    return _heading_indent(lines, 'Program Info:')


def repr_tracking_submission(info):
    tile_indices = [f'({i[0]}, {i[1]})' for i in info['tile_indices']]

    period_info = [
        f'* Start: {info["period_start"]}',
        f'* End:   {info["period_end"]}',
        f'* Freq:  {info["period_freq"]}'
    ]
    period_info_str = _heading_indent(period_info, '* Period: ', 8)

    lines = [
        f'* Submitted on {info["submitted"]}',
        f'* Tile Grid: "{info["tile_grid"]["name"]}"',
        f'* Tile Indices : {", ".join(tile_indices)}',
        period_info_str
    ]
    return _heading_indent(lines, 'Submission Info:')


def repr_tracking_tracking(info):
    lines = [
        f'* Name: {info["name"]}',
        f'* Prefix: {info["prefix"]}',
        f'* Collections: {", ".join(info["collections"])}',
        f'* Image template: {info["name_template"]}',
        f'* Image prefix: {info["prefix_template"]}'
    ]
    return _heading_indent(lines, 'Tracking Info:')


def repr_tracking_orders(info, show_states=True, show_runtimes=True):
    lines = [f'* Count: {len(info)}']
    if show_states:
        states = summarize_states(info)
        lines_ = [f'- {state}: {n}' for state, n in states.items()]
        lines.extend(_heading_indent(lines_, '* States:').splitlines())

    if show_runtimes:
        runtimes = summarize_runtimes(info)
        mean = _format_runtime(runtimes['mean'])
        std = _format_runtime(runtimes['std'])
        line = f'* Runtime: {mean} +/- {std} minutes'
        lines.append(line)

    return _heading_indent(lines, 'Orders:')


def repr_metadata_order(info, header='Order:'):
    summary = _summarize_order(info)
    s_runtime = _format_runtime(summary['runtime'])
    lines = [
        f'- Name: {summary["name"]}',
        f'- Prefix: {summary["prefix"]}',
        f'- ID: {summary["id"]}',
        f'- Task state: {summary["state"]}',
        f'- Runtime: {s_runtime} minutes',
        f'- Output URL: {summary["output_url"]}',
    ]
    return _heading_indent(lines, header)


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

    return {
        'runtimes': runtimes,
        'total': np.nansum(runtimes),
        'n': np.isfinite(runtimes).sum(),
        'mean': np.nanmean(runtimes) if runtimes.size else np.nan,
        'std': np.nanstd(runtimes) if runtimes.size else np.nan
    }


def _summarize_order(order):
    summary = {k: order[k] for k in ('name', 'prefix', )}
    summary['id'] = order['status']['id']
    summary['state'] = order['status']['state']
    summary['runtime'] = calculate_order_runtime(
        order['status']['start_timestamp_ms'],
        order['status']['update_timestamp_ms'])
    summary['output_url'] = list(set(order['status']['output_url']))

    return summary


def _heading_indent(lines, heading='', length=4):
    indent = '\n' + ' ' * length
    if heading:
        lines = [heading] + lines
    return indent.join(lines)



def _format_runtime(time_ms):
    if time_ms:
        return '{0:02.2f}'.format(time_ms / 60. / 1000.)
    else:
        return 'nan'
