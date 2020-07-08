# flake8: noqa
import os
from ccg_django_utils.conf import EnvConfig
from rdrf.settings import *
import angelman

env = EnvConfig()


FALLBACK_REGISTRY_CODE = "angelman"
LOCALE_PATHS = env.getlist("locale_paths", ['/data/translations/locale'])

# Adding the angelman app first, so that its templates overrides base templates
INSTALLED_APPS = [
    FALLBACK_REGISTRY_CODE,
] + INSTALLED_APPS

ROOT_URLCONF = '%s.urls' % FALLBACK_REGISTRY_CODE

SEND_ACTIVATION_EMAIL = False

RECAPTCHA_SITE_KEY = env.get("recaptcha_site_key", "")
RECAPTCHA_SECRET_KEY = env.get("recaptcha_secret_key", "")

PROJECT_TITLE = env.get("project_title", "Global Angelman Syndrome Registry")
PROJECT_TITLE_LINK = "login_router"

VERSION = env.get('app_version', '%s (ang)' % angelman.VERSION)

REGISTRATION_FORM = "angelman.forms.angelman_registration_form.ANGRegistrationForm"
REGISTRATION_CLASS = "angelman.registry.groups.registration.angelman_registration.AngelmanRegistration"

SECURITY_WHITELISTED_URLS += (
    "parent_edit",
    "parent_page",
)

SCRIPT_NAME = env.get("script_name", os.environ.get("HTTP_SCRIPT_NAME", ""))
WEBAPP_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_ROOT = env.get('STATIC_ROOT', os.path.join(WEBAPP_ROOT, 'static'))
STATIC_URL = env.get('STATIC_URL', '{0}/static/'.format(SCRIPT_NAME))
