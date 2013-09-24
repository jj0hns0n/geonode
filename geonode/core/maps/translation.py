from modeltranslation.translator import translator, TranslationOptions
from geonode.core.maps.models import Map
from geonode.core.maps.models import MapLayer

class MapTranslationOptions(TranslationOptions):
    fields = ('title', 'abstract', 'purpose',)

translator.register(Map, MapTranslationOptions)
