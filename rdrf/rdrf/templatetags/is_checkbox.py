from django import template
from django.forms import CheckboxInput

register = template.Library()

@register.filter(name='is_checkbox')
def is_checkbox(field):
    if (field.field.widget.__class__.__name__ == CheckboxInput().__class__.__name__):
        return True
    return False
