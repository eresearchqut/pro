from operator import attrgetter
import pycountry
from django.forms import CharField, ChoiceField, DateField, BooleanField
from django.forms.widgets import RadioSelect, Select
from django.utils.translation import gettext as _

from registration.forms import RegistrationForm
from rdrf.helpers.utils import get_preferred_languages
from registry.patients.models import Patient


def _tuple(code, name):
    return code, _(name)


def _countries():
    countries = sorted(pycountry.countries, key=attrgetter('name'))
    result = [_tuple("", "Country")]
    return result + [_tuple(c.alpha_2, c.name) for c in countries]


def _preferred_languages():
    languages = get_preferred_languages()
    return [_tuple(lang.code, lang.name) for lang in languages] if languages else [_tuple('en', 'English')]


class ANGPatientRegistrationForm(RegistrationForm):

    placeholders = {
        'username': _("Username"),
        'password1': _("Password"),
        'password2': _("Repeat Password"),
        'first_name': _("Given Names"),
        'surname': _("Surname"),
        'date_of_birth': _("Date of Birth"),
        'address': _("Address"),
        'suburb': _("Suburb / Town"),
        'state': _("State / County / Province / Region"),
        'postcode': _("Zip / Postal Code"),
        'phone_number': _('Phone Number')
    }

    no_placeholder_fields = ['gender']

    country_choices = _countries()

    language_choices = _preferred_languages()

    password_fields = ['password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if field not in self.no_placeholder_fields:
                self.fields[field].widget.attrs['class'] = 'form-control'
                self.fields[field].widget.attrs['placeholder'] = self.placeholders.get(field, _(''))
            if field in self.password_fields:
                self.fields[field].widget.render_value = True

    preferred_languages = ChoiceField(required=False, choices=language_choices)
    first_name = CharField(required=True, max_length=30)
    surname = CharField(required=True, max_length=30)
    date_of_birth = DateField(required=True)
    gender = ChoiceField(choices=Patient.SEX_CHOICES, widget=RadioSelect, required=True)
    address = CharField(required=True, max_length=100)
    suburb = CharField(required=True, max_length=30)
    country = ChoiceField(required=True, widget=Select, choices=country_choices, initial="")
    state = CharField(required=True, widget=Select)
    postcode = CharField(required=True, max_length=30)
    phone_number = CharField(required=True, max_length=30)
    registry_code = CharField(required=True)


class ANGRegistrationForm(ANGPatientRegistrationForm):

    ANGPatientRegistrationForm.placeholders.update({
        'parent_guardian_first_name': _("Parent/Guardian Given Names"),
        'parent_guardian_last_name': _("Parent/Guardian Surname"),
        'parent_guardian_date_of_birth': _("Parent/Guardian Date of Birth"),
        'parent_guardian_gender': _("Parent/Guardian gender"),
        'parent_guardian_address': _("Parent/Guardian Address"),
        'parent_guardian_suburb': _("Parent/Guardian Suburb / Town"),
        'parent_guardian_state': _("Parent/Guardian State / County / Province / Region"),
        'parent_guardian_postcode': _("Parent/Guardian Zip / Postal Code"),
        'parent_guardian_phone': _('Parent/Guardian Phone Number')
    })

    ANGPatientRegistrationForm.no_placeholder_fields.extend(['parent_guardian_gender', 'same_address'])

    tooltip_info = {
        'parent_guardian_address': _("Please enter an address through which we can contact you"),
        'parent_guardian_phone': _('''Please enter a phone number through which we can contact you,
                                      including the country code (e.g. +61 for Australia)''')
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field, tooltip in self.tooltip_info.items():
            self.fields[field].widget.attrs['data-toggle'] = 'tooltip'
            self.fields[field].widget.attrs['data-placement'] = 'left'
            self.fields[field].widget.attrs['title'] = tooltip

    parent_guardian_first_name = CharField(required=True)
    parent_guardian_last_name = CharField(required=True)
    parent_guardian_date_of_birth = DateField(required=True)
    parent_guardian_gender = ChoiceField(choices=Patient.SEX_CHOICES, widget=RadioSelect, required=True)
    parent_guardian_address = CharField(required=True, max_length=100)
    parent_guardian_suburb = CharField(required=True, max_length=30)
    parent_guardian_country = ChoiceField(required=True, widget=Select, choices=ANGPatientRegistrationForm.country_choices,
                                          initial="-1")
    parent_guardian_state = CharField(required=False, widget=Select, max_length=30)
    parent_guardian_postcode = CharField(required=True, max_length=30)
    parent_guardian_phone = CharField(required=True, max_length=30)
    same_address = BooleanField(required=False)

    def _clean_fields(self):
        base_required_fields = ['address', 'suburb', 'country', 'state', 'postcode', 'phone_number']
        if self.data.get('same_address', False):
            for f in base_required_fields:
                self.fields[f].required = False
        super()._clean_fields()
