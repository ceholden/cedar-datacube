""" Classes and other core tools for tracking & image metadata
"""
from collections import Mapping, defaultdict
import datetime as dt
import json
import os

import numpy as np


_HERE = os.path.abspath(os.path.dirname(__file__))
SCHEMA_TRACKING = os.path.join(_HERE, 'schema_tracking.json')
SCHEMA_IMAGE = os.path.join(_HERE, 'schema_image.json')


class TrackingMetadata(Mapping):

    def __init__(self, metadata, schema=None):
        self._metadata = metadata
        self.schema = schema
        # TODO -- validate

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

    # repr, printing, etc info
    def __repr__(self):
        return repr_tracking(self)

    def __html_repr__(self):
        # TODO
        return "CEDAR Tracking Metadata"


def repr_metadata_program(info):
    lines = [
        f'* {info["name"]}={info["version"]}',
        f'* earthengine-api={info["ee"]}'
    ]
    return wrapping_indent(lines, 'Program Info:')


def repr_tracking_submission(info):
    tile_indices = [f'({i[0]}, {i[1]})' for i in info['tile_indices']]

    period_info = [
        f'* Start: {info["period_start"]}',
        f'* End:   {info["period_end"]}',
        f'* Freq:  {info["period_freq"]}'
    ]
    period_info_str = wrapping_indent(period_info, '* Period: ', 8)

    lines = [
        f'* Submitted on {info["submitted"]}',
        f'* Tile Grid: "{info["tile_grid"]["name"]}"',
        f'* Tile Indices : {", ".join(tile_indices)}',
        period_info_str
    ]
    return wrapping_indent(lines, 'Submission Info:')


def repr_tracking_tracking(info):
    lines = [
        f'* Name: {info["name"]}',
        f'* Prefix: {info["prefix"]}',
        f'* Collections: {", ".join(info["collections"])}',
        f'* Image template: {info["name_template"]}',
        f'* Image prefix: {info["prefix_template"]}'
    ]
    return wrapping_indent(lines, 'Tracking Info:')


def repr_tracking_orders(info, show_states=True, show_runtimes=True):
    summary = summarize_orders(info)

    lines = [f'* Count: {len(info)}']
    if show_states:
        lines_ = [f'- {state}: {n}' for state, n in summary['states'].items()]
        lines.extend(wrapping_indent(lines_, '* States:').splitlines())

    if show_runtimes:
        s_mean, s_std = [_format_runtime(summary['runtimes'][k])
                         for k in ('mean', 'std', )]
        line = f'* Runtime: {s_mean} +/- {s_std} minutes'
        lines.append(line)

    return wrapping_indent(lines, 'Orders:')


def repr_metadata_order(info, header='Order:'):
    summary = summarize_order(info)
    s_runtime = _format_runtime(summary['runtime'])
    lines = [
        f'- Name: {summary["name"]}',
        f'- Prefix: {summary["prefix"]}',
        f'- ID: {summary["id"]}',
        f'- Task state: {summary["state"]}',
        f'- Runtime: {s_runtime} minutes',
        f'- Output URL: {summary["output_url"]}',
    ]
    return wrapping_indent(lines, header)


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


# =============================================================================
def calculate_order_runtime(start_time, update_time, nan=None):
    if start_time and update_time:
        return update_time - start_time
    elif start_time:
        now = dt.datetime.now().timestamp()
        return now - start_time
    else:
        return nan


def summarize_order(order):
    summary = {k: order[k] for k in ('name', 'prefix', )}
    summary['id'] = order['status']['id']
    summary['state'] = order['status']['state']
    summary['runtime'] = calculate_order_runtime(
        order['status']['start_timestamp_ms'],
        order['status']['update_timestamp_ms'])
    summary['output_url'] = list(set(order['status']['output_url']))

    return summary


def summarize_orders(orders):
    """ Return summaries and stats (counts by state & runtimes) of all orders
    """
    summaries = [summarize_order(o) for o in orders]

    order_states = defaultdict(lambda: 0)
    for summary in summaries:
        order_states[summary['state']] += 1
    order_states = dict(order_states)

    runtimes = np.asarray([
        summary['runtime'] for summary in summaries
        if summary['runtime'] is not None
    ])

    return {
        'summaries': summaries,
        'states': order_states,
        'runtimes': {
            'total': runtimes.sum(),
            'n': runtimes.size,
            'mean': np.mean(runtimes) if runtimes.size else np.nan,
            'std': np.std(runtimes) if runtimes.size else np.nan
        }
    }


def wrapping_indent(lines, heading='', length=4):
    indent = '\n' + ' ' * length
    if heading:
        lines = [heading] + lines
    return indent.join(lines)



def _format_runtime(time_ms):
    if time_ms:
        return '{0:02.2f}'.format(time_ms / 60. / 1000.)
    else:
        return 'nan'
