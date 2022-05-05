from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy
from django.db.models import Q, F, Sum, Value, ExpressionWrapper, IntegerField, CharField
from django.core.serializers.json import DjangoJSONEncoder

import datetime

from .models import VoceSpesa, GAE, Stanziamento, Variazione, Impegno, Mandato
from .forms import GaeForm

from django.contrib.auth.mixins import PermissionRequiredMixin

# from .forms import ResearcherRoleForm, ProjectForm

from django.views import View
from UdyniManagement.menu import UdyniMenu
from UdyniManagement.views import ListViewMenu, CreateViewMenu, UpdateViewMenu, DeleteViewMenu


#=============================
# Gestione GAE

class GAElist(PermissionRequiredMixin, ListViewMenu):
    model = GAE
    permission_required = ""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "GAE"
        return context


class GAEadd(PermissionRequiredMixin, CreateViewMenu):
    model = GAE
    form_class = GaeForm
    success_url = reverse_lazy('acc_gae_list')
    template_name = "Accounting/gae_form.html"
    permission_required = ""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Add new GAE"
        context['back_url'] = 'acc_gae_list'
        return context


class GAEmod(PermissionRequiredMixin, UpdateViewMenu):
    model = GAE
    fields = ['name', 'description']
    success_url = reverse_lazy('acc_gae_list')
    template_name = "Accounting/gae_form.html"
    permission_required = ""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Modify GAE"
        context['back_url'] = 'acc_gae_list'
        return context


class GAEdel(PermissionRequiredMixin, DeleteViewMenu):
    model = GAE
    success_url = reverse_lazy('acc_gae_list')
    template_name = "UdyniManagement/confirm_delete.html"
    permission_required = ""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Delete GAE"
        context['message'] = "Are you sure you want to delete the GAE: {0!s}?".format(context['object'])
        context['back_url'] = 'acc_gae_list'
        return context


#=============================
# Residui in tempo reale. Sintetici.

class GAEResidui(PermissionRequiredMixin, View):
    permission_required = ''
    http_method_names = ['get', ]

    def get(self, request, *args, **kwargs):
        objects = GAE.objects.all().order_by('name')
        gae = []
        for obj in objects:
            gae.append({
                'name': obj.name,
                'desc': obj.description,
                'project': obj.project.name,
            })

        context = {
            'title': 'Available funds',
            'gae': gae,
            'menu': UdyniMenu().getMenu(request.user),
        }
        return render(request, 'Accounting/gae_residui.html', context)


#===============================
# Situazione GAE dettagliata (stanziamenti, variazioni, spese)

class GAESituazione(PermissionRequiredMixin, View):
    permission_required = ''
    http_method_names = ['get', ]

    def get(self, request, *args, **kwargs):
        objects = GAE.objects.all().order_by('name')
        gae = []
        for obj in objects:
            gae.append({
                'pk': obj.pk,
                'name': obj.name,
                'desc': obj.description,
                'project': obj.project.name,
            })

        context = {
            'title': "'Situazione' GAE",
            'gae': gae,
            'menu': UdyniMenu().getMenu(request.user),
        }
        return render(request, 'Accounting/gae_situazione.html', context)


class GAEAjaxSituazione(PermissionRequiredMixin, View):
    permission_required = ''
    http_method_names = ['get', ]

    def get(self, request, *args, **kwargs):
        # Get GAE
        gae = get_object_or_404(GAE, pk=self.kwargs['gae'])
        situazione = self.__build_situazione(gae)
        voci = {}
        for v in situazione.keys():
            voci[v] = VoceSpesa.objects.get(voce=v).description

        context = {
            'situazione': situazione,
            'voci': voci,
        }
        # Return formatted table through AJAX
        return render(request, 'Accounting/gae_situazione_table.html', context)

    def __build_situazione(self, gae):

        stanziamenti = (
            Stanziamento.objects
            .filter(gae=gae)
            .order_by('voce', 'esercizio')
        )

        variazioni = (
            Variazione.objects
            .filter(gae=gae)
            .order_by('voce', 'esercizio', 'data')
        )

        situazione = {}

        for s in stanziamenti:

            voce = s.voce.voce
            if voce not in situazione:
                situazione[voce] = {}

            situazione[voce][s.esercizio] = {
                'stanziamento': s.stanziamento,
                'assestato': s.assestato,
                'var_piu': s.var_piu,
                'var_meno': s.var_meno,
                'impegnato': s.impegnato,
                'pagato': s.pagato,
                'residuo': s.residuo,
                'variazioni': [],
            }

        for v in variazioni:

            voce = v.voce.voce
            if voce not in situazione:
                print("[E] variazione su voce non presente nella situazione!")
                continue

            if v.esercizio not in situazione[voce]:
                print("[E] variazione su esercizio non presenze nella situazione!")
                continue

            situazione[voce][v.esercizio]['variazioni'].append({
                'numero': v.numero,
                'descrizione': v.descrizione,
                'importo': v.importo,
                'data': v.data,
            })

        return situazione


#=================================
# GAE dettaglio impegni
class GAEImpegni(PermissionRequiredMixin, View):
    permission_required = ''
    http_method_names = ['get', ]

    def get(self, request, *args, **kwargs):
        objects = GAE.objects.all().order_by('name')
        gae = []
        for obj in objects:
            gae.append({
                'pk': obj.pk,
                'name': obj.name,
                'desc': obj.description,
                'project': obj.project.name,
            })

        context = {
            'title': "'Situazione' GAE",
            'gae': gae,
            'menu': UdyniMenu().getMenu(request.user),
        }
        return render(request, 'Accounting/gae_impegni.html', context)


class GAEAjaxImpegni(PermissionRequiredMixin, View):
    permission_required = ''
    http_method_names = ['get', ]

    def get(self, request, *args, **kwargs):

        gae = get_object_or_404(GAE, pk=self.kwargs['gae'])

        m_prev = (
            Mandato.objects
            .filter(Q(impegno__gae=gae))
            .annotate(
                im_voce=F('impegno__voce__voce'),
                im_numero=F('impegno__numero'),
                im_esercizio=F('impegno__esercizio'),
                im_esorig=F('impegno__esercizio_orig'),
                im_desc=F('impegno__description'),
                im_importo=F('importo'),
                im_mandato_n=F('numero'),
                im_mandato_terzo=F('terzo'),
            )
            .values(
                'im_voce',
                'im_numero',
                'im_esercizio',
                'im_esorig',
                'im_desc',
                'im_importo',
                'im_mandato_n',
                'im_mandato_terzo',
            )
            .order_by('im_esercizio', 'im_numero', 'im_mandato_n')
        )

        m_act = (
            Impegno.objects
            .filter(
                Q(gae=gae) &
                Q(esercizio=datetime.date.today().year)
            )
            .annotate(
                im_voce=F('voce__voce'),
                im_numero=F('numero'),
                im_esercizio=F('esercizio'),
                im_esorig=F('esercizio_orig'),
                im_desc=F('description'),
                im_importo=F('im_competenza') + F('im_residui') - F('pagato_competenza') - F('pagato_residui'),
                im_mandato_n=ExpressionWrapper(
                    Value(0),
                    output_field=IntegerField(),
                ),
                im_mandato_terzo=ExpressionWrapper(
                    Value(""),
                    output_field=CharField(max_length=200),
                ),
            )
            .filter(Q(im_importo__gt=0))
            .values(
                'im_voce',
                'im_numero',
                'im_esercizio',
                'im_esorig',
                'im_desc',
                'im_importo',
                'im_mandato_n',
                'im_mandato_terzo',
            )
            .order_by('im_esorig', 'im_numero', 'im_esercizio', 'im_mandato_n')
        )
        # Union
        impegni_raw = m_prev.union(m_act).order_by('im_esorig', 'im_numero', 'im_esercizio', 'im_mandato_n')

        # Group by 'numero impegno'
        impegni = {}
        for im in impegni_raw:
            tag = "{0!s}_{1!s}".format(im['im_esorig'], im['im_numero'])

            if tag not in impegni:
                impegni[tag] = {
                    'esercizio_orig': im['im_esorig'],
                    'numero': im['im_numero'],
                    'voce': im['im_voce'],
                    'desc': im['im_desc'],
                    'pagato': 0.0,
                    'dapagare': 0.0,
                    'mandati': [],
                }

            if im['im_mandato_n'] != 0:
                impegni[tag]['mandati'].append({
                    'esercizio': im['im_esercizio'],
                    'numero': im['im_mandato_n'],
                    'importo': im['im_importo'],
                    'terzo': im['im_mandato_terzo'],
                })
                impegni[tag]['pagato'] += im['im_importo']
            else:
                impegni[tag]['dapagare'] += im['im_importo']

        context = {
            'impegni': impegni,
        }
        # Return formatted table through AJAX
        return render(request, 'Accounting/gae_impegni_table.html', context)


# class Impegno(models.Model):
#     gae = models.ForeignKey(GAE, on_delete=models.CASCADE)
#     esercizio = models.IntegerField()
#     esercizio_orig = models.IntegerField()
#     numero = models.BigIntegerField()
#     description = models.CharField(max_length=300)
#     voce = models.ForeignKey(VoceSpesa, on_delete=models.PROTECT)
#     im_competenza = models.FloatField(default=0.0)
#     im_residui = models.FloatField(default=0.0)
#     doc_competenza = models.FloatField(default=0.0)
#     doc_residui = models.FloatField(default=0.0)
#     pagato_competenza = models.FloatField(default=0.0)
#     pagato_residui = models.FloatField(default=0.0)

# class Mandato(models.Model):
#     impegno = models.ForeignKey(Impegno, on_delete=models.CASCADE)
#     numero = models.IntegerField()
#     description = models.CharField(max_length=300)
#     id_terzo = models.IntegerField()
#     terzo = models.CharField(max_length=200)
#     importo = models.FloatField()
#     data = models.DateField(null=True, blank=True)

