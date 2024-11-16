from flask import Flask, request, jsonify
import re

app = Flask(__name__)

# Definição das faixas com regex automático
faixas = {
    r"(até|abaixo_de|ate|menor_que|menor)[ _de]*r?\$?\s*2[.,]?800": "Abaixo de R$2.800",
    r"(entre|r?)\s*r?\$?\s*2[.,]?801[ _a_e]*r?\$?\s*3[.,]?200": "Entre R$2.801 e R$3.200",
    r"(entre|r?)\s*r?\$?\s*3[.,]?201[ _a_e]*r?\$?\s*3[.,]?600": "Entre R$3.201 e R$3.600",
    r"(entre|r?)\s*r?\$?\s*3[.,]?601[ _a_e]*r?\$?\s*4[.,]?000": "Entre R$3.601 e R$4.000",
    r"(maior_que|acima_de|maior|acima)[ _de]*r?\$?\s*4[.,]?000": "Acima de R$4.000"
}

def limpar_e_mapear(valor):
    valor = valor.lower().strip()
    for padrao, faixa in faixas.items():
        if re.search(padrao, valor):
            return faixa
    return "Faixa não identificada"

@app.route('/process', methods=['POST'])
def processar_dados_em_massa():
    # Recebe a lista de dados do JSON
    entrada = request.json.get("dados", [])
    if not isinstance(entrada, list):
        return jsonify({"error": "Esperado uma lista no campo 'dados'"}), 400

    # Processa cada item no array
    resultado = [{"Valor sujo": item.get("Valor sujo", ""), 
                  "Faixa padronizada": limpar_e_mapear(item.get("Valor sujo", ""))} 
                 for item in entrada]

    # Consolidar o retorno em um único JSON
    return jsonify({"resultados": resultado})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
