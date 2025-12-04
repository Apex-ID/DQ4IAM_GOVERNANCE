# relatorios_gerenciais/dicionario_dados.py

# Mapeia Tabela -> Coluna -> Definição Amigável
DICIONARIO_AD = {
    'ad_users': {
        'cn': {'nome': 'Nome Comum', 'desc': 'Nome completo do objeto no diretório.'},
        'sAMAccountName': {'nome': 'Login de Rede (SAM)', 'desc': 'Identificador único para logon em sistemas legados.'},
        'userPrincipalName': {'nome': 'UPN (E-mail)', 'desc': 'Identificador moderno para logon em nuvem/Office 365.'},
        'manager': {'nome': 'Gestor Responsável', 'desc': 'DN do usuário responsável hierarquicamente.'},
        'department': {'nome': 'Departamento', 'desc': 'Centro de custo ou setor de lotação.'},
        'title': {'nome': 'Cargo', 'desc': 'Função oficial do colaborador.'},
        'whenCreated': {'nome': 'Data de Criação', 'desc': 'Data em que a conta foi gerada.'},
        'lastLogonTimestamp': {'nome': 'Último Logon Real', 'desc': 'Data da última autenticação replicada.'},
    },
    'ad_computers': {
        'cn': {'nome': 'Hostname', 'desc': 'Nome da máquina na rede.'},
        'operatingSystem': {'nome': 'Sistema Operacional', 'desc': 'Versão do SO instalado.'},
        'managedBy': {'nome': 'Dono do Ativo', 'desc': 'Responsável técnico ou administrativo.'},
        'description': {'nome': 'Descrição Técnica', 'desc': 'Função ou localização física da máquina.'},
    },
    'ad_groups': {
        'cn': {'nome': 'Nome do Grupo', 'desc': 'Identificador do grupo.'},
        'member': {'nome': 'Membros', 'desc': 'Lista de usuários que pertencem ao grupo.'},
        'description': {'nome': 'Finalidade', 'desc': 'Descrição do propósito do acesso.'},
    }
}
# Alias para tabelas de staging (usam a mesma definição)
DICIONARIO_AD['ad_users_staging'] = DICIONARIO_AD['ad_users']
DICIONARIO_AD['ad_computers_staging'] = DICIONARIO_AD['ad_computers']
DICIONARIO_AD['ad_groups_staging'] = DICIONARIO_AD['ad_groups']

def obter_info_coluna(tabela, coluna):
    """Retorna (Nome Amigável, Descrição) ou valores padrão."""
    # Tenta limpar nome da tabela (tira _staging se não achar direto)
    tab_info = DICIONARIO_AD.get(tabela, {})
    col_info = tab_info.get(coluna, {'nome': coluna, 'desc': 'Campo técnico do Active Directory.'})
    return col_info