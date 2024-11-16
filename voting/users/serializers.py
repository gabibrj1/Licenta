from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User

#serializer pentru modeulul User
class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)  # Parola este optionala pentru buletin
    cnp = serializers.CharField(required=False, allow_blank=True)  # CNP-ul este optional

    class Meta:
        model = User
        fields = [
            'email', 'first_name', 'last_name', 'password', 'cnp', 'series', 
            'number', 'place_of_birth', 'address', 'issuing_authority', 
            'sex', 'date_of_issue', 'date_of_expiry'
        ]

    def validate(self, data):
        """
        Validare pentru a asigura unicitatea email-ului sau CNP-ului
        """
        email = data.get('email', None)
        cnp = data.get('cnp', None)

        if not email and not cnp:
            raise serializers.ValidationError("Trebuie sa furnizati fie un email, fie un CNP.")

        if email and User.objects.filter(email=email).exists():
            raise serializers.ValidationError({"email": "Acest email este deja inregistrat. Te rugam sa te autentifici!"})

        if cnp and User.objects.filter(cnp=cnp).exists():
            raise serializers.ValidationError("Acest CNP este deja inregistrat.")

        return data

    def create(self, validated_data):
        """
        creeaza un nou utilizator. seteaza parola daca este furnizata.
        """
        #crearea unui utiliz cu datele validate
        user = User(
            email=validated_data.get('email', ''),
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            cnp=validated_data.get('cnp', None) if validated_data.get('cnp') else None,
            series=validated_data.get('series', ''),
            number=validated_data.get('number', ''),
            place_of_birth=validated_data.get('place_of_birth', ''),
            address=validated_data.get('address', ''),
            issuing_authority=validated_data.get('issuing_authority', ''),
            sex=validated_data.get('sex', ''),
            date_of_issue=validated_data.get('date_of_issue', None),
            date_of_expiry=validated_data.get('date_of_expiry', None)
        )

        if 'password' in validated_data:
            user.set_password(validated_data['password'])

        #seteaza utiliz inactiv pana la verificare
        user.is_active = False
        user.save()
        return user

#serializer pt autentificare
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        """
        valideaza datele pentru autentificare, returneaza token-ul JWT la succes.
        """
        email = data.get('email')
        password = data.get('password')

        try:
            #gaseste utilizatorii dupa email
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("Autentificare eșuată. Verificați email-ul și parola.")

        if not user.check_password(password):
            raise serializers.ValidationError("Autentificare eșuată. Verificați email-ul și parola.")

        if not user.is_active:
            raise serializers.ValidationError("Contul nu este activ. Vă rugăm să verificați email-ul.")
        
        return {
            'email': user.email,
            'tokens': self.get_tokens_for_user(user)
        }

    @staticmethod
    def get_tokens_for_user(user):
        """
        Genereaza token-uri JWT pentru utilizator.
        """
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
