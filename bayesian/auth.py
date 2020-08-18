"""Authorization token handling."""
import logging
from functools import wraps
from flask import g, request
from requests import get
from bayesian.utility.user_utils import get_user
from bayesian.utility.v2.sa_models import RegistrationStatus

from .default_config import AUTH_URL


logger = logging.getLogger(__name__)


def get_access_token(service_name):
    """Return the access token for service."""
    services = {'github': 'https://github.com'}
    url = '{auth_url}/api/token?for={service}'.format(
        auth_url=AUTH_URL, service=services.get(service_name))
    token = request.headers.get('Authorization')
    headers = {"Authorization": token}
    try:
        _response = get(url, headers=headers)
        if _response.status_code == 200:
            response = _response.json()
            return {"access_token": response.get('access_token')}
        else:
            return {"access_token": None}

    except Exception:
        logger.error('Unable to connect to Auth service')


def get_user_type(view):
    """Validate and get user type based on UUID from the request."""
    @wraps(view)
    def wrapper(*args, **kwargs):
        """Read uuid and decides user type based on its validity."""
        # Rule of UUID validation and setting user status ::
        #  ==============================================================
        #   UUID in request | UUID in RDS | RDS User State | User Status
        #  ==============================================================
        #    MISSING        | -- NA --    | -- NA --       | FREE
        #    PRESENT        | MISSING     | -- NA --       | FREE
        #    PRESENT        | PRESENT     | REGISTERED     | REGISTERED
        #    PRESENT        | PRESENT     | !REGISTERED    | FREE
        #  ==============================================================

        # By default set this to 'freetier'.
        g.registration_status = RegistrationStatus.freetier

        # Read uuid from request header.
        uuid = request.headers.get('uuid', None)

        # Check user with uuid if it is present in RDS.
        if uuid is not None:
            try:
                # Read user details from RDS based on uuid
                user = get_user(uuid)
                if user.status == 'REGISTERED':
                    g.registration_status = RegistrationStatus.registered
            except Exception as e:
                logger.warning('User get for UUID: %s failed with %s', uuid, e)

        logger.debug('For UUID: %s, got user type: %s', uuid, g.registration_status)
        return view(*args, **kwargs)

    return wrapper
