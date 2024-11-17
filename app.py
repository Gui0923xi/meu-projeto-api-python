from flask import Flask, request, jsonify
import re

app = Flask(__name__)

# Mapeamento direto de valores para transcrição
mapeamento = {
    "até r$2.800": "Abaixo de R$2.800",
    "maior que r$4.000": "Acima de R$4.000"
}

# Regex gerados dinamicamente
regex_map = {}

# Função para limpar os dados
def limpar_dados(dados):
    dados_limpos = []
    for dado in dados:
        dado = dado.strip().lower()  # Remove espaços e normaliza para lowercase
        dado = re.sub(r"[^\w\s.,$]", "", dado)  # Remove caracteres inválidos
        dado = re.sub(r"\s+", " ", dado)  # Normaliza espaços múltiplos
        dados_limpos.append(dado)
    return dados_limpos

# Função para gerar regex dinamicamente
def gerar_regex(dados):
    global regex_map
    regex_map = {}  # Limpa o mapa de regex antes de gerar novos
    logs = []  # Logs para cada faixa processada

    for item in dados:
        log_item = {"faixa": item, "status": "Não processada", "detalhes": ""}

        # Faixas como "Entre R$X e R$Y"
        if re.search(r"(entre|de)\s*r\$\s?[0-9]+[.,]?[0-9]*\s*(e|a)\s*r\$\s?[0-9]+[.,]?[0-9]*", item):
            match = re.findall(r"(entre|de)\s*r\$\s?([0-9]+[.,]?[0-9]*)\s*(e|a)\s*r\$\s?([0-9]+[.,]?[0-9]*)", item)
            for m in match:
                valor1, valor2 = m[1], m[3]
                regex_key = rf"r\$\s?{re.escape(valor1)}.*(e|a).*r\$\s?{re.escape(valor2)}"
                regex_map[regex_key] = f"Entre R${valor1} e R${valor2}"
                log_item["status"] = "Processada"
                log_item["detalhes"] = f"Regex gerado: {regex_key}"

        # "Até R$X"
        elif re.search(r"até\s*r\$\s?[0-9]+[.,]?[0-9]*", item):
            match = re.findall(r"até\s*r\$\s?([0-9]+[.,]?[0-9]*)", item)
            for m in match:
                regex_key = rf"até\s*r\$\s?{re.escape(m)}"
                regex_map[regex_key] = f"Abaixo de R${m}"
                log_item["status"] = "Processada"
                log_item["detalhes"] = f"Regex gerado: {regex_key}"

        # "Maior que R$X"
        elif re.search(r"(maior|acima)\s*que\s*r\$\s?[0-9]+[.,]?[0-9]*", item):
            match = re.findall(r"(maior|acima)\s*que\s*r\$\s?([0-9]+[.,]?[0-9]*)", item)
            for m in match:
                regex_key = rf"(maior|acima)\s*que\s*r\$\s?{re.escape(m[1])}"
                regex_map[regex_key] = f"Acima de R${m[1]}"
                log_item["status"] = "Processada"
                log_item["detalhes"] = f"Regex gerado: {regex_key}"

        else:
            log_item["detalhes"] = "Nenhum padrão conhecido foi encontrado."

        logs.append(log_item)

    return regex_map, logs

# Função para transcrever valores
def transcrever_valores(dados):
    sucesso = []
    nao_identificados = []
    logs = []

    for item in dados:
        item_original = item.strip()
        item_normalizado = item_original.lower().strip()
        resultado = mapeamento.get(item_normalizado)

        log_item = {
            "faixa": item_original,
            "status": "Não identificado" if resultado is None else "Identificado",
            "detalhes": ""
        }

        if resultado:
            sucesso.append(resultado)
            log_item["detalhes"] = "Transcrição realizada com sucesso."
        else:
            # Tratamento de valores específicos
            valor_match = re.match(r"^r\$\s?(\d+[.,]?\d*)$", item_normalizado)
            if valor_match:
                valor = valor_match.group(1).replace(",", ".")
                resultado = f"Abaixo de R${valor}"
                sucesso.append(resultado)
                log_item["status"] = "Identificado"
                log_item["detalhes"] = f"Valor específico tratado automaticamente: {resultado}"
            else:
                nao_identificados.append(item_original)
                log_item["detalhes"] = "Valor não encontrado no mapeamento ou regex."

        logs.append(log_item)

    return sucesso, nao_identificados, logs

# Endpoint para atualizar regex
@app.route('/update-regex', methods=['POST'])
def atualizar_regex():
    try:
        dados = request.json.get("dados", "").split(",")
        if not dados:
            return jsonify({"erro": "Nenhum dado fornecido"}), 400

        dados_limpos = limpar_dados(dados)
        regex_gerados, _ = gerar_regex(dados_limpos)

        return jsonify(regex_gerados), 200
    except Exception as e:
        return jsonify({"erro": f"Erro ao atualizar regex: {str(e)}"}), 500

# Endpoint para processar dados
@app.route('/process', methods=['POST'])
def processar_dados():
    try:
        dados = request.json.get("dados", "").split(",")
        regex = request.json.get("regex", {})

        if not dados or not regex:
            return jsonify({"erro": "Dados ou regex não fornecidos"}), 400

        sucesso = []
        nao_identificados = []
        logs = []

        for item in dados:
            item_original = item.strip()
            identificado = False

            log_item = {
                "faixa": item_original,
                "status": "Não identificado",
                "detalhes": ""
            }

            for padrao, descricao in regex.items():
                if re.search(padrao, item.lower()):
                    sucesso.append(descricao)
                    identificado = True
                    log_item["status"] = "Identificado"
                    log_item["detalhes"] = f"Regex aplicado: {padrao}, Descrição: {descricao}"
                    break

            if not identificado:
                nao_identificados.append(item_original)
                log_item["detalhes"] = "Nenhum regex aplicável encontrado."

            logs.append(log_item)

        return jsonify({
            "sucesso": sucesso,
            "nao_identificados": nao_identificados,
            "logs": logs
        }), 200

    except Exception as e:
        return jsonify({"erro": f"Erro ao processar os dados: {str(e)}"}), 500

# Endpoint para transcrever dados
@app.route('/transcrever', methods=['POST'])
def transcrever():
    try:
        dados = request.json.get("dados", "").split(",")
        if not dados:
            return jsonify({"erro": "Nenhum dado fornecido"}), 400

        sucesso, nao_identificados, logs = transcrever_valores(dados)
        return jsonify({
            "sucesso": sucesso,
            "nao_identificados": nao_identificados,
            "logs": logs
        }), 200

    except Exception as e:
        return jsonify({"erro": f"Erro ao transcrever os valores: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
