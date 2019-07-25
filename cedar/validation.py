""" JSON Schema validation helpers
"""
import json
import os
from pathlib import Path

from jsonschema import Draft7Validator, RefResolver, validators


def validate_with_defaults(obj, schema, resolve=None):
    """ Validate a configuration file and fill in defaults (modifies ``obj``)
    """
    if resolve:
        resolver = RefResolver('file://' + str(resolve) + '/', schema)
    else:
        resolver = None

    # Allow tuple/list as 'array' type
    # See: https://github.com/Julian/jsonschema/issues/148
    types_ = {'array': (list, tuple)}

    validator = DefaultValidatingDraft7Validator(schema, resolver=resolver,
                                                 types=types_)
    validator.validate(obj)


# Adapted from python-jsonschema FAQ
# https://python-jsonschema.readthedocs.io/en/stable/faq/
def _extend_with_default(validator_class):
    validate_properties = validator_class.VALIDATORS["properties"]

    def set_defaults(validator, properties, instance, schema):
        for property, subschema in properties.items():
            if "default" in subschema:
                instance.setdefault(property, subschema["default"])

        for error in validate_properties(
                validator, properties, instance, schema):
            yield error

    return validators.extend(validator_class, {"properties" : set_defaults})


DefaultValidatingDraft7Validator = _extend_with_default(Draft7Validator)
