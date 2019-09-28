from django.urls import path, include
from rest_framework import routers
from rest_framework.urlpatterns import format_suffix_patterns

from qlive import views as qlive_views

router = routers.SimpleRouter()
router.register('qlive_user', qlive_views.UsersView)
router.register('qlive_room', qlive_views.LiveShowViewSet)
router.register('qlive_gift', qlive_views.GiftViewSet)
router.register('qlive_pay', qlive_views.PayViewSet)
router.register('get_livelist', qlive_views.LiveRoomsView)
router.register('get_playurl', qlive_views.LiveRoomView)
router.register('get_configs', qlive_views.ConfigsView)
router.register('qlive_like', qlive_views.LikeView)

urlpatterns = [
    path('', include(router.urls)),
    path('pay_notify/', qlive_views.PayNotifyView.as_view(), name='pay_notify'),
    path('im_notify/', qlive_views.IMNotifyView.as_view(), name='im_notify'),
]

urlpatterns = format_suffix_patterns(urlpatterns)
