from django.conf.urls import url
from .views import login_user, logout_user, change_user_passwd, licence_key

urlpatterns = [
    url(r'^$', login_user, name='login'),
    url(r'^logout/$', logout_user, name='logout'),
    url(r'^change-password/$', change_user_passwd, name='change-pwd'),
    url(r'^licence/$', licence_key, name='activation'),
]