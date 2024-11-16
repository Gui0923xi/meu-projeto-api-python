from flask import Flask, request, jsonify
import re
import json
import os

app = Flask(__name__)

# Carrega os regex salvos em um arquivo JSON
def carregar_regex():
    if os.path.exists("regex_config.json"):
        with open("regex_config.json", "r") as file:
            return json.load(file)
    return {}

# Salva os regex em um arquivo JSON
def salvar_regex(novos_regex):
    with open("regex_config.json", "w") as file:
        json.dump(novos_regex, file)

# Função para processar dados usando regex
def processar_dados(dados, regex_config):
    resultados = []
    for valor in dados:
        padronizado = "Faixa não identificada"
        for padrao, descricao in regex_config.items():
            if re.search(padrao, valor, re.IGNORECASE):
                padronizado = descricao
                break
        resultados.append(padronizado)
    return resultados

# Endpoint para processar dados
@app.route('/process', methods=['POST'])
def process():
    try:
        entrada = request.json.get("dados", [])
        if not entrada:
            return jsonify({"erro": "Nenhum dado fornecido"}), 400

        # Carrega os regex configurados
        regex_config = carregar_regex()

        # Divide a string de entrada em uma lista separada por vírgula
        dados_lista = [item.strip() for item in entrada[0].split(",")]

        # Processa os dados em massa
        resultados = processar_dados(dados_lista, regex_config)

        # Junta os resultados padronizados em uma única string separada por vírgula
        resposta = ", ".join(resultados)
        return jsonify({"resultado": resposta}), 200

    except Exception as e:
        return jsonify({"erro": f"Erro ao processar os dados: {str(e)}"}), 500

# Endpoint para atualizar regex
@app.route('/update-regex', methods=['POST'])
def update_regex():
    try:
        novos_regex = request.json.get("regex", {})
        if not novos_regex:
            return jsonify({"erro": "Nenhum regex fornecido"}), 400

        # Salva os regex no arquivo
        salvar_regex(novos_regex)
        return jsonify({"mensagem": "Regex atualizado com sucesso"}), 200

    except Exception as e:
        return jsonify({"erro": f"Erro ao atualizar regex: {str(e)}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
