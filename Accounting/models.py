from django.db import models
from Projects.models import Project


class GAE(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    name = models.CharField(max_length=16, unique=True, db_index=True)
    description = models.TextField()

    def __str__(self):
        return "GAE {0!s}: {1!s}".format(self.name, self.description)

    class Meta:
        ordering = ["project", "name"]


class VoceSpesa(models.Model):
    voce = models.CharField(max_length=20, unique=True, db_index=True)
    description = models.CharField(max_length=300)

    def __str__(self):
        return "{0:d}: {1!s}".format(self.voce, self.description)

    class Meta:
        ordering = ["voce", ]


class Stanziamento(models.Model):
    gae = models.ForeignKey(GAE, on_delete=models.CASCADE)
    esercizio = models.IntegerField()
    voce = models.ForeignKey(VoceSpesa, on_delete=models.PROTECT)
    stanziamento = models.FloatField(default=0.0)
    var_piu = models.FloatField(default=0.0)
    var_meno = models.FloatField(default=0.0)
    assestato = models.FloatField(default=0.0)
    impegnato = models.FloatField(default=0.0)
    residuo = models.FloatField(default=0.0)
    pagato = models.FloatField(default=0.0)
    da_pagare = models.FloatField(default=0.0)

    def __str__(self):
        return "Stato GAE {0!s} Voce {1!s}".format(self.gae.name, self.voce.voce)

    class Meta:
        ordering = ["gae", "esercizio", "voce"]
        constraints = [
            models.UniqueConstraint(fields=['gae', 'esercizio', 'voce', ], name="%(app_label)s_%(class)s_unique"),
        ]


class Variazione(models.Model):
    gae = models.ForeignKey(GAE, on_delete=models.CASCADE)
    esercizio = models.IntegerField()
    voce = models.ForeignKey(VoceSpesa, on_delete=models.PROTECT)
    tipo = models.CharField(max_length=10)
    numero = models.IntegerField()
    stato = models.CharField(max_length=3)
    riferimenti = models.TextField()
    descrizione = models.TextField()
    cdrSrc = models.CharField(max_length=30)
    cdrDst = models.CharField(max_length=30)
    importo = models.FloatField(default=0.0)
    data = models.DateField()

    def __str__(self):
        return "Variazione GAE {0!s} Voce {1!s} Importo {2:.2f}".format(self.gae.name, self.voce.voce, self.importo)

    class Meta:
        ordering = ["gae", "data"]
        constraints = [
            models.UniqueConstraint(fields=['gae', 'data', 'numero', 'voce'], name="%(app_label)s_%(class)s_unique"),
        ]


class Impegno(models.Model):
    gae = models.ForeignKey(GAE, on_delete=models.CASCADE)
    esercizio = models.IntegerField()
    esercizio_orig = models.IntegerField()
    numero = models.BigIntegerField()
    description = models.CharField(max_length=300)
    voce = models.ForeignKey(VoceSpesa, on_delete=models.PROTECT)
    im_competenza = models.FloatField(default=0.0)
    im_residui = models.FloatField(default=0.0)
    doc_competenza = models.FloatField(default=0.0)
    doc_residui = models.FloatField(default=0.0)
    pagato_competenza = models.FloatField(default=0.0)
    pagato_residui = models.FloatField(default=0.0)

    def __str__(self):
        return "{0:d}/{1:d}: {2:s} (Totale: {3:.2f} Pagato: {4:.2f}".format(self.numero, self.esercizio_orig, self.description, self.im_competenza+self.im_residui, self.pagato_competenza+self.pagato_residui)

    class Meta:
        ordering = ['gae', 'esercizio_orig', 'numero']
        constraints = [
            models.UniqueConstraint(fields=['esercizio_orig', 'numero', 'esercizio'], name="%(app_label)s_%(class)s_unique"),
        ]


class Mandato(models.Model):
    impegno = models.ForeignKey(Impegno, on_delete=models.CASCADE)
    numero = models.IntegerField()
    description = models.CharField(max_length=300)
    id_terzo = models.IntegerField()
    terzo = models.CharField(max_length=200)
    importo = models.FloatField()
    data = models.DateField(null=True, blank=True)

    def __str__(self):
        return "{0:d} ({1:d}): {2:s} [€ {3:.2f}]".format(self.numero, self.impegno.esercizio, self.terzo, self.importo)

    class Meta:
        ordering = ['impegno', 'data']
        constraints = [
            models.UniqueConstraint(fields=['impegno', 'numero', ], name="%(app_label)s_%(class)s_unique"),
        ]
