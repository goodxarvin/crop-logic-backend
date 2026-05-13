from rest_framework.generics import ListAPIView
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from . import serializers
from ..models import Province, City, Address

class ProvinceListAPIView(ListAPIView):
    serializer_class = serializers.ProvinceSerializer
    queryset = Province.objects.all()

    # def get(self, request, *args, **kwargs):
    #     return Response()


class CityListAPIView(ListAPIView):
    serializer_class = serializers.CitySerializer

    def get_queryset(self):
        province_id = self.kwargs["province_pk"]
        return City.objects.filter(province_id=province_id)



class AddressViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated,]
    serializer_class = serializers.AddressSerializer
    
    def get_queryset(self):
        user_id = self.request.user.id
        return Address.objects.filter(user_id=user_id)

    def perform_create(self, serializer):
        serializer.save(
            user=self.request.user
        )