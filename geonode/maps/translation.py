from modeltranslation.translator import translator, TranslationOptions
from geonode.maps.models import Map
from geonode.maps.models import MapLayer

class MapTranslationOptions(TranslationOptions):
    fields = ('title', 'abstract', 'purpose', 'keywords_region', 'constraints_use',
                'constraints_other', 'language', 'topic_category', 'supplemental_information', 'distribution_description',
                'data_quality_statement', 'csw_typename', 'csw_anytext', 'projection',)

translator.register(Map, MapTranslationOptions)
