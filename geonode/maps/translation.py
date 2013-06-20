from modeltranslation.translator import translator, TranslationOptions
from geonode.maps.models import Map
from geonode.maps.models import MapLayer

class MapTranslationOptions(TranslationOptions):
    fields = ('title', 'abstract', 'purpose',)

translator.register(Map, MapTranslationOptions)
