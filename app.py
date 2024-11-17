from flask import Flask, request, jsonify
import re

app = Flask(__name__)

# Armazena os regex gerados dinamicamente
regex_map = {}

# Função para gerar regex dinamicamente com base nos dados
def gerar_regex(dados):
    global regex_map
    regex_map = {}  # Limpa o mapa de regex antes de gerar novos

    for item in dados:
        item = item.lower().strip()  # Normaliza o texto para evitar erros

        # Faixas como "Entre R$X e R$Y" ou "De R$X a R$Y"
        if re.search(r"(entre|de)\s*r\$[0-9]+[.,]?[0-9]*\s*(e|a)\s*r\$[0-9]+[.,]?[0-9]*", item):
            match = re.findall(r"(entre|de)\s*r\$([0-9]+[.,]?[0-9]*)\s*(e|a)\s*r\$([0-9]+[.,]?[0-9]*)", item)
            for m in match:
                valor1, valor2 = m[1], m[3]
                regex_key = rf"r\$?{re.escape(valor1)}.*(e|a).*r\$?{re.escape(valor2)}"
                regex_map[regex_key] = f"Entre R${valor1} e R${valor2}"

        # "Até R$X" -> "Abaixo de R$X"
        elif re.search(r"até\s*r\$[0-9]+[.,]?[0-9]*", item):
            match = re.findall(r"até\s*r\$([0-9]+[.,]?[0-9]*)", item)
            for m in match:
                regex_key = rf"até\s*r\$?{re.escape(m)}"
                regex_map[regex_key] = f"Abaixo de R${m}"

        # "Maior que R$X" -> "Acima de R$X"
        elif re.search(r"(maior|acima)\s*que\s*r\$[0-9]+[.,]?[0-9]*", item):
            match = re.findall(r"(maior|acima)\s*que\s*r\$([0-9]+[.,]?[0-9]*)", item)
            for m in match:
                regex_key = rf"(maior|acima)\s*que\s*r\$?{re.escape(m[1])}"
                regex_map[regex_key] = f"Acima de R${m[1]}"

        # "Menor que R$X" -> "Abaixo de R$X"
        elif re.search(r"(menor|abaixo)\s*que\s*r\$[0-9]+[.,]?[0-9]*", item):
            match = re.findall(r"(menor|abaixo)\s*que\s*r\$([0-9]+[.,]?[0-9]*)", item)
            for m in match:
                regex_key = rf"(menor|abaixo)\s*que\s*r\$?{re.escape(m[1])}"
                regex_map[regex_key] = f"Abaixo de R${m[1]}"

        # Números soltos como "R$X"
        elif re.match(r"^r\$[0-9]+[.,]?[0-9]*$", item):
            valor = item.replace("r$", "")
            regex_key = rf"r\$?{re.escape(valor)}"
            regex_map[regex_key] = f"Abaixo de R${valor}"

    return regex_map


# Endpoint para atualizar os regex
@app.route('/update-regex', methods=['POST'])
def atualizar_regex():
    try:
        # Recebe os dados enviados pelo cliente
        dados = request.json.get("dados", "").split(",")
        if not dados:
            return jsonify({"erro": "Nenhum dado fornecido"}), 400

        # Gera os regex dinamicamente
        regex_gerados = gerar_regex(dados)

        # Retorna apenas o regex limpo, sem mensagens adicionais
        return jsonify(regex_gerados), 200

    except Exception as e:
        return jsonify({"erro": f"Erro ao atualizar regex: {str(e)}"}), 500


# Endpoint para processar os dados
@app.route('/process', methods=['POST'])
def processar_dados():
    try:
        # Recebe os dados enviados pelo cliente
        dados = request.json.get("dados", "").split(",")
        regex = request.json.get("regex", {})

        if not dados or not regex:
            return jsonify({"erro": "Dados ou regex não fornecidos"}), 400

        # Aplica os regex nos dados
        sucesso = []
        nao_identificados = []

        for item in dados:
            item = item.strip()
            identificado = False
            for padrao, descricao in regex.items():
                if re.search(padrao, item):
                    sucesso.append(descricao)
                    identificado = True
                    break  # Garante que cada dado seja mapeado apenas uma vez
            if not identificado:
                nao_identificados.append(item)

        # Concatena os resultados em strings únicas
        sucesso_str = ", ".join(sucesso)
        nao_identificados_str = ", ".join(nao_identificados)

        return jsonify({
            "sucesso": sucesso_str,
            "nao_identificados": nao_identificados_str
        }), 200

    except Exception as e:
        return jsonify({"erro": f"Erro ao processar os dados: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(debug=True)
