from flask import Flask, request, jsonify
import re

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

# Função para dividir texto separado por vírgula em lista
def split_text(text):
    return [item.strip() for item in text.split(",") if item.strip()]

# Endpoint para gerar regex a partir dos dados fornecidos
@app.route('/update-regex', methods=['POST'])
def atualizar_regex():
    try:
        # Recebe os dados enviados pelo cliente como texto separado por vírgulas
        dados_raw = request.json.get("dados", "")
        if not dados_raw:
            return jsonify({"erro": "Nenhum dado fornecido"}), 400

        # Divide o texto em uma lista
        dados = split_text(dados_raw)

        # Gera os regex dinamicamente
        regex_gerados = gerar_regex(dados)

        # Retorna os regex no formato JSON diretamente utilizável no /process
        return jsonify(regex_gerados), 200

    except Exception as e:
        return jsonify({"erro": f"Erro ao atualizar regex: {str(e)}"}), 500

# Endpoint para processar os dados utilizando regex fornecido
@app.route('/process', methods=['POST'])
def processar_dados():
    try:
        # Recebe os dados e regex enviados pelo cliente
        dados_raw = request.json.get("dados", "")
        regex_map = request.json.get("regex", {})
        if not dados_raw or not regex_map:
            return jsonify({"erro": "Dados ou regex não fornecidos"}), 400

        # Divide os dados em itens separados por vírgula
        dados = split_text(dados_raw)

        resultados = []
        for item in dados:
            resultado = set()  # Usa um conjunto para evitar duplicação dentro do mesmo item
            for padrao, descricao in regex_map.items():
                if re.search(padrao, item):
                    resultado.add(descricao)

            # Adiciona somente resultados únicos ao final
            if not resultado:
                resultados.append("Faixa não identificada")
            else:
                resultados.append(", ".join(sorted(resultado)))  # Ordena e junta os resultados únicos

        # Remove duplicações gerais no resultado final
        resultados_unicos = list(dict.fromkeys(resultados))

        return jsonify({"resultados": resultados_unicos}), 200

    except Exception as e:
        return jsonify({"erro": f"Erro ao processar os dados: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
