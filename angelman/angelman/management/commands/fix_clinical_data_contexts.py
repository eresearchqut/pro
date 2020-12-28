from collections import defaultdict
import re
import sys

from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from rdrf.models.definition.models import RDRFContext, Registry, ClinicalData, ContextFormGroupItem
from registry.patients.models import Patient


class Command(BaseCommand):
    help = "Fixes imported clinical data entries which do not have the context_id field set"

    def add_arguments(self, parser):
        parser.add_argument("registry_code")

    def handle(self, registry_code, **options):
        self.registry_model = None
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
        cd_models = (
            ClinicalData.objects.filter(
                registry_code=reg_code, django_model='Patient',
                context_id__isnull=True
            ).order_by('-id').values('id', 'django_id', 'collection', 'data'))
        self.stdout.write(f"Found {cd_models.count()} entries to fix")
        result = defaultdict(list)
        data_dict = {}
        cfgs_map = {}
        for cfg in ContextFormGroupItem.objects.filter(registry_form__registry=self.registry_model):
            cfgs_map[cfg.registry_form.name] = cfg.context_form_group.id
        print(f"CFGs map={cfgs_map}")
        for entry in cd_models:
            if entry["collection"] != "progress":
                form_names = [f["name"] for f in entry["data"]["forms"]]
                print(f"Forms={form_names}")
            else:
                data = entry["data"]
                for k, v in data.items():
                    if v and k.endswith("form_current"):
                        search_result = re.search('(.+)_form_current', k)
                        if search_result:
                            form_names = [search_result.groups()[0]]
                print(f"Progress forms={form_names}")

            cfgs = list(set(cfgs_map[f] for f in form_names if f in cfgs_map))
            print(f"CFGs={cfgs}")
            patient_id = entry["django_id"]
            patient = Patient.objects.filter(pk=patient_id).first()
            if patient:
                content_type = ContentType.objects.get_for_model(patient)
                context = RDRFContext.objects.filter(registry=self.registry_model,
                                                     content_type=content_type,
                                                     object_id=patient_id,
                                                     context_form_group_id=cfgs[0]).first()
                if not context:
                    context = RDRFContext.objects.create(registry=self.registry_model,
                                                         content_type=content_type,
                                                         object_id=patient_id,
                                                         context_form_group_id=cfgs[0])

                result[context.id].append(entry['id'])
                data = entry["data"]
                data["context_id"] = context.id
                data_dict[entry['id']] = data

        for context_id, ids in result.items():
            ClinicalData.objects.filter(pk__in=ids).update(context_id=context_id)
        for entry_id, data in data_dict.items():
            ClinicalData.objects.filter(pk=entry_id).update(data=data)
