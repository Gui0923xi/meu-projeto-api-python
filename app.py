import os
from flask import Flask, request, jsonify
import pandas as pd
import re

app = Flask(__name__)

# Definição das faixas para o processamento
faixas = {
    r"(até|abaixo_de|ate|menor_que|menor)[ _de]*r?\$?\s*2[.,]?800": "Abaixo de R$2.800",
    r"(entre|r?)\s*r?\$?\s*2[.,]?801[ _a_e]*r?\$?\s*3[.,]?200": "Entre R$2.801 e R$3.200",
    r"(entre|r?)\s*r?\$?\s*3[.,]?201[ _a_e]*r?\$?\s*3[.,]?600": "Entre R$3.201 e R$3.600",
    r"(entre|r?)\s*r?\$?\s*3[.,]?601[ _a_e]*r?\$?\s*4[.,]?000": "Entre R$3.601 e R$4.000",
    r"(maior_que|acima_de|maior|acima)[ _de]*r?\$?\s*4[.,]?000": "Acima de R$4.000",
}

def limpar_e_mapear(valor):
    valor = valor.lower().strip()
    for padrao, faixa in faixas.items():
        if re.search(padrao, valor):
            return faixa
    return "Faixa não identificada"

@app.route('/process', methods=['POST'])
def process():
    # Recebe uma lista de valores "sujos" em um array JSON
    dados = request.json.get("dados", [])
    
    # Processa cada valor na lista e mapeia para a faixa padronizada correspondente
    resultados = [{"Valor sujo": item["Valor sujo"], "Faixa padronizada": limpar_e_mapear(item["Valor sujo"])} for item in dados]
    
    # Retorna os resultados como uma lista JSON
    return jsonify(resultados)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
