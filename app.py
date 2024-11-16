from flask import Flask, request, jsonify
import re
import json

app = Flask(__name__)

# Função para converter regex de texto separado por vírgula para dicionário
def parse_regex_text_to_dict(regex_text):
    try:
        regex_pairs = regex_text.split(",")
        regex_dict = {}
        for pair in regex_pairs:
            key, value = pair.split(":")
            regex_dict[key.strip().strip('"')] = value.strip().strip('"')
        return regex_dict
    except Exception as e:
        raise ValueError(f"Erro ao converter regex: {str(e)}")

# Endpoint para processar os dados
@app.route('/process', methods=['POST'])
def processar_dados():
    try:
        # Recebe os dados enviados pelo cliente
        dados_raw = request.json.get("dados", [])
        regex_raw = request.json.get("regex", "")
        if not dados_raw or not regex_raw:
            return jsonify({"erro": "Dados ou regex não fornecidos"}), 400

        # Divide os dados em itens separados por vírgula
        dados = []
        for linha in dados_raw:
            if isinstance(linha, str):
                # Divide a linha por vírgula e remove espaços em branco
                dados.extend([item.strip() for item in linha.split(",")])
            else:
                dados.append(linha)

        # Converte regex de texto para dicionário
        try:
            regex_map = parse_regex_text_to_dict(regex_raw)
        except ValueError as e:
            return jsonify({"erro": str(e)}), 400

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
