import pandas as pd
import streamlit as st

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(layout="wide", page_title="Consulta de Vagas")

# --- TÍTULO E DESCRIÇÃO ---
st.title("Consulta de Vagas por Apartamento - 2020 a 2024")
st.markdown("Selecione sua torre e apartamento na barra lateral para verificar o tipo de vaga (coberta ou descoberta) para cada ano.")

# --- CARREGAMENTO DOS DADOS ---
# Altere para o nome do seu arquivo CSV.
ARQUIVO_DADOS_CSV = "relacao_de_vagas.csv"

@st.cache_data
def carregar_dados_csv(caminho_arquivo):
    """Carrega dados de um arquivo CSV com formato específico e o transforma."""
    try:
        # Lê o arquivo CSV, pulando as duas primeiras linhas de cabeçalho irregular
        # e define os nomes das colunas manualmente.
        # Assume que o separador é Tab ('\t'). Se for vírgula, mude para sep=','.
        df = pd.read_csv(
            caminho_arquivo,
            sep=',',
        )
              # --- Transformação dos Dados ---
        # 1. Separar a coluna 'Unidade' em 'Torre' e 'Apto'
        split_cols = df['Unidade'].astype(str).str.split('-', n=1, expand=True)
        if split_cols.shape[1] != 2:
            st.error("Não foi possível dividir a coluna 'Unidade' em 'Torre' e 'Apto'. Verifique se o formato é 'Torre-Apto' (ex: '1-101') em todas as linhas.")
            return None
        df[['Torre', 'Apto']] = split_cols

        # 2. Renomear as colunas de ano para o formato esperado pela aplicação
                # Garante que as colunas de filtro sejam do tipo string
        df['Torre'] = df['Torre'].astype(str)
        df['Apto'] = df['Apto'].astype(str)

        return df
    except FileNotFoundError:
        st.error(f"Arquivo '{caminho_arquivo}' não encontrado. Verifique o nome e se ele está na mesma pasta que o script.")
        return None
    except pd.errors.EmptyDataError:
        st.error(f"O arquivo CSV '{caminho_arquivo}' está vazio ou não contém dados após as duas primeiras linhas.")
        return None
    except Exception as e:
        st.error(f"Ocorreu um erro ao carregar ou processar o arquivo CSV: {e}")
        return None

df = carregar_dados_csv(ARQUIVO_DADOS_CSV)

# --- INTERFACE DO USUÁRIO E LÓGICA PRINCIPAL ---
if df is not None:
    st.sidebar.header("Filtros para Consulta")

    # Filtro de Torre
    torres = sorted(df['Torre'].unique())
    torre_selecionada = st.sidebar.selectbox(
        "Selecione a Torre",
        options=torres
    )

    # Filtro de Apartamento (as opções são atualizadas com base na torre selecionada)
    apartamentos = sorted(df[df['Torre'] == torre_selecionada]['Apto'].unique())
    apto_selecionado = st.sidebar.selectbox(
        "Selecione o Apartamento",
        options=apartamentos
    )

    st.divider()

    # --- EXIBIÇÃO DOS RESULTADOS ---
    st.header(f"Resultado para: Torre {torre_selecionada} - Apto {apto_selecionado}")

    # Filtra o DataFrame para encontrar a linha correspondente à seleção do usuário
    resultado = df.loc[(df['Torre'] == torre_selecionada) & (df['Apto'] == apto_selecionado)]

    if not resultado.empty:
        dados_vaga = resultado.iloc[0]
        colunas_ano = ['2020', '2021', '2022', '2023','2024']
        col1, col2, col3, col4,col5 = st.columns(5)
        colunas_st = [col1, col2, col3, col4,col5]

        for i, col_ano in enumerate(colunas_ano, 1):
            with colunas_st[i-1]:
                # Adicionamos .strip() para remover espaços em branco no início ou fim do texto
                tipo_vaga = str(dados_vaga[col_ano]).strip()
                st.metric(label=f"{i}° Ano do Sorteio", value=tipo_vaga)
                
    else:
        st.warning("Nenhuma informação encontrada para a combinação de Torre e Apartamento selecionada.")

    # --- SEÇÃO DE ANÁLISE GERAL ---
    st.divider()
    st.header("Análise Geral do Sorteio")

    with st.expander("Clique para ver a análise de vagas cobertas"):
        # --- LÓGICA DA ANÁLISE ---
        colunas_ano = ['2020', '2021', '2022', '2023','2024']
        
        # Cria uma cópia do DataFrame para a análise
        df_analise = df.copy()
        
        # Calcula a contagem de vagas 'coberta' para cada unidade.
        # O .sum(axis=1) soma os valores True (que são tratados como 1) para cada linha.
        df_analise['contagem_cobertas'] = df_analise[colunas_ano].apply(
            lambda x: x.str.strip().str.lower().eq('coberta')
        ).sum(axis=1)

        # --- EXIBIÇÃO DA ANÁLISE ---
        col1_analise, col2_analise = st.columns(2)

        with col1_analise:
            # 1. Unidades com mais de uma vaga coberta
            mais_de_uma_coberta = df_analise[df_analise['contagem_cobertas'] > 1].sort_values(by=['Torre', 'Apto'])
            
            st.subheader("Unidades com Vaga Coberta > 1 Vez")
            if not mais_de_uma_coberta.empty:
                # Formata a saída para ser mais legível
                unidades_sortudas = mais_de_uma_coberta.apply(
                    lambda row: f"Torre {row['Torre']} Apto {row['Apto']} ({row['contagem_cobertas']} vezes)", 
                    axis=1
                ).reset_index(drop=True)
                st.dataframe(unidades_sortudas, use_container_width=True)
            else:
                st.info("Nenhuma unidade foi contemplada com vaga coberta mais de uma vez.")

        with col2_analise:
            # 2. Unidades que nunca tiveram vaga coberta
            nenhuma_coberta = df_analise[df_analise['contagem_cobertas'] == 0].sort_values(by=['Torre', 'Apto'])
            st.subheader("Unidades que Nunca Tiveram Vaga Coberta")
            if not nenhuma_coberta.empty:
                st.dataframe(nenhuma_coberta[['Torre', 'Apto']], use_container_width=True)
            else:
                st.info("Todas as unidades foram contempladas com vaga coberta ao menos uma vez.")
else:
    st.warning("Não foi possível carregar os dados. Verifique as mensagens de erro acima.")
