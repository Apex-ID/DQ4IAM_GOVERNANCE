# construtor_schemas/utils.py
import docx
import pdfplumber
import re
import logging

logger = logging.getLogger(__name__)

def normalizar_texto(texto):
    """Limpa espaços, quebras de linha e caracteres invisíveis."""
    if not texto: return ""
    return texto.strip().replace('\n', ' ').replace('\r', '')

def limpar_nome_coluna(nome):
    """Garante que o nome da coluna seja seguro para SQL (snake_case)."""
    # Remove acentos e caracteres especiais, mantendo letras, numeros e _
    nome = normalizar_texto(nome).lower()
    # Substitui espaços por underline
    nome = re.sub(r'\s+', '_', nome)
    # Remove tudo que não for alfanumérico ou _
    nome = re.sub(r'[^a-z0-9_]', '', nome)
    return nome

def processar_dicionario(arquivo, extensao):
    if extensao == '.docx':
        return ler_docx(arquivo)
    elif extensao == '.pdf':
        return ler_pdf(arquivo)
    return []

def ler_docx(arquivo):
    doc = docx.Document(arquivo)
    estrutura = []
    
    for table in doc.tables:
        # Tenta identificar se a tabela é de dicionário de dados
        # Procurando cabeçalhos comuns
        if not table.rows: continue
        
        # Pega o texto da primeira linha para identificar colunas
        headers = [cell.text.lower().strip() for cell in table.rows[0].cells]
        
        # Mapeamento dinâmico de índices
        idx_nome = -1
        idx_tipo = -1
        idx_desc = -1
        
        for i, h in enumerate(headers):
            if 'atributo' in h or 'coluna' in h or 'campo' in h: idx_nome = i
            elif 'tipo' in h: idx_tipo = i
            elif 'descri' in h: idx_desc = i
            
        # Se não achou colunas de Nome e Tipo, pula a tabela
        if idx_nome == -1 or idx_tipo == -1:
            continue
            
        # Itera sobre as linhas de dados
        for row in table.rows[1:]:
            cells = row.cells
            try:
                nome_bruto = cells[idx_nome].text
                tipo_bruto = cells[idx_tipo].text
                desc_bruto = cells[idx_desc].text if idx_desc != -1 else ""

                nome_sql = limpar_nome_coluna(nome_bruto)
                
                # Ignora linhas vazias ou cabeçalhos repetidos
                if not nome_sql or nome_sql == 'nome_do_atributo':
                    continue

                estrutura.append({
                    'coluna_original': nome_bruto,
                    'coluna_sql': nome_sql,
                    'tipo_original': normalizar_texto(tipo_bruto),
                    'tipo_sql': sanitizar_tipo_sql(tipo_bruto), # Função inteligente
                    'descricao': normalizar_texto(desc_bruto)
                })
            except IndexError:
                continue
                
    return estrutura

def ler_pdf(arquivo):
    # (Implementação simplificada mantida, foco no DOCX que é seu padrão)
    estrutura = []
    try:
        with pdfplumber.open(arquivo) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    if not table: continue
                    # Lógica simplificada: assume col 0 = nome, col 1 = tipo
                    if "Atributo" in str(table[0]) or "Coluna" in str(table[0]):
                        for row in table[1:]:
                            if row[0]:
                                estrutura.append({
                                    'coluna_original': row[0],
                                    'coluna_sql': limpar_nome_coluna(row[0]),
                                    'tipo_original': row[1],
                                    'tipo_sql': sanitizar_tipo_sql(row[1]),
                                    'descricao': row[2] if len(row) > 2 else ""
                                })
    except Exception as e:
        logger.error(f"Erro ao ler PDF: {e}")
    return estrutura

def sanitizar_tipo_sql(texto_tipo):
    """
    Converte o texto do Word (ex: 'Texto Livre', 'Numérico') para tipos PostgreSQL.
    """
    t = texto_tipo.upper()
    
    # Mapeamento inteligente
    if 'TIMESTAMPTZ' in t: return 'TIMESTAMPTZ'
    if 'TIMESTAMP' in t: return 'TIMESTAMP'
    if 'DATE' in t: return 'DATE'
    if 'BIGINT' in t: return 'BIGINT'
    if 'INTEGER' in t or 'INT' in t: return 'INTEGER'
    if 'UUID' in t: return 'UUID'
    if 'BOOLEAN' in t: return 'BOOLEAN'
    if 'TEXT' in t: return 'TEXT'
    
    # Captura VARCHAR com tamanho: "VARCHAR(255)"
    varchar_match = re.search(r'VARCHAR\s*\((\d+)\)', t)
    if varchar_match:
        return f"VARCHAR({varchar_match.group(1)})"
    
    if 'CHAR' in t: return 'VARCHAR(255)'
    
    return 'TEXT' # Fallback seguro