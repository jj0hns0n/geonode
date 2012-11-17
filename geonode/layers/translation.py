from modeltranslation.translator import translator, TranslationOptions
from geonode.layers.models import Layer
from geonode.layers.models import TopicCategory

class LayerTranslationOptions(TranslationOptions):
    fields = ('title','abstract','purpose','keywords_region','constraints_use',
'constraints_other','language','supplemental_information','distribution_description',
'data_quality_statement','csw_anytext','topic_category','name','typename',)

class TopicCategoryTranslationOptions(TranslationOptions):
    fields = ('description',)

translator.register(Layer, LayerTranslationOptions)
translator.register(TopicCategory, TopicCategoryTranslationOptions)


