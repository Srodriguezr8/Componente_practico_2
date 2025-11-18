from django.db.models import Q

class SearchQuerysetMixin:
    """Mixin genérico para filtrar listas por campos definidos."""
    search_fields = [] 

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get('q', '')
        if query and self.search_fields:
            conditions = Q()
            for field in self.search_fields:
                conditions |= Q(**{f"{field}__icontains": query})
            queryset = queryset.filter(conditions)
        return queryset
