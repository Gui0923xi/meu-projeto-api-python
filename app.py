import openai
from flask import Flask, request, jsonify
import re

app = Flask(__name__)

import openai

openai.api_key = "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"

def gerar_regex(dados):
    try:
        prompt = f"Crie regex para os seguintes dados: {dados}"
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Você é um assistente especializado em gerar expressões regulares (regex)."},
                {"role": "user", "content": prompt}
            ]
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        return f"Erro ao gerar regex: {str(e)}"


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
