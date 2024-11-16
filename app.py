from flask import Flask, request, jsonify
import re

app = Flask(__name__)

# Função para detectar padrões dinamicamente
def gerar_regex(dados):
    """
    Gera automaticamente regexs baseadas nas variações encontradas nos dados.
    """
    faixas = {
        "Abaixo de R$2.800": r"(até|abaixo_de|ate|menor_que|menor)[ _de]*r?\$?\s*2[.,]?800",
        "Entre R$2.801 e R$3.200": r"(entre|r?)\s*r?\$?\s*2[.,]?801[ _a_e]*r?\$?\s*3[.,]?200",
        "Entre R$3.201 e R$3.600": r"(entre|r?)\s*r?\$?\s*3[.,]?201[ _a_e]*r?\$?\s*3[.,]?600",
        "Entre R$3.601 e R$4.000": r"(entre|r?)\s*r?\$?\s*3[.,]?601[ _a_e]*r?\$?\s*4[.,]?000",
        "Entre R$4.001 e R$4.400": r"(entre|r?)\s*r?\$?\s*4[.,]?001[ _a_e]*r?\$?\s*4[.,]?400",
        "Entre R$4.401 e R$4.800": r"(entre|r?)\s*r?\$?\s*4[.,]?401[ _a_e]*r?\$?\s*4[.,]?800",
        "Acima de R$4.000": r"(maior_que|acima_de|maior|acima)[ _de]*r?\$?\s*4[.,]?000",
        "Acima de R$4.800": r"(maior_que|acima_de|maior|acima)[ _de]*r?\$?\s*4[.,]?800"
    }

    # Basear-se nos dados recebidos para buscar variações não mapeadas
    variações_detectadas = {}
    for valor in dados:
        texto = valor.lower().strip()
        match_found = False

        for faixa, regex in faixas.items():
            if re.search(regex, texto):
                variações_detectadas[texto] = faixa
                match_found = True
                break

        if not match_found:
            variações_detectadas[texto] = "Faixa não identificada"

    return variações_detectadas

@app.route('/process', methods=['POST'])
def process():
    """
    Endpoint para processar múltiplos valores de uma só vez.
    """
    # Recebe os dados como JSON
    dados = request.json.get("dados", [])
    
    # Extrai os valores sujos da entrada
    valores_sujos = [valor.get("Valor sujo", "") for valor in dados]
    
    # Gera as regex dinâmicas
    resultados = gerar_regex(valores_sujos)

    # Monta a resposta com os resultados padronizados
    resposta = [
        {"Valor sujo": valor, "Faixa padronizada": faixa}
        for valor, faixa in resultados.items()
    ]
    
    return jsonify(resposta)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
