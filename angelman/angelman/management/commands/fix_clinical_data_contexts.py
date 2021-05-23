from collections import defaultdict
import multiprocessing
import sys

from django import db
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from tqdm import tqdm
from rdrf.models.definition.models import RDRFContext, Registry, ClinicalData, ContextFormGroupItem
from rdrf.db.contexts_api import RDRFContextManager
from rdrf.db.dynamic_data import DynamicDataWrapper
from registry.patients.models import Patient

import logging

logger = logging.getLogger(__name__)


def calculate_progress(args):
    registry_code, patient, context = args
    dyn_patient = DynamicDataWrapper(patient, rdrf_context_id=context.id)
    dyn_patient.save_form_progress(registry_code, context_model=context)


class Command(BaseCommand):
    help = """Fixes imported clinical data entries which do not have the context_id field set.
              Also computes form progress for fixed cdes collections"""

    def add_arguments(self, parser):
        parser.add_argument("registry_code")
        parser.add_argument("processes")

    def handle(self, registry_code, processes, **options):
        self.registry_model = None
        self.processes = int(processes)
        try:
            self.registry_model = Registry.objects.get(code=registry_code)
        except Registry.DoesNotExist:
            self.stderr.write("Error: Unknown registry code: %s" %
                              registry_code)
            sys.exit(1)
            return

        if self.registry_model is not None:
            self._fix_entries()
            self.stdout.write("Done")

    def _fix_entries(self):
        reg_code = self.registry_model.code
        context_mgr = RDRFContextManager(self.registry_model)
        cd_models = (
            ClinicalData.objects.filter(
                registry_code=reg_code, django_model='Patient',
                context_id__isnull=True
            ).order_by('-id'))
        self.stdout.write(f"Found {cd_models.count()} entries to fix")
        cfgs_map = {}
        for cfg in ContextFormGroupItem.objects.filter(registry_form__registry=self.registry_model):
            cfgs_map[cfg.registry_form.name] = cfg.context_form_group.id
        self.stdout.write(f"CFGs map={cfgs_map}")
        patients_and_contexts = defaultdict(list)
        with_default_contexts_created = set()
        for entry in tqdm(cd_models, desc="Creating contexts"):
            if entry.collection == "cdes":
                form_names = [f["name"] for f in entry.data["forms"]]
            elif entry.collection == "history":
                form_names = [f["name"] for f in entry.data["record"]["forms"]]
            else:
                continue
            cfgs = list(set(cfgs_map[f] for f in form_names if f in cfgs_map))
            # self.stdout.write(f"CFGs={cfgs}")
            if len(cfgs) == 0:
                continue
            patient_id = entry.django_id
            patient = Patient.objects.filter(pk=patient_id).first()
            if patient:
                if patient_id not in with_default_contexts_created:
                    # Ensure all fixed context are created
                    context_mgr.get_or_create_default_context(patient)
                    with_default_contexts_created.add(patient_id)

                content_type = ContentType.objects.get_for_model(patient)
                context = RDRFContext.objects.filter(registry=self.registry_model,
                                                     content_type=content_type,
                                                     object_id=patient_id,
                                                     context_form_group_id=cfgs[0]).first()
                if not context:
                    logger.info(f"Created new context for patient {patient_id} and context form group {cfgs[0]}")
                    context = RDRFContext.objects.create(registry=self.registry_model,
                                                         content_type=content_type,
                                                         object_id=patient_id,
                                                         context_form_group_id=cfgs[0])

                entry.data["context_id"] = context.id
                entry.context_id = context.id
                entry.save()
                if entry.collection == "cdes":
                    patients_and_contexts[patient].append(context)

        self.stdout.write("Creating default contexts for remaining patients")
        for patient in tqdm(Patient.objects.all(), desc="Creating contexts"):
            context_mgr.get_or_create_default_context(patient)

        self.stdout.write("Calculating form progress...")
        seen = set()
        args = []
        for patient, contexts in patients_and_contexts.items():
            for c in contexts:
                if (patient.id, c.id) in seen:
                    continue
                args.append((self.registry_model.code, patient, c))
                seen.add((patient.id, c.id))

        db.connections.close_all()
        with multiprocessing.Pool(processes=self.processes) as pool:
            for _ in tqdm(pool.imap(calculate_progress, args), desc="Calculating progress", total=len(args)):
                pass
