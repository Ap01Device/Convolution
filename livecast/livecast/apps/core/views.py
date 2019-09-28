import logging
import random

from rest_framework import permissions, viewsets, status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import permission_classes, action, api_view
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from core.models import User, Config
from core import utils as core_utils
from core.permissions import IsOwnerOrReadOnly

logger = logging.getLogger(__name__)


@api_view(('GET',))
@permission_classes((AllowAny,))
def access_token(request):
    data = request.query_params

    if 'app_id' not in data:
        return Response({'detail': 'Parameter error'}, status=status.HTTP_400_BAD_REQUEST)

    access_token = core_utils.get_access_token(data['app_id'])

    return Response(access_token)
