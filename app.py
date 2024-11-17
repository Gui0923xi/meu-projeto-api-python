from flask import Flask, request, jsonify
import re

app = Flask(__name__)

# Armazena os regex gerados dinamicamente
regex_map = {}

# Função para gerar regex dinamicamente com base nos dados
def gerar_regex(dados):
    global regex_map
    regex_map = {}  # Limpa o mapa de regex antes de gerar novos
    logs = []  # Lista para armazenar logs de processamento

    for item in dados:
        item = item.lower().strip()  # Normaliza o texto para evitar erros
        log_item = {"faixa": item, "status": "Não processada", "detalhes": ""}

        # Faixas como "Entre R$X e R$Y" ou "De R$X a R$Y"
        if re.search(r"(entre|de)\s*r\$\s?[0-9]+[.,]?[0-9]*\s*(e|a)\s*r\$\s?[0-9]+[.,]?[0-9]*", item):
            match = re.findall(r"(entre|de)\s*r\$\s?([0-9]+[.,]?[0-9]*)\s*(e|a)\s*r\$\s?([0-9]+[.,]?[0-9]*)", item)
            for m in match:
                valor1, valor2 = m[1], m[3]
                regex_key = rf"r\$?\s?{re.escape(valor1)}.*(e|a).*r\$?\s?{re.escape(valor2)}"
                regex_map[regex_key] = f"Entre R${valor1} e R${valor2}"
                log_item["status"] = "Processada"
                log_item["detalhes"] = f"Regex gerado: {regex_key}"

        # "Até R$X" -> "Abaixo de R$X"
        elif re.search(r"até\s*r\$\s?[0-9]+[.,]?[0-9]*", item):
            match = re.findall(r"até\s*r\$\s?([0-9]+[.,]?[0-9]*)", item)
            for m in match:
                regex_key = rf"até\s*r\$\s?{re.escape(m)}"
                regex_map[regex_key] = f"Abaixo de R${m}"
                log_item["status"] = "Processada"
                log_item["detalhes"] = f"Regex gerado: {regex_key}"

        # "Maior que R$X" -> "Acima de R$X"
        elif re.search(r"(maior|acima)\s*que\s*r\$\s?[0-9]+[.,]?[0-9]*", item):
            match = re.findall(r"(maior|acima)\s*que\s*r\$\s?([0-9]+[.,]?[0-9]*)", item)
            for m in match:
                regex_key = rf"(maior|acima)\s*que\s*r\$\s?{re.escape(m[1])}"
                regex_map[regex_key] = f"Acima de R${m[1]}"
                log_item["status"] = "Processada"
                log_item["detalhes"] = f"Regex gerado: {regex_key}"

        # Valores numéricos simples como "R$X"
        elif re.match(r"^r\$\s?[0-9]+[.,]?[0-9]*$", item):
            valor = item.replace("r$", "").strip()
            regex_key = rf"r\$\s?{re.escape(valor)}"
            regex_map[regex_key] = f"Valor específico: R${valor}"
            log_item["status"] = "Processada"
            log_item["detalhes"] = f"Regex gerado: {regex_key}"

        # Caso não corresponda a nenhum padrão
        else:
            log_item["detalhes"] = "Nenhum padrão conhecido foi encontrado."

        logs.append(log_item)

    return regex_map, logs


# Endpoint para atualizar os regex
@app.route('/update-regex', methods=['POST'])
def atualizar_regex():
    try:
        # Recebe os dados enviados pelo cliente
        dados = request.json.get("dados", "").split(",")
        if not dados:
            return jsonify({"erro": "Nenhum dado fornecido"}), 400

        # Gera os regex dinamicamente e obtém os logs
        regex_gerados, logs = gerar_regex(dados)

        # Retorna regex gerados e os logs para análise
        return jsonify({"regex_gerados": regex_gerados, "logs": logs}), 200

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
        logs = []  # Lista para armazenar os logs detalhados

        for item in dados:
            item_original = item.strip()  # Preserva a faixa original para log
            item = item_original.lower()  # Normaliza para comparações (letras minúsculas)
            item = re.sub(r"[.,]", "", item)  # Remove pontos e vírgulas inconsistentes
            item = re.sub(r"\s+", " ", item)  # Remove espaços extras

            identificado = False
            log_item = {"faixa": item_original, "status": "Não identificado", "detalhes": ""}

            for padrao, descricao in regex.items():
                if re.search(padrao, item):
                    sucesso.append(descricao)
                    log_item["status"] = "Identificado"
                    log_item["detalhes"] = f"Regex aplicado: {padrao}, Descrição: {descricao}"
                    identificado = True
                    break  # Garante que cada dado seja mapeado apenas uma vez

            if not identificado:
                nao_identificados.append(item_original)
                if not re.search(r"r\$?\d+", item):
                    log_item["detalhes"] = "Faixa não contém valores monetários claros."
                elif not re.search(r"até|maior|acima|entre|menor|abaixo", item):
                    log_item["detalhes"] = "Faixa não contém palavras-chave identificáveis."
                else:
                    log_item["detalhes"] = "Faixa não corresponde a nenhum regex fornecido."

            logs.append(log_item)

        # Retorna o log detalhado e os resultados
        return jsonify({
            "sucesso": sucesso,
            "nao_identificados": nao_identificados,
            "logs": logs
        }), 200

    except Exception as e:
        return jsonify({"erro": f"Erro ao processar os dados: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(debug=True)
