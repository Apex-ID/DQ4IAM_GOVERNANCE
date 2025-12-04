"""
REGRAS PARA TABELAS DE PRODUÇÃO (DADOS TIPADOS)
-----------------------------------------------
Foco: Performance e Precisão.
Neste ambiente, assumimos que os tipos de dados JÁ SÃO NATIVOS:
- userAccountControl, adminCount -> INTEGER
- lastLogonTimestamp, pwdLastSet -> TIMESTAMPTZ
Portanto, NÃO usamos Regex nem CAST(AS TEXT).
"""

REGRAS_PRODUCAO = [
    # --- GRUPO 1: COMPLETUDE ---
    {
        'nome': '1. Contas de Usuário sem Gerente',
        'dimensao': 'Completude',
        'tabelas_alvo': ['ad_users'],
        'impacto': 'Contas órfãs de responsabilidade.',
        'sql': """SELECT "cn" as origem, 'Vazio' as detalhe FROM ad_users WHERE "manager" IS NULL OR "manager" = ''"""
    },
    {
        'nome': '2. Contas de Usuário sem Departamento',
        'dimensao': 'Completude',
        'tabelas_alvo': ['ad_users'],
        'impacto': 'Impede identificação de custos.',
        'sql': """SELECT "cn" as origem, 'Vazio' as detalhe FROM ad_users WHERE "department" IS NULL OR "department" = ''"""
    },
    {
        'nome': '3. Contas de Usuário sem Cargo',
        'dimensao': 'Completude',
        'tabelas_alvo': ['ad_users'],
        'impacto': 'Impede validação de SoD.',
        'sql': """SELECT "cn" as origem, 'Vazio' as detalhe FROM ad_users WHERE "title" IS NULL OR "title" = ''"""
    },
    {
        'nome': '4. Contato Incompleto',
        'dimensao': 'Completude',
        'tabelas_alvo': ['ad_users'],
        'impacto': 'Falha na comunicação.',
        'sql': """SELECT "cn" as origem, 'Sem Email/Tel' as detalhe FROM ad_users WHERE ("mail" IS NULL OR "mail" = '') OR ("telephoneNumber" IS NULL OR "telephoneNumber" = '')"""
    },
    {
        'nome': '5. Computadores sem Dono',
        'dimensao': 'Completude',
        'tabelas_alvo': ['ad_computers'],
        'impacto': 'Ativo sem responsável.',
        'sql': """SELECT "cn" as origem, 'Vazio' as detalhe FROM ad_computers WHERE "managedBy" IS NULL OR "managedBy" = ''"""
    },
    {
        'nome': '6. Computadores sem Descrição',
        'dimensao': 'Completude',
        'tabelas_alvo': ['ad_computers'],
        'impacto': 'Falta de documentação.',
        'sql': """SELECT "cn" as origem, 'Vazio' as detalhe FROM ad_computers WHERE "description" IS NULL OR "description" = ''"""
    },
    {
        'nome': '7. Grupos sem Dono',
        'dimensao': 'Completude',
        'tabelas_alvo': ['ad_groups'],
        'impacto': 'Grupos não auditados.',
        'sql': """SELECT "cn" as origem, 'Vazio' as detalhe FROM ad_groups WHERE "managedBy" IS NULL OR "managedBy" = ''"""
    },
    {
        'nome': '8. Grupos sem Descrição',
        'dimensao': 'Completude',
        'tabelas_alvo': ['ad_groups'],
        'impacto': 'Função desconhecida.',
        'sql': """SELECT "cn" as origem, 'Vazio' as detalhe FROM ad_groups WHERE "description" IS NULL OR "description" = ''"""
    },
    {
        'nome': '9. OUs sem Descrição',
        'dimensao': 'Completude',
        'tabelas_alvo': ['ad_ous'],
        'impacto': 'Falta de documentação.',
        'sql': """SELECT "ou" as origem, 'Vazio' as detalhe FROM ad_ous WHERE "description" IS NULL OR "description" = ''"""
    },
    {
        'nome': '10. OUs sem GPO',
        'dimensao': 'Completude',
        'tabelas_alvo': ['ad_ous'],
        'impacto': 'Objetos sem política de segurança.',
        'sql': """SELECT "ou" as origem, 'Vazio' as detalhe FROM ad_ous WHERE "gPLink" IS NULL OR "gPLink" = ''"""
    },

    # --- GRUPO 2: TEMPORALIDADE (Comparação Direta de Data) ---
    {
        'nome': '11. Usuários Inativos (>90 dias)',
        'dimensao': 'Temporalidade',
        'tabelas_alvo': ['ad_users'],
        'impacto': 'Risco latente.',
        'sql': """SELECT "cn" as origem, 'Inativo' as detalhe FROM ad_users WHERE "lastLogonTimestamp" < NOW() - INTERVAL '90 days'"""
    },
    {
        'nome': '12. Usuários Nunca Logados',
        'dimensao': 'Temporalidade',
        'tabelas_alvo': ['ad_users'],
        'impacto': 'Contas fantasma.',
        'sql': """SELECT "cn" as origem, 'Nunca Logou' as detalhe FROM ad_users WHERE "lastLogonTimestamp" IS NULL"""
    },
    {
        'nome': '13. Senha Antiga (>180 dias)',
        'dimensao': 'Temporalidade',
        'tabelas_alvo': ['ad_users'],
        'impacto': 'Risco de força bruta.',
        'sql': """SELECT "cn" as origem, 'Senha Antiga' as detalhe FROM ad_users WHERE "pwdLastSet" < NOW() - INTERVAL '180 days'"""
    },
    {
        'nome': '14. Computadores Inativos (>90 dias)',
        'dimensao': 'Temporalidade',
        'tabelas_alvo': ['ad_computers'],
        'impacto': 'Máquinas sem patches.',
        'sql': """SELECT "cn" as origem, 'Inativo' as detalhe FROM ad_computers WHERE "lastLogonTimestamp" < NOW() - INTERVAL '90 days'"""
    },

    # --- GRUPO 3: CONSISTÊNCIA (Operações Matemáticas Diretas) ---
    {
        'nome': '15. Gerente Inválido',
        'dimensao': 'Consistência',
        'tabelas_alvo': ['ad_users'],
        'impacto': 'Gerente não existe no AD.',
        'sql': """
            SELECT u."cn" as origem, 'Gerente não encontrado' as detalhe
            FROM ad_users u
            LEFT JOIN ad_users m ON u."manager" = m."distinguishedName"
            WHERE u."manager" IS NOT NULL AND u."manager" != '' AND m."distinguishedName" IS NULL
        """
    },
    {
        'nome': '16. Gerente Desabilitado',
        'dimensao': 'Consistência',
        'tabelas_alvo': ['ad_users'],
        'impacto': 'Reporta a gerente desligado.',
        # Bitwise direto (campo é INTEGER)
        'sql': """
            SELECT u."cn" as origem, 'Gerente OFF' as detalhe
            FROM ad_users u
            JOIN ad_users m ON u."manager" = m."distinguishedName"
            WHERE (u."userAccountControl" & 2) = 0   -- Usuário Ativo
              AND (m."userAccountControl" & 2) > 0   -- Gerente Desabilitado
        """
    },
    {
        'nome': '17. Conta Desabilitada com Grupos',
        'dimensao': 'Consistência',
        'tabelas_alvo': ['ad_users'],
        'impacto': 'Acesso latente.',
        'sql': """
            SELECT "cn" as origem, 'Tem Grupos' as detalhe
            FROM ad_users
            WHERE ("userAccountControl" & 2) > 0 
              AND ("memberOf" IS NOT NULL AND "memberOf" != '')
        """
    },
    {
        'nome': '18. Admin Count=1',
        'dimensao': 'Consistência',
        'tabelas_alvo': ['ad_users'],
        'impacto': 'Privilegiado.',
        'sql': """SELECT "cn" as origem, 'AdminCount=1' as detalhe FROM ad_users WHERE "adminCount" = 1"""
    },
    {
        'nome': '19. Computador Órfão',
        'dimensao': 'Consistência',
        'tabelas_alvo': ['ad_computers'],
        'impacto': 'Dono inexistente.',
        'sql': """
            SELECT c."cn" as origem, 'Dono sumiu' as detalhe
            FROM ad_computers c
            LEFT JOIN ad_users u ON c."managedBy" = u."distinguishedName"
            WHERE c."managedBy" IS NOT NULL AND c."managedBy" != '' AND u."distinguishedName" IS NULL
        """
    },
    {
        'nome': '20. Grupos Aninhados',
        'dimensao': 'Consistência',
        'tabelas_alvo': ['ad_groups'],
        'impacto': 'Complexidade de auditoria.',
        'sql': """SELECT "cn" as origem, 'Aninhado' as detalhe FROM ad_groups WHERE "memberOf" IS NOT NULL AND "memberOf" != ''"""
    },
    {
        'nome': '21. Computador Fora de Padrão',
        'dimensao': 'Consistência',
        'tabelas_alvo': ['ad_computers'],
        'impacto': 'Sem GPO correta.',
        'sql': """SELECT "cn" as origem, 'Container incorreto' as detalhe FROM ad_computers WHERE "distinguishedName" LIKE '%CN=Computers,%'"""
    },
    {
        'nome': '22. Grupos Admin sem Proteção',
        'dimensao': 'Consistência',
        'tabelas_alvo': ['ad_groups'],
        'impacto': 'Nome Admin mas sem proteção.',
        'sql': """
            SELECT "cn" as origem, 'AdminCount 0 ou Nulo' as detalhe
            FROM ad_groups
            WHERE "cn" LIKE '%Admin%' 
              AND ("adminCount" IS NULL OR "adminCount" = 0)
        """
    },
    {
        'nome': '23. Grupos Vazios',
        'dimensao': 'Consistência',
        'tabelas_alvo': ['ad_groups'],
        'impacto': 'Grupo sem membros.',
        'sql': """SELECT "cn" as origem, 'Vazio' as detalhe FROM ad_groups WHERE "member" IS NULL OR "member" = ''"""
    },

    # --- GRUPO 4: VALIDADE ---
    {
        'nome': '24. UPN Fora do Padrão',
        'dimensao': 'Validade',
        'tabelas_alvo': ['ad_users'],
        'impacto': 'Falha de autenticação.',
        'sql': """SELECT "sAMAccountName" as origem, 'UPN Ruim' as detalhe FROM ad_users WHERE "userPrincipalName" NOT LIKE '%@office.ufs.br'"""
    },
    {
        'nome': '25. Logon Legado Extenso',
        'dimensao': 'Validade',
        'tabelas_alvo': ['ad_users'],
        'impacto': 'Incompatibilidade legado.',
        'sql': """SELECT "cn" as origem, '> 20 caracteres' as detalhe FROM ad_users WHERE LENGTH("sAMAccountName") > 20"""
    },
    {
        'nome': '26. Sistemas Obsoletos',
        'dimensao': 'Validade',
        'tabelas_alvo': ['ad_computers'],
        'impacto': 'Risco crítico.',
        'sql': """
            SELECT "cn" as origem, "operatingSystem" as detalhe
            FROM ad_computers
            WHERE "operatingSystem" ILIKE '%Windows 7%' 
               OR "operatingSystem" ILIKE '%XP%' 
               OR "operatingSystem" ILIKE '%2003%' 
               OR "operatingSystem" ILIKE '%2008%'
               OR "operatingSystem" ILIKE '%2000%'
        """
    },

    # --- GRUPO 5: ESTRUTURAL (Corrigido para Tipos Nativos) ---
    {
        'nome': '27. Ciclos Hierárquicos',
        'dimensao': 'Consistência',
        'tabelas_alvo': ['ad_users'],
        'impacto': 'Loop infinito.',
        'sql': """
            WITH RECURSIVE Hierarquia AS (
                SELECT "distinguishedName" as raiz, "manager", "distinguishedName" as atual, 1 as nivel 
                FROM ad_users WHERE "manager" IS NOT NULL AND "manager" != ''
                UNION ALL
                SELECT h.raiz, u."manager", u."distinguishedName", h.nivel + 1 
                FROM ad_users u 
                INNER JOIN Hierarquia h ON u."distinguishedName" = h."manager" 
                WHERE h.nivel < 5
            )
            SELECT h.raiz as origem, 'Ciclo' as detalhe 
            FROM Hierarquia h 
            WHERE h."manager" = h.raiz 
        """
    },
    {
        'nome': '28. Padronização de Departamento',
        'dimensao': 'Consistência',
        'tabelas_alvo': ['ad_users'],
        'impacto': 'Variações raras.',
        'sql': """
            SELECT "department" as origem, 'Variação rara' as detalhe
            FROM ad_users
            WHERE "department" IN (
                SELECT "department" FROM ad_users 
                WHERE "department" IS NOT NULL AND "department" != '' 
                GROUP BY "department" HAVING COUNT(*) < 3
            )
        """
    },
    {
        'nome': '29. Zombie Containers',
        'dimensao': 'Precisão',
        'tabelas_alvo': ['ad_ous'],
        'impacto': 'OUs mortas.',
        'sql': """
            SELECT ou."distinguishedName" as origem, 'OU Zumbi' as detalhe
            FROM ad_ous ou
            WHERE NOT EXISTS (
                SELECT 1 FROM ad_users u WHERE u."distinguishedName" LIKE '%' || ou."distinguishedName" 
                AND (u."userAccountControl" & 2) = 0  -- SEM REGEX, POIS É INTEIRO
            )
            AND NOT EXISTS (
                SELECT 1 FROM ad_computers c WHERE c."distinguishedName" LIKE '%' || ou."distinguishedName" 
                AND c."lastLogonTimestamp" > NOW() - INTERVAL '90 days' -- SEM CAST, POIS É DATA
            )
        """
    },

    # --- GRUPO 6: UNICIDADE ---
    {
        'nome': '30. Duplicidade de Linha (Usuários)',
        'dimensao': 'Unicidade',
        'tabelas_alvo': ['ad_users'],
        'impacto': 'Registro duplicado.',
        'sql': """
            SELECT "cn" as origem, 'Clone' as detalhe
            FROM ad_users
            WHERE "distinguishedName" IN (SELECT "distinguishedName" FROM ad_users GROUP BY "distinguishedName" HAVING COUNT(*) > 1)
        """
    },
    {
        'nome': '31. Duplicidade de Linha (Computadores)',
        'dimensao': 'Unicidade',
        'tabelas_alvo': ['ad_computers'],
        'impacto': 'Registro duplicado.',
        'sql': """
            SELECT "cn" as origem, 'Clone' as detalhe
            FROM ad_computers
            WHERE "distinguishedName" IN (SELECT "distinguishedName" FROM ad_computers GROUP BY "distinguishedName" HAVING COUNT(*) > 1)
        """
    },
    {
        'nome': '32. Duplicidade de Linha (Grupos)',
        'dimensao': 'Unicidade',
        'tabelas_alvo': ['ad_groups'],
        'impacto': 'Registro duplicado.',
        'sql': """
            SELECT "cn" as origem, 'Clone' as detalhe
            FROM ad_groups
            WHERE "distinguishedName" IN (SELECT "distinguishedName" FROM ad_groups GROUP BY "distinguishedName" HAVING COUNT(*) > 1)
        """
    },
    {
        'nome': '33. Duplicidade de Linha (OUs)',
        'dimensao': 'Unicidade',
        'tabelas_alvo': ['ad_ous'],
        'impacto': 'Registro duplicado.',
        'sql': """
            SELECT "ou" as origem, 'Clone' as detalhe
            FROM ad_ous
            WHERE "distinguishedName" IN (SELECT "distinguishedName" FROM ad_ous GROUP BY "distinguishedName" HAVING COUNT(*) > 1)
        """
    },
    {
        'nome': '34. Múltiplas Contas - Mesmo E-mail',
        'dimensao': 'Unicidade',
        'tabelas_alvo': ['ad_users'],
        'impacto': 'E-mail duplicado.',
        'sql': """
            SELECT "mail" as origem, 'Duplicado' as detalhe
            FROM ad_users
            WHERE "mail" IS NOT NULL AND "mail" != ''
            GROUP BY "mail" HAVING COUNT(*) > 1
        """
    },
    {
        'nome': '35. Múltiplas Contas - Mesmo Nome Completo',
        'dimensao': 'Unicidade',
        'tabelas_alvo': ['ad_users'],
        'impacto': 'Nomes idênticos.',
        'sql': """
            SELECT "cn" as origem, 'Duplicado' as detalhe
            FROM ad_users
            WHERE "cn" IS NOT NULL AND "cn" != ''
            GROUP BY "cn" HAVING COUNT(*) > 1
        """
    },
    {
        'nome': '36. Possível Conta Admin Vinculada',
        'dimensao': 'Consistência',
        'tabelas_alvo': ['ad_users'],
        'impacto': 'Conta administrativa secundária.',
        'sql': """
            SELECT u1."sAMAccountName" as origem, 'Par: ' || u2."sAMAccountName" as detalhe
            FROM ad_users u1
            JOIN ad_users u2 ON u1."sAMAccountName" LIKE '%' || u2."sAMAccountName" || '%'
            WHERE u1."id" != u2."id" AND LENGTH(u2."sAMAccountName") > 4 AND (u1."sAMAccountName" LIKE 'adm.%' OR u1."sAMAccountName" LIKE 'admin.%')
        """
    }
]