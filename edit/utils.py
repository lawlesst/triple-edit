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
        Dumps the context as JSON.

        Improve if there is a need to serialize more
        complex objects.

        See: https://docs.djangoproject.com/en/dev/topics/serialization/
        """
        return json.dumps(context)

def get_env(key):
    try:
        return os.environ[key]
    except KeyError:
        raise Exception("Required environment variable not found: {}.".format(key))
