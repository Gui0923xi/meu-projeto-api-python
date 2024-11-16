from flask import Flask, request, jsonify
import re

app = Flask(__name__)

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

# Endpoint para atualizar os regex
@app.route('/update-regex', methods=['POST'])
def atualizar_regex():
    """
    Recebe uma lista de dados e gera regex dinamicamente.
    """
    try:
        dados = request.json.get("dados", [])
        if isinstance(dados, str):
            dados = [item.strip().lower() for item in dados.split(",")]  # Padroniza os dados

        if not dados or not isinstance(dados, list):
            return jsonify({"erro": "Nenhum dado válido fornecido"}), 400

        regex_gerados = gerar_regex(dados)
        return jsonify(regex_gerados), 200  # Retorna apenas o mapa de regex

    except Exception as e:
        return jsonify({"erro": f"Erro ao atualizar regex: {str(e)}"}), 500

# Endpoint para processar os dados
@app.route('/process', methods=['POST'])
def processar_dados():
    """
    Processa os dados recebidos aplicando os regex enviados na requisição.
    """
    try:
        payload = request.json
        print("Payload recebido:", payload)  # Log do payload recebido

        # Recupera os dados e regex do payload
        dados = payload.get("dados", [])
        regex_map = payload.get("regex", {})

        # Verifica se os dados foram enviados como string (separados por vírgulas)
        if isinstance(dados, str):
            # Converte a string separada por vírgulas em lista e padroniza
            dados = [item.strip().lower() for item in dados.split(",")]

        if not dados or not isinstance(dados, list):
            return jsonify({"erro": "Nenhum dado válido fornecido"}), 400

        if not regex_map or not isinstance(regex_map, dict):
            return jsonify({"erro": "Nenhum regex válido fornecido"}), 400

        # Processa os dados aplicando os regex
        resultados = []
        for item in dados:
            print("Item sendo processado:", item)  # Log do item
            resultado = []
            for padrao, descricao in regex_map.items():
                try:
                    print(f"Aplicando regex: {padrao} ao item: {item}")  # Log do regex aplicado
                    if re.search(padrao, item):
                        resultado.append(descricao)
                except re.error as regex_error:
                    print(f"Erro ao aplicar regex '{padrao}': {regex_error}")
            resultados.append(", ".join(resultado) if resultado else "Faixa não identificada")

        print("Resultados finais:", resultados)  # Log dos resultados finais
        return jsonify({"resultados": resultados}), 200
    except Exception as e:
        print("Erro interno:", e)
        return jsonify({"erro": f"Erro ao processar os dados: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
