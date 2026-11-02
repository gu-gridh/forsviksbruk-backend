"""
Abstract Schemas

OpenAPI schema customization for digital humanities projects.
"""

from rest_framework.schemas.openapi import AutoSchema


class GenericSchema(AutoSchema):
    """Custom schema for APIs with better tag handling"""

    def get_tags(self, path, method):
        """Generate appropriate tags for API documentation"""
        # If user have specified tags, use them.
        if self._tags:
            return self._tags

        # First element of a specific path could be valid tag. This is a fallback solution.
        # PUT, PATCH, GET(Retrieve), DELETE:        /user_profile/{id}/       tags = [user-profile]
        # POST, GET(List):                          /user_profile/            tags = [user-profile]
        if path.startswith('/'):
            path = path[1:]

        path_parts = path.split('/')
        if len(path_parts) >= 3:
            tags = [path_parts[2].replace('_', '-')]
        else:
            tags = ['api']

        return tags
