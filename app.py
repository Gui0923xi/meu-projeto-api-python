from flask import Flask, request, jsonify
import re

app = Flask(__name__)

# Armazena os regex gerados dinamicamente
regex_map = {}

# Função para gerar regex dinamicamente com base nos dados
def gerar_regex(dados):
    global regex_map
    # Limpa o mapa de regex antes de gerar novos
    regex_map = {}

    # Analisamos os dados para identificar padrões
    for item in dados:
        if re.search(r"r\$[0-9]+[.,]?[0-9]*_a_r\$[0-9]+[.,]?[0-9]*", item):
            match = re.findall(r"r\$[0-9]+[.,]?[0-9]*_a_r\$[0-9]+[.,]?[0-9]*", item)
            for m in match:
                valor1, valor2 = m.replace("r$", "").replace("_a_", " ").split(" ")
                regex_map[rf"{re.escape(m)}"] = f"Entre R${valor1} e R${valor2}"

        elif re.search(r"maior_que_r\$[0-9]+[.,]?[0-9]*", item):
            match = re.findall(r"maior_que_r\$[0-9]+[.,]?[0-9]*", item)
            for m in match:
                valor = m.replace("maior_que_r$", "")
                regex_map[rf"{re.escape(m)}"] = f"Maior que R${valor}"

        elif re.search(r"até_r\$[0-9]+[.,]?[0-9]*", item):
            match = re.findall(r"até_r\$[0-9]+[.,]?[0-9]*", item)
            for m in match:
                valor = m.replace("até_r$", "")
                regex_map[rf"{re.escape(m)}"] = f"Até R${valor}"

    return regex_map


# Endpoint para atualizar os regex
@app.route('/update-regex', methods=['POST'])
def atualizar_regex():
    try:
        # Recebe os dados enviados pelo cliente
        dados = request.json.get("dados", [])
        if not dados:
            return jsonify({"erro": "Nenhum dado fornecido"}), 400

        # Gera os regex dinamicamente
        regex_gerados = gerar_regex(dados)

        return jsonify({"mensagem": "Regex atualizado com sucesso", "regex": regex_gerados}), 200

    except Exception as e:
        return jsonify({"erro": f"Erro ao atualizar regex: {str(e)}"}), 500


# Endpoint para processar os dados
@app.route('/process', methods=['POST'])
def processar_dados():
    try:
        # Recebe os dados enviados pelo cliente
        dados = request.json.get("dados", [])
        if not dados:
            return jsonify({"erro": "Nenhum dado fornecido"}), 400

        # Aplica os regex nos dados
        resultados = []
        for item in dados:
            resultado = []
            for padrao, descricao in regex_map.items():
                if re.search(padrao, item):
                    resultado.append(descricao)
            if not resultado:
                resultado.append("Faixa não identificada")
            resultados.append(", ".join(resultado))

        return jsonify({"resultados": resultados}), 200

    except Exception as e:
        return jsonify({"erro": f"Erro ao processar os dados: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(debug=True)
