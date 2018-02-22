"""Images-related resources for the API."""

from ..resource import (
    Resource,
    ResourceCollection,
)


class Image(Resource):
    """API resouce for images."""


class Images(ResourceCollection):
    """Images collection API methods."""

    uri_name = 'images'
    resource_class = Image