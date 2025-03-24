from django.core.management.base import BaseCommand
from vote.models import VotingSection, LocalCandidate

class Command(BaseCommand):
    help = 'Populează baza de date cu secții de vot și candidați locali de test'
    
    def handle(self, *args, **kwargs):
        # Adaugă secții de vot
        self.stdout.write('Adăugare secții de vot...')
        
        sections = [
            {
                'section_id': 'BUC-001',
                'name': 'Școala Gimnazială nr. 5',
                'address': 'Str. Academiei nr. 35',
                'city': 'București',
                'county': 'București'
            },
            {
                'section_id': 'BUC-002',
                'name': 'Liceul Teoretic "Ion Creangă"',
                'address': 'Str. C.A. Rosetti nr. 14',
                'city': 'București',
                'county': 'București'
            },
            {
                'section_id': 'CJ-001',
                'name': 'Colegiul Național "Emil Racoviță"',
                'address': 'Str. Mihail Kogălniceanu nr. 9',
                'city': 'Cluj-Napoca',
                'county': 'Cluj'
            },
            {
                'section_id': 'TM-001',
                'name': 'Universitatea de Vest',
                'address': 'Bd. Vasile Pârvan nr. 4',
                'city': 'Timișoara',
                'county': 'Timiș'
            },
            {
                'section_id': 'IS-001',
                'name': 'Colegiul Național "Mihai Eminescu"',
                'address': 'Str. Mihail Kogălniceanu nr. 10',
                'city': 'Iași',
                'county': 'Iași'
            }
        ]
        
        for section_data in sections:
            voting_section, created = VotingSection.objects.get_or_create(
                section_id=section_data['section_id'],
                defaults=section_data
            )
            if created:
                self.stdout.write(f'  Adăugat: {voting_section}')
            else:
                self.stdout.write(f'  Existent: {voting_section}')
        
        # Adaugă candidați locali
        self.stdout.write('\nAdăugare candidați locali...')
        
        candidates = [
            # București - Primari
            {
                'name': 'Mihai Popescu',
                'party': 'Partidul Social Democrat',
                'position': 'mayor',
                'county': 'București',
                'city': 'București',
                'photo_url': 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?ixlib=rb-1.2.1&auto=format&fit=crop&w=256&q=80'
            },
            {
                'name': 'Alexandra Ionescu',
                'party': 'Partidul Național Liberal',
                'position': 'mayor',
                'county': 'București',
                'city': 'București',
                'photo_url': 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?ixlib=rb-1.2.1&auto=format&fit=crop&w=256&q=80'
            },
            {
                'name': 'Dan Vasilescu',
                'party': 'Alianța USR PLUS',
                'position': 'mayor',
                'county': 'București',
                'city': 'București',
                'photo_url': 'https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?ixlib=rb-1.2.1&auto=format&fit=crop&w=256&q=80'
            },
            
            # București - Consilieri Locali
            {
                'name': 'Elena Dumitrescu',
                'party': 'Partidul Social Democrat',
                'position': 'councilor',
                'county': 'București',
                'city': 'București',
                'photo_url': 'https://images.unsplash.com/photo-1546961329-78bef0414d7c?ixlib=rb-1.2.1&auto=format&fit=crop&w=256&q=80'
            },
            {
                'name': 'George Stanciu',
                'party': 'Partidul Național Liberal',
                'position': 'councilor',
                'county': 'București',
                'city': 'București',
                'photo_url': 'https://images.unsplash.com/photo-1499996860823-5214fcc65f8f?ixlib=rb-1.2.1&auto=format&fit=crop&w=256&q=80'
            },
            
            # Cluj - Primari
            {
                'name': 'Radu Mureșan',
                'party': 'Uniunea Democrată Maghiară din România',
                'position': 'mayor',
                'county': 'Cluj',
                'city': 'Cluj-Napoca',
                'photo_url': 'https://images.unsplash.com/photo-1542909168-82c3e7fdca5c?ixlib=rb-1.2.1&auto=format&fit=crop&w=256&q=80'
            },
            {
                'name': 'Ana Moldovan',
                'party': 'Partidul Național Liberal',
                'position': 'mayor',
                'county': 'Cluj',
                'city': 'Cluj-Napoca',
                'photo_url': 'https://images.unsplash.com/photo-1554151228-14d9def656e4?ixlib=rb-1.2.1&auto=format&fit=crop&w=256&q=80'
            },
            
            # Cluj - Președinte Consiliu Județean
            {
                'name': 'Marius Pop',
                'party': 'Partidul Social Democrat',
                'position': 'county_president',
                'county': 'Cluj',
                'city': 'Cluj-Napoca',
                'photo_url': 'https://images.unsplash.com/photo-1545167622-3a6ac756afa4?ixlib=rb-1.2.1&auto=format&fit=crop&w=256&q=80'
            }
        ]
        
        for candidate_data in candidates:
            candidate, created = LocalCandidate.objects.get_or_create(
                name=candidate_data['name'],
                party=candidate_data['party'],
                position=candidate_data['position'],
                county=candidate_data['county'],
                defaults=candidate_data
            )
            if created:
                self.stdout.write(f'  Adăugat: {candidate}')
            else:
                self.stdout.write(f'  Existent: {candidate}')
                
        self.stdout.write(self.style.SUCCESS('Populare finalizată cu succes!'))