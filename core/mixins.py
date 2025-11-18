class TitleContextMixin:
    """
    Mixin genérico para añadir títulos a las vistas.
    Puede usarse en cualquier vista basada en clases.
    """
    title1 = None
    title2 = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.title1:
            context["title1"] = self.title1
        if self.title2:
            context["title2"] = self.title2
        return context
