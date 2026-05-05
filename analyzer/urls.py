from django.urls import path
from . import views

urlpatterns = [
    path('',                                views.home,              name='home'),
    path('dashboard/<int:session_id>/',     views.dashboard,         name='dashboard'),
    path('forensics/<int:session_id>/',     views.forensics,         name='forensics'),
    path('delete/<int:session_id>/',        views.delete_session,    name='delete_session'),
    path('sessions/',                       views.all_sessions,      name='all_sessions'),
    path('search/<int:session_id>/',        views.search_messages,   name='search_messages'),
    path('translate/',                      views.translate_message,  name='translate_message'),
    path('debug/<int:session_id>/',         views.debug_analysis,    name='debug'),
]