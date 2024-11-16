from flask import Flask, request, jsonify
import re

app = Flask(__name__)

# Armazena os regex gerados dinamicamente
regex_map = {}

# Função para gerar regex dinamicamente com base nos dados
def gerar_regex(dados):
    """
    Gera um dicionário de regex baseados nos padrões de entrada.
    """
    global regex_map
    regex_map = {}  # Limpa o mapa de regex antes de gerar novos

    for item in dados:
        if re.search(r"r\$[0-9]+[.,]?[0-9]*_a_r\$[0-9]+[.,]?[0-9]*", item):
            matches = re.findall(r"r\$[0-9]+[.,]?[0-9]*_a_r\$[0-9]+[.,]?[0-9]*", item)
            for match in matches:
                valor1, valor2 = match.replace("r$", "").replace("_a_", " ").split(" ")
                regex_map[rf"{re.escape(match)}"] = f"Entre R${valor1} e R${valor2}"

        elif re.search(r"maior_que_r\$[0-9]+[.,]?[0-9]*", item):
            matches = re.findall(r"maior_que_r\$[0-9]+[.,]?[0-9]*", item)
            for match in matches:
                valor = match.replace("maior_que_r$", "")
                regex_map[rf"{re.escape(match)}"] = f"Maior que R${valor}"

        elif re.search(r"até_r\$[0-9]+[.,]?[0-9]*", item):
            matches = re.findall(r"até_r\$[0-9]+[.,]?[0-9]*", item)
            for match in matches:
                valor = match.replace("até_r$", "")
                regex_map[rf"{re.escape(match)}"] = f"Até R${valor}"

    return regex_map


# Endpoint para atualizar os regex
@app.route('/update-regex', methods=['POST'])
def atualizar_regex():
    """
    Recebe uma lista de dados e gera regex dinamicamente.
    """
    try:
        dados = request.json.get("dados", [])
        if not dados or not isinstance(dados, list):
            return jsonify({"erro": "Nenhum dado válido fornecido"}), 400

        regex_gerados = gerar_regex(dados)
        return jsonify({"mensagem": "Regex atualizado com sucesso", "regex": regex_gerados}), 200

    except Exception as e:
        return jsonify({"erro": f"Erro ao atualizar regex: {str(e)}"}), 500


# Endpoint para processar os dados
@app.route('/process', methods=['POST'])
def processar_dados():
    """
    Processa os dados recebidos aplicando os regex gerados.
    """
    try:
        dados = request.json.get("dados", [])
        if not dados or not isinstance(dados, list):
            return jsonify({"erro": "Nenhum dado válido fornecido"}), 400

        if not regex_map:
            return jsonify({"erro": "Nenhum regex foi configurado. Atualize os regex primeiro."}), 400

        resultados = []
        for item in dados:
            resultado = []
            for padrao, descricao in regex_map.items():
                if re.search(padrao, item):
                    resultado.append(descricao)
            resultados.append(", ".join(resultado) if resultado else "Faixa não identificada")

        return jsonify({"resultados": resultados}), 200

    except Exception as e:
        return jsonify({"erro": f"Erro ao processar os dados: {str(e)}"}), 500


# Endpoint para consultar os regex atuais
@app.route('/get-regex', methods=['GET'])
def consultar_regex():
    """
    Retorna os regex atualmente configurados.
    """
    return jsonify({"regex": regex_map}), 200


if __name__ == '__main__':
    app.run(debug=True)
