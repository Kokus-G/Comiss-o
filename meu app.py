import streamlit as st
import pandas as pd
import pyodbc
import toml
from datetime import datetime, timedelta, time
from PIL import Image

# Carregar as configurações do TOML
with open("config.toml", "r") as f:
    config = toml.load(f)

# Extrair as configurações do banco de dados
driver = config['database']['driver']
server = config['database']['server']
database = config['database']['database']
uid = config['database']['uid']
pwd = config['database']['pwd']

# Montar a string de conexão
dados_conexao = f"Driver={{{driver}}};Server={server};Database={database};UID={uid};PWD={pwd};"

# Configurações de layout da página do Streamlit
st.set_page_config(layout="wide")

# Estabelecendo a conexão
try:
    conexao = pyodbc.connect(dados_conexao)
    cursor = conexao.cursor()
    st.success("Conexão estabelecida com sucesso!")
except pyodbc.Error as e:
    st.error(f"Erro ao estabelecer a conexão: {e}")

# Dados dos usuários autorizados (usuário: senha)
usuarios_autorizados = {
    "cristiano": "4",
    "tiano": "5",
    "marcos": "6",
    "kaike": "7",
    "amilton": "13",
    "titi": "14",
    "sousa": "15",
    "jefferson": "16",
    "reginaldo": "17",
    "severino": "19",
    "matheus": "20",
    "ernesto": "21",
    "adriano": "23",
    "neto": "26",
    "andrielle": "30",
    "ph": "90",
    "chagas": "92",
    "fernando": "3"
}

# Lista de usuários não sujeitos ao desconto de R$20
usuarios_isentos = ["matheus", "anderson"]

# Função para autenticar o usuário
def autenticar_usuario(username, password):
    return usuarios_autorizados.get(username.lower()) == password

# Função para carregar os dados do banco de dados
@st.cache_data()  # Cache para otimizar o carregamento dos dados
def carregar_dados(data_inicio, data_fim):
    # Formatar as datas no formato SQL
    data_inicio = data_inicio.strftime('%Y-%m-%d %H:%M:%S')
    data_fim = data_fim.strftime('%Y-%m-%d %H:%M:%S')

    # Comando SQL para obter os dados no intervalo de datas
    comando = f"""
    SELECT [Código Vendedor], [Data/Hora Vencimento], [Nº Cupom], [Valor], [ValorLiquido]
    FROM [MISTERCHEFNET].[dbo].[Comissões]
    WHERE [Data/Hora Vencimento] >= '{data_inicio}'
    AND [Data/Hora Vencimento] <= '{data_fim}'
    """
    try:
        cursor.execute(comando)
        resultados = cursor.fetchall()
        colunas = [column[0] for column in cursor.description]
        df_comissao = pd.DataFrame.from_records(resultados, columns=colunas)
        st.write("Dados carregados do banco de dados:", df_comissao)  # Debugging
        return df_comissao
    except pyodbc.Error as e:
        st.error(f"Erro ao executar o comando SQL: {e}")
        return pd.DataFrame()

# Layout do aplicativo
def main():
    # Página de Login
    st.title("Intranet Zero Grau")
    username = st.sidebar.text_input("Usuário")
    password = st.sidebar.text_input("Senha", type="password")

    # Filtro de data
    st.sidebar.write("Selecione o intervalo de datas:")
    data_inicio_default = datetime.combine(datetime.today() - timedelta(days=7), time(10, 30))
    data_fim_default = datetime.combine(datetime.today(), time(10, 29))
    data_inicio = st.sidebar.date_input("Data de Início", data_inicio_default.date(), format="DD/MM/YYYY")
    data_fim = st.sidebar.date_input("Data de Fim", data_fim_default.date(), format="DD/MM/YYYY")

    # Ajuste os horários para as datas selecionadas
    data_inicio = datetime.combine(data_inicio, time(10, 30))
    data_fim = datetime.combine(data_fim, time(10, 29))

    if st.sidebar.button("Login"):
        if autenticar_usuario(username, password):
            st.sidebar.success("Login bem-sucedido!")
            mostrar_dashboard(username, data_inicio, data_fim)
            return  # Saia da função para não renderizar a página de login novamente
        else:
            st.sidebar.error("Usuário ou senha incorretos.")

    # Mostrar a imagem inicial se o login não for bem-sucedido ou ainda não foi feito
    try:
        logo_restaurante = Image.open("C:/Users/Terminal 1/mu_code/images/zero_grau.png")
    except FileNotFoundError:
        st.error("Imagem não encontrada.")
        return

    st.image(logo_restaurante, use_column_width=True)

# Mostrar dashboard do usuário logado
def mostrar_dashboard(username, data_inicio, data_fim):
    codigo_vendedor = usuarios_autorizados.get(username.lower())
    if codigo_vendedor is None:
        st.error("Código do vendedor não encontrado.")
        return

    df_comissao = carregar_dados(data_inicio, data_fim)

    # Verificar se a coluna "Código Vendedor" existe no DataFrame
    if "Código Vendedor" not in df_comissao.columns:
        st.error("Coluna 'Código Vendedor' não encontrada no DataFrame.")
        return

    # Filtrar o DataFrame com base no código do vendedor logado
    df_filtrado = df_comissao[df_comissao["Código Vendedor"].astype(str) == str(codigo_vendedor)]
    st.write(f"Dados filtrados para o vendedor {username} ({codigo_vendedor}):", df_filtrado)  # Debugging

    # Exibir o DataFrame filtrado
    st.dataframe(df_filtrado)

    # Calcular o ticket médio
    if "Nº Cupom" in df_filtrado.columns and "Valor" in df_filtrado.columns:
        valor_total = df_filtrado["Valor"].astype(float).sum()
        numero_pedidos = df_filtrado["Nº Cupom"].nunique()  # Contar número único de cupons
        if numero_pedidos > 0:
            ticket_medio = valor_total / numero_pedidos * 10
        else:
            ticket_medio = 0
        st.markdown(f"<h2 style='color: blue;'>Ticket Médio: R${ticket_medio:.2f}</h2>", unsafe_allow_html=True)
    else:
        st.warning("Não foi possível calcular o ticket médio.")

    # Calcular o valor líquido total e a comissão a receber (70% do valor líquido total)
    if "ValorLiquido" in df_filtrado.columns:
        valor_liquido_total = df_filtrado["ValorLiquido"].astype(float).sum()  # Conversão para float
        comissao_a_receber = float(valor_liquido_total) * 0.7
        st.markdown(f"<h2 style='color: green;'>Comissão a Receber: R${comissao_a_receber:.2f}</h2>", unsafe_allow_html=True)

        # Calcular a comissão real
        if username.lower() not in usuarios_isentos:
            comissao_real = comissao_a_receber - 20
        else:
            comissao_real = comissao_a_receber
        st.markdown(f"<h2 style='color: red;'>Comissão Real: R${comissao_real:.2f}</h2>", unsafe_allow_html=True)
    else:
        st.warning("Não foi possível calcular a comissão a receber.")

    # Gráfico do ticket médio
    st.title("Gráfico de Ticket Médio")
    if "Data/Hora Vencimento" in df_filtrado.columns:
        df_filtrado['Data/Hora Vencimento'] = pd.to_datetime(df_filtrado['Data/Hora Vencimento'])
        df_filtrado = df_filtrado.set_index('Data/Hora Vencimento')
        df_diario = df_filtrado.resample('D').agg({'Valor': 'sum', 'Nº Cupom': 'nunique'})
        df_diario['Ticket Médio'] = df_diario.apply(lambda row: row['Valor'] / row['Nº Cupom'] if row['Nº Cupom'] > 0 else 0, axis=1)

        # Garantir que o gráfico de gauge seja exibido corretamente
        import plotly.graph_objs as go

        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = ticket_medio,
            title = {'text': "Ticket Médio"},
            gauge = {
                'axis': {'range': [None, 500]},
                'steps': [
                    {'range': [0, 100], 'color': "#ADD8E6"},  # Light Blue
                    {'range': [100, 250], 'color': "#FFA500"},  # Orange
                    {'range': [250, 500], 'color': "#8B0000"}  # Dark Red
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': ticket_medio
                }
            }
        ))

        st.plotly_chart(fig)
    else:
        st.warning("Não foi possível gerar o gráfico de ticket médio.")

# Iniciar o aplicativo
if __name__ == "__main__":
    main()
