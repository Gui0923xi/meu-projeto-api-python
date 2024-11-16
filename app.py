import openai
from flask import Flask, request, jsonify
import re

app = Flask(__name__)

# Configurar sua API Key do OpenAI
openai.api_key = "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"

def obter_regex_chatgpt(valores):
    """
    Envia os valores para o ChatGPT e retorna regex gerados dinamicamente.
    """
    prompt = f"""
    Gere expressões regulares (regex) para identificar as seguintes faixas de valores:
    {valores}

    Retorne um JSON no formato:
    {{
        "regex1": "Descrição da faixa 1",
        "regex2": "Descrição da faixa 2",
        ...
    }}
    """
    try:
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=prompt,
            max_tokens=300,
            temperature=0.5
        )
        regex_data = response["choices"][0]["text"]
        return eval(regex_data.strip())  # Converte a resposta em dicionário
    except Exception as e:
        return {"error": f"Erro ao gerar regex: {str(e)}"}

def limpar_e_mapear(valor, faixas):
    """
    Limpa o valor e aplica o regex gerado dinamicamente.
    """
    valor = re.sub(r'[^\w\s,.R$]', '', valor.lower().strip())
    valor = re.sub(r'[.,]', '', valor)  # Remove pontuações problemáticas
    for padrao, faixa in faixas.items():
        if re.search(padrao, valor):
            return faixa
    return "Faixa não identificada"

@app.route('/process', methods=['POST'])
def processar_dados_com_chatgpt():
    """
    Endpoint que processa os dados utilizando regex gerados pelo ChatGPT.
    """
    entrada = request.json.get("dados", [])
    if not isinstance(entrada, list) or len(entrada) == 0 or not isinstance(entrada[0], str):
        return jsonify({"error": "Esperado um array contendo uma única string no campo 'dados'"}), 400
    
    # Separar os valores enviados em uma lista
    valores = entrada[0].split(',')

    # Obter regex gerados pelo ChatGPT
    faixas = obter_regex_chatgpt(valores)
    if "error" in faixas:
        return jsonify(faixas), 500  # Retorna erro caso falhe a geração do regex

    # Processar os valores
    faixas_padronizadas = []
    for valor in valores:
        faixa = limpar_e_mapear(valor, faixas)
        faixas_padronizadas.append(faixa)
    
    # Retornar apenas os dados padronizados, separados por vírgula
    return jsonify(", ".join(faixas_padronizadas))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
