from flask import Flask, request, jsonify
import re
import logging

app = Flask(__name__)

# Configuração de logs
logging.basicConfig(level=logging.DEBUG)

# Armazena os regex gerados dinamicamente
regex_map = {}

# Função para gerar regex dinamicamente com base nos dados
def gerar_regex(dados_lista):
    regex_gerados = {}
    logs = []

    for item in dados_lista:
        log_item = {"faixa": item, "status": "", "detalhes": ""}
        try:
            item = item.lower().strip()  # Normaliza o texto para evitar erros

            # Faixas como "Entre R$X e R$Y" ou "De R$X a R$Y"
            if re.search(r"(entre|de)\s*r\$[0-9]+[.,]?[0-9]*\s*(e|a)\s*r\$[0-9]+[.,]?[0-9]*", item):
                match = re.findall(r"(entre|de)\s*r\$([0-9]+[.,]?[0-9]*)\s*(e|a)\s*r\$([0-9]+[.,]?[0-9]*)", item)
                for m in match:
                    valor1, valor2 = m[1], m[3]
                    regex_key = rf"r\$?{re.escape(valor1)}.*(e|a).*r\$?{re.escape(valor2)}"
                    regex_gerados[regex_key] = f"Entre R${valor1} e R${valor2}"
                    log_item["status"] = "Processada"
                    log_item["detalhes"] = f"Regex gerado: {regex_key}"

            # "Até R$X" -> "Abaixo de R$X"
            elif re.search(r"até\s*r\$[0-9]+[.,]?[0-9]*", item):
                match = re.findall(r"até\s*r\$([0-9]+[.,]?[0-9]*)", item)
                for m in match:
                    regex_key = rf"até\s*r\$?{re.escape(m)}"
                    regex_gerados[regex_key] = f"Abaixo de R${m}"
                    log_item["status"] = "Processada"
                    log_item["detalhes"] = f"Regex gerado: {regex_key}"

            # "Maior que R$X" -> "Acima de R$X"
            elif re.search(r"(maior|acima)\s*que\s*r\$[0-9]+[.,]?[0-9]*", item):
                match = re.findall(r"(maior|acima)\s*que\s*r\$([0-9]+[.,]?[0-9]*)", item)
                for m in match:
                    regex_key = rf"(maior|acima)\s*que\s*r\$?{re.escape(m[1])}"
                    regex_gerados[regex_key] = f"Acima de R${m[1]}"
                    log_item["status"] = "Processada"
                    log_item["detalhes"] = f"Regex gerado: {regex_key}"

            # "Menor que R$X" -> "Abaixo de R$X"
            elif re.search(r"(menor|abaixo)\s*que\s*r\$[0-9]+[.,]?[0-9]*", item):
                match = re.findall(r"(menor|abaixo)\s*que\s*r\$([0-9]+[.,]?[0-9]*)", item)
                for m in match:
                    regex_key = rf"(menor|abaixo)\s*que\s*r\$?{re.escape(m[1])}"
                    regex_gerados[regex_key] = f"Abaixo de R${m[1]}"
                    log_item["status"] = "Processada"
                    log_item["detalhes"] = f"Regex gerado: {regex_key}"

            # Números soltos como "R$X"
            elif re.match(r"^r\$[0-9]+[.,]?[0-9]*$", item):
                valor = item.replace("r$", "")
                regex_key = rf"r\$?{re.escape(valor)}"
                regex_gerados[regex_key] = f"Abaixo de R${valor}"
                log_item["status"] = "Processada"
                log_item["detalhes"] = f"Regex gerado: {regex_key}"

            else:
                log_item["status"] = "Não identificado"
                log_item["detalhes"] = "Faixa não corresponde a nenhum padrão conhecido."

        except Exception as e:
            log_item["status"] = "Erro"
            log_item["detalhes"] = f"Erro ao processar: {str(e)}"

        logs.append(log_item)

    return regex_gerados, logs


# Endpoint para atualizar os regex
@app.route('/update-regex', methods=['POST'])
def update_regex():
    try:
        dados = request.json.get("dados", "")
        if not dados:
            return jsonify({"erro": "Nenhum dado fornecido"}), 400

        # Divida os dados em uma lista
        dados_lista = [d.strip() for d in dados.split(",") if d.strip()]
        if not dados_lista:
            return jsonify({"erro": "Lista de dados vazia"}), 400

        # Gere os regex e logs
        regex_gerados, logs = gerar_regex(dados_lista)

        return jsonify({
            "regex": regex_gerados,
            "logs": logs
        }), 200

    except Exception as e:
        return jsonify({"erro": f"Erro no servidor: {str(e)}"}), 500


# Endpoint para processar os dados
@app.route('/process', methods=['POST'])
def process():
    try:
        dados = request.json.get("dados", "").split(",")
        regex = request.json.get("regex", {})

        if not dados or not regex:
            return jsonify({"erro": "Dados ou regex não fornecidos"}), 400

        # Aplica os regex nos dados
        sucesso = []
        nao_identificados = []
        logs = []

        for item in dados:
            item = item.strip()
            identificado = False
            for padrao, descricao in regex.items():
                if re.search(padrao, item):
                    sucesso.append(descricao)
                    identificado = True
                    break
            if not identificado:
                nao_identificados.append(item)
                logs.append({
                    "faixa": item,
                    "status": "Não identificado",
                    "detalhes": "Nenhum regex aplicável encontrado."
                })

        return jsonify({
            "sucesso": sucesso,
            "nao_identificados": nao_identificados,
            "logs": logs
        }), 200

    except Exception as e:
        return jsonify({"erro": f"Erro no servidor: {str(e)}"}), 500


# Endpoint para transcrever dados diretamente
@app.route('/transcrever', methods=['POST'])
def transcrever():
    try:
        dados = request.json.get("dados", "").split(",")
        transcritos = []
        logs = []

        for item in dados:
            item = item.strip()
            if "r$" in item.lower():
                valor = item.lower().replace("r$", "").strip()
                transcritos.append(f"Abaixo de R${valor}")
                logs.append({
                    "faixa": item,
                    "status": "Transcrito",
                    "detalhes": f"Transcrição realizada para Abaixo de R${valor}"
                })
            else:
                logs.append({
                    "faixa": item,
                    "status": "Não identificado",
                    "detalhes": "Faixa não pôde ser transcrita."
                })

        return jsonify({
            "transcritos": transcritos,
            "logs": logs
        }), 200

    except Exception as e:
        return jsonify({"erro": f"Erro no servidor: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(debug=True)
