from django.urls import path, reverse_lazy
from django.views.generic.base import RedirectView
from UdyniManagement.views import EmptyView

from . import views

urlpatterns = [
    path('', EmptyView.as_view(), name='reporting_index'),

    path('costs/', views.PersonnelCostList.as_view(), name='cost_view'),
    path('costs/add', views.PersonnelCostCreate.as_view(), name='cost_add'),
    path('costs/<int:pk>/modify', views.PersonnelCostUpdate.as_view(), name='cost_mod'),
    path('costs/<int:pk>/delete', views.PersonnelCostDelete.as_view(), name='cost_del'),

    path('presences/', views.PresenceDataList.as_view(), name='presencedata_view'),
    path('presences/detail/<int:researcher>/<int:year>', views.PresenceDataDetail.as_view(), name='presencedata_detailyear'),
    path('presences/detail/<int:researcher>/<int:year>/<int:month>', views.PresenceDataDetail.as_view(), name='presencedata_detailmonth'),
    path('presences/import', views.PresenceDataImport.as_view(), name='presencedata_import'),
    path('presences/store', views.PresenceDataStore.as_view(), name='presencedata_store'),
    path('presences/update', views.PresenceDataUpdate.as_view(), name='presencedata_update'),
    path('presences/export2ts/<int:researcher>/<int:year>', views.PresenceDataExportTS.as_view(), name="presencedata_export2ts"),

    path('epascodes/', views.EpasCodeList.as_view(), name='epas_view'),
    path('epascodes/import', views.EpasCodeImport.as_view(), name='epas_import'),
    path('epascodes/update', views.EpasCodeUpdate.as_view(), name='epas_update'),

    path('bankholidays/', views.BankHolidayList.as_view(), name='bankholiday_view'),
    path('bankholidays/add', views.BankHolidayCreate.as_view(), name='bankholiday_add'),
    path('bankholidays/<int:pk>/modify', views.BankHolidayUpdate.as_view(), name='bankholiday_mod'),
    path('bankholidays/<int:pk>/delete', views.BankHolidayDelete.as_view(), name='bankholiday_del'),

    path('reporting/', views.ReportingList.as_view(), name='reporting_view'),
    path('reporting/add', views.ReportingCreate.as_view(), name='reporting_add'),
    path('reporting/<int:pk>/modify', views.ReportingUpdate.as_view(), name='reporting_mod'),
    path('reporting/<int:pk>/delete', views.ReportingDelete.as_view(), name='reporting_del'),
    path('reporting/ajax/wps', views.ReportingUpdateWPs.as_view(), name="reporting_update_wps"),
    path('reporting/ajax/costs', views.ReportingUpdateCosts.as_view(), name="reporting_update_costs"),

    path('timesheets/', views.TimeSheetsView.as_view(), name='timesheets_view'),
    path('timesheets/<int:researcher>', RedirectView.as_view(url=reverse_lazy('timesheets_view'), permanent=False)),
    path('timesheets/<int:researcher>/<int:year>', RedirectView.as_view(url=reverse_lazy('timesheets_view'), permanent=False)),
    path('timesheets/<int:researcher>/<int:year>/list', views.TimeSheetsList.as_view(), name='timesheets_list'),
    path('timesheets/<int:researcher>/<int:year>/generate', views.TimeSheetsGenerate.as_view(), name='timesheets_generate'),
    path('timesheets/<int:researcher>/<int:year>/hints', views.TimeSheetsGenerateHints.as_view(), name='timesheets_generatehints'),
    path('timesheets/<int:researcher>/<int:year>/print', views.TimeSheetsPrint.as_view(), name='timesheets_print'),

    path('timesheets/ajax/<int:researcher>/<int:year>/generate', views.TimesheetAjaxDenied.as_view(), name='timesheets_ajax_generate_base'),
    path('timesheets/ajax/<int:researcher>/<int:year>/generate/<int:month>', views.TimeSheetsAjaxGenerate.as_view(), name='timesheets_ajax_generate'),
    path('timesheets/ajax/<int:researcher>/<int:year>/view/<int:month>', views.TimeSheetsAjaxView.as_view(), name='timesheets_ajax_view'),
    path('timesheets/ajax/<int:researcher>/<int:year>/hints', views.TimeSheetsAjaxSaveHints.as_view(), name="timesheets_ajax_savehints"),
]

menu = {
    'name': 'Reporting',
    'link': reverse_lazy('reporting_index'),
    'icon': 'fa-file-invoice-dollar',
    'subsections': [
        {
            'name': 'Personnel costs',
            'link': reverse_lazy('cost_view'),
            'permissions': [],
        },
        {
            'name': 'Presences',
            'link': reverse_lazy('presencedata_view'),
            'permissions': [],
        },
        {
            'name': 'Expenses reporting',
            'link': '', #reverse_lazy(''),
            'permissions': [],
        },
        {
            'name': 'Personnel reporting',
            'link': reverse_lazy('reporting_view'),
            'permissions': [],
        },
        {
            'name': 'Timesheets',
            'link': reverse_lazy('timesheets_view'),
            'permissions': [],
        },
        {
            'name': 'Bank holidays',
            'link': reverse_lazy('bankholiday_view'),
            'permissions': [],
        },
        {
            'name': 'EPAS codes',
            'link': reverse_lazy('epas_view'),
            'permissions': [],
        },
    ],
    'permissions': [],
}