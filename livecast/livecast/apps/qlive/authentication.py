from django.utils.translation import ugettext_lazy as _

from rest_framework.authentication import TokenAuthentication
from rest_framework import exceptions
from qlive.models import UserToken, User


class UserTokenAuthentication(TokenAuthentication):
    keyword = 'QLiveToken'

    def get_model(self):
        if self.model is not None:
            return self.model
        return UserToken

    def authenticate(self, request):
        model = self.get_model()
        key = request.META.get('HTTP_AUTHORIZATION', '')
        if not key:
            raise exceptions.AuthenticationFailed(_('Can`t find token. %s' % key))
        try:
            key = key.split()[1]
        except Exception:
            raise exceptions.AuthenticationFailed(_('Token wrong format %s' % key))
        try:
            token = model.objects.get(key=key)
        except model.DoesNotExist:
            raise exceptions.AuthenticationFailed(_('Invalid token. %s' % key))
        try:
            user = User.objects.get(user_id=token.user_id)
        except model.DoesNotExist:
            raise exceptions.AuthenticationFailed(_('Can`t find user. %s' % key))

        return user, token
