from django.urls import path
from . import views



urlpatterns = [
    path(r'contact', views.contact, name='contact'),
    path(r'', views.DB, name='DB'),
    # path(r'data_upload', views.data_upload, name='data_upload'),
    path(r'bugs', views.bugs, name='bugs'),
    path(r'success', views.success, name='success'),
    path(r'download_data_report', views.download_data_report, name='download_data_report'),
    path(r'PepView/', views.PepView, name='PepView'),
    path(r'references', views.references, name='references'),
    path(r'data_validation_error', views.data_validation_error, name='data_validation_error'),
    path(r'top_bugs', views.top_bugs, name='top_bugs'),
    path(r'test_view', views.test_view, name='test_view'),
    path(r'user_activity', views.user_activity, name='user_activity'),
    path(r'bug_list', views.bug_list, name='bug_list'),
    path(r'suggestion_list', views.suggestion_list, name='suggestion_list'),
    path(r'logout_view', views.logout_view, name='logout_view'),
    path(r'load_data', views.load_data, name='load_data'),
    path('download_backup/', views.download_backup, name='download_backup'),
    path('upload_backup/', views.upload_backup, name='upload_backup'),
    path('fileUploader/', views.fileUploader, name='fileUploader'),
    path('errors/', views.errors, name='errors'),
    path('upload_chunk/', views.upload_chunk, name='upload_chunk'),
    path('merge_chunks/', views.merge_chunks, name='merge_chunks'),
    path('upload_page/', views.upload_page, name='upload_page'),
    path('upload_complete/', views.upload_complete, name='upload_complete'),
    path('load_backupdata/', views.load_backupdata, name='load_backupdata'),

    
]