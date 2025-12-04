# relatorios_gerenciais/catalogo_formulas.py

FORMULAS_QUALIDADE = {
    'completude': {
        'titulo': 'Completude (Completeness)',
        'formula': '(Total de Células Preenchidas / Total de Células Possíveis) * 100',
        'desc': 'Mede a proporção de dados armazenados contra o potencial de 100%. Células vazias ou nulas reduzem a pontuação.'
    },
    'validade': {
        'titulo': 'Validade (Validity)',
        'formula': '(Células Preenchidas Válidas / Total de Células Preenchidas) * 100',
        'desc': 'Verifica se os dados presentes respeitam a sintaxe, tipo (Data, Inteiro, UUID) e formato definidos no Dicionário de Dados.'
    },
    'unicidade': {
        'titulo': 'Unicidade (Uniqueness)',
        'formula': '(Registros Distintos / Total de Registros) * 100',
        'desc': 'Garante que cada entidade seja representada apenas uma vez. Duplicatas são identificadas por chaves primárias ou compostas.'
    },
    'consistencia': {
        'titulo': 'Consistência e Acurácia',
        'formula': '((Total Registros - Registros com Falha) / Total Registros) * 100',
        'desc': 'Mede a coerência lógica entre dados relacionados (ex: Usuário ativo deve ter Gerente ativo) baseado em Regras de Negócio SQL.'
    }
}