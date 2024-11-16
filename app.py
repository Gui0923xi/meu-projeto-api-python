from flask import Flask, request, jsonify
import re

app = Flask(__name__)

# Endpoint para gerar regex
@app.route('/update-regex', methods=['POST'])
def atualizar_regex():
    """
    Recebe uma lista de dados e gera regex dinamicamente.
    """
    try:
        dados = request.json.get("dados", [])
        if not dados or not isinstance(dados, list):
            return jsonify({"erro": "Nenhum dado válido fornecido"}), 400

        regex_map = gerar_regex(dados)
        return jsonify({"mensagem": "Regex atualizado com sucesso", "regex": regex_map}), 200

    except Exception as e:
        return jsonify({"erro": f"Erro ao atualizar regex: {str(e)}"}), 500

# Função para gerar regex dinamicamente com base nos dados
def gerar_regex(dados):
    """
    Gera um dicionário de regex baseados nos padrões de entrada.
    """
    regex_map = {}

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

# Endpoint para processar dados com regex enviado na requisição
@app.route('/process', methods=['POST'])
def processar_dados():
    """
    Processa os dados recebidos aplicando os regex enviados na requisição.
    """
    try:
        dados = request.json.get("dados", [])
        regex_map = request.json.get("regex", {})

        if not dados or not isinstance(dados, list):
            return jsonify({"erro": "Nenhum dado válido fornecido"}), 400

        if not regex_map or not isinstance(regex_map, dict):
            return jsonify({"erro": "Nenhum regex válido fornecido"}), 400

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

if __name__ == '__main__':
    app.run(debug=True)
