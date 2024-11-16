from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from allauth.socialaccount.models import SocialAccount

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]
    #metoda pentru a prelua informatii despre utilizator
    def get(self, request):
        user = request.user
        social_account = SocialAccount.objects.filter(user=user).first()

        if social_account:
            return Response({
                'message': f"Autentificarea cu contul social ({social_account.provider.capitalize()}) a reușit!"
            }, status=200)
        else:
            return Response({
                'email': user.email
            }, status=200)
