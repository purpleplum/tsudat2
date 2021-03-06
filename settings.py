# -*- coding: utf-8 -*-
# Django settings for GeoNode project.
from urllib import urlencode
import os
import geonode

_ = lambda x: x

DEBUG = True
SITENAME = "TsuDAT"
SITEURL="http://203.77.224.69/"
TEMPLATE_DEBUG = DEBUG

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
GEONODE_ROOT = os.path.dirname(geonode.__file__)

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

DATABASE_ENGINE = 'django.contrib.gis.db.backends.postgis'
DATABASE_NAME = 'tsudat'
DATABASE_USER = 'tsdat'             # Not used with sqlite3.
DATABASE_PASSWORD = 'secret'         # Not used with sqlite3.
DATABASE_HOST = ''             # Not used with sqlite3.
DATABASE_PORT = ''             # Not used with sqlite3.

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Australia/Sydney'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en'

LANGUAGES = (
    ('en', 'English'),
    ('id', 'Bahasa Indonesia'),
)

SITE_ID = 1

# Setting a custom test runner to avoid running the tests for some problematic 3rd party apps
TEST_RUNNER='geonode.testrunner.GeoNodeTestRunner'

NOSE_ARGS = [
      '--verbosity=2',
      '--cover-erase',
      '--nocapture',
      '--with-coverage',
      '--cover-package=geonode',
      '--cover-inclusive',
      '--cover-tests',
      '--detailed-errors',
      '--with-xunit',

# This is very beautiful/usable but requires: pip install rudolf
#      '--with-color',

# The settings below are useful while debugging test failures or errors

#      '--failed',
#      '--pdb-failures',
#      '--stop',
#      '--pdb',
      ]

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True


MEDIA_ROOT = '/var/www/geonode/uploaded'
MEDIA_URL = '/uploaded/'
STATIC_ROOT = '/var/www/geonode/static/'
STATIC_URL = '/static/'
GEONODE_UPLOAD_PATH = MEDIA_ROOT + 'geonode'
GEONODE_CLIENT_LOCATION = STATIC_URL + 'geonode/'
ADMIN_MEDIA_PREFIX = STATIC_URL + 'admin/'

# Additional directories which hold static files
STATICFILES_DIRS = [
    os.path.join(PROJECT_ROOT, "media"),
    os.path.join(GEONODE_ROOT, 'media'),
    '/etc/geonode/media',
]

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'myv-y4#7j-d*p-__@j#*3z@!y24fz8%^z2v6atuy4bo9vqr1_a'

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.contrib.messages.context_processors.messages',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.request',
    # The context processor belows add things like SITEURL
    # and GEOSERVER_BASE_URL to all pages that use a RequestContext
    'geonode.context_processors.resource_urls',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # The setting below makes it possible to serve different languages per
    # user depending on things like headers in HTTP requests.
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)

# This isn't required for running the geonode site, but it when running sites that inherit the geonode.settings module.
LOCALE_PATHS = (
    os.path.join(PROJECT_ROOT, "locale"),
    os.path.join(PROJECT_ROOT, "maps", "locale"),
)

ROOT_URLCONF = 'tsudat2.urls'

# Note that Django automatically includes the "templates" dir in all the
# INSTALLED_APPS, se there is no need to add maps/templates or admin/templates
TEMPLATE_DIRS = (
    os.path.join(PROJECT_ROOT, 'templates'),
    os.path.join(GEONODE_ROOT, 'templates'),
    '/etc/geonode/templates',
)

# The FULLY QUALIFIED url to the GeoServer instance for this GeoNode.
GEOSERVER_BASE_URL = SITEURL + 'geoserver/'

# Default password for the geoserver admin user, autogenerated during bootstrap
GEOSERVER_TOKEN = open('/var/lib/geonode/geoserver_token')

# The username and password for a user that can add and edit layer details on GeoServer
GEOSERVER_CREDENTIALS = "geoserver_admin", GEOSERVER_TOKEN

AUTHENTICATION_BACKENDS = ('geonode.security.auth.GranularBackend',)

# CSW settings
CATALOGUE = {
    'default': {
        # The underlying CSW implementation
        # default is pycsw in local mode (tied directly to GeoNode Django DB)
        'ENGINE': 'geonode.catalogue.backends.pycsw_local',
        # pycsw in non-local mode
        #'ENGINE': 'geonode.catalogue.backends.pycsw',
        # GeoNetwork opensource
        #'ENGINE': 'geonode.catalogue.backends.geonetwork',
        # deegree and others
        #'ENGINE': 'geonode.catalogue.backends.generic',

        # The FULLY QUALIFIED base url to the CSW instance for this GeoNode
        'URL': '%scatalogue/csw' % SITEURL,
        #'URL': 'http://localhost:8080/geonetwork/srv/en/csw',
        #'URL': 'http://localhost:8080/deegree-csw-demo-3.0.4/services',

        # login credentials (for GeoNetwork)
        'USER': 'admin',
        'PASSWORD': 'admin',
    }
}

# pycsw settings
PYCSW = {
    # pycsw configuration
    'CONFIGURATION': {
        'metadata:main': {
            'identification_title': '%s Catalogue' % SITENAME,
            'identification_abstract': 'GeoNode is an open source platform that facilitates the creation, sharing, and collaborative use of geospatial data',
            'identification_keywords': '%s,sdi,catalogue,discovery,metadata,GeoNode' % SITENAME,
            'identification_keywords_type': 'theme',
            'identification_fees': 'None',
            'identification_accessconstraints': 'None',
            'provider_name': 'Organization Name',
            'provider_url': SITEURL,
            'contact_name': 'Lastname, Firstname',
            'contact_position': 'Position Title',
            'contact_address': 'Mailing Address',
            'contact_city': 'City',
            'contact_stateorprovince': 'Administrative Area',
            'contact_postalcode': 'Zip or Postal Code',
            'contact_country': 'Country',
            'contact_phone': '+xx-xxx-xxx-xxxx',
            'contact_fax': '+xx-xxx-xxx-xxxx',
            'contact_email': 'Email Address',
            'contact_url': 'Contact URL',
            'contact_hours': 'Hours of Service',
            'contact_instructions': 'During hours of service. Off on weekends.',
            'contact_role': 'pointOfContact',
        },
        'metadata:inspire': {
            'enabled': 'true',
            'languages_supported': 'eng,gre',
            'default_language': 'eng',
            'date': 'YYYY-MM-DD',
            'gemet_keywords': 'Utility and governmental services',
            'conformity_service': 'notEvaluated',
            'contact_name': 'Organization Name',
            'contact_email': 'Email Address',
            'temp_extent': 'YYYY-MM-DD/YYYY-MM-DD',
        }
    }
}

GOOGLE_API_KEY = ""
LOGIN_REDIRECT_URL = "/"

DEFAULT_LAYERS_OWNER='admin'

# Where should newly created maps be focused?
DEFAULT_MAP_CENTER = (120.509033,-2.350415)

# How tightly zoomed should newly created maps be?
# 0 = entire world;
# maximum zoom is between 12 and 15 (for Google Maps, coverage varies by area)
DEFAULT_MAP_ZOOM = 6


DEFAULT_LAYER_SOURCE = {
    "ptype":"gxp_wmscsource",
    "url":"/geoserver/wms",
    "restUrl": "/gs/rest"
}

MAP_BASELAYERS = [{
    "source": {"ptype": "gx_olsource"},
    "type":"OpenLayers.Layer",
    "args":["No background"],
    "visibility": False,
    "fixed": True,
    "group":"background"
  },{
    "source": { "ptype":"gx_olsource"},
    "type":"OpenLayers.Layer.OSM",
    "args":["OpenStreetMap"],
    "visibility": True,
    "fixed": True,
    "group":"background"
  },{
    "source": {"ptype":"gx_olsource"},
    "type":"OpenLayers.Layer.WMS",
    "group":"background",
    "visibility": False,
    "fixed": True,
    "args":[
      "bluemarble",
      "http://maps.opengeo.org/geowebcache/service/wms",
      {
        "layers":["bluemarble"],
        "format":"image/png",
        "tiled": True,
        "tilesOrigin":[-20037508.34,-20037508.34]
      },
      {"buffer":0}
    ]

}]


"""
MAP_BASELAYERSOURCES = {
    "any": {
        "ptype":"gx_olsource"
    },
    "google":{
        "ptype":"gx_googlesource",
        "apiKey": GOOGLE_API_KEY
    }
}

MAP_BASELAYERS = [{
    "source":"any",
    "type":"OpenLayers.Layer",
    "args":["No background"],
    "visibility": False,
    "fixed": True,
    "group":"background"
  },{
    "source":"any",
    "type":"OpenLayers.Layer.OSM",
    "args":["OpenStreetMap"],
    "visibility": False,
    "fixed": True,
    "group":"background"
  },{
    "source":"any",
    "type":"OpenLayers.Layer.WMS",
    "group":"background",
    "visibility": False,
    "fixed": True,
    "args":[
      "bluemarble",
      "http://maps.opengeo.org/geowebcache/service/wms",
      {
        "layers":["bluemarble"],
        "format":"image/png",
        "tiled": True,
        "tilesOrigin":[-20037508.34,-20037508.34]
      },
      {"buffer":0}
    ]
  },{
    "source":"google",
    "group":"background",
    "name":"ROADMAP",
    "visibility": False,
    "fixed": True,
  },{
    "source":"google",
    "group":"background",
    "name":"TERRAIN",
    "visibility": False,
    "fixed": True,
  },{
    "source":"google",
    "group":"background",
    "name":"SATELLITE",
    "visibility": False,
    "fixed": True,
  },{
    "source":"google",
    "group":"background",
    "name":"HYBRID",
    "visibility": True,
    "fixed": True,
}]
"""


INSTALLED_APPS = (
    # Apps bundled with Django
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.sitemaps',
    'django.contrib.staticfiles',
    'django.contrib.messages',
    'django.contrib.gis',

    # Third party apps
    'django_forms_bootstrap',
    'notification',
    'django_extensions',
    'registration',
    'pagination',
    'profiles',
    'avatar',
    'dialogos',
    'timezones',
    'agon_ratings',
    'taggit',
    'south',

    # GeoNode internal apps
    'geonode.maps',
    'geonode.layers',
    'geonode.people',
    'geonode.proxy',
    'geonode.security',
    'geonode.catalogue',

    # Tsudat Apps
    'tsudat2.tsudat',

    # Message transport
    'djcelery',
    'djkombu', #Only used if BROKER_TRANSPORT='django'
)

TSUDAT_BASE_DIR='/data/run_tsudat/'
#TSUDAT_MUX_DIR='/data/Tsu-DAT_Data/earthquake_data'   # *instance* path to mux data
TSUDAT_MUX_DIR='/var/tsudat/muxfiles'
TSUDAT_DEF_DIR='/var/tsudat/deffiles'


# Celery Settings http://ask.github.com/celery/configuration.html
CELERY_IMPORTS = ("tsudat.tasks", )
CELERY_SEND_TASK_ERROR_EMAILS = True
CELERY_SEND_EVENTS = True
CELERYD_LOG_LEVEL = "DEBUG"
CELERYBEAT_SCHEDULER = "djcelery.schedulers.DatabaseScheduler"
CELERY_RESULT_BACKEND = "database"
CELERY_RESULT_DBURI = "postgresql://tsudat:tsudat@localhost/tsudat"

BROKER_TRANSPORT = "amqplib"
BROKER_HOST = "localhost"
BROKER_PORT = 5672
BROKER_VHOST = "/"
BROKER_USER = "guest"
BROKER_PASSWORD = "guest"

# If Django is used as the Broker Transport
# djkombu is required in INSTALLED_APPS
#BROKER_TRANSPORT = "django"

import djcelery
djcelery.setup_loader()

def get_user_url(u):
    from django.contrib.sites.models import Site
    s = Site.objects.get_current()
    return "http://" + s.domain + "/profiles/" + u.username


ABSOLUTE_URL_OVERRIDES = {
    'auth.user': get_user_url
}

SERIALIZATION_MODULES = {
    'json': 'wadofstuff.django.serializers.json'
}

# For django-profiles
AUTH_PROFILE_MODULE = 'people.Contact'

REGISTRATION_OPEN = False

SERVE_MEDIA = DEBUG;

#Import uploaded shapefiles into a database such as PostGIS?
DB_DATASTORE=False

#Database datastore connection settings
DB_DATASTORE_NAME = ''
DB_DATASTORE_USER = ''
DB_DATASTORE_PASSWORD = ''
DB_DATASTORE_HOST = ''
DB_DATASTORE_PORT = ''
DB_DATASTORE_TYPE=''

try:
    from local_settings import *
except ImportError:
    pass
