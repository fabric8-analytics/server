"""Authorization token handling."""
import logging
from functools import wraps
from flask import g, request
from requests import get
from bayesian.utility.user_utils import get_user, UserStatus, UserException
from bayesian.utility.v2.sa_models import HeaderData

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


def validate_user(view):
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

        # By default set this to 'freetier' and uuid to None
        g.user_status = UserStatus.FREETIER
        g.uuid = None

        try:
            header_data = HeaderData(**request.headers)
            if header_data.uuid:
                user = get_user(header_data.uuid)
                g.user_status = UserStatus[user.status]
                g.uuid = str(header_data.uuid) if header.uuid else None
        except ValidationError as e:
            raise HTTPError(400, "Not a valid uuid '{}'".format(header_data.uuid)) from e
        except UserException as e:
            raise HTTPError(500, "Unable to get user status for uuid '{}'".format(
                header_data.uuid)) from e

        logger.debug('For UUID: %s, got user type: %s final uuid: %d',
                     header_data.uuid, g.user_status, g.uuid)
        return view(*args, **kwargs)

    return wrapper
