import autocomplete_light
from models import Group 

autocomplete_light.register(Group,
    search_fields=['^name',],
    autocomplete_js_attributes={'placeholder': 'Group Name ..',},
)
