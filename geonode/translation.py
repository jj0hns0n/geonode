from modeltranslation.translator import translator, TranslationOptions
from layers.models import layer

class LayerTranslationOptions(TranslationOptions):
	fields = ('name','typename','workplace','store','storetype')

translator.register(layer,LayerTranslationOptions)

