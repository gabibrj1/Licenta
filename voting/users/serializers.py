from rest_framework import serializers
from .models import User

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)  # Parola este optionala pentru buletin
    cnp = serializers.CharField(required=False, allow_blank=True)  # CNP-ul este optional

    class Meta:
        model = User
        #lista campurilor din modelul User care vor fi serializate --> incluse in API
        fields = ['email', 'first_name', 'last_name', 'password', 'cnp', 'series', 'number', 'place_of_birth', 'address', 'issuing_authority', 'sex', 'date_of_issue', 'date_of_expiry']

    def validate(self, data):
        """ 
        Functia de validare care asigura ca fie email ul; fie cnp ul sunt furnizate;
        iar aceste date sunt unice pentru fiecare utilizator
        """
        email = data.get('email', None)
        cnp = data.get('cnp', None)
        
        # validam ca exista fie email, fie cnp
        if not email and not cnp:
            raise serializers.ValidationError("Trebuie să furnizați fie un email, fie un CNP.")

        # verif unicitatea email-ului daca este furnizat
        if email and User.objects.filter(email=email).exists():
            raise serializers.ValidationError({"email": "Acest email este deja inregistrat. Te rugam sa te autentifici!"})

        # verif unicitatea CNP-ului daca este furnizat
        if cnp and User.objects.filter(cnp=cnp).exists():
            raise serializers.ValidationError("Acest CNP este deja înregistrat.")

        return data

    def create(self, validated_data):
        """
        Crreaza un obiect User nou cu datele validate --> in cazul inreg prin mail
        parola este setata si utiliz este inactiv pana la verif
        """
        #Construim obiectul utilizatorului folosind doar datele necesare din validated_data
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

        # setam parola doar daca este furnizată (cazul inregistrarii prin email)
        if 'password' in validated_data:
            user.set_password(validated_data['password'])

        # utiliza este inactiv pana la verificare
        user.is_active = False
        user.save()
        return user
