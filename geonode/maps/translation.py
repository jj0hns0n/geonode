from modeltranslation.translator import translator, TranslationOptions
from geonode.maps.models import Map
from geonode.maps.models import MapLayer

class MapTranslationOptions(TranslationOptions):
    fields = ('title', 'abstract', 'purpose', 'keywords_region', 'constraints_use',
    'constraints_other', 'language', 'topic_category', 'supplemental_information', 'distribution_description',
    'data_quality_statement', 'csw_typename', 'csw_anytext', 'projection',)

class MapLayerTranslationOptions(TranslationOptions):
    fields = ('name', 'layer_params', 'source_params',)

translator.register(Map, MapTranslationOptions)
translator.register(MapLayer, MapLayerTranslationOptions)

