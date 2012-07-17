import logging
import requests

from xml.etree import ElementTree

from django.conf import settings
from django.shortcuts import redirect, render_to_response
from django.template import RequestContext


logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger(__name__)


# Set the sonicwall Session Timeout (in seconds)
SONICWALL_SESSION_TIMEOUT = getattr(settings, 'SONICWALL_SESSION_TIMEOUT', 3600)

# Set the sonicwall Idle Timeout (in seconds)
SONICWALL_IDLE_TIMEOUT = getattr(settings, 'SONICWALL_IDLE_TIMEOUT', 300)

# The LHM callback on the SonicWALL
SONICWALL_CALLBACK = "externalGuestLogin.cgi"

# Set the xPath to the Sonicwall reply
RESPONSE_CODE_XPATH = "AuthenticationReply/ResponseCode"

ERROR_CODES = {
    "2": "Your LHM session has expired. You may try to initiate a new session.",
    "3": "You have exceeded your idle timeout. Please log back in.",
    "4": "The maximum number of sessions has been reached. Please try again later.",
    "51": "Session Limit Reached: The maximum number of guest session has been reached. Sorry for the inconvenience. Please close and relaunch your browser to try again.",
    "100": "Session creation failed: Your session cannot be created at this time. Sorry for the inconvenience. Please close and relaunch your browser to try again.",
    "251": "Session creation failed: The request for authorization failed message authentication. Sorry for the inconvenience. Please close and relaunch your browser to try again.",
    "253": "Session creation failed: The request for authorization failed to match a known session identity. Sorry for the inconvenience. Please close and relaunch your browser to try again.",
    "254": "Session creation failed: The request for authorization was missing an essential parameter. Sorry for the inconvenience. Please close and relaunch your browser to try again.",
    "255": "Session creation failed: The request for authorization failed due to an unspecified error. Sorry for the inconvenience. Please close and relaunch your browser to try again.",
}


def authorize(request, template_name='sonicwall/authorize.html'):
    """
    This view handles the LHM authorization process:

        1. Display the authorization page
        2. POST to the SonicWall LHM appliance
        3. Redirect the user back to the SonicWall
    
    """

    context = {}

    # Sample LHM redirect querystring:
    # http://server/lhm?sessionId=0b712fd83b9f5313db5af1cea6b1004f&ip=10.50.165.231&mac=00:0e:35:bd:c9:37&ufi=0006b11184300&mgmtBaseUrl=https://10.50.165.193:4043/&clientRedirectUrl=https://10.50.165.193:444/&req=http%3A//www.google.com/ig

    # The "cc" querystring value sent by the SonicWALL specifies which error has occurred:
    # "Session Expiration" (cc=2), "Idle Timeout" (cc=3), or "Max Sessions" (cc=4). 
    if 'cc' in request.GET:
        error_code = request.GET['cc']
        try:
            context['error'] = ERROR_CODES[error_code]
        except KeyError:
            context['error'] = 'An unexpected error has occurred.'

    if request.method == 'POST':
        try:
            try:
                # Assemble the data to post back to the SonicWALL to authorize the LHM session
                payload = {
                    "sessId": request.GET['sessionId'],
                    "userName": request.GET['mac'],
                    "sessionLifetime": SONICWALL_SESSION_TIMEOUT,
                    "idleTimeout": SONICWALL_IDLE_TIMEOUT,
                }

                # Combine mgmtBaseUrl from the original redirect with the login cgi
                lhm_url = request.GET['mgmtBaseUrl'] + SONICWALL_CALLBACK
            except Exception:
                logger.exception("Uncaught exception while processing request parameters")
                raise

            # POST the authorization parameters to the LHM
            try:
                logger.debug("POSTing to SonicWall %s with payload: %s", lhm_url, payload)
                response = requests.post(lhm_url, payload, verify=False)
            except Exception:
                logger.exception("Uncaught exception while communicating with LHM")
                raise
            else:
                logger.debug("SonicWall response: %s", response.text)

            # Determine the LHM response code
            try:
                doc = ElementTree.fromstring(response.text)
                node = doc.find(RESPONSE_CODE_XPATH)
                response_code = node.text
            except Exception:
                logger.exception("Uncaught XML exception while parsing LHM response")
                raise
            else:
                logger.debug("SonicWall response code: %s", response_code)

        except Exception:
            context['error'] = 'An unexpected error has occurred.'

        else:
            # Authorization succeeded
            if response_code == "50":
                self.logger.info('Succesful LHM authorization; redirecting to: %s', request.GET['req'])
                return redirect(request.GET['req'])

            # Authorization failed, so determine why
            try:
                context['error'] = ERROR_CODES[response_code]
            except KeyError:
                context['error'] = 'An unexpected error has occurred.'

    return render_to_response(template_name, context, context_instance=RequestContext(request))
