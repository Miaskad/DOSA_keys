from django.conf.urls import url
from .views import dosing, cistern_list, cistern_info, keys, fuel_info

urlpatterns = [
    url(r'^$', dosing, name='dosing'),
    url(r'^cisterns/$', cistern_list, name='cistern_list'),
    url(r'^cisterns/(?P<cist_id>\d+)/', cistern_info, name='cist_info'),
    url(r'^keys/$', keys, name='keys'),
    url(r'^fuels/(?P<fuel_id>\d+)/', fuel_info, name='fuel_info'),
]
