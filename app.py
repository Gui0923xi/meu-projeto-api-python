from flask import Flask, request, jsonify
import re

app = Flask(__name__)

# Armazena os regex gerados dinamicamente
regex_map = {}

# Função para dividir texto separado por vírgula em lista
def split_text(text):
    return [item.strip() for item in text.split(",") if item.strip()]

# Endpoint para processar os dados utilizando regex fornecido
@app.route('/process', methods=['POST'])
def processar_dados():
    try:
        # Recebe os dados e regex enviados pelo cliente como texto separado por vírgulas
        dados_raw = request.json.get("dados", "")
        regex_raw = request.json.get("regex", "")
        if not dados_raw or not regex_raw:
            return jsonify({"erro": "Dados ou regex não fornecidos"}), 400

        # Divide os dados em itens separados por vírgula
        dados = split_text(dados_raw)

        # Converte o regex de texto para um dicionário
        regex_map = {}
        regex_list = split_text(regex_raw)
        for pair in regex_list:
            if ":" in pair:
                key, value = pair.split(":", 1)
                regex_map[key.strip().strip('"')] = value.strip().strip('"')

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
