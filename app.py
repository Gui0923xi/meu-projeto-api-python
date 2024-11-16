from flask import Flask, request, jsonify
import re
import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)

### Funções de Regex Automático ###

def gerar_regex_automatico(valores):
    """
    Gera padrões regex automaticamente com base nos dados fornecidos.
    """
    regex_map = {}
    
    for valor in valores:
        valor_limpo = re.sub(r"[^\w\s]", "", valor.lower().strip())
        
        if "até" in valor_limpo or "abaixo" in valor_limpo or "menor" in valor_limpo:
            regex_map[valor] = r"(até|abaixo_de|ate|menor_que|menor).*"
        elif "entre" in valor_limpo:
            regex_map[valor] = r"entre\s*\d+[.,]?\d*\s*e\s*\d+[.,]?\d*"
        elif "acima" in valor_limpo or "maior" in valor_limpo:
            regex_map[valor] = r"(maior_que|acima_de|maior|acima).*"
        else:
            regex_map[valor] = r".*"  # Padrão genérico caso nenhuma regra seja detectada
    
    return regex_map

def limpar_e_mapear_automatico(valor, regex_map):
    """
    Mapeia um valor para uma faixa com base no regex gerado automaticamente.
    """
    valor_limpo = valor.lower().strip()
    for padrao, descricao in regex_map.items():
        if re.search(descricao, valor_limpo):
            return padrao  # Retorna o padrão original como a faixa correspondente
    return "Faixa não identificada"

### Conexão com Google Sheets ###

def conectar_google_sheets(sheet_name, range_name):
    """
    Conecta ao Google Sheets usando as credenciais e retorna os dados.
    """
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name('credenciais.json', scope)
    client = gspread.authorize(credentials)

    # Acesse o Google Sheets
    sheet = client.open(sheet_name).sheet1

    # Obtenha os valores da faixa especificada
    dados = sheet.get(range_name)
    return sheet, dados

def atualizar_google_sheets(sheet, range_name, valores):
    """
    Atualiza o Google Sheets com os valores processados.
    """
    cell_range = f"{range_name.split(':')[0]}2:{range_name.split(':')[1]}"
    sheet.update(cell_range, valores)

### Endpoint Principal ###

@app.route('/process-sheets', methods=['POST'])
def processar_sheets():
    """
    Processa dados do Google Sheets em massa e retorna o resultado.
    """
    payload = request.json
    sheet_name = payload.get("sheet_name")
    range_name = payload.get("range_name")

    # Obter dados do Google Sheets
    sheet, dados = conectar_google_sheets(sheet_name, range_name)

    # Extraindo valores da primeira coluna (Valor Sujo)
    valores_para_regex = [row[0] for row in dados if row]

    # Gerar regex automaticamente com base nos dados
    regex_map = gerar_regex_automatico(valores_para_regex)

    # Processar os valores usando regex automático
    resultados = []
    for valor in valores_para_regex:
        faixa = limpar_e_mapear_automatico(valor, regex_map)
        resultados.append([faixa])  # Atualiza os resultados para a próxima coluna

    # Atualizar Google Sheets com os valores processados
    atualizar_google_sheets(sheet, range_name, resultados)

    return jsonify({"message": "Dados processados e atualizados no Google Sheets com sucesso."})

### Execução da API ###

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
