from django.core.management.base import BaseCommand
import csv
from qualidade_ad.models import DicionarioOrganograma, HistoricoOrganograma

class Command(BaseCommand):
    help = 'Importa o Organograma Oficial UFS 2025'

    def add_arguments(self, parser):
        parser.add_argument('caminho_csv', type=str)

    def handle(self, *args, **options):
        caminho = options['caminho_csv']
        self.stdout.write(f"Iniciando importação de: {caminho}")

        try:
            with open(caminho, 'r', encoding='utf-8') as f:
                # Ajustado para o formato do seu CSV (quotechar aspas simples)
                reader = csv.DictReader(f, quotechar="'", delimiter=',')
                
                count_criado = 0
                count_atualizado = 0
                
                for row in reader:
                    codigo = row['codigo_unidade'].strip()
                    sigla = row['sigla'].strip()
                    nome = row['nome'].strip()
                    hierarquia = row['hierarquia'].strip()

                    # Tenta pegar a unidade existente
                    obj, created = DicionarioOrganograma.objects.update_or_create(
                        codigo_unidade=codigo,
                        defaults={
                            'sigla': sigla,
                            'nome': nome,
                            'hierarquia': hierarquia
                        }
                    )

                    if created:
                        count_criado += 1
                        # Registra no histórico
                        HistoricoOrganograma.objects.create(
                            unidade_afetada=obj,
                            acao='IMPORTACAO',
                            detalhes=f"Unidade importada inicialmente via CSV. Nome: {nome}"
                        )
                    else:
                        count_atualizado += 1

            self.stdout.write(self.style.SUCCESS(f"Importação Concluída! Criados: {count_criado} | Atualizados: {count_atualizado}"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erro: {e}"))