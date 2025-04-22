from django.core.management.base import BaseCommand
from news.models import ElectionAnalyticsChart, ChartDataset, ChartLabels, ChartDataPoint
from django.db import transaction

class Command(BaseCommand):
    help = 'Populează baza de date cu grafice analitice electorale'

    def handle(self, *args, **options):
        self.stdout.write('Începe popularea graficelor analitice...')
        
        # Datele pentru grafice
        charts_data = [
            {
                'title': 'Prezența la vot în ultimele alegeri',
                'description': 'Evoluția prezenței la vot la alegerile prezidențiale din România în ultimii 20 de ani',
                'chart_type': 'line',
                'display_order': 1,
                'labels': ['2000', '2004', '2008', '2012', '2016', '2020'],
                'datasets': [
                    {
                        'label': 'Prezență la vot (%)',
                        'data': [65, 57, 58, 64, 39, 52],
                        'background_color': None,
                        'border_color': '#2e86de',
                        'fill': False
                    }
                ]
            },
            {
                'title': 'Distribuția voturilor pe grupe de vârstă',
                'description': 'Procentul de participare la vot în funcție de grupele de vârstă la ultimele alegeri',
                'chart_type': 'bar',
                'display_order': 2,
                'labels': ['18-24', '25-34', '35-44', '45-54', '55-64', '65+'],
                'datasets': [
                    {
                        'label': 'Participare (%)',
                        'data': [32, 48, 56, 67, 72, 68],
                        'background_color': '#54a0ff,#2e86de,#0c75c7,#065a9d,#044680,#02386a',
                        'border_color': 'transparent',
                        'fill': True
                    }
                ]
            },
            {
                'title': 'Metode de vot utilizate',
                'description': 'Distribuția metodelor de vot utilizate la ultimele alegeri',
                'chart_type': 'pie',
                'display_order': 3,
                'labels': ['La secție', 'Prin corespondență', 'Electronic', 'Mobil'],
                'datasets': [
                    {
                        'label': 'Metode de vot',
                        'data': [75, 10, 12, 3],
                        'background_color': '#ff6b6b,#5f27cd,#1dd1a1,#feca57',
                        'border_color': 'transparent',
                        'fill': True
                    }
                ]
            },
            {
                'title': 'Încrederea în diferite sisteme de vot',
                'description': 'Nivelul de încredere al publicului în diverse sisteme de vot (sondaj)',
                'chart_type': 'radar',
                'display_order': 4,
                'labels': ['Tradițional', 'Electronic', 'Aplicație Mobilă', 'Blockchain', 'Corespondență'],
                'datasets': [
                    {
                        'label': 'Încredere (2020)',
                        'data': [85, 62, 58, 45, 70],
                        'background_color': 'rgba(46, 134, 222, 0.3)',
                        'border_color': '#2e86de',
                        'fill': True
                    },
                    {
                        'label': 'Încredere (2023)',
                        'data': [78, 75, 70, 65, 67],
                        'background_color': 'rgba(255, 107, 107, 0.3)',
                        'border_color': '#ff6b6b',
                        'fill': True
                    }
                ]
            },
            {
                'title': 'Adoptarea votului electronic în Europa',
                'description': 'Procentul populației cu acces la vot electronic în țările europene',
                'chart_type': 'bar',
                'display_order': 5,
                'labels': ['Estonia', 'Elveția', 'Norvegia', 'Finlanda', 'România', 'Franța', 'Germania'],
                'datasets': [
                    {
                        'label': 'Acces la vot electronic (%)',
                        'data': [98, 45, 32, 25, 5, 10, 8],
                        'background_color': '#1dd1a1,#1dd1a1,#1dd1a1,#1dd1a1,#ff6b6b,#1dd1a1,#1dd1a1',
                        'border_color': 'transparent',
                        'fill': True
                    }
                ]
            },
            {
    'title': 'Motivele absenteismului electoral',
    'description': 'Principalele motive pentru care cetățenii nu participă la vot',
    'chart_type': 'doughnut',
    'display_order': 6,
    'labels': ['Lipsa de interes', 'Neîncredere în sistem', 'Lipsă de timp', 'Probleme logistice', 'Alte motive'],
    'datasets': [
        {
            'label': 'Procent (%)',
            'data': [35, 25, 20, 15, 5],
            'background_color': '#f39c12,#3498db,#9b59b6,#2ecc71,#e74c3c',
            'border_color': 'rgba(255, 255, 255, 0.5)',
            'fill': True
        }
    ]
}

        ]
        
        # Folosim transaction pentru a asigura integritatea datelor
        with transaction.atomic():
            # Ștergem datele existente (opțional, depinde de nevoi)
            self.stdout.write('Ștergerea datelor analitice existente...')
            ElectionAnalyticsChart.objects.all().delete()
            
            # Creăm graficele și datele asociate
            for chart_data in charts_data:
                # Creăm graficul
                chart = ElectionAnalyticsChart.objects.create(
                    title=chart_data['title'],
                    description=chart_data['description'],
                    chart_type=chart_data['chart_type'],
                    display_order=chart_data['display_order'],
                    is_active=True
                )
                
                self.stdout.write(self.style.SUCCESS(f"Graficul '{chart.title}' a fost creat."))
                
                # Creăm etichetele
                labels = []
                for i, label_text in enumerate(chart_data['labels']):
                    label = ChartLabels.objects.create(
                        chart=chart,
                        label=label_text,
                        position=i
                    )
                    labels.append(label)
                
                # Creăm seturile de date și punctele de date asociate
                for i, dataset_info in enumerate(chart_data['datasets']):
                    dataset = ChartDataset.objects.create(
                        chart=chart,
                        label=dataset_info['label'],
                        background_color=dataset_info['background_color'],
                        border_color=dataset_info['border_color'],
                        fill=dataset_info['fill'],
                        display_order=i
                    )
                    
                    # Creăm punctele de date
                    for j, value in enumerate(dataset_info['data']):
                        if j < len(labels):
                            ChartDataPoint.objects.create(
                                chart=chart,
                                dataset=dataset,
                                label=labels[j],
                                value=value
                            )
        
        self.stdout.write(self.style.SUCCESS('Popularea graficelor analitice a fost finalizată cu succes!'))