from flask import Flask, request, jsonify
import re

app = Flask(__name__)

# Armazena os regex gerados dinamicamente
regex_map = {}

# Função para gerar regex dinamicamente com base nos dados
def gerar_regex(dados):
    global regex_map
    novos_regex = {}

    for item in dados:
        # Detecta faixas numéricas: Exemplo "De R$2.001 a R$2.400" ou "Entre R$2.801 e R$3.200"
        if re.search(r"(de|entre)\s*r\$[0-9]+[.,]?[0-9]*\s*(a|e)\s*r\$[0-9]+[.,]?[0-9]*", item, re.IGNORECASE):
            match = re.findall(r"(de|entre)\s*r\$([0-9]+[.,]?[0-9]*)\s*(a|e)\s*r\$([0-9]+[.,]?[0-9]*)", item, re.IGNORECASE)
            for m in match:
                valor1, valor2 = m[1], m[3]
                regex_key = rf"r\$?{re.escape(valor1)}.*(a|e).*r\$?{re.escape(valor2)}"
                novos_regex[regex_key] = f"Entre R${valor1} e R${valor2}"

        # Detecta números soltos com "Até R$X"
        elif re.search(r"até\s*r\$[0-9]+[.,]?[0-9]*", item, re.IGNORECASE):
            match = re.findall(r"até\s*r\$([0-9]+[.,]?[0-9]*)", item, re.IGNORECASE)
            for m in match:
                valor = m
                regex_key = rf"até\s*r\$?{re.escape(valor)}"
                novos_regex[regex_key] = f"Abaixo de R${valor}"

        # Detecta números soltos com "Maior que R$X"
        elif re.search(r"maior\s*que\s*r\$[0-9]+[.,]?[0-9]*", item, re.IGNORECASE):
            match = re.findall(r"maior\s*que\s*r\$([0-9]+[.,]?[0-9]*)", item, re.IGNORECASE)
            for m in match:
                valor = m
                regex_key = rf"maior\s*que\s*r\$?{re.escape(valor)}"
                novos_regex[regex_key] = f"Maior que R${valor}"

        # Detecta valores individuais como "R$X"
        elif re.search(r"r\$[0-9]+[.,]?[0-9]*", item, re.IGNORECASE):
            match = re.findall(r"r\$([0-9]+[.,]?[0-9]*)", item, re.IGNORECASE)
            for m in match:
                valor = m
                regex_key = rf"r\$?{re.escape(valor)}"
                novos_regex[regex_key] = f"Valor R${valor}"

    regex_map.update(novos_regex)
    return novos_regex

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

        # Gera regex para os novos dados
        novos_regex = gerar_regex(dados)

        # Retorna os regex no formato JSON diretamente utilizável no /process
        return jsonify(novos_regex), 200

    except Exception as e:
        print(f"Erro no /update-regex: {str(e)}")
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

        resultados_sucesso = []
        resultados_nao_encontrados = []

        for item in dados:
            matches = []  # Lista para armazenar todas as correspondências para o item
            for padrao, descricao in regex_map.items():
                if re.search(padrao, item):
                    matches.append(descricao)

            # Escolher a correspondência mais específica (priorizando faixas)
            if not matches:
                resultados_nao_encontrados.append(item)
            else:
                # Ordenar correspondências por comprimento (mais específica = mais detalhada)
                matches.sort(key=len, reverse=True)
                resultados_sucesso.append({
                    "dado": item,
                    "faixa": matches[0]  # Escolher a correspondência mais longa/específica
                })

        return jsonify({
            "sucesso": resultados_sucesso,
            "nao_identificados": resultados_nao_encontrados
        }), 200

    except Exception as e:
        return jsonify({"erro": f"Erro ao processar os dados: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
