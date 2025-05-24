from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime
import csv
import os
from prezenta.models import VotingPresence, PresenceSummary
from django.db import transaction
from django.db.models import Sum
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Populează datele de prezență din fișierul CSV'

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv-file',
            type=str,
            default=r'C:\Users\brj\Desktop\voting\data\presence_2025-05-18_21-00.csv',
            help='Calea către fișierul CSV'
        )
        parser.add_argument(
            '--vote-type',
            type=str,
            default='prezidentiale',
            help='Tipul de vot (prezidentiale, prezidentiale_tur2, parlamentare, locale)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Șterge datele existente înainte de populare'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=1000,
            help='Numărul de înregistrări procesate într-un batch'
        )

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        vote_type = options['vote_type']
        batch_size = options['batch_size']
        
        if not os.path.exists(csv_file):
            self.stdout.write(self.style.ERROR(f'Fișierul {csv_file} nu există!'))
            return
        
        file_size = os.path.getsize(csv_file) / (1024 * 1024)
        self.stdout.write(f'Procesez fișierul: {csv_file}')
        self.stdout.write(f'Dimensiune fișier: {file_size:.2f} MB')
        
        if options['clear']:
            # Șterge datele pentru ambele locații
            deleted_ro = VotingPresence.objects.filter(vote_type=vote_type, location_type='romania').count()
            deleted_str = VotingPresence.objects.filter(vote_type=vote_type, location_type='strainatate').count()
            deleted_sum_ro = PresenceSummary.objects.filter(vote_type=vote_type, location_type='romania').count()
            deleted_sum_str = PresenceSummary.objects.filter(vote_type=vote_type, location_type='strainatate').count()
            
            VotingPresence.objects.filter(vote_type=vote_type).delete()
            PresenceSummary.objects.filter(vote_type=vote_type).delete()
            
            self.stdout.write(self.style.WARNING(
                f'Șterse - România: {deleted_ro} prezență, {deleted_sum_ro} sumare; '
                f'Străinătate: {deleted_str} prezență, {deleted_sum_str} sumare'
            ))
        
        # Data pentru turul 1 prezidențiale
        vote_datetime = timezone.make_aware(datetime(2024, 12, 8, 21, 0, 0))
        
        created_romania = 0
        created_strainatate = 0
        error_count = 0
        
        try:
            with open(csv_file, 'r', encoding='utf-8-sig') as file:
                reader = csv.DictReader(file, delimiter=',')
                column_mapping = self.create_column_mapping(reader.fieldnames)
                
                self.stdout.write(f'Total coloane: {len(reader.fieldnames)}')
                self.stdout.write('Încep procesarea...')
                
                batch_romania = []
                batch_strainatate = []
                
                for row_num, row in enumerate(reader, 1):
                    try:
                        # Determină locația pe baza județului
                        judet = self.clean_string(self.get_column_value(row, column_mapping, 'judet'))
                        
                        if judet == 'SR':
                            # Străinătate - țara este în UAT
                            location_type = 'strainatate'
                            presence_data = self.process_csv_row(row, column_mapping, vote_type, location_type, vote_datetime)
                            if presence_data:
                                batch_strainatate.append(presence_data)
                        else:
                            # România - județele normale
                            location_type = 'romania'
                            presence_data = self.process_csv_row(row, column_mapping, vote_type, location_type, vote_datetime)
                            if presence_data:
                                batch_romania.append(presence_data)
                        
                        # Procesează batch-urile când se ating dimensiunile
                        if len(batch_romania) >= batch_size:
                            created = self.create_batch(batch_romania)
                            created_romania += created
                            batch_romania = []
                        
                        if len(batch_strainatate) >= batch_size:
                            created = self.create_batch(batch_strainatate)
                            created_strainatate += created
                            batch_strainatate = []
                        
                        if (created_romania + created_strainatate) % 5000 == 0:
                            self.stdout.write(f'Procesate {created_romania + created_strainatate} înregistrări...')
                    
                    except Exception as e:
                        error_count += 1
                        if error_count <= 10:
                            self.stdout.write(self.style.WARNING(f'Eroare la rândul {row_num}: {str(e)}'))
                
                # Procesează ultimele batch-uri
                if batch_romania:
                    created_romania += self.create_batch(batch_romania)
                if batch_strainatate:
                    created_strainatate += self.create_batch(batch_strainatate)
            
            self.stdout.write(self.style.SUCCESS(
                f'România: {created_romania} înregistrări | Străinătate: {created_strainatate} înregistrări'
            ))
            
            # Creează sumarele separate
            self.create_county_summaries(vote_type, 'romania', vote_datetime)
            self.create_county_summaries(vote_type, 'strainatate', vote_datetime)
            
            # Afișează statistici finale
            self.show_final_statistics(vote_type, 'romania')
            self.show_final_statistics(vote_type, 'strainatate')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Eroare la procesarea fișierului: {str(e)}'))
            import traceback
            self.stdout.write(traceback.format_exc())
    
    def create_column_mapping(self, fieldnames):
        """Creează maparea coloanelor"""
        mapping = {}
        
        column_aliases = {
            'judet': ['Judet', '\ufeffJudet', 'Județ'],
            'uat': ['UAT'],
            'localitate': ['Localitate'],
            'siruta': ['Siruta'],
            'nr_sectie': ['Nr sectie de votare'],
            'nume_sectie': ['Nume sectie de votare'],
            'mediu': ['Mediu'],
            'inscrisi_permanente': ['Înscriși pe liste permanente'],
            'lp': ['LP'],
            'ls': ['LS'],
            'lsc': ['LSC'],
            'um': ['UM'],
            'lt': ['LT']
        }
        
        for key, aliases in column_aliases.items():
            for alias in aliases:
                if alias in fieldnames:
                    mapping[key] = alias
                    break
        
        # Coloane demografice
        for age in range(18, 121):
            for alias in [f'Barbati {age}', f'Bărbați {age}']:
                if alias in fieldnames:
                    mapping[f'men_{age}'] = alias
                    break
            
            for alias in [f'Femei {age}']:
                if alias in fieldnames:
                    mapping[f'women_{age}'] = alias
                    break
        
        # Grupe de vârstă
        age_groups = {
            'men_18_24': ['Barbati 18-24', 'Bărbați 18-24'],
            'men_25_34': ['Barbati 25-34', 'Bărbați 25-34'],
            'men_35_44': ['Barbati 35-44', 'Bărbați 35-44'],
            'men_45_64': ['Barbati 45-64', 'Bărbați 45-64'],
            'men_65_plus': ['Barbati 65+', 'Bărbați 65+'],
            'women_18_24': ['Femei 18-24'],
            'women_25_34': ['Femei 25-34'],
            'women_35_44': ['Femei 35-44'],
            'women_45_64': ['Femei 45-64'],
            'women_65_plus': ['Femei 65+']
        }
        
        for key, aliases in age_groups.items():
            for alias in aliases:
                if alias in fieldnames:
                    mapping[key] = alias
                    break
        
        return mapping
    
    def get_column_value(self, row, column_mapping, key):
        """Obține valoarea unei coloane"""
        if key in column_mapping:
            return row.get(column_mapping[key], '')
        return ''
    
    def process_csv_row(self, row, column_mapping, vote_type, location_type, vote_datetime):
        """Procesează un rând din CSV"""
        
        judet_raw = self.clean_string(self.get_column_value(row, column_mapping, 'judet'))
        uat = self.clean_string(self.get_column_value(row, column_mapping, 'uat'))
        
        # Pentru străinătate (SR), țara este în UAT
        if location_type == 'strainatate':
            county = uat if uat else 'Necunoscut'  # Țara este în UAT
        else:
            county = judet_raw  # Pentru România, județul normal
        
        if not county:
            return None
        
        locality = self.clean_string(self.get_column_value(row, column_mapping, 'localitate'))
        siruta = self.clean_string(self.get_column_value(row, column_mapping, 'siruta'))
        section_number = self.safe_int(self.get_column_value(row, column_mapping, 'nr_sectie'))
        section_name = self.clean_string(self.get_column_value(row, column_mapping, 'nume_sectie'))
        
        mediu_raw = self.clean_string(self.get_column_value(row, column_mapping, 'mediu')).lower()
        environment = 'urban' if mediu_raw in ['urban', 'urbană', 'u'] else 'rural'
        
        # Date despre înscriși și votanți
        registered_permanent = self.safe_int(self.get_column_value(row, column_mapping, 'inscrisi_permanente'))
        voters_permanent = self.safe_int(self.get_column_value(row, column_mapping, 'lp'))
        voters_supplementary = self.safe_int(self.get_column_value(row, column_mapping, 'ls'))
        voters_mobile = self.safe_int(self.get_column_value(row, column_mapping, 'um'))
        
        # Pentru străinătate, LSC este "liste de corespondență"
        voters_correspondence = self.safe_int(self.get_column_value(row, column_mapping, 'lsc'))
        
        # Date demografice
        men_18_24 = self.safe_int(self.get_column_value(row, column_mapping, 'men_18_24'))
        men_25_34 = self.safe_int(self.get_column_value(row, column_mapping, 'men_25_34'))
        men_35_44 = self.safe_int(self.get_column_value(row, column_mapping, 'men_35_44'))
        men_45_64 = self.safe_int(self.get_column_value(row, column_mapping, 'men_45_64'))
        men_65_plus = self.safe_int(self.get_column_value(row, column_mapping, 'men_65_plus'))
        
        women_18_24 = self.safe_int(self.get_column_value(row, column_mapping, 'women_18_24'))
        women_25_34 = self.safe_int(self.get_column_value(row, column_mapping, 'women_25_34'))
        women_35_44 = self.safe_int(self.get_column_value(row, column_mapping, 'women_35_44'))
        women_45_64 = self.safe_int(self.get_column_value(row, column_mapping, 'women_45_64'))
        women_65_plus = self.safe_int(self.get_column_value(row, column_mapping, 'women_65_plus'))
        
        # Date demografice detaliate
        demographic_data = {}
        for age in range(18, 121):
            men_value = self.safe_int(self.get_column_value(row, column_mapping, f'men_{age}'))
            women_value = self.safe_int(self.get_column_value(row, column_mapping, f'women_{age}'))
            
            if men_value > 0:
                demographic_data[f'men_{age}'] = men_value
            if women_value > 0:
                demographic_data[f'women_{age}'] = women_value
        
        # Pentru străinătate, adaugă și datele de corespondență în demographic_data
        if location_type == 'strainatate':
            demographic_data['voters_correspondence'] = voters_correspondence
        
        return {
            'county': county,
            'uat': uat if location_type == 'romania' else locality,  # Pentru străinătate păstrează localitatea
            'locality': locality,
            'siruta': siruta,
            'section_number': section_number,
            'section_name': section_name,
            'environment': environment,
            'vote_type': vote_type,
            'vote_datetime': vote_datetime,
            'location_type': location_type,
            'registered_permanent': registered_permanent,
            'voters_permanent': voters_permanent,
            'voters_supplementary': voters_supplementary,
            'voters_mobile': voters_mobile if location_type == 'romania' else voters_correspondence,  # Pentru străinătate folosește LSC
            'men_18_24': men_18_24,
            'men_25_34': men_25_34,
            'men_35_44': men_35_44,
            'men_45_64': men_45_64,
            'men_65_plus': men_65_plus,
            'women_18_24': women_18_24,
            'women_25_34': women_25_34,
            'women_35_44': women_35_44,
            'women_45_64': women_45_64,
            'women_65_plus': women_65_plus,
            'demographic_data': demographic_data
        }
    
    def create_batch(self, batch_data):
        """Creează batch de înregistrări"""
        try:
            with transaction.atomic():
                presence_objects = [VotingPresence(**data) for data in batch_data]
                VotingPresence.objects.bulk_create(presence_objects, batch_size=500)
                return len(batch_data)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Eroare batch: {str(e)}'))
            created = 0
            for data in batch_data:
                try:
                    VotingPresence.objects.create(**data)
                    created += 1
                except Exception as individual_error:
                    logger.error(f'Eroare înregistrare {data.get("county")}: {individual_error}')
            return created
    
    def clean_string(self, value):
        """Curăță string"""
        if not value:
            return ''
        return str(value).strip()
    
    def safe_int(self, value):
        """Convertește la int"""
        if not value or value == '':
            return 0
        try:
            if isinstance(value, str):
                value = value.replace(' ', '').replace(',', '').replace('.', '')
                if not value:
                    return 0
            return int(float(value))
        except (ValueError, TypeError):
            return 0
    
    def create_county_summaries(self, vote_type, location_type, vote_datetime):
        """Creează sumarele pe județe/țări"""
        self.stdout.write(f'Creez sumarele pentru {location_type}...')
        
        counties = VotingPresence.objects.filter(
            vote_type=vote_type,
            location_type=location_type
        ).values_list('county', flat=True).distinct()
        
        for county in counties:
            county_data = VotingPresence.objects.filter(
                county=county,
                vote_type=vote_type,
                location_type=location_type
            ).aggregate(
                total_registered=Sum('registered_permanent'),
                total_permanent=Sum('voters_permanent'),
                total_supplementary=Sum('voters_supplementary'),
                total_mobile=Sum('voters_mobile'),
                total_men=Sum('men_18_24') + Sum('men_25_34') + Sum('men_35_44') + Sum('men_45_64') + Sum('men_65_plus'),
                total_women=Sum('women_18_24') + Sum('women_25_34') + Sum('women_35_44') + Sum('women_45_64') + Sum('women_65_plus')
            )
            
            # Urban/rural
            urban_rural = VotingPresence.objects.filter(
                county=county,
                vote_type=vote_type,
                location_type=location_type
            ).values('environment').annotate(
                voters=Sum('voters_permanent') + Sum('voters_supplementary') + Sum('voters_mobile')
            )
            
            urban_voters = 0
            rural_voters = 0
            for data in urban_rural:
                if data['environment'] == 'urban':
                    urban_voters = data['voters'] or 0
                else:
                    rural_voters = data['voters'] or 0
            
            total_voters = (county_data['total_permanent'] or 0) + \
                          (county_data['total_supplementary'] or 0) + \
                          (county_data['total_mobile'] or 0)
            
            PresenceSummary.objects.update_or_create(
                vote_type=vote_type,
                location_type=location_type,
                county=county,
                vote_datetime=vote_datetime,
                defaults={
                    'total_registered': county_data['total_registered'] or 0,
                    'total_voters': total_voters,
                    'total_permanent': county_data['total_permanent'] or 0,
                    'total_supplementary': county_data['total_supplementary'] or 0,
                    'total_mobile': county_data['total_mobile'] or 0,
                    'urban_voters': urban_voters,
                    'rural_voters': rural_voters,
                    'total_men': county_data['total_men'] or 0,
                    'total_women': county_data['total_women'] or 0
                }
            )
    
    def show_final_statistics(self, vote_type, location_type):
        """Afișează statistici finale"""
        self.stdout.write(f'\n=== STATISTICI {location_type.upper()} ===')
        
        general_stats = VotingPresence.objects.filter(
            vote_type=vote_type,
            location_type=location_type
        ).aggregate(
            total_registered=Sum('registered_permanent'),
            total_voters=Sum('voters_permanent') + Sum('voters_supplementary') + Sum('voters_mobile'),
            total_permanent=Sum('voters_permanent'),
            total_supplementary=Sum('voters_supplementary'),
            total_mobile=Sum('voters_mobile')
        )
        
        # Numărul de secții
        total_sections = VotingPresence.objects.filter(
            vote_type=vote_type,
            location_type=location_type
        ).count()
        
        self.stdout.write(f'Număr secții de votare: {total_sections:,}')
        self.stdout.write(f'Înscriși pe liste permanente: {general_stats["total_registered"]:,}')
        self.stdout.write(f'Votanți pe liste permanente: {general_stats["total_permanent"]:,}')
        self.stdout.write(f'Votanți pe liste suplimentare: {general_stats["total_supplementary"]:,}')
        
        if location_type == 'strainatate':
            self.stdout.write(f'Votanți pe liste de corespondență: {general_stats["total_mobile"]:,}')
        else:
            self.stdout.write(f'Votanți cu urnă mobilă: {general_stats["total_mobile"]:,}')
        
        self.stdout.write(f'Total votanți: {general_stats["total_voters"]:,}')
        
        if general_stats['total_registered'] and general_stats['total_registered'] > 0:
            participation_rate = (general_stats['total_voters'] / general_stats['total_registered']) * 100
            self.stdout.write(f'Rata de participare: {participation_rate:.2f}%')