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

        # Prioriza faixas "Entre R$X e R$Y"
        if re.search(r"r\$[0-9]+[.,]?[0-9]*_a_r\$[0-9]+[.,]?[0-9]*", item):
            match = re.findall(r"r\$[0-9]+[.,]?[0-9]*_a_r\$[0-9]+[.,]?[0-9]*", item)
            for m in match:
                if m not in regex_map:  # Evita duplicatas
                    valor1, valor2 = m.replace("r$", "").replace("_a_", " ").split(" ")
                    regex_map[rf"{re.escape(m)}"] = f"Entre R${valor1} e R${valor2}"

        # Trata valores do tipo "maior_que_R$X" -> "Acima de R$X"
        elif re.search(r"maior_que_r\$[0-9]+[.,]?[0-9]*", item):
            match = re.findall(r"maior_que_r\$[0-9]+[.,]?[0-9]*", item)
            for m in match:
                if m not in regex_map:
                    valor = m.replace("maior_que_r$", "")
                    regex_map[rf"{re.escape(m)}"] = f"Acima de R${valor}"

        # Trata valores do tipo "até_R$X" -> "Abaixo de R$X"
        elif re.search(r"até_r\$[0-9]+[.,]?[0-9]*", item):
            match = re.findall(r"até_r\$[0-9]+[.,]?[0-9]*", item)
            for m in match:
                if m not in regex_map:
                    valor = m.replace("até_r$", "")
                    regex_map[rf"{re.escape(m)}"] = f"Abaixo de R${valor}"

        # Trata números soltos como "R$X" -> Adiciona contexto "Abaixo de R$X" (padrão)
        elif re.match(r"^r\$[0-9]+[.,]?[0-9]*$", item):
            if item not in regex_map:
                valor = item.replace("r$", "")
                regex_map[rf"{re.escape(item)}"] = f"Abaixo de R${valor}"

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
