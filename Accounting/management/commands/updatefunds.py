import time
import datetime
import os
import logging

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from Accounting.models import GAE, VoceSpesa, Stanziamento, Variazione, Impegno, Mandato
from sigla.sigla import SIGLA


class Command(BaseCommand):
    help = 'Update funds, impegni and mandati'

    def handle(self, *args, **options):
        # Start logger
        self.logger = logging.getLogger('UpdateFunds')
        self.logger.setLevel(logging.INFO if not settings.DEBUG else logging.DEBUG)

        # Define formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # Add console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO if not settings.DEBUG else logging.DEBUG)
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)

        # Add file logger
        fh = logging.FileHandler(os.path.join(settings.BASE_DIR, "updatefunds.log"))
        fh.setLevel(logging.WARNING)
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)

        # Load SIGLA interface
        sigla = SIGLA(settings.SIGLA_USERNAME, settings.SIGLA_PASSWORD, self.logger)

        # First get projects informations
        # NOTE: better to take all projects as the call for a single one takes anyway tens of seconds...
        progetti = sigla.getProgetti()

        # Get all GAEs
        gaes = GAE.objects.all()

        # Cycle over each GAE and update info
        for gae in gaes:
            s = time.time()

            # Get start date of project
            prj = gae.project.sigla_name
            start = progetti[prj]['start']

            # Years to check
            years = list(range(start.year, datetime.date.today().year + 1, 1))

            for y in years:
                try:
                    # Get competenza
                    c = sigla.getCompetenza(gae.name, y)

                    # Cycle over each 'voce'
                    new_pk = []
                    for k, v in c.items():

                        # Get Voce
                        try:
                            voce = VoceSpesa.objects.get(voce=k)
                        except VoceSpesa.DoesNotExist:
                            # Does not exist. Add 'voce' to database
                            voce = VoceSpesa()
                            voce.voce = k
                            voce.description = v['descrizione']
                            voce.save()

                        # Get or create 'stanziamento'
                        try:
                            stanziamento = Stanziamento.objects.get(gae=gae, esercizio=y, voce=voce)
                        except Stanziamento.DoesNotExist:
                            # Does not exist. Create a new one
                            stanziamento = Stanziamento()
                            stanziamento.gae = gae
                            stanziamento.voce = voce
                            stanziamento.esercizio = y

                        stanziamento.stanziamento = v['stanziamento']
                        stanziamento.var_piu = v['var_piu']
                        stanziamento.var_meno = v['var_meno']
                        stanziamento.assestato = v['assestato']
                        stanziamento.impegnato = v['impegnato']
                        stanziamento.residuo = v['residuo']
                        stanziamento.pagato = v['pagato']
                        stanziamento.da_pagare = v['dapagare']
                        stanziamento.save()
                        new_pk.append(stanziamento.pk)
                        if settings.DEBUG:
                            self.logger.debug("Updated 'stanziamento' for gae {0:s}, year {1:d}, 'voce' {2:s}".format(gae.name, y, k))

                    # Delete 'stanziamento' not updated by comeptenza (otherwise residui will add up at every update)
                    Stanziamento.objects.filter(Q(gae=gae, esercizio=y) & ~Q(pk__in=new_pk)).delete()

                    # Each stanziamento competenza should be updated with
                    # modifications in the following years as residui

                    for res_y in range(y + 1, years[-1] + 1, 1):
                        r = sigla.getResidui(gae.name, res_y, y)

                        # Cycle over each 'voce'
                        for k, v in r.items():
                            try:
                                voce = VoceSpesa.objects.get(voce=k)
                            except VoceSpesa.DoesNotExist:
                                # Does not exist. Add 'voce' to database
                                voce = VoceSpesa()
                                voce.voce = k
                                voce.description = v['descrizione']
                                voce.save()

                            try:
                                # Update stanziamento
                                stanziamento = Stanziamento.objects.get(gae=gae, esercizio=y, voce=voce)

                            except Stanziamento.DoesNotExist:
                                # Nessuno stanziamento di compenza sulla voce.
                                stanziamento = Stanziamento()
                                stanziamento.gae = gae
                                stanziamento.voce = voce
                                stanziamento.esercizio = y
                                stanziamento.stanziamento = 0.0
                                stanziamento.var_piu = 0.0
                                stanziamento.var_meno = 0.0
                                stanziamento.assestato = 0.0
                                stanziamento.impegnato = 0.0
                                stanziamento.residuo = 0.0
                                stanziamento.pagato = 0.0
                                stanziamento.da_pagare = 0.0

                            stanziamento.var_piu += v['esercizi'][y]['var_piu_imp']
                            stanziamento.var_meno += v['esercizi'][y]['var_meno_imp']
                            #stanziamento.assestato = v['esercizi'][y]['assestato'] # NOTE: questo assestato si riferisce allo stanziamento improprio del residuo...
                            stanziamento.assestato += (v['esercizi'][y]['var_piu_imp'] - v['esercizi'][y]['var_meno_imp'])
                            stanziamento.impegnato += v['esercizi'][y]['var_piu_obblpro'] - v['esercizi'][y]['var_meno_obblpro'] + v['esercizi'][y]['impegnato']
                            stanziamento.residuo = v['esercizi'][y]['residuo']
                            stanziamento.pagato += v['esercizi'][y]['pagato']
                            stanziamento.da_pagare = v['esercizi'][y]['dapagare']
                            stanziamento.save()

                except Exception as e:
                    self.logger.error("Failed to update 'stanziamenti' for GAE {0:s} for year {1:d} (Error: {2!s})".format(gae.name, y, e))

                try:
                    # Get variazioni
                    v = sigla.getVariazioni(gae.name, y)

                    for var in v:
                        # Get Voce
                        try:
                            voce = VoceSpesa.objects.get(voce=var['voce'])
                        except VoceSpesa.DoesNotExist:
                            # Does not exist. This should not happen as the voce should have been added in the previous step
                            self.logger.error("'voce' {0:s} does not exist in database. Something is wrong (GAE: {1:s}, esercizio: {2:d}, variazione: {3:d})".format(var['voce'], gae.name, y, var['numero']))
                            continue

                        try:
                            variazione = Variazione.objects.get(gae=gae, data=var['data'], numero=var['numero'], voce=voce)
                            if y < datetime.date.today().year:
                                # If 'variazione' already exists and is relative to a past year, we can leave it as it will not change
                                continue
                        except Variazione.DoesNotExist:
                            variazione = Variazione()
                            variazione.gae = gae
                            if var['tipo'] == 'Residuo':
                                variazione.esercizio = var['es_residuo']
                            else:
                                variazione.esercizio = y
                            variazione.numero = var['numero']
                            variazione.voce = voce
                            if settings.DEBUG:
                                self.logger.debug("Adding 'variazione ' {0:d} for gae {1:s} year {2:d} 'voce' {3:s}".format(var['numero'], gae.name, y, var['voce']))

                        # Update variazione if needed
                        variazione.tipo = var['tipo']
                        variazione.stato = var['stato']
                        variazione.riferimenti = var['riferimenti'] if var['riferimenti'] is not None else "None"
                        variazione.descrizione = var['descrizione'] if var['descrizione'] is not None else "None"
                        variazione.cdrSrc = var['cdr_prop']
                        variazione.cdrDst = var['cdr_ass']
                        variazione.importo = var['importo']
                        variazione.data = var['data']
                        variazione.save()

                except Exception as e:
                     self.logger.error("Failed to update 'variazioni' for GAE {0:s} for year {1:d} (Error: {2!s})".format(gae.name, y, e))

                try:
                    # Get impegni
                    impegni = sigla.getImpegni(gae.name, y)

                    for im in impegni:
                        # Get Voce
                        try:
                            voce = VoceSpesa.objects.get(voce=im['voce'])
                        except VoceSpesa.DoesNotExist:
                            # Does not exist. This should not happen as the voce should have been added in the previous step
                            self.logger.error("'voce' {0:s} does not exist in database. Something is wrong (GAE: {1:s}, esercizio: {2:d}, impegno: {3:d})".format(im['voce'], gae.name, y, im['impegno']))
                            continue

                        try:
                            impegno = Impegno.objects.get(gae=gae, esercizio=y, esercizio_orig=im['esercizio_orig'], numero=im['impegno'])
                            if y < datetime.date.today().year:
                                # If 'impegno' already exists and is relative to a past year, we can leave it as it will not change
                                continue
                        except Impegno.DoesNotExist:
                            impegno = Impegno()
                            impegno.gae = gae
                            impegno.esercizio = y
                            impegno.esercizio_orig = im['esercizio_orig']
                            impegno.numero = im['impegno']
                            impegno.voce = voce
                            if settings.DEBUG:
                                self.logger.debug("Adding 'impegno' {0:d} for gae {1:s} year {2:d} 'voce' {3:s}".format(im['impegno'], gae.name, y, im['voce']))

                        # Update impegno if needed
                        impegno.description = im['descrizione']
                        impegno.im_competenza = im['competenza']
                        impegno.im_residui = im['residui']
                        impegno.doc_competenza = im['doc_competenza']
                        impegno.doc_residui = im['doc_residuo']
                        impegno.pagato_competenza = im['pagato_competenza']
                        impegno.pagato_residui = im['pagato_residuo']
                        impegno.save()

                except Exception as e:
                    self.logger.error("Failed to update 'impegni' for GAE {0:s} for year {1:d} (Error: {2!s})".format(gae.name, y, e))

            if settings.DEBUG:
                self.logger.debug("GAE {0:s} done in {1:.2f}s".format(gae.name, time.time() - s))

        # Delete old 'mandati'
        Mandato.objects.all().delete()

        # Create 'mandati'
        for im in Impegno.objects.all():

            try:
                if settings.DEBUG:
                    self.logger.debug("Checking 'impegno' {0!s}".format(im))
                mandati = sigla.getMandati(im.numero, im.esercizio_orig, im.esercizio)
                if not len(mandati):
                    continue

                for m in mandati:
                    # If 'mandato' has not date, skip it as it was not paid
                    if m['data'] is None:
                        continue
                    # If 'mandato' is canceled, ignore
                    if m['stato'] == 'A':
                        continue

                    try:
                        mandato = Mandato.objects.get(impegno=im, numero=m['numero'])
                        # We already have a 'mandato' linked to 'impegno' with the same number.
                        # We have different amounts referring to different invoices, but payed together
                        mandato.importo += m['importo']
                        mandato.save()
                    except Mandato.DoesNotExist:
                        mandato = Mandato()
                        mandato.impegno = im
                        mandato.numero = m['numero']
                        mandato.description = m['descrizione']
                        mandato.id_terzo = m['id_terzo']
                        mandato.terzo = m['terzo']
                        mandato.importo = m['importo']
                        mandato.data = m['data']
                        mandato.save()

                        if settings.DEBUG:
                            self.logger.debug("Added 'mandato' {0:d} for 'impegno' {1:d}/{2:d}".format(mandato.numero, mandato.impegno.numero, mandato.impegno.esercizio_orig))

            except Exception as e:
                self.logger.error("Failed to get 'mandati' for 'impegno' {0:d}/{1:d} for year {2:d} (Error: {3!s})".format(im.numero, im.esercizio_orig, im.esercizio, e))
