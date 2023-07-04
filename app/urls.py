from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

from . import detection

urlpatterns = [
    path('', views.home, name='home'),

    path('login', views.loginPage, name='login'),
    path('logout', views.logoutUser, name='logout'),

    path('list_trainer', views.ListTrainer, name='list_trainer'),
    path('add_trainer_page', views.AddTrainerPage, name='add_trainer_page'),
    path('add_trainer', views.AddTrainer, name='add_trainer'),
    path('update_trainer/<int:pk>', views.UpdateTrainer, name='update_trainer'),
    path('delete_trainer/<int:pk>', views.DeleteTrainer, name='delete_trainer'),

    path('list_attendee/', views.ListAttendee, name='list_attendee'),
    path('add_attendee_page', views.AddAttendeePage, name='add_attendee_page'),
    path('add_attendee', views.AddAttendee, name='add_attendee'),
    path('update_attendee/<int:pk>', views.UpdateAttendee, name='update_attendee'),
    path('delete_attendee/<int:pk>', views.DeleteAttendee, name='delete_attendee'),

    path('list_classroom/', views.ListClassroom, name='list_classroom'),
    path('add_classroom_page', views.AddClassroomPage, name='add_classroom_page'),
    path('add_classroom', views.AddClassroom, name='add_classroom'),
    path('update_classroom/<int:pk>', views.UpdateClassroom, name='update_classroom'),
    path('delete_classroom/<int:pk>', views.DeleteClassroom, name='delete_classroom'),

    path('train_data_set/', detection.trainFace, name='train_data_set'),

    path('list_trainer_classroom/', views.ListTrainerClassroom, name='list_trainer_classroom'),

    path('join_classroom/', views.JoinClassroom, name='join_classroom'),

    path('edit_trainer_profile/', views.EditTrainerProfile, name='edit_trainer_profile'),
    path('edit_attendee_profile/', views.EditAttendeeProfile, name='edit_attendee_profile'),

    path('trainer_classroom/', views.TrainerClassrooms, name='trainer_classroom'),
    path('add_to_classroom/<int:classroom_id>', views.AddToClassroom, name='add_to_classroom'),
    path('delete_recourse/<int:pk>', views.DeleteResources, name='delete_recourse'),

    path('open_camera/', views.OpenCameras, name='open_camera'),

    path('scan-qr-code/', views.scan_qr_code, name='scan-qr-code'),
    path('attendance-success/', views.attendance_success, name='attendance-success'),

    # path('reset_password/',
    #      auth_views.PasswordResetView.as_view(template_name='app/password_reset.html'),
    #      name='password_reset'),

    path('reset_password/', views.password_reset_view, name='password_reset'),

    path('reset_password_sent/',
         auth_views.PasswordResetDoneView.as_view(template_name='app/password_reset_sent.html'),
         name='password_reset_done'),

    path('reset/<uidb64>/<token>',
         auth_views.PasswordResetConfirmView.as_view(template_name='app/password_reset_form.html'),
         name='password_reset_confirm'),

    path('reset_password_complete/',
         auth_views.PasswordResetCompleteView.as_view(template_name='app/password_reset_done.html'),
         name='password_reset_complete'),

     path('classroom/<int:pk>',views.classroom_info,name = 'course_single'),
     path('enroll/<int:pk>',views.enroll_classroom,name = 'enroll'),
     path('send_message/',views.message_view,name = 'send_message'),
     path('unenroll_classroom/<int:pk>',views.unenroll_classroom,name = 'unenroll_classroom'),

]
