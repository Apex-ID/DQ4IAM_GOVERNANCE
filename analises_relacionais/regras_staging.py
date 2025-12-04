"""
REGRAS PARA TABELAS DE STAGING (DADOS BRUTOS / TEXTO)
-----------------------------------------------------
Foco: Validação defensiva. Como os dados em Staging são puramente TEXTO,
usamos REGEX (~ '^[0-9]+$') e verificação de LENGTH para evitar que o PostgreSQL
tente converter strings vazias ou inválidas para Números/Datas, o que causaria erro.
"""

REGRAS_STAGING = [
    # ==============================================================================
    # GRUPO 1: COMPLETUDE (Campos Vazios)
    # ==============================================================================
    {
        'nome': '1. Contas de Usuário sem Gerente',
        'dimensao': 'Completude',
        'tabelas': 'ad_users_staging',
        'impacto': 'Contas órfãs de responsabilidade.',
        'sql': """
            SELECT "cn" as origem, 'Campo manager vazio' as detalhe 
            FROM ad_users_staging 
            WHERE "manager" IS NULL OR "manager" = ''
        """
    },
    {
        'nome': '2. Contas de Usuário sem Departamento',
        'dimensao': 'Completude',
        'tabelas': 'ad_users_staging',
        'impacto': 'Impede identificação de custos e RBAC.',
        'sql': """
            SELECT "cn" as origem, 'Campo department vazio' as detalhe 
            FROM ad_users_staging 
            WHERE "department" IS NULL OR "department" = ''
        """
    },
    {
        'nome': '3. Contas de Usuário sem Cargo',
        'dimensao': 'Completude',
        'tabelas': 'ad_users_staging',
        'impacto': 'Impede validação de SoD.',
        'sql': """
            SELECT "cn" as origem, 'Campo title vazio' as detalhe 
            FROM ad_users_staging 
            WHERE "title" IS NULL OR "title" = ''
        """
    },
    {
        'nome': '4. Contato Incompleto',
        'dimensao': 'Completude',
        'tabelas': 'ad_users_staging',
        'impacto': 'Falha na comunicação e suporte.',
        'sql': """
            SELECT "cn" as origem, 'Sem E-mail ou Telefone' as detalhe 
            FROM ad_users_staging 
            WHERE ("mail" IS NULL OR "mail" = '') 
               OR ("telephoneNumber" IS NULL OR "telephoneNumber" = '')
        """
    },
    {
        'nome': '5. Computadores sem Dono',
        'dimensao': 'Completude',
        'tabelas': 'ad_computers_staging',
        'impacto': 'Ativo de TI sem responsável.',
        'sql': """
            SELECT "cn" as origem, 'Campo managedBy vazio' as detalhe 
            FROM ad_computers_staging 
            WHERE "managedBy" IS NULL OR "managedBy" = ''
        """
    },
    {
        'nome': '6. Computadores sem Descrição',
        'dimensao': 'Completude',
        'tabelas': 'ad_computers_staging',
        'impacto': 'Falta de documentação técnica.',
        'sql': """
            SELECT "cn" as origem, 'Campo description vazio' as detalhe 
            FROM ad_computers_staging 
            WHERE "description" IS NULL OR "description" = ''
        """
    },
    {
        'nome': '7. Grupos sem Dono',
        'dimensao': 'Completude',
        'tabelas': 'ad_groups_staging',
        'impacto': 'Grupos não auditados.',
        'sql': """
            SELECT "cn" as origem, 'Campo managedBy vazio' as detalhe 
            FROM ad_groups_staging 
            WHERE "managedBy" IS NULL OR "managedBy" = ''
        """
    },
    {
        'nome': '8. Grupos sem Descrição',
        'dimensao': 'Completude',
        'tabelas': 'ad_groups_staging',
        'impacto': 'Função desconhecida.',
        'sql': """
            SELECT "cn" as origem, 'Campo description vazio' as detalhe 
            FROM ad_groups_staging 
            WHERE "description" IS NULL OR "description" = ''
        """
    },
    {
        'nome': '9. OUs sem Descrição',
        'dimensao': 'Completude',
        'tabelas': 'ad_ous_staging',
        'impacto': 'Falta de documentação estrutural.',
        'sql': """
            SELECT "ou" as origem, 'Campo description vazio' as detalhe 
            FROM ad_ous_staging 
            WHERE "description" IS NULL OR "description" = ''
        """
    },
    {
        'nome': '10. OUs sem GPO',
        'dimensao': 'Completude',
        'tabelas': 'ad_ous_staging',
        'impacto': 'Objetos soltos sem política de segurança.',
        'sql': """
            SELECT "ou" as origem, 'Campo gPLink vazio' as detalhe 
            FROM ad_ous_staging 
            WHERE "gPLink" IS NULL OR "gPLink" = ''
        """
    },

    # ==============================================================================
    # GRUPO 2: TEMPORALIDADE (Blindagem de Data em Texto)
    # ==============================================================================
    {
        'nome': '11. Usuários Inativos (>90 dias)',
        'dimensao': 'Temporalidade',
        'tabelas': 'ad_users_staging',
        'impacto': 'Vetor de ataque lateral.',
        # Verifica se tem tamanho suficiente para ser data antes de converter
        'sql': """
            SELECT "cn" as origem, 'Inativo' as detalhe 
            FROM ad_users_staging 
            WHERE LENGTH("lastLogonTimestamp") > 10 
            AND CAST("lastLogonTimestamp" AS TIMESTAMPTZ) < NOW() - INTERVAL '90 days'
        """
    },
    {
        'nome': '12. Usuários Nunca Logados',
        'dimensao': 'Temporalidade',
        'tabelas': 'ad_users_staging',
        'impacto': 'Contas fantasma.',
        'sql': """
            SELECT "cn" as origem, 'Nunca Logou' as detalhe 
            FROM ad_users_staging 
            WHERE "lastLogonTimestamp" IS NULL OR "lastLogonTimestamp" = ''
        """
    },
    {
        'nome': '13. Senha Antiga (>180 dias)',
        'dimensao': 'Temporalidade',
        'tabelas': 'ad_users_staging',
        'impacto': 'Risco de força bruta.',
        'sql': """
            SELECT "cn" as origem, 'Senha Antiga' as detalhe 
            FROM ad_users_staging 
            WHERE LENGTH("pwdLastSet") > 10 
            AND CAST("pwdLastSet" AS TIMESTAMPTZ) < NOW() - INTERVAL '180 days'
        """
    },
    {
        'nome': '14. Computadores Inativos (>90 dias)',
        'dimensao': 'Temporalidade',
        'tabelas': 'ad_computers_staging',
        'impacto': 'Máquinas sem patches.',
        'sql': """
            SELECT "cn" as origem, 'Inativo' as detalhe 
            FROM ad_computers_staging 
            WHERE LENGTH("lastLogonTimestamp") > 10 
            AND CAST("lastLogonTimestamp" AS TIMESTAMPTZ) < NOW() - INTERVAL '90 days'
        """
    },

    # ==============================================================================
    # GRUPO 3: CONSISTÊNCIA (Blindagem de Inteiro com Regex)
    # ==============================================================================
    {
        'nome': '15. Gerente Inválido',
        'dimensao': 'Consistência',
        'tabelas': 'ad_users_staging',
        'impacto': 'Gerente não existe no AD.',
        'sql': """
            SELECT u."cn" as origem, u."manager" as detalhe
            FROM ad_users_staging u
            LEFT JOIN ad_users_staging m ON u."manager" = m."distinguishedName"
            WHERE u."manager" IS NOT NULL AND u."manager" != '' 
              AND m."distinguishedName" IS NULL
        """
    },
    {
        'nome': '16. Gerente Desabilitado',
        'dimensao': 'Consistência',
        'tabelas': 'ad_users_staging',
        'impacto': 'Reporta a gerente desligado.',
        # Regex: Verifica se é apenas números antes de converter e testar o bit 2
        'sql': """
            SELECT u."cn" as origem, 'Gerente OFF' as detalhe
            FROM ad_users_staging u
            JOIN ad_users_staging m ON u."manager" = m."distinguishedName"
            WHERE 
                (u."userAccountControl" ~ '^[0-9]+$' AND (CAST(u."userAccountControl" AS INTEGER) & 2) = 0)
                AND 
                (m."userAccountControl" ~ '^[0-9]+$' AND (CAST(m."userAccountControl" AS INTEGER) & 2) > 0)
        """
    },
    {
        'nome': '17. Conta Desabilitada com Grupos',
        'dimensao': 'Consistência',
        'tabelas': 'ad_users_staging',
        'impacto': 'Acesso latente.',
        'sql': """
            SELECT "cn" as origem, 'Tem Grupos' as detalhe
            FROM ad_users_staging
            WHERE ("userAccountControl" ~ '^[0-9]+$' AND (CAST("userAccountControl" AS INTEGER) & 2) > 0)
            AND ("memberOf" IS NOT NULL AND "memberOf" != '')
        """
    },
    {
        'nome': '18. Admin Count=1',
        'dimensao': 'Consistência',
        'tabelas': 'ad_users_staging',
        'impacto': 'Privilegiado.',
        'sql': """
            SELECT "cn" as origem, 'AdminCount=1' as detalhe 
            FROM ad_users_staging 
            WHERE "adminCount" ~ '^[0-9]+$' AND CAST("adminCount" AS INTEGER) = 1
        """
    },
    {
        'nome': '19. Computador Órfão',
        'dimensao': 'Consistência',
        'tabelas': 'ad_computers_staging',
        'impacto': 'Dono inexistente.',
        'sql': """
            SELECT c."cn" as origem, 'Dono sumiu' as detalhe
            FROM ad_computers_staging c
            LEFT JOIN ad_users_staging u ON c."managedBy" = u."distinguishedName"
            WHERE c."managedBy" IS NOT NULL AND c."managedBy" != '' 
              AND u."distinguishedName" IS NULL
        """
    },
    {
        'nome': '20. Grupos Aninhados',
        'dimensao': 'Consistência',
        'tabelas': 'ad_groups_staging',
        'impacto': 'Complexidade de auditoria.',
        'sql': """
            SELECT "cn" as origem, 'Aninhado' as detalhe 
            FROM ad_groups_staging 
            WHERE "memberOf" IS NOT NULL AND "memberOf" != ''
        """
    },
    {
        'nome': '21. Computador Fora de Padrão',
        'dimensao': 'Consistência',
        'tabelas': 'ad_computers_staging',
        'impacto': 'Sem GPO correta.',
        'sql': """
            SELECT "cn" as origem, 'Container CN=Computers' as detalhe 
            FROM ad_computers_staging 
            WHERE "distinguishedName" LIKE '%CN=Computers,%'
        """
    },
    {
        'nome': '22. Grupos Admin sem Proteção',
        'dimensao': 'Consistência',
        'tabelas': 'ad_groups_staging',
        'impacto': 'Nome Admin mas sem proteção.',
        # Verifica se NÃO é número (vazio ou lixo) ou se é 0
        'sql': """
            SELECT "cn" as origem, 'AdminCount 0 ou Nulo' as detalhe
            FROM ad_groups_staging
            WHERE "cn" LIKE '%Admin%' 
              AND (
                  "adminCount" IS NULL OR "adminCount" = '' 
                  OR NOT ("adminCount" ~ '^[0-9]+$') 
                  OR CAST("adminCount" AS INTEGER) = 0
              )
        """
    },
    {
        'nome': '23. Grupos Vazios',
        'dimensao': 'Consistência',
        'tabelas': 'ad_groups_staging',
        'impacto': 'Grupo sem membros.',
        'sql': """
            SELECT "cn" as origem, 'Vazio' as detalhe 
            FROM ad_groups_staging 
            WHERE "member" IS NULL OR "member" = ''
        """
    },

    # ==============================================================================
    # GRUPO 4: VALIDADE (Texto)
    # ==============================================================================
    {
        'nome': '24. UPN Fora do Padrão',
        'dimensao': 'Validade',
        'tabelas': 'ad_users_staging',
        'impacto': 'Falha de autenticação.',
        'sql': """
            SELECT "sAMAccountName" as origem, 'UPN Ruim' as detalhe 
            FROM ad_users_staging 
            WHERE "userPrincipalName" NOT LIKE '%@office.ufs.br'
        """
    },
    {
        'nome': '25. Logon Legado Extenso',
        'dimensao': 'Validade',
        'tabelas': 'ad_users_staging',
        'impacto': 'Incompatibilidade legado.',
        'sql': """
            SELECT "cn" as origem, '> 20 caracteres' as detalhe 
            FROM ad_users_staging 
            WHERE LENGTH("sAMAccountName") > 20
        """
    },
    {
        'nome': '26. Sistemas Operacionais Obsoletos',
        'dimensao': 'Validade',
        'tabelas': 'ad_computers_staging',
        'impacto': 'Risco crítico de segurança.',
        'sql': """
            SELECT "cn" as origem, "operatingSystem" as detalhe
            FROM ad_computers_staging
            WHERE "operatingSystem" IS NOT NULL AND "operatingSystem" != ''
              AND "operatingSystem" NOT ILIKE '%Windows 10%'
              AND "operatingSystem" NOT ILIKE '%Windows 11%'
              AND "operatingSystem" NOT ILIKE '%Server 2016%'
              AND "operatingSystem" NOT ILIKE '%Server 2019%'
              AND "operatingSystem" NOT ILIKE '%Server 2022%'
        """
    },

    # ==============================================================================
    # GRUPO 5: ESTRUTURAL (Recursão)
    # ==============================================================================
    {
        'nome': '27. Ciclos Hierárquicos',
        'dimensao': 'Consistência',
        'tabelas': 'ad_users_staging',
        'impacto': 'Loop infinito na hierarquia.',
        'sql': """
            WITH RECURSIVE Hierarquia AS (
                SELECT "distinguishedName" as raiz, "manager", "distinguishedName" as atual, 1 as nivel 
                FROM ad_users_staging WHERE "manager" IS NOT NULL AND "manager" != ''
                UNION ALL
                SELECT h.raiz, u."manager", u."distinguishedName", h.nivel + 1 
                FROM ad_users_staging u 
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
        'tabelas': 'ad_users_staging',
        'impacto': 'Variações raras de escrita.',
        'sql': """
            SELECT "department" as origem, 'Variação rara' as detalhe
            FROM ad_users_staging
            WHERE "department" IN (
                SELECT "department" FROM ad_users_staging 
                WHERE "department" IS NOT NULL AND "department" != '' 
                GROUP BY "department" HAVING COUNT(*) < 3
            )
        """
    },
    {
        'nome': '29. Zombie Containers',
        'dimensao': 'Precisão',
        'tabelas': 'ad_ous_staging',
        'impacto': 'OUs mortas.',
        'sql': """
            SELECT ou."distinguishedName" as origem, 'OU Zumbi' as detalhe
            FROM ad_ous_staging ou
            WHERE NOT EXISTS (
                SELECT 1 FROM ad_users_staging u WHERE u."distinguishedName" LIKE '%' || ou."distinguishedName" 
                AND (u."userAccountControl" ~ '^[0-9]+$' AND (CAST(u."userAccountControl" AS INTEGER) & 2) = 0)
            )
            AND NOT EXISTS (
                SELECT 1 FROM ad_computers_staging c WHERE c."distinguishedName" LIKE '%' || ou."distinguishedName" 
                AND (LENGTH(c."lastLogonTimestamp") > 10 AND CAST(c."lastLogonTimestamp" AS TIMESTAMPTZ) > NOW() - INTERVAL '90 days')
            )
        """
    },

    # ==============================================================================
    # GRUPO 6: UNICIDADE DE LINHA (Clones)
    # ==============================================================================
    {
        'nome': '30. Duplicidade de Linha (Usuários)',
        'dimensao': 'Unicidade',
        'tabelas': 'ad_users_staging',
        'impacto': 'Registro duplicado.',
        'sql': """
            SELECT "cn" as origem, 'Clone' as detalhe
            FROM ad_users_staging
            WHERE "distinguishedName" IN (SELECT "distinguishedName" FROM ad_users_staging GROUP BY "distinguishedName" HAVING COUNT(*) > 1)
        """
    },
    {
        'nome': '31. Duplicidade de Linha (Computadores)',
        'dimensao': 'Unicidade',
        'tabelas': 'ad_computers_staging',
        'impacto': 'Registro duplicado.',
        'sql': """
            SELECT "cn" as origem, 'Clone' as detalhe
            FROM ad_computers_staging
            WHERE "distinguishedName" IN (SELECT "distinguishedName" FROM ad_computers_staging GROUP BY "distinguishedName" HAVING COUNT(*) > 1)
        """
    },
    {
        'nome': '32. Duplicidade de Linha (Grupos)',
        'dimensao': 'Unicidade',
        'tabelas': 'ad_groups_staging',
        'impacto': 'Registro duplicado.',
        'sql': """
            SELECT "cn" as origem, 'Clone' as detalhe
            FROM ad_groups_staging
            WHERE "distinguishedName" IN (SELECT "distinguishedName" FROM ad_groups_staging GROUP BY "distinguishedName" HAVING COUNT(*) > 1)
        """
    },
    {
        'nome': '33. Duplicidade de Linha (OUs)',
        'dimensao': 'Unicidade',
        'tabelas': 'ad_ous_staging',
        'impacto': 'Registro duplicado.',
        'sql': """
            SELECT "ou" as origem, 'Clone' as detalhe
            FROM ad_ous_staging
            WHERE "distinguishedName" IN (SELECT "distinguishedName" FROM ad_ous_staging GROUP BY "distinguishedName" HAVING COUNT(*) > 1)
        """
    },
    
    # ==============================================================================
    # NOVAS REGRAS DE IDENTIDADE
    # ==============================================================================
    {
        'nome': '34. Múltiplas Contas - Mesmo E-mail',
        'dimensao': 'Unicidade',
        'tabelas': 'ad_users_staging',
        'impacto': 'E-mail duplicado.',
        'sql': """
            SELECT "mail" as origem, 'Duplicado' as detalhe
            FROM ad_users_staging
            WHERE "mail" IS NOT NULL AND "mail" != ''
            GROUP BY "mail" HAVING COUNT(*) > 1
        """
    },
    {
        'nome': '35. Múltiplas Contas - Mesmo Nome Completo',
        'dimensao': 'Unicidade',
        'tabelas': 'ad_users_staging',
        'impacto': 'Nomes idênticos.',
        'sql': """
            SELECT "cn" as origem, 'Duplicado' as detalhe
            FROM ad_users_staging
            WHERE "cn" IS NOT NULL AND "cn" != ''
            GROUP BY "cn" HAVING COUNT(*) > 1
        """
    },
    {
        'nome': '36. Possível Conta Admin Vinculada',
        'dimensao': 'Consistência',
        'tabelas': 'ad_users_staging',
        'impacto': 'Conta administrativa secundária.',
        'sql': """
            SELECT u1."sAMAccountName" as origem, 'Par: ' || u2."sAMAccountName" as detalhe
            FROM ad_users_staging u1
            JOIN ad_users_staging u2 ON u1."sAMAccountName" LIKE '%' || u2."sAMAccountName" || '%'
            WHERE u1."id" != u2."id" AND LENGTH(u2."sAMAccountName") > 4 AND (u1."sAMAccountName" LIKE 'adm.%' OR u1."sAMAccountName" LIKE 'admin.%')
        """
    }
]