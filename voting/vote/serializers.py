from rest_framework import serializers
from .models import VoteSystem, VoteOption, VoteCast

class VoteOptionSerializer(serializers.ModelSerializer):
    votes_count = serializers.SerializerMethodField()
    
    class Meta:
        model = VoteOption
        fields = ['id', 'title', 'description', 'image_url', 'order', 'votes_count']
    
    def get_votes_count(self, obj):
        return obj.votes.count()


class VoteSystemSerializer(serializers.ModelSerializer):
    options = VoteOptionSerializer(many=True, read_only=True)
    total_votes = serializers.SerializerMethodField()
    
    class Meta:
        model = VoteSystem
        fields = ['id', 'name', 'description', 'category', 'created_at', 'start_date', 
                  'end_date', 'status', 'rules', 'options', 'total_votes']
    
    def get_total_votes(self, obj):
        return VoteCast.objects.filter(vote_system=obj).count()


class CreateVoteSystemSerializer(serializers.ModelSerializer):
    options = serializers.ListField(write_only=True)
    
    class Meta:
        model = VoteSystem
        fields = ['name', 'description', 'category', 'start_date', 'end_date', 'rules', 'options']
    
    def create(self, validated_data):
        options_data = validated_data.pop('options')
        
        # Creăm sistemul de vot
        vote_system = VoteSystem.objects.create(**validated_data)
        
        # Creăm opțiunile de vot
        for i, option_data in enumerate(options_data):
            VoteOption.objects.create(
                vote_system=vote_system,
                title=option_data.get('title', ''),
                description=option_data.get('description', ''),
                image_url=option_data.get('image_url', ''),
                order=i
            )
        
        return vote_system
    
    def update(self, instance, validated_data):
        options_data = validated_data.pop('options', None)
        
        # Actualizăm câmpurile sistemului de vot
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Dacă avem opțiuni noi, le actualizăm
        if options_data:
            # Ștergem opțiunile vechi
            instance.options.all().delete()
            
            # Creăm opțiunile noi
            for i, option_data in enumerate(options_data):
                VoteOption.objects.create(
                    vote_system=instance,
                    title=option_data.get('title', ''),
                    description=option_data.get('description', ''),
                    image_url=option_data.get('image_url', ''),
                    order=i
                )
        
        return instance


class VoteCastSerializer(serializers.ModelSerializer):
    class Meta:
        model = VoteCast
        fields = ['id', 'vote_system', 'option', 'vote_datetime']