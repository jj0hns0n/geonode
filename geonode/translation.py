from modeltranslation.translator import translator, TranslationOptions
from layers.models import Layer

class LayerTranslationOptions(TranslationOptions):
	fields = ('abstract','purpose',)

translator.register(Layer,LayerTranslationOptions)

