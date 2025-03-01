from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
import logging

logger = logging.getLogger(__name__)

class UserProfileView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        logger.info(f"🔹 Autentificare utilizator: ID={user.id} | Email={user.email} | CNP={getattr(user, 'cnp', None)}")

        if not user.is_active:
            return Response({"detail": "Utilizatorul nu este activ."}, status=403)

        # Dacă utilizatorul s-a logat cu email și parolă (nu are CNP)
        if not hasattr(user, 'cnp') or not user.cnp:
            return Response({
                'email': user.email
            }, status=200)

        # Dacă utilizatorul s-a logat cu buletinul (are CNP și este verificat)
        if hasattr(user, 'cnp') and user.is_verified_by_id:
            return Response({
                'cnp': user.cnp,
                'first_name': user.first_name,
                'last_name': user.last_name
            }, status=200)

        # În orice alt caz, returnăm 403
        return Response({"detail": "Acces interzis."}, status=403)
