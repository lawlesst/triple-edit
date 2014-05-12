from django.http import HttpResponse

import os
import json


class JSONResponseMixin(object):
    def render_to_response(self, context):
        "Returns a JSON response containing 'context' as payload"
        return self.get_json_response(self.convert_context_to_json(context))

    def get_json_response(self, content, **httpresponse_kwargs):
        "Construct an `HttpResponse` object."
        params = self.request.GET
        if params.get('callback') is not None:
            content = "%s(%s)" % (params['callback'], content)
        return HttpResponse(
            content,
            content_type='application/json',
            **httpresponse_kwargs
        )

    def convert_context_to_json(self, context):
        """
        Fix this if there is a need to serializing more
        complex objects.
        """
        #"Convert the context dictionary into a JSON object"
        # Note: this needs to be better to ensure that you are seralizing what
        # is needed as JSON.  For now just popping known problems.
        #Also see - https://docs.djangoproject.com/en/dev/topics/serialization/
        # remove = ['user', 'resource', 'profile']
        # for rem in remove:
        #     try:
        #         del context[rem]
        #     except KeyError, TypeError:
        #         pass
        return json.dumps(context)

def get_env(key):
    try:
        return os.environ[key]
    except KeyError:
        raise Exception("Required environment variable not found: {}.".format(key))
