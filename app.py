from flask import Flask, request, jsonify
import re
import json

app = Flask(__name__)

# Armazena os regex gerados dinamicamente
regex_map = {}

# Função para gerar regex dinamicamente com base nos dados
def gerar_regex(dados):
    global regex_map
    regex_map = {}

    for item in dados:
        # Detecta faixas numéricas: Exemplo "Entre R$2.801 e R$3.200"
        if re.search(r"r\$[0-9]+[.,]?[0-9]*_a_r\$[0-9]+[.,]?[0-9]*", item):
            match = re.findall(r"r\$[0-9]+[.,]?[0-9]*_a_r\$[0-9]+[.,]?[0-9]*", item)
            for m in match:
                valor1, valor2 = m.replace("r$", "").replace("_a_", " ").split(" ")
                regex_map[rf"{re.escape(m)}"] = f"Entre R${valor1} e R${valor2}"

        # Detecta números soltos com "Até R$X"
        elif re.search(r"até_r\$[0-9]+[.,]?[0-9]*", item, re.IGNORECASE):
            match = re.findall(r"até_r\$[0-9]+[.,]?[0-9]*", item, re.IGNORECASE)
            for m in match:
                valor = m.replace("até_r$", "")
                regex_map[rf"{re.escape(m)}"] = f"Abaixo de R${valor}"

        # Detecta números soltos com "R$X"
        elif re.search(r"r\$[0-9]+[.,]?[0-9]*", item):
            match = re.findall(r"r\$[0-9]+[.,]?[0-9]*", item)
            for m in match:
                valor = m.replace("r$", "")
                regex_map[rf"{re.escape(m)}"] = f"Abaixo de R${valor}"

        # Detecta números soltos com "Maior que R$X"
        elif re.search(r"maior_que_r\$[0-9]+[.,]?[0-9]*", item, re.IGNORECASE):
            match = re.findall(r"maior_que_r\$[0-9]+[.,]?[0-9]*", item, re.IGNORECASE)
            for m in match:
                valor = m.replace("maior_que_r$", "")
                regex_map[rf"{re.escape(m)}"] = f"Maior que R${valor}"

    return regex_map

# Endpoint para atualizar os regex
@app.route('/update-regex', methods=['POST'])
def atualizar_regex():
    try:
        # Recebe os regex enviados pelo cliente como texto separado por vírgulas
        raw_regex = request.json.get("regex", "")
        if not raw_regex:
            return jsonify({"erro": "Nenhum regex fornecido"}), 400

        # Divide o texto em partes separadas por vírgula e converte para dicionário
        regex_str = raw_regex.replace("}{", "},{")  # Ajusta casos sem separação clara
        regex_list = regex_str.split(",")  # Divide pelos delimitadores de vírgula
        regex_dict = json.loads("{" + ",".join(regex_list) + "}")

        global regex_map
        regex_map = regex_dict  # Atualiza o regex_map com o dicionário enviado

        return jsonify({"mensagem": "Regex atualizado com sucesso", "regex": regex_map}), 200

    except Exception as e:
        return jsonify({"erro": f"Erro ao atualizar regex: {str(e)}"}), 500

# Endpoint para processar os dados
@app.route('/process', methods=['POST'])
def processar_dados():
    try:
        # Recebe os dados enviados pelo cliente como texto separado por vírgulas
        dados_raw = request.json.get("dados", [])
        if not dados_raw:
            return jsonify({"erro": "Nenhum dado fornecido"}), 400

        # Divide os dados em itens separados por vírgula
        dados = []
        for linha in dados_raw:
            if isinstance(linha, str):
                # Divide a linha por vírgula e remove espaços em branco
                dados.extend([item.strip() for item in linha.split(",")])
            else:
                dados.append(linha)

        # Verifica se o regex_map está vazio
        if not regex_map:
            return jsonify({"erro": "Nenhum regex configurado. Atualize o regex primeiro."}), 400

        resultados = []
        for item in dados:
            resultado = set()  # Usa um conjunto para evitar duplicação dentro do mesmo item
            for padrao, descricao in regex_map.items():
                if re.search(padrao, item):
                    resultado.add(descricao)
            if not resultado:
                resultados.append("Faixa não identificada")
            else:
                resultados.append(", ".join(resultado))  # Converte o conjunto para uma string

        return jsonify({"resultados": resultados}), 200

    except Exception as e:
        return jsonify({"erro": f"Erro ao processar os dados: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
