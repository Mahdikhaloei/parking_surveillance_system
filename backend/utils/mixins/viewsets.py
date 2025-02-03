from rest_framework.generics import get_object_or_404
from rest_framework.viewsets import GenericViewSet


class MultipleFieldLookupMixin(GenericViewSet):
    """Apply this mixin to any view or viewset to get multiple field filtering
    based on a `lookup_fields` attribute, instead of the default single field filtering.
    """
    lookup_fields: list[str] = []

    def get_object(self):
        queryset = self.get_queryset()
        queryset = self.filter_queryset(queryset)
        filters = {}
        for field in self.lookup_fields:
            if self.kwargs[field]:
                filters[field] = self.kwargs[field]
        obj = get_object_or_404(queryset, **filters)
        self.check_object_permissions(self.request, obj)
        return obj
