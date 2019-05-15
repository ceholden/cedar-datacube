""" Sensor specific ARD submission tools
"""
from . import landsat


#: dict: Mapping of GEE collection to ARD creating function
CREATE_ARD_COLLECTION = {}
CREATE_ARD_COLLECTION.update({
    k: landsat.create_ard for k in landsat.METADATA.keys()
})
