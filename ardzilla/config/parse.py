""" Parse and validate a configuration file
"""
import json
import os
from pathlib import Path

from jsonschema import Draft7Validator, validators


DEFAULT_SCHEMA_FILENAME = 'schema.json'
DEFAULT_SCHEMA_FILE = os.path.join(os.path.dirname(__file__),
                                   DEFAULT_SCHEMA_FILENAME)


def validate_with_defaults(obj, schema=None):
    """ Validate a configuration file and fill in defaults (modifies ``obj``)
    """
    if schema is None:
        schema = get_default_schema()
    validator = DefaultValidatingDraft7Validator(schema)
    validator.validate(obj)


_DEFAULT_SCHEMA = None
def get_default_schema():
    # skip reloading from disk after first time
    global _DEFAULT_SCHEMA
    if _DEFAULT_SCHEMA is None:
        with open(DEFAULT_SCHEMA_FILE) as f:
            _DEFAULT_SCHEMA = json.load(f)
    return _DEFAULT_SCHEMA.copy()


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
