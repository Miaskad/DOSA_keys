from django.conf.urls import include, url
from loads.views import com_settings

urlpatterns = [
    url(r'^', include('main.urls')),
    url(r'^admin/settings/', com_settings, name='settings'),
    url(r'^admin/', include('local_admin.urls')),
    url(r'^user/', include('users.urls')),
    ]