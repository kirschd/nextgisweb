# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, absolute_import

from pyramid.authentication import (
    AuthTktAuthenticationPolicy,
    BasicAuthAuthenticationPolicy as
    PyramidBasicAuthAuthenticationPolicy)

from ..auth import User


class BasicAuthenticationPolicy(PyramidBasicAuthAuthenticationPolicy):

    def unauthenticated_userid(self, request):
        """ Standard Pyramid function always returns login as 
        userid, but we need number representation of ID. We'll 
        swap these by parsing request headers. """

        username = super(BasicAuthenticationPolicy, self) \
            .unauthenticated_userid(request)

        if username is not None:
            user = User.filter_by(keyname=username).first()
            if user is None:
                return None
            else:
                return user.id


class AuthenticationPolicy(object):

    def __init__(self, settings):
        def check(username, password, request):
            user = User.filter_by(keyname=username, disabled=False).first()
            if user is None or not (user.password == password):
                return None
            else:
                return user

        self.members = (
            AuthTktAuthenticationPolicy(
                secret=settings.get('secret'),
                cookie_name='tkt', hashalg='sha512',
                max_age=24 * 3600, reissue_time=3600,
                http_only=True),

            BasicAuthenticationPolicy(
                check=check, realm=b'NextGISWeb'),
        )

    def authenticated_userid(self, request):
        for m in self.members:
            userid = m.authenticated_userid(request)
            if userid is not None:
                return userid

    def effective_principals(self, request):
        return []

    def remember(self, request, userid):
        headers = []
        for m in self.members:
            res = m.remember(request, userid)
            if res:
                headers.extend(res)

        return headers

    def forget(self, request):
        headers = []
        for m in self.members:
            res = m.forget(request)
            if res:
                headers.extend(res)

        return headers

    def unauthenticated_userid(self, request):
        return None
