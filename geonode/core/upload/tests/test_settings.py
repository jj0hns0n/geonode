'''Just a convenience to allow running the tests without a full postgres setup'''
try:
    from geonode.core.upload.tests.local_settings import *
except ImportError:
    pass
